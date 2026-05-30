---
title: database-index-optimization
priority: medium
tags: [database, sqlite, performance, index]
maintainer: AI Assistant
version: 1.0.0
read_only_db: false
---

## 简介
SQLite数据库索引优化指南，通过合理设计复合索引、分析查询计划、维护索引统计信息，显著提升查询性能。

## 适用场景
- 优化工单列表查询性能
- 加速客户搜索和筛选
- 提升统计数据查询速度
- 解决大数据量下的慢查询问题

## 复合索引设计原则

### 1. 最左前缀原则

**原理**: SQLite的B-Tree索引只能从左到右使用，查询条件必须包含索引的最左列才能生效。

**示例**:
```sql
-- 创建复合索引
CREATE INDEX idx_tickets_status_created ON tickets(status, created_at DESC);

-- ✅ 能使用索引
SELECT * FROM tickets WHERE status = 'open' ORDER BY created_at DESC;
SELECT * FROM tickets WHERE status = 'open';

-- ❌ 不能使用索引（缺少最左列status）
SELECT * FROM tickets ORDER BY created_at DESC;
```

**最佳实践**:
- 将等值查询字段放在前面（如status）
- 将范围查询或排序字段放在后面（如created_at）
- 避免在索引列上使用函数或表达式

---

### 2. 选择性高的列优先

**原理**: 选择性（Selectivity）= 不同值的数量 / 总行数。选择性越高，索引效率越好。

**示例**:
```sql
-- tickets表各字段的选择性
-- status: 4个值（open/in_progress/completed/cancelled），选择性低
-- client: 100+个值，选择性高
-- priority: 4个值（L/M/H/U），选择性低
-- created_at: 几乎唯一，选择性最高

-- ✅ 推荐：高选择性列在前
CREATE INDEX idx_tickets_client_status ON tickets(client, status);

-- ❌ 不推荐：低选择性列在前
CREATE INDEX idx_tickets_status_client ON tickets(status, client);
```

---

### 3. 覆盖索引（Covering Index）

**原理**: 如果索引包含了查询所需的所有字段，SQLite可以直接从索引中读取数据，无需回表查询。

**示例**:
```sql
-- 查询只需要id、ticket_no、status三个字段
SELECT id, ticket_no, status FROM tickets WHERE status = 'open';

-- 创建覆盖索引（包含所有查询字段）
CREATE INDEX idx_tickets_status_covering ON tickets(status, id, ticket_no);

-- 执行计划显示"USING INDEX"而非"USING INDEX + TABLE"
EXPLAIN QUERY PLAN SELECT id, ticket_no, status FROM tickets WHERE status = 'open';
```

**权衡**: 
- 覆盖索引可大幅提升查询速度
- 但会增加索引大小和维护成本
- 仅对高频查询的关键路径使用

---

## 必需创建的复合索引

### 索引1: 工单状态+时间排序

**用途**: 工单列表页按状态筛选并按时间倒序排列

**SQL**:
```sql
CREATE INDEX IF NOT EXISTS idx_tickets_status_created 
ON tickets(status, created_at DESC);
```

**典型查询**:
```sql
SELECT * FROM tickets 
WHERE status = 'open' 
ORDER BY created_at DESC 
LIMIT 20;
```

**预期收益**: 查询时间从500ms降至50ms以内

---

### 索引2: 客户搜索+多状态筛选

**用途**: 按客户名称搜索并筛选特定状态的工单

**SQL**:
```sql
CREATE INDEX IF NOT EXISTS idx_tickets_client_status 
ON tickets(client, status);
```

**典型查询**:
```sql
SELECT * FROM tickets 
WHERE client LIKE '%张三%' 
AND status IN ('open', 'in_progress');
```

**注意**: LIKE '%xxx%'无法使用前缀索引优化，需考虑全文搜索（FTS5）

---

### 索引3: 结算状态+时间排序

**用途**: 财务统计页面按结算状态筛选

**SQL**:
```sql
CREATE INDEX IF NOT EXISTS idx_tickets_billing_created 
ON tickets(billing_status, created_at DESC);
```

**典型查询**:
```sql
SELECT * FROM tickets 
WHERE billing_status = 'unpaid' 
ORDER BY created_at DESC;
```

---

### 索引4: 技术员+时间范围

**用途**: 统计某技术员的工单数量和收入

**SQL**:
```sql
CREATE INDEX IF NOT EXISTS idx_tickets_technician_date 
ON tickets(technician_id, created_at);
```

