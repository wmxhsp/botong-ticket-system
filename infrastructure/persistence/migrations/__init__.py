"""
博通 (Botong) — 版本化数据库迁移

新式迁移文件位于 versions/ 目录下，文件命名: v{版本号}_{时间戳}.py

用法:
    python scripts/migrate.py status     # 查看迁移状态
    python scripts/migrate.py create     # 生成新迁移文件
    python scripts/migrate.py up         # 执行待处理迁移
"""
