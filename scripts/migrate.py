#!/usr/bin/env python3
"""
博通 (Botong) — 数据库迁移管理 CLI

用法:
    python scripts/migrate.py status           # 查看迁移状态
    python scripts/migrate.py create 描述信息   # 生成新迁移文件框架
    python scripts/migrate.py up               # 执行待处理迁移
    python scripts/migrate.py down             # 回滚最后一步（仅新式迁移）
    python scripts/migrate.py history          # 查看历史记录
"""

import os
import sys
import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ─── 配置 ───
MIGRATIONS_DIR = PROJECT_ROOT / "infrastructure" / "persistence" / "migrations" / "versions"
DB_PATH = os.environ.get("TICKETS_DB_PATH", str(PROJECT_ROOT / "tickets.db"))


def _get_db():
    """获取数据库连接"""
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def cmd_status():
    """查看迁移状态"""
    conn = _get_db()
    try:
        # 确保 _schema_version 表存在
        conn.execute("""
            CREATE TABLE IF NOT EXISTS _schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT DEFAULT (datetime('now','localtime')),
                description TEXT
            )
        """)
        conn.commit()

        # 当前版本
        row = conn.execute("SELECT MAX(version) as v FROM _schema_version").fetchone()
        current = row["v"] if row and row["v"] else 0

        # 可用迁移文件
        migration_files = sorted(MIGRATIONS_DIR.glob("v*.py"))

        # 旧式迁移（legacy_db.py 中内联）
        legacy_count = _get_legacy_version()

        print(f"📊 数据库迁移状态")
        print(f"   📁 数据库:      {DB_PATH}")
        print(f"   📌 当前版本:    v{current}")
        print(f"   🏛️  旧式迁移:   v{legacy_count}（legacy_db.py 内联）")
        print(f"   📄 新式迁移文件: {len(migration_files)} 个")

        # 列出新式迁移文件
        if migration_files:
            print(f"\n   新式迁移文件列表:")
            for f in migration_files:
                v = _parse_version(f.name)
                applied = conn.execute(
                    "SELECT 1 FROM _schema_version WHERE version = ?", (v,)
                ).fetchone()
                status = "✅ 已应用" if applied else "⏳ 待执行"
                desc = _get_migration_description(f)
                print(f"      v{v:03d}  {status}  {desc}")

        # 待处理
        new_files = [f for f in migration_files
                     if not conn.execute(
                         "SELECT 1 FROM _schema_version WHERE version = ?",
                         (_parse_version(f.name),)).fetchone()]
        if new_files:
            print(f"\n   ⏳ {len(new_files)} 个迁移待执行: python scripts/migrate.py up")
        else:
            print(f"\n   ✅ 数据库是最新版本")

    finally:
        conn.close()


def cmd_create(description: str):
    """生成新迁移文件"""
    # 查找下一个可用版本号
    existing = sorted(MIGRATIONS_DIR.glob("v*.py"))
    if existing:
        last_v = max(_parse_version(f.name) for f in existing)
    else:
        last_v = _get_legacy_version()

    new_version = last_v + 1
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"v{new_version:03d}_{timestamp}.py"
    filepath = MIGRATIONS_DIR / filename

    # 生成迁移模板
    template = f'''"""
博通 (Botong) — 数据库迁移 v{new_version:03d}
{description}

创建时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

# ─── 迁移信息 ───
VERSION = {new_version}
DESCRIPTION = "{description}"

# ─── 依赖版本（必须先应用的版本） ───
DEPENDS_ON = [{last_v}]


def upgrade(conn):
    """
    执行升级迁移
    
    Args:
        conn: sqlite3.Connection 对象
    """
    # 在这里写你的 DDL 语句
    # 示例:
    # conn.execute("ALTER TABLE tickets ADD COLUMN priority TEXT DEFAULT 'M'")
    pass


def downgrade(conn):
    """
    执行回滚迁移
    
    Args:
        conn: sqlite3.Connection 对象
    """
    # 在这里写回滚语句
    # 示例:
    # conn.execute("ALTER TABLE tickets DROP COLUMN priority")
    pass
'''
    filepath.write_text(template, encoding="utf-8")
    print(f"✅ 已创建迁移文件: {filepath}")
    print(f"   版本: v{new_version:03d}")
    print(f"   描述: {description}")
    print(f"   编辑该文件，在 upgrade() 中写入 DDL 语句")


