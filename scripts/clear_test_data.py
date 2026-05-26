#!/usr/bin/env python3
"""
清理数据库所有测试数据，保留表结构
"""
import sqlite3
import os
import shutil
from datetime import datetime
from pathlib import Path

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "tickets.db"

# 检查数据库文件是否存在
if not DB_FILE.exists():
    print(f"❌ 找不到数据库文件: {DB_FILE}")
    exit(1)

print(f"✅ 找到数据库文件: {DB_FILE}")

# 备份数据库
BACKUP_DIR = BASE_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)
BACKUP_FILE = BACKUP_DIR / f"tickets.db.{datetime.now().strftime('%Y-%m-%d_%H%M%S')}"
shutil.copy2(DB_FILE, BACKUP_FILE)
print(f"✅ 已备份数据库到: {BACKUP_FILE}")

# 连接数据库
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# 获取所有表名
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != '_schema_version'")
tables = [row[0] for row in cursor.fetchall()]

print(f"\n📋 找到 {len(tables)} 个表:")
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"   - {table}: {count} 条记录")

# 禁用外键检查以便删除数据
cursor.execute("PRAGMA foreign_keys = OFF")
conn.commit()

print("\n🗑️  开始清空数据...")
for table in tables:
    try:
        cursor.execute(f"DELETE FROM {table}")
        deleted = cursor.rowcount
        print(f"   ✅ {table}: 删除 {deleted} 条记录")
    except Exception as e:
        print(f"   ⚠️ {table}: 删除失败 - {e}")

# 重新启用外键检查
cursor.execute("PRAGMA foreign_keys = ON")
conn.commit()

# 重置自增ID
print("\n🔄 重置自增ID...")
for table in tables:
    try:
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name = ?", (table,))
    except Exception:
        pass

conn.commit()

print("\n✅ 清理完成！")
print("   表结构已保留，所有业务数据已清空")
print(f"   备份文件: {BACKUP_FILE}")

conn.close()
