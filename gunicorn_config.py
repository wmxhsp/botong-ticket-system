import os

bind = f"0.0.0.0:{os.environ.get('BOTO_PORT', '5053')}"
workers = int(os.environ.get('BOTO_WORKERS', '2'))
threads = int(os.environ.get('BOTO_THREADS', '4'))
timeout = 120
keepalive = 5
preload_app = True

accesslog = os.environ.get('BOTO_ACCESS_LOG', '-')
errorlog = os.environ.get('BOTO_ERROR_LOG', '-')
loglevel = os.environ.get('BOTO_LOG_LEVEL', 'info')


def on_starting(server):
    pass


def post_fork(server, worker):
    from infrastructure.persistence.legacy_db import init_db
    init_db()
