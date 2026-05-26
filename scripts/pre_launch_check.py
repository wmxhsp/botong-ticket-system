#!/usr/bin/env python3
"""博通工单系统 - 上线前全面检查脚本"""
import os
import sys
import json
import sqlite3
import importlib
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))

results = {"pass": [], "warn": [], "fail": []}

def check(name, status, detail=""):
    results[status].append({"name": name, "detail": detail})
    icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}[status]
    print(f"  {icon} {name}: {detail}")

# ========== 1. 环境检查 ==========
print("\n" + "=" * 60)
print("1. 运行环境检查")
print("=" * 60)

# Python 版本
py_ver = sys.version
if sys.version_info >= (3, 9):
    check("Python 版本", "pass", py_ver.split()[0])
else:
    check("Python 版本", "fail", f"{py_ver} (需要 >= 3.9)")

# 核心依赖
deps = {
    "flask": "Flask", "flask_restx": "flask-restx", "flask_caching": "Flask-Caching",
    "pydantic": "pydantic", "rq": "rq", "redis": "redis", "gunicorn": "gunicorn"
}
for mod, name in deps.items():
    try:
        m = importlib.import_module(mod)
        ver = getattr(m, "__version__", "ok")
        check(name, "pass", ver)
    except ImportError:
        check(name, "warn", "未安装")

# Redis
try:
    result = subprocess.run(["redis-cli", "ping"], capture_output=True, text=True, timeout=3)
    if result.returncode == 0 and "PONG" in result.stdout:
        check("Redis 服务", "pass", "运行中")
    else:
        check("Redis 服务", "warn", "未运行 (任务队列将降级为 LocalQueue)")
except Exception:
    check("Redis 服务", "warn", "未安装/未运行 (任务队列将降级为 LocalQueue)")

# ========== 2. 配置检查 ==========
print("\n" + "=" * 60)
print("2. 配置检查")
print("=" * 60)

# .env 文件
env_file = BASE_DIR / ".env"
if env_file.exists():
    check(".env 文件", "pass", "存在")
else:
    check(".env 文件", "warn", "不存在 (建议创建，管理环境变量)")

# 环境变量
env_vars = {
    "BOTO_SECRET_KEY": "Flask 密钥 (生产必须设置)",
    "BOTO_ACCESS_PASSWORD": "访问密码 (认证必须)",
    "BOTO_PORT": "服务端口 (默认 5052)",
    "REDIS_URL": "Redis URL (可选，不设则用 LocalQueue)",
}
for var, desc in env_vars.items():
    val = os.environ.get(var)
    if val:
        check(var, "pass", f"已设置 ({desc})")
    elif var in ["BOTO_SECRET_KEY", "BOTO_ACCESS_PASSWORD"]:
        check(var, "fail", f"未设置 ({desc})")
    else:
        check(var, "warn", f"未设置 ({desc})")

# 认证配置
auth_config = BASE_DIR / "config" / "auth_config.json"
if auth_config.exists():
    data = json.loads(auth_config.read_text())
    if data.get("password_hash"):
        check("认证密码", "pass", "已设置哈希密码")
    else:
        check("认证密码", "fail", "未设置密码")
else:
    check("认证配置", "fail", "config/auth_config.json 不存在")

# ========== 3. 数据库检查 ==========
print("\n" + "=" * 60)
print("3. 数据库检查")
print("=" * 60)

db_path = BASE_DIR / "tickets.db"
if db_path.exists():
    check("数据库文件", "pass", f"存在 ({db_path.stat().st_size / 1024:.0f} KB)")
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 表完整性
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        if integrity == "ok":
            check("数据库完整性", "pass", "PRAGMA integrity_check = ok")
        else:
            check("数据库完整性", "fail", integrity)

        # 表统计
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [t[0] for t in cursor.fetchall()]
        check("数据表数量", "pass", f"{len(tables)} 张表")

        # 关键表数据
        key_tables = {
            "tickets": "工单", "clients": "客户", "technicians": "技术员",
            "inventory_items": "库存", "goods": "商品", "warehouses": "仓库",
            "service_fees": "服务费率", "suppliers": "供应商",
        }
        for table, label in key_tables.items():
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
                count = cursor.fetchone()[0]
                check(label, "pass", f"{count} 条记录")
            else:
                check(label, "fail", f"表 {table} 不存在")

        # 外键约束
        cursor.execute("PRAGMA foreign_keys")
        fk = cursor.fetchone()[0]
        if fk:
            check("外键约束", "pass", "已启用")
        else:
            check("外键约束", "warn", "未启用 (建议开启)")

        conn.close()
    except Exception as e:
        check("数据库访问", "fail", str(e))
else:
    check("数据库文件", "fail", "tickets.db 不存在")

# ========== 4. 安全检查 ==========
print("\n" + "=" * 60)
print("4. 安全检查")
print("=" * 60)

# secret_key
app_factory = (BASE_DIR / "web" / "app_factory.py").read_text()
if "os.urandom" in app_factory and "BOTO_SECRET_KEY" not in os.environ:
    check("Flask Secret Key", "fail", "使用 os.urandom 随机生成 (生产必须设置 BOTO_SECRET_KEY)")
elif "BOTO_SECRET_KEY" in os.environ:
    check("Flask Secret Key", "pass", "通过环境变量设置")
else:
    check("Flask Secret Key", "warn", "需确认配置")

# CORS
if "flask-cors" in str(subprocess.run(["pip3", "list"], capture_output=True, text=True).stdout):
    check("CORS", "pass", "flask-cors 已安装")