**典型查询**:
```sql
SELECT COUNT(*), SUM(total) 
FROM tickets 
WHERE technician_id = 5 
AND created_at >= '2026-05-01' 
AND created_at < '2026-06-01';
```

---

### 索引5: 预约时间+状态

**用途**: 今日待办、明日预约提醒

**SQL**:
```sql
CREATE INDEX IF NOT EXISTS idx_tickets_scheduled_status 
ON tickets(scheduled_at, status);
```

**典型查询**:
```sql
SELECT * FROM tickets 
WHERE scheduled_at >= '2026-05-31 00:00:00' 
AND scheduled_at < '2026-06-01 00:00:00' 
AND status IN ('open', 'in_progress');
```

---

## EXPLAIN QUERY PLAN分析方法

### 1. 基本用法

**语法**:
```sql
EXPLAIN QUERY PLAN <your_query>;
```

**示例**:
```sql
EXPLAIN QUERY PLAN 
SELECT * FROM tickets 
WHERE status = 'open' 
ORDER BY created_at DESC 
LIMIT 20;
```

---

### 2. 解读执行计划

**输出示例A（使用索引）**:
```
QUERY PLAN
`--SEARCH tickets USING INDEX idx_tickets_status_created (status=?)
```
✅ **优秀**: 使用了索引进行查找

---

**输出示例B（全表扫描）**:
```
QUERY PLAN
`--SCAN TABLE tickets
```
❌ **糟糕**: 全表扫描，需要添加索引

---

**输出示例C（使用索引但未覆盖）**:
```
QUERY PLAN
`--SEARCH tickets USING INDEX idx_tickets_status (status=?)
 `--USE TEMP B-TREE FOR ORDER BY
```
⚠️ **一般**: 使用了索引，但排序仍需临时表，需优化索引顺序

---

**输出示例D（索引+回表）**:
```
QUERY PLAN
`--SEARCH tickets USING COVERING INDEX idx_tickets_status_covering (status=?)
```
✅✅ **完美**: 覆盖索引，无需回表

---

### 3. 常见优化模式

**模式1: 添加缺失索引**
```sql
-- 当前：全表扫描
EXPLAIN QUERY PLAN SELECT * FROM tickets WHERE client = '张三';
-- SCAN TABLE tickets

-- 优化：添加索引
CREATE INDEX idx_tickets_client ON tickets(client);

-- 验证：使用索引
EXPLAIN QUERY PLAN SELECT * FROM tickets WHERE client = '张三';
-- SEARCH tickets USING INDEX idx_tickets_client (client=?)
```

---

**模式2: 调整索引列顺序**
```sql
-- 当前：索引未充分利用
CREATE INDEX idx_tickets_created_status ON tickets(created_at, status);
EXPLAIN QUERY PLAN SELECT * FROM tickets WHERE status = 'open' ORDER BY created_at DESC;
-- SCAN TABLE tickets（无法使用索引）

-- 优化：调整列顺序
DROP INDEX idx_tickets_created_status;
CREATE INDEX idx_tickets_status_created ON tickets(status, created_at DESC);

-- 验证：正确使用索引
EXPLAIN QUERY PLAN SELECT * FROM tickets WHERE status = 'open' ORDER BY created_at DESC;
-- SEARCH tickets USING INDEX idx_tickets_status_created (status=?)
```

---

**模式3: 使用覆盖索引避免回表**
```sql
-- 当前：索引+回表
CREATE INDEX idx_tickets_status ON tickets(status);
EXPLAIN QUERY PLAN SELECT id, ticket_no, status FROM tickets WHERE status = 'open';
-- SEARCH tickets USING INDEX idx_tickets_status (status=?)
-- USE TEMP B-TREE FOR id, ticket_no（需要回表）

-- 优化：覆盖索引
DROP INDEX idx_tickets_status;
CREATE INDEX idx_tickets_status_covering ON tickets(status, id, ticket_no);

-- 验证：无需回表
EXPLAIN QUERY PLAN SELECT id, ticket_no, status FROM tickets WHERE status = 'open';
-- SEARCH tickets USING COVERING INDEX idx_tickets_status_covering (status=?)
```

---

## 慢查询日志监控

### 1. 启用SQLite慢查询日志

**方法**: 设置阈值，记录超过该时间的查询

**Python实现** (`infrastructure/persistence/legacy_db.py`):
```python
import time
import logging

