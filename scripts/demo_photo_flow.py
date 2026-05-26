#!/usr/bin/env python3
"""演示：把原始图片保存为 raw 文件、入队处理并轮询状态文件直到完成。"""
import os
import sys
import time
import json
from datetime import datetime

# 将项目根加入 sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# 初始化 DI 容器（使用本地回退队列）
from infrastructure.di.bootstrap import bootstrap
bootstrap(flask_app=None, use_events=False, use_cache=False)
from infrastructure.di.container import Container

# 准备目录与示例 raw 文件
ticket_id = 1
now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
base_dir = os.getcwd()
static_dir = os.path.join(base_dir, 'static', 'uploads', 'tickets', str(ticket_id))
os.makedirs(static_dir, exist_ok=True)
raw_path = os.path.join(static_dir, f"raw_{ticket_id}_{now_str}.jpg")
# 写入小的占位二进制文件（并非真实图片，但用于演示）
with open(raw_path, 'wb') as f:
    f.write(b"\xff\xd8\xff\x00" + os.urandom(256))

filename = f"wm_{ticket_id}_{now_str}.jpg"

# 入队任务
from infrastructure.queue.interfaces import Task
queue = Container.resolve('queue')
task = Task(name='tasks.photo_tasks.process_watermark', payload={'raw_path': raw_path, 'ticket_id': ticket_id, 'filename': filename})
# 写入状态文件（模拟 upload 路由行为）
os.makedirs(os.path.join(os.getcwd(), '.data'), exist_ok=True)
status_path = os.path.join(os.getcwd(), '.data', 'photo_task_status.json')
entry = {
    'task_id': task.task_id or f"local-{task.name}-{int(time.time())}",
    'ticket_id': ticket_id,
    'filename': filename,
    'status': 'queued',
    'created_at': datetime.now().isoformat(),
}
with open(status_path, 'a', encoding='utf-8') as sf:
    sf.write(json.dumps(entry, ensure_ascii=False) + "\n")

task_id = queue.enqueue(task)
print('Enqueued task_id:', task_id)

# 轮询状态文件
status_path = os.path.join(os.getcwd(), '.data', 'photo_task_status.json')
start = time.time()
print('Waiting for task to finish (timeout 30s)...')
finished = False
while time.time() - start < 30:
    if os.path.exists(status_path):
        with open(status_path, 'r', encoding='utf-8') as sf:
            lines = [l.strip() for l in sf if l.strip()]
        for l in lines[::-1]:
            try:
                obj = json.loads(l)
            except Exception:
                continue
            if obj.get('ticket_id') == ticket_id and obj.get('filename') == filename and obj.get('status') in ('finished','failed'):
                print('Task status:', obj.get('status'))
                print('Entry:', obj)
                finished = True
                break
    if finished:
        break
    time.sleep(0.5)

if not finished:
    print('Timeout waiting for task. Check logs/queue_failed.log or .data/photo_task_status.json')
else:
    print('Demo finished')
