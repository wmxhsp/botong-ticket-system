---
title: deployment-operations
priority: medium
tags: [deployment, docker, tailscale, backup, monitoring]
maintainer: AI Assistant
version: 1.0.0
read_only_db: false
last_updated: 2026-05-31
related_skills: [mcp-deployment-security]
---

## 简介
部署和运维完整指南：Docker容器化部署、Tailscale远程访问、开机启动配置、日志监控、数据备份策略和故障排查手册。

## 适用场景
- 首次部署系统到服务器
- 配置远程访问和开机自启
- 设置自动备份和监控告警
- 排查系统故障和性能问题

---

## 一、Docker部署配置

### 1.1 Docker Compose配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5053:5053"
    volumes:
      - ./tickets.db:/app/tickets.db
      - ./static/uploads:/app/static/uploads
      - ./logs:/app/logs
    environment:
      - BOTO_PORT=5053
      - BOTO_SECRET_KEY=${BOTO_SECRET_KEY}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

### 1.2 部署步骤

```bash
# 1. 克隆代码
git clone <repository-url>
cd botong-ticket-system

# 2. 配置环境变量
cp .env.example .env
nano .env  # 编辑密钥等敏感信息

# 3. 构建并启动
docker compose up -d

# 4. 查看日志
docker compose logs -f web

# 5. 验证服务
curl http://localhost:5053/api/v1/health
```

---

## 二、Tailscale远程访问

### 2.1 安装Tailscale

```bash
# macOS
brew install tailscale
sudo tailscale up

# Linux
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

### 2.2 配置远程访问

**方式1: 环境变量**
```bash
# .env文件
BOTO_TAILSCALE_HOST=your-machine.tailxxxxx.ts.net
BOTO_HOST=0.0.0.0
```

**方式2: 配置文件**
```bash
cp config/tailscale.example.json config/tailscale.json
# 编辑config/tailscale.json，设置主机名
```

**方式3: 使用启动脚本**
```bash
./scripts/start_tailscale.sh
```

### 2.3 访问地址

- **本地**: http://localhost:5053
- **Tailscale**: http://your-machine.tailxxxxx.ts.net:5053

---

## 三、开机启动配置

### 3.1 macOS

```bash
# 一键安装
./scripts/install-boot.sh

# 或手动安装
cp scripts/com.boto.ticket.system.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.boto.ticket.system.plist

# 查看状态
launchctl list | grep boto
```

### 3.2 Linux (systemd)

```bash
# 配置并安装服务
sed -e "s|%USER%|$(whoami)|g" \
    -e "s|%APP_DIR%|$(pwd)|g" \
    scripts/botong.service | sudo tee /etc/systemd/system/botong.service

# 启用并启动
sudo systemctl daemon-reload
sudo systemctl enable --now botong

# 查看状态
sudo systemctl status botong
```

### 3.3 Windows

```batch
# 直接双击运行
scripts\botong-start.bat

# 或放入启动文件夹
# C:\Users\你的用户名\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
```

---

## 四、日志监控和告警

### 4.1 日志位置

- **应用日志**: `logs/app.log`
- **错误日志**: `logs/error.log`
- **慢查询日志**: `logs/slow_queries.log`
- **Docker日志**: `docker compose logs -f web`

### 4.2 日志轮转配置

```python
# infrastructure/logging.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
```

### 4.3 监控告警

**企业微信机器人告警**:
```python
# infrastructure/messaging/wecom_bot.py
import requests

def send_alert(message: str):
    webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY"
    
    payload = {
        "msgtype": "text",
        "text": {
            "content": f"🚨 系统告警\n{message}"
        }
    }
    
    requests.post(webhook_url, json=payload)
```

**触发场景**:
- 服务宕机
- 数据库连接失败
- 磁盘空间不足（< 10%）
- 错误率超过阈值（> 5%/分钟）

---

## 五、数据备份策略

### 5.1 自动备份脚本

```bash
#!/bin/bash
# scripts/backup_db.sh

BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_FILE="tickets.db"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 复制数据库文件
cp $DB_FILE "$BACKUP_DIR/${DB_FILE}.${DATE}"

# 压缩备份
tar czf "$BACKUP_DIR/tickets_${DATE}.tar.gz" "$BACKUP_DIR/${DB_FILE}.${DATE}"

# 删除原文件
rm "$BACKUP_DIR/${DB_FILE}.${DATE}"

# 清理旧备份（保留最近30天）
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: tickets_${DATE}.tar.gz"
```

### 5.2 定时任务配置

**macOS/Linux (cron)**:
```bash
# 每天凌晨2点备份
0 2 * * * /path/to/scripts/backup_db.sh >> /path/to/logs/backup.log 2>&1
```

**systemd timer**:
```ini
# /etc/systemd/system/botong-backup.timer
[Unit]
Description=Daily database backup

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

### 5.3 备份恢复

```bash
# 列出备份
ls -lh backups/

# 恢复指定备份
tar xzf backups/tickets_20260531_020000.tar.gz -C /tmp/
cp /tmp/tickets.db.20260531_020000 tickets.db

# 重启服务
docker compose restart web
```

---

## 六、故障排查手册

### 6.1 常见问题

**问题1: 服务无法启动**
```bash
# 检查端口占用
lsof -i :5053

# 查看日志
docker compose logs web

# 检查配置文件
cat .env
```

**问题2: 数据库锁定**
```bash
# SQLite WAL模式可能产生锁文件
rm tickets.db-shm tickets.db-wal

# 重启服务
docker compose restart
```

**问题3: 内存泄漏**
```bash
# 监控内存使用
docker stats

# 重启服务释放内存
docker compose restart web
```

**问题4: 磁盘空间不足**
```bash
# 检查磁盘使用
df -h

# 清理日志
find logs/ -name "*.log" -mtime +7 -delete

# 清理Docker
docker system prune -a
```

### 6.2 性能诊断

**慢查询分析**:
```bash
# 查看慢查询日志
tail -n 100 logs/slow_queries.log

# 使用sqlite-botong MCP分析
EXPLAIN QUERY PLAN SELECT * FROM tickets WHERE status = 'open';
```

**API响应时间**:
```bash
# 使用curl测试
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5053/api/v1/tickets

# curl-format.txt内容:
# time_connect: %{time_connect}\n
# time_starttransfer: %{time_starttransfer}\n
# time_total: %{time_total}\n
```

---

## 验收标准

### 部署
- [ ] Docker Compose成功启动所有服务
- [ ] 健康检查端点返回200
- [ ] Tailscale远程访问可用
- [ ] 开机自启配置生效

### 监控
- [ ] 日志正常写入文件
- [ ] 日志轮转配置正确
- [ ] 告警机器人可发送消息

### 备份
- [ ] 自动备份脚本正常运行
- [ ] 定时任务已配置
- [ ] 备份恢复流程测试通过

---

## 常见问题

### Q1: 如何迁移数据到新服务器？
**A**: 
```bash
# 1. 备份旧服务器
./scripts/backup_db.sh

# 2. 传输备份文件
scp backups/tickets_*.tar.gz user@new-server:/path/to/

# 3. 在新服务器恢复
tar xzf tickets_*.tar.gz
cp tickets.db.* tickets.db

# 4. 启动服务
docker compose up -d
```

### Q2: 如何升级系统版本？
**A**: 
```bash
# 1. 备份数据
./scripts/backup_db.sh

# 2. 拉取最新代码
git pull origin main

# 3. 重新构建
docker compose build

# 4. 重启服务
docker compose up -d

# 5. 验证功能
curl http://localhost:5053/api/v1/health
```

### Q3: 如何处理数据库损坏？
**A**: 
```bash
# 1. 停止服务
docker compose down

# 2. 从备份恢复
cp backups/tickets.db.LATEST tickets.db

# 3. 重启服务
docker compose up -d

# 4. 验证数据完整性
```

---

## 相关技能
- **mcp-deployment-security**: MCP服务部署安全配置

## 维护人
AI Assistant

## 最后更新
2026-05-31
