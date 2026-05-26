"""
博通 (Botong) v3.0 — Flask 应用入口

使用 create_app() 工厂模式，职责拆分到:
  - web/app_factory.py  — 应用工厂（中间件/DI/路由注册）
  - web/auth_routes.py  — 认证路由（登录/登出/改密）
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app_factory import create_app

app = create_app()

if __name__ == "__main__":
    debug_enabled = os.environ.get("BOTO_DEBUG", "0") == "1"

    queue_type = "LocalQueue"
    try:
        from infrastructure.di.container import Container
        q = Container.resolve("queue")
        if q:
            queue_type = type(q).__name__
    except Exception:
        pass

    print("=" * 50)
    print("🚀 博通 (Botong) v3.0 启动中...")
    print("📂 数据源: tickets.db")
    print(f"🏗️  架构: DI容器 + 事件驱动 + {queue_type}")
    print("⏰ 提醒调度: RQ 任务队列")
    print("🔒 认证: HMAC 签名 + Cookie 自动续期")
    port = int(os.environ.get("BOTO_PORT", app.config.get("BOTO_PORT", 5053)))
    print(f"🌐 本地访问: http://localhost:{port}")
    print(f"🔧 调试模式: {'开' if debug_enabled else '关'}")
    print(f"📖 API 文档: http://localhost:{port}/docs")
    print(f"🔍 健康检查: http://localhost:{port}/api/v1/health")
    print("=" * 50)

    try:
        app.run(debug=debug_enabled, host="0.0.0.0", port=port, use_reloader=debug_enabled)
    except OSError as e:
        print(f"❌ 端口 {port} 已被占用！请先关闭原有进程。")
        print(f"   错误: {e}")