logger = logging.getLogger('slow_queries')

class SlowQueryLogger:
    def __init__(self, threshold_ms=100):
        self.threshold_ms = threshold_ms
    
    def execute(self, cursor, query, params=None):
        start_time = time.time()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        if elapsed_ms > self.threshold_ms:
            logger.warning(
                f"Slow query ({elapsed_ms:.2f}ms): {query[:200]} "
                f"params={params}"
            )
        
        return cursor

# 使用
slow_query_logger = SlowQueryLogger(threshold_ms=100)
slow_query_logger.execute(cursor, "SELECT * FROM tickets WHERE status = ?", ("open",))
```

---

### 2. 定期分析慢查询日志

**日志格式**:
```
2026-05-31 10:23:45 WARNING slow_queries: Slow query (234.56ms): SELECT * FROM tickets WHERE client LIKE ? params=('%张三%',)
2026-05-31 10:24:12 WARNING slow_queries: Slow query (156.78ms): SELECT COUNT(*) FROM tickets WHERE created_at >= ? params=('2026-05-01',)
```

**分析脚本** (`scripts/analyze_slow_queries.py`):
```python
import re
from collections import Counter

def analyze_slow_queries(log_file='logs/slow_queries.log'):
    queries = []
    
    with open(log_file, 'r') as f:
        for line in f:
            match = re.search(r'Slow query \((\d+\.\d+)ms\): (.+?) params=', line)
            if match:
                elapsed_ms = float(match.group(1))
                query = match.group(2)
                queries.append((elapsed_ms, query))
    
    # 统计最慢的查询
    queries.sort(key=lambda x: x[0], reverse=True)
    
    print("Top 10 Slowest Queries:")
    for i, (elapsed, query) in enumerate(queries[:10], 1):
        print(f"{i}. {elapsed:.2f}ms - {query[:100]}")
    
    # 统计出现频率最高的查询模式
    query_patterns = Counter(q for _, q in queries)
    print("\nMost Frequent Query Patterns:")
    for pattern, count in query_patterns.most_common(5):
        print(f"  {count}x - {pattern[:100]}")

if __name__ == '__main__':
    analyze_slow_queries()
```

---

## 索引维护策略

### 1. 定期执行ANALYZE

**作用**: 更新SQLite内部统计信息，帮助查询优化器选择更好的执行计划

**SQL**:
```sql
ANALYZE;  -- 分析所有表
ANALYZE tickets;  -- 只分析tickets表
```

**频率建议**:
- 数据量变化超过20%时执行
- 每月至少执行一次
- 批量导入数据后立即执行

**自动化脚本** (`scripts/maintain_indexes.py`):
```python
import sqlite3
import logging

logger = logging.getLogger(__name__)