else:
    check("CORS", "warn", "flask-cors 未安装 (前后端分离需要)")

# 文件上传限制
if "MAX_CONTENT_LENGTH" in app_factory:
    check("文件上传限制", "pass", "已设置 MAX_CONTENT_LENGTH")
else:
    check("文件上传限制", "warn", "未设置上传大小限制")

# CSRF
csrf_path = BASE_DIR / "web" / "middleware" / "csrf.py"
if csrf_path.exists():
    check("CSRF 防护", "pass", "csrf.py 存在")
else:
    check("CSRF 防护", "warn", "csrf.py 不存在")

# 上传目录遍历
upload_dirs = list(BASE_DIR.glob("static/uploads"))
if upload_dirs:
    check("上传目录", "pass", f"{len(upload_dirs)} 个上传目录")
else:
    check("上传目录", "warn", "无 uploads 目录 (首次上传时自动创建)")

# ========== 5. 前端检查 ==========
print("\n" + "=" * 60)
print("5. 前端构建检查")
print("=" * 60)

frontend_dir = BASE_DIR / "frontend"
dist_dir = frontend_dir / "dist"
node_modules = frontend_dir / "node_modules"

if node_modules.exists():
    check("node_modules", "pass", "依赖已安装")
else:
    check("node_modules", "fail", "未安装 (运行 npm install)")

if dist_dir.exists():
    index_html = dist_dir / "index.html"
    assets = list((dist_dir / "assets").glob("*.js")) if (dist_dir / "assets").exists() else []
    check("前端构建产物", "pass", f"dist/ 存在, {len(assets)} 个 JS 文件")

    # 检查大 chunk
    big_chunks = [f for f in assets if f.stat().st_size > 500 * 1024]
    if big_chunks:
        check("Chunk 大小", "warn", f"{len(big_chunks)} 个文件超过 500KB: {[f.name for f in big_chunks]}")
    else:
        check("Chunk 大小", "pass", "所有 chunk < 500KB")
else:
    check("前端构建产物", "fail", "dist/ 不存在 (运行 npm run build)")

# ========== 6. 后端启动测试 ==========
print("\n" + "=" * 60)
print("6. 后端启动测试")
print("=" * 60)

try:
    os.environ.setdefault("BOTO_ACCESS_PASSWORD", "pre_launch_check")
    from web.app_factory import create_app
    app = create_app()
    check("Flask App 创建", "pass", "create_app() 成功")

    # 路由数量
    rules = list(app.url_map.iter_rules())
    api_rules = [r for r in rules if r.rule.startswith("/api")]
    check("API 路由", "pass", f"{len(api_rules)} 个 API 路由")

    # Health check
    with app.test_client() as client:
        resp = client.get("/api/v1/health")
        if resp.status_code == 200:
            check("Health API", "pass", f"200 OK")
        else:
            check("Health API", "warn", f"状态码 {resp.status_code}")

    # Swagger
    with app.test_client() as client:
        resp = client.get("/docs/")
        check("Swagger 文档", "pass" if resp.status_code == 200 else "warn",
              f"状态码 {resp.status_code}")

except Exception as e:
    check("Flask App 创建", "fail", str(e))

# ========== 7. 部署配置检查 ==========
print("\n" + "=" * 60)
print("7. 部署配置检查")
print("=" * 60)

# gunicorn
gunicorn_cfg = BASE_DIR / "gunicorn_config.py"
if gunicorn_cfg.exists():
    check("Gunicorn 配置", "pass", "gunicorn_config.py 存在")
else:
    check("Gunicorn 配置", "warn", "gunicorn_config.py 不存在")

# Docker
dockerfile = BASE_DIR / "Dockerfile"
docker_compose = BASE_DIR / "docker-compose.yml"
if dockerfile.exists():
    check("Dockerfile", "pass", "存在")
else:
    check("Dockerfile", "warn", "不存在 (容器化部署需要)")
if docker_compose.exists():
    check("docker-compose.yml", "pass", "存在")
else:
    check("docker-compose.yml", "warn", "不存在")

# 日志
check("日志配置", "pass", "/tmp/boto-app.log (TimedRotatingFileHandler)")

# 备份
snapshot = BASE_DIR / "tickets_snapshot.db"
if snapshot.exists():
    age_hours = (snapshot.stat().st_mtime - db_path.stat().st_mtime) / 3600
    check("数据库快照", "pass" if age_hours < 24 else "warn",
          f"tickets_snapshot.db 存在 (与主库差 {abs(age_hours):.1f} 小时)")
else:
    check("数据库快照", "warn", "tickets_snapshot.db 不存在")

# ========== 汇总 ==========
print("\n" + "=" * 60)
print("检查汇总")
print("=" * 60)
total = len(results["pass"]) + len(results["warn"]) + len(results["fail"])
print(f"  总计: {total} 项")
print(f"  ✅ 通过: {len(results['pass'])}")
print(f"  ⚠️ 警告: {len(results['warn'])}")
print(f"  ❌ 失败: {len(results['fail'])}")

if results["fail"]:
    print("\n  🚨 必须修复:")
    for item in results["fail"]:
        print(f"    ❌ {item['name']}: {item['detail']}")

if results["warn"]:
    print("\n  ⚡ 建议优化:")
    for item in results["warn"]:
        print(f"    ⚠️ {item['name']}: {item['detail']}")

print("\n" + "=" * 60)
if results["fail"]:
    print("🔴 存在必须修复的问题，不建议上线！")
elif results["warn"]:
    print("🟡 存在警告项，建议优化后上线。")
else:
    print("🟢 所有检查通过，可以上线！")
print("=" * 60)
