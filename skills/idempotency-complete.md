---
title: idempotency-and-concurrency
priority: high
tags: [idempotent, concurrency, safety, ticket]
maintainer: AI Assistant
version: 1.0.0
last_updated: 2026-05-31
read_only_db: false
---

## 简介

处理 API 幂等键、并发冲突、重试与锁策略，避免重复创建/重复扣减/重复记账。本文档整合了幂等性理论基础和工单场景下的实务操作指南。

## 使用场景

- 审计 `api/v1/tickets.py` 中的幂等逻辑
- 在 `application/services/ticket_service.py` 增加并发保护测试
- 处理重复请求或客户端重试导致的重复创建/收款问题
- 设计幂等键、TTL 与清理策略

## 关注点

### 1. 幂等键设计

**核心原则**：
- **唯一性**：每个业务操作应有唯一的幂等键（如工单创建使用 client_id + timestamp + random）
- **范围控制**：幂等键应在合理的业务范围内唯一（如同一客户同一天内）
- **TTL设置**：设置合理的过期时间（建议24-72小时），避免数据库膨胀
- **清理策略**：定期清理过期的幂等记录（每日凌晨执行）

**实现示例**：
```python
# 生成幂等键
import hashlib
import time

def generate_idempotency_key(client_id: str, action: str) -> str:
    timestamp = int(time.time())
    random_suffix = os.urandom(8).hex()
    raw_key = f"{client_id}:{action}:{timestamp}:{random_suffix}"
    return hashlib.sha256(raw_key.encode()).hexdigest()[:32]
```

### 2. 持久层实现

**数据库表结构**：
```sql
CREATE TABLE idempotency_keys (
    key_hash VARCHAR(64) PRIMARY KEY,
    original_key TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, completed, failed
    response_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_expires_at ON idempotency_keys(expires_at);
```

**检查与设置逻辑**：
```python
def check_idempotent(key: str) -> Optional[dict]:
    """检查幂等键是否已存在且已完成"""
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    record = db.execute(
        "SELECT status, response_data FROM idempotency_keys WHERE key_hash = ? AND expires_at > ?",
        (key_hash, datetime.now())
    ).fetchone()
    
    if record and record['status'] == 'completed':
        return json.loads(record['response_data'])
    return None

def set_idempotent(key: str, response: dict, ttl_hours: int = 48):
    """设置幂等键及响应数据"""
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    expires_at = datetime.now() + timedelta(hours=ttl_hours)
    
    db.execute(
        """INSERT INTO idempotency_keys (key_hash, original_key, status, response_data, expires_at)
           VALUES (?, ?, 'completed', ?, ?)
           ON CONFLICT(key_hash) DO NOTHING""",
        (key_hash, key, json.dumps(response), expires_at)
    )
```

### 3. 并发冲突处理

**完工/收款/库存操作的并发竞态**：

**方案A：乐观锁（推荐）**
```python
# 在 tickets 表添加 version 字段
UPDATE tickets SET status = 'completed', version = version + 1 
WHERE id = ? AND version = ? AND status = 'in_progress'

# 如果影响行数为0，说明已被其他请求修改，抛出并发冲突异常
if cursor.rowcount == 0:
    raise ConcurrencyConflictError("工单已被其他请求处理")
```

**方案B：数据库行级锁**
```python
# 使用 SELECT FOR UPDATE 锁定行
ticket = db.execute(
    "SELECT * FROM tickets WHERE id = ? FOR UPDATE",
    (ticket_id,)
).fetchone()

# 在事务中执行业务逻辑
# ...

# 提交事务后自动释放锁
db.commit()
```

**方案C：应用层分布式锁（Redis）**
```python
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def acquire_lock(resource_id: str, ttl_seconds: int = 10) -> bool:
    lock_key = f"lock:{resource_id}"
    return redis_client.set(lock_key, "1", nx=True, ex=ttl_seconds)

def release_lock(resource_id: str):
    lock_key = f"lock:{resource_id}"
    redis_client.delete(lock_key)
```

### 4. 常见错误与防御模式

**错误1：未检查幂等键直接执行业务逻辑**
```python
# ❌ 错误做法
def create_ticket(data):
    ticket = Ticket(**data)
    db.add(ticket)
    db.commit()
    return ticket

# ✅ 正确做法
def create_ticket(data, idempotency_key):
    # 先检查幂等键
    existing = check_idempotent(idempotency_key)
    if existing:
        return existing  # 返回之前的结果
    
    # 执行业务逻辑
    ticket = Ticket(**data)
    db.add(ticket)
    db.commit()
    
    # 设置幂等键
    set_idempotent(idempotency_key, ticket.to_dict())
    return ticket
```

**错误2：幂等键TTL设置过长**
```python
# ❌ 错误：TTL设置为30天，导致数据库膨胀
set_idempotent(key, response, ttl_hours=720)

# ✅ 正确：根据业务场景设置合理TTL
# 工单创建：48小时
# 支付操作：72小时
# 库存扣减：24小时
set_idempotent(key, response, ttl_hours=48)
```

**错误3：未处理并发冲突**
```python
# ❌ 错误：直接更新，可能覆盖其他请求的修改
db.execute("UPDATE tickets SET status = ? WHERE id = ?", ('completed', ticket_id))

# ✅ 正确：使用乐观锁检测冲突
result = db.execute(
    "UPDATE tickets SET status = ?, version = version + 1 WHERE id = ? AND version = ?",
    ('completed', ticket_id, current_version)
)
if result.rowcount == 0:
    raise ConcurrencyConflictError("工单状态已被修改")
```

## 入口文件/函数

- `application/services/ticket_service.py::check_idempotent` / `set_idempotent`
- `application/services/ticket_service.py::complete_ticket` （包含并发保护）
- `infrastructure/persistence/repositories/ticket_repository.py` （仓储层锁实现）
- `api/v1/tickets.py` （API层幂等键提取与验证）

## 验证用例

### 用例1：幂等键重复请求
```python
# 使用相同 X-Idempotency-Key 多次创建工单只会成功一次
key = "test-idempotency-key-001"
response1 = api.create_ticket(data, idempotency_key=key)
response2 = api.create_ticket(data, idempotency_key=key)

assert response1['id'] == response2['id']  # 返回同一工单
assert Ticket.query.count() == 1  # 数据库中只有一条记录
```

### 用例2：并发完工与收款
```python
# 并发完工与收款不应出现重复支出/重复扣减
import threading

def complete_ticket_concurrently():
    api.complete_ticket(ticket_id)

threads = [threading.Thread(target=complete_ticket_concurrently) for _ in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()

# 验证：只完成一次，无重复扣减
ticket = Ticket.query.get(ticket_id)
assert ticket.status == 'completed'
assert Expense.query.filter_by(ticket_id=ticket_id).count() == 1
```

### 用例3：清理过期幂等记录
```python
# 清理过期幂等记录后新的相同键可再次生效
old_key = "expired-key"
set_idempotent(old_key, {'id': 1}, ttl_hours=1)

# 等待过期（或使用测试工具模拟时间）
time.sleep(3601)

# 清理任务执行
cleanup_expired_idempotency_keys()

# 相同的键可以再次使用
new_response = api.create_ticket(data, idempotency_key=old_key)
assert new_response is not None
```

## 相关技能

- `database-index-optimization.md` - 数据库索引优化（idempotency_keys表索引）
- `security-hardening.md` - 安全性加固（防止幂等键重放攻击）
- `caching-strategies.md` - 缓存策略（幂等键缓存优化）