def maintain_indexes(db_path='tickets.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. 检查索引使用情况
        cursor.execute("""
            SELECT name, tbl_name 
            FROM sqlite_master 
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
        """)
        indexes = cursor.fetchall()
        
        logger.info(f"Found {len(indexes)} indexes")
        
        # 2. 执行ANALYZE
        cursor.execute("ANALYZE")
        logger.info("ANALYZE completed")
        
        # 3. 检查是否有未使用的索引（可选）
        # 需要启用STAT4 pragma
        cursor.execute("PRAGMA stats")
        
    except Exception as e:
        logger.error(f"Index maintenance failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    maintain_indexes()
```

---

### 2. 删除冗余索引

**原则**: 
- 如果已有索引`(a, b)`，则单独索引`(a)`是冗余的
- 如果某个索引从未被使用，应删除以减少写入开销

**检测未使用索引**:
```sql
-- SQLite不直接提供索引使用统计
-- 需要通过应用层日志或EXPLAIN QUERY PLAN手动检查

-- 列出所有索引
SELECT name, tbl_name, sql 
FROM sqlite_master 
WHERE type='index' AND name NOT LIKE 'sqlite_%';
```

**删除冗余索引**:
```sql
-- 假设已有复合索引idx_tickets_status_created
-- 则可以删除单独的status索引
DROP INDEX IF EXISTS idx_tickets_status;
```

---

### 3. 索引碎片整理

**问题**: 频繁增删改导致索引碎片化，影响查询性能

**解决方法**: VACUUM命令重建数据库文件

**SQL**:
```sql
VACUUM;
```

**注意**:
- VACUUM会锁定整个数据库，耗时较长
- 建议在低峰期执行
- 执行前确保有足够的磁盘空间（需要原文件大小的2倍）

**自动化** (`scripts/vacuum_db.py`):
```python
import sqlite3
import os
import time

def vacuum_db(db_path='tickets.db'):
    start_time = time.time()
    
    # 检查可用空间
    db_size = os.path.getsize(db_path)
    free_space = os.statvfs('.').f_bavail * os.statvfs('.').f_frsize
    
    if free_space < db_size:
        raise Exception(f"Insufficient disk space. Need {db_size}, have {free_space}")
    
    conn = sqlite3.connect(db_path)
    try:
        print("Starting VACUUM...")
        conn.execute("VACUUM")
        elapsed = time.time() - start_time
        print(f"VACUUM completed in {elapsed:.2f}s")
        
        new_size = os.path.getsize(db_path)
        print(f"Database size: {db_size} -> {new_size} bytes")
        
    finally:
        conn.close()

if __name__ == '__main__':
    vacuum_db()
```

---

## 全文搜索优化（FTS5）

### 问题: LIKE '%xxx%'无法使用索引

**现状**:
```sql
-- 全表扫描，性能差
SELECT * FROM tickets WHERE client LIKE '%张三%';
```

### 解决方案: 使用FTS5虚拟表

**创建FTS5表**:
```sql
-- 创建全文搜索虚拟表
CREATE VIRTUAL TABLE tickets_fts USING fts5(
  ticket_no,
  client,
  description,
  content='tickets',
  content_rowid='id'
);

-- 同步现有数据
INSERT INTO tickets_fts(rowid, ticket_no, client, description)
SELECT id, ticket_no, client, description FROM tickets;

-- 创建触发器自动同步新增/修改
CREATE TRIGGER tickets_ai AFTER INSERT ON tickets BEGIN
  INSERT INTO tickets_fts(rowid, ticket_no, client, description)
  VALUES (new.id, new.ticket_no, new.client, new.description);
END;

CREATE TRIGGER tickets_ad AFTER DELETE ON tickets BEGIN
  DELETE FROM tickets_fts WHERE rowid = old.id;
END;

CREATE TRIGGER tickets_au AFTER UPDATE ON tickets BEGIN
  UPDATE tickets_fts 
  SET ticket_no = new.ticket_no, 
      client = new.client, 
      description = new.description
  WHERE rowid = old.id;
END;
```

**使用FTS5搜索**:
```sql
-- 快速全文搜索
SELECT t.* 
FROM tickets t
JOIN tickets_fts f ON t.id = f.rowid
WHERE tickets_fts MATCH '张三';

-- 支持前缀搜索
WHERE tickets_fts MATCH '张*';

-- 多字段搜索
WHERE tickets_fts MATCH 'client:张三 OR description:维修';
```

**预期收益**: 搜索时间从500ms降至10ms以内

---

## 验收标准

### 索引创建
- [ ] 5个核心复合索引已创建
- [ ] 所有高频查询都命中索引
- [ ] 无冗余索引

### 性能指标
- [ ] 工单列表查询耗时 < 50ms（1000条数据）
- [ ] 客户搜索耗时 < 100ms
- [ ] 统计数据查询耗时 < 200ms

### 维护机制
- [ ] ANALYZE每月自动执行
- [ ] 慢查询日志持续监控
- [ ] 季度审查索引使用情况

---

## 常见问题

### Q1: 索引越多越好吗？
**A**: 
- 不是。每个索引都会增加写入开销（INSERT/UPDATE/DELETE）
- 一般每张表不超过5-7个索引
- 优先为高频查询路径创建索引

### Q2: 如何判断索引是否生效？
**A**: 
- 使用`EXPLAIN QUERY PLAN`查看执行计划
- 对比添加索引前后的查询时间
- 监控慢查询日志

### Q3: 索引会占用多少空间？
**A**: 
- 索引大小约为原表的10%-30%
- 可通过`SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size();`查看数据库总大小
- 定期VACUUM回收碎片空间

### Q4: FTS5会影响写入性能吗？
**A**: 
- 会。每次INSERT/UPDATE/DELETE都需要同步更新FTS5表
- 但对于读多写少的场景（如搜索），收益远大于成本
- 可通过异步批量同步降低影响

---

## 维护人
AI Assistant

## 最后更新
2026-05-31

## 相关技能
- ticket-system-optimization
- api-response-optimization