def cmd_up():
    """执行待处理的迁移"""
    conn = _get_db()
    try:
        migration_files = sorted(MIGRATIONS_DIR.glob("v*.py"))
        pending = []

        for f in migration_files:
            v = _parse_version(f.name)
            applied = conn.execute(
                "SELECT 1 FROM _schema_version WHERE version = ?", (v,)
            ).fetchone()
            if not applied:
                pending.append((v, f))

        if not pending:
            print("✅ 没有待执行的迁移")
            return

        print(f"⏳ 执行 {len(pending)} 个迁移...")
        for v, f in pending:
            desc = _get_migration_description(f)
            print(f"   应用 v{v:03d}: {desc}...", end=" ")

            try:
                # 动态导入迁移模块
                spec = importlib.util.spec_from_file_location(f"migration_v{v:03d}", f)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)

                # 在事务中执行升级
                conn.execute("BEGIN")
                mod.upgrade(conn)
                conn.execute(
                    "INSERT INTO _schema_version (version, description) VALUES (?, ?)",
                    (v, desc))
                conn.commit()
                print("✅")

            except Exception as e:
                conn.rollback()
                print(f"❌ 失败: {e}")
                print(f"   回滚完成，数据库状态未改变")
                return

        print(f"✅ 全部迁移执行完成")

    finally:
        conn.close()


def cmd_down():
    """回滚最后一个新式迁移"""
    conn = _get_db()
    try:
        # 找到最后一个通过新式迁移系统应用的版本
        migration_files = sorted(MIGRATIONS_DIR.glob("v*.py"))
        if not migration_files:
            print("ℹ️  没有可回滚的新式迁移（旧式内联迁移不支持回滚）")
            return

        last_applied = None
        for f in reversed(migration_files):
            v = _parse_version(f.name)
            applied = conn.execute(
                "SELECT * FROM _schema_version WHERE version = ?", (v,)
            ).fetchone()
            if applied:
                last_applied = (v, f, applied["description"])
                break

        if not last_applied:
            print("✅ 没有已应用的新式迁移")
            return

        v, f, desc = last_applied
        print(f"⏳  回滚 v{v:03d}: {desc}...", end=" ")

        try:
            spec = importlib.util.spec_from_file_location(f"migration_v{v:03d}", f)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            conn.execute("BEGIN")
            mod.downgrade(conn)
            conn.execute("DELETE FROM _schema_version WHERE version = ?", (v,))
            conn.commit()
            print("✅")
            print(f"   回滚完成，数据库版本回到 v{v-1:03d}")

        except Exception as e:
            conn.rollback()
            print(f"❌ 回滚失败: {e}")

    finally:
        conn.close()


def cmd_history():
    """查看迁移历史"""
    conn = _get_db()
    try:
        rows = conn.execute(
            "SELECT version, applied_at, description FROM _schema_version ORDER BY version"
        ).fetchall()
        if not rows:
            print("ℹ️  没有迁移记录")
            return

        print(f"📋 迁移历史 (共 {len(rows)} 条)")

        # 确定哪些是新式迁移
        new_style_versions = set()
        for f in MIGRATIONS_DIR.glob("v*.py"):
            new_style_versions.add(_parse_version(f.name))

        for row in rows:
            style = "📄" if row["version"] in new_style_versions else "🏛️"
            print(f"   {style} v{row['version']:03d}  [{row['applied_at']}] {row['description']}")

    finally:
        conn.close()


# ─── 辅助函数 ───

def _parse_version(filename: str) -> int:
    """从文件名解析版本号: v001_xxx.py → 1"""
    match = re.match(r"v(\d+)_", filename)
    if match:
        return int(match.group(1))
    return 0


def _get_migration_description(filepath: Path) -> str:
    """从迁移文件提取描述"""
    content = filepath.read_text(encoding="utf-8")
    # 尝试从模块级变量读取
    match = re.search(r'DESCRIPTION\s*=\s*["\']([^"\']+)["\']', content)
    if match:
        return match.group(1)
    return filepath.name


def _get_legacy_version() -> int:
    """获取 legacy_db.py 中定义的旧式迁移版本"""
    try:
        from infrastructure.persistence.legacy_db import _SCHEMA_VERSION
        return _SCHEMA_VERSION
    except Exception:
        # 尝试从文件解析
        legacy_path = PROJECT_ROOT / "infrastructure" / "persistence" / "legacy_db.py"
        if legacy_path.exists():
            match = re.search(r'_SCHEMA_VERSION\s*=\s*(\d+)', legacy_path.read_text())
            if match:
                return int(match.group(1))
        return 0


# ─── CLI 入口 ───

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "status":
        cmd_status()
    elif command == "create" and len(sys.argv) >= 3:
        cmd_create(" ".join(sys.argv[2:]))
    elif command == "up":
        cmd_up()
    elif command == "down":
        cmd_down()
    elif command == "history":
        cmd_history()
    else:
        print(f"未知命令: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    # CLI 模式下延迟导入
    import importlib.util
    main()
