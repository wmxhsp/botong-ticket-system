# 博通 — 工程实践指南

> 编写: Senior Developer (高级开发工程师)
> 适用范围: 博通 (Botong) 售后管理系统及后续项目

---

## 一、代码质量原则

### 1.1 可读性优先

**坏代码** (猜谜游戏):
```python
def proc(a, b, c=None):
    x = db_q("SELECT * FROM t WHERE id=?", (a,))
    if x and x.get("s") == "open":
        ...
```

**好代码** (自解释):
```python
def activate_ticket(ticket_id: int, operator: str = "") -> Dict:
    """将工单从待处理状态激活为进行中"""
    ticket = db_query_one("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    if not ticket:
        raise TicketNotFoundError(f"工单 #{ticket_id} 不存在")
    if ticket["status"] != "open":
        raise TicketStatusError("只有待处理工单可以激活")
    
    db_execute("UPDATE tickets SET status = 'in-progress' WHERE id = ?", (ticket_id,))
    add_history(ticket_id, "activate", f"由 {operator} 激活")
```

**原则**:
- 变量名用完整英文单词，不用缩写 (`ticket` 而非 `t`, `client` 而非 `c`)
- 函数名用动词开头 (`create_ticket`, `get_status_stats`)
- 每个函数只做一件事，超过 30 行考虑拆分
- 布尔参数不要传裸值 — `process(True)` → `process(is_urgent=True)`

### 1.2 防御性编程

```python
# ❌ 脆弱写法
data = request.get_json()
client = data["client"]
name = client["name"]

# ✅ 防御性写法
data = request.get_json(force=True, silent=True) or {}
client = data.get("client", "")
name = client.get("name", "") if isinstance(client, dict) else ""
```

```python
# ❌ 可能报错
result["items"].append(new_item)

# ✅ 安全写法
if "items" not in result:
    result["items"] = []
result["items"].append(new_item)
```

### 1.3 不要重复造轮子

```python
# ❌ 到处重复的分页逻辑（在 5 个 API 端点里各写一遍）
offset = (page - 1) * per_page
count = conn.execute("SELECT COUNT(*) ...").fetchone()[0]
rows = conn.execute("SELECT ... LIMIT ? OFFSET ?", [per_page, offset])

# ✅ 统一用 Repository 的方法
tickets, total = repo.find_list(filters=filters, page=page, per_page=per_page)
return ApiResponse.paginated(items=tickets, total=total, page=page, per_page=per_page)
```

---

## 二、分层架构规范

### 2.1 职责边界

```
┌─────────────────────────────────────────┐
│  API Layer (api/v1/*.py)                │
│  职责: HTTP 请求/响应、参数校验、路由    │
│  规范: 使用 ApiResponse 统一格式         │
│  禁止: 直接调用 db_query                │
├─────────────────────────────────────────┤
│  Service Layer (application/services/)  │
│  职责: 业务流程编排、领域事件发布        │
│  规范: 接收 DTO/dict，返回 dict          │
│  禁止: 操作 request/response 对象        │
├─────────────────────────────────────────┤
│  Repository Layer (infrastructure/)     │
│  职责: 数据存取、SQL 查询               │
│  规范: 返回 dict/list，不抛业务异常      │
│  禁止: 包含业务逻辑                     │
└─────────────────────────────────────────┘
```

### 2.2 新增功能的正确方式

当需要新功能时，**不要**把代码塞进旧的 `routes/api/xxx.py`。应该：

```python
# Step 1: 新增仓储方法
# infrastructure/persistence/repositories/ticket_repo.py
def find_by_client(self, client: str) -> List[Dict]:
    return db_query("SELECT * FROM tickets WHERE client LIKE ?", (f"%{client}%",))

# Step 2: 新增 Service 方法（含领域事件）
# application/services/ticket_service.py
def search_by_client(self, client: str) -> List[Dict]:
    tickets = self._repo.find_by_client(client)
    for t in tickets:
        t["status_name"] = self.STATUS_NAMES.get(t["status"], t["status"])
    return tickets

# Step 3: 新增 API 端点
# api/v1/tickets.py
@bp_tickets.route("/search")
def search_tickets():
    client = request.args.get("client", "")
    svc = get_service()
    tickets = svc.search_by_client(client)
    return ApiResponse.list_response(items=tickets, total=len(tickets))

# Step 4: 注册路由（如果已注册则跳过）
# infrastructure/di/bootstrap.py 中已自动注册所有 api.v1.* 模块
```

### 2.3 错误处理规范

```python
# API 层：统一错误格式
try:
    ticket = svc.get_ticket(ticket_id)
    return ApiResponse.success(ticket)
except TicketNotFoundError as e:
    return ApiResponse.not_found(str(e))  # → {"code": 404, "success": false, "error": "..."}
except Exception as e:
    logger.error(f"get_ticket error: {e}", exc_info=True)
    return ApiResponse.server_error()       # → {"code": 500, "success": false, "error": "服务器内部错误"}
```

---

## 三、数据库最佳实践

### 3.1 SQL 查询优化

```python
# ❌ N+1 查询问题（查 50 个工单，额外 50 次查询利润）
for t in tickets:
    t["profit"] = db_query_one("SELECT SUM(amount) FROM income WHERE source_id=?", (t["id"],))

# ✅ 一次查询搞定（用 JOIN + GROUP BY）
profits = db_query(f"""
    SELECT t.id,
           COALESCE(i.income, 0) AS income,
           COALESCE(e.expense, 0) AS expense
    FROM tickets t
    LEFT JOIN (SELECT source_id, SUM(amount) as income FROM income_records
               WHERE source_id IN ({placeholders}) GROUP BY source_id) i ON t.id = i.source_id
    LEFT JOIN ...
    WHERE t.id IN ({placeholders})
""")
```

### 3.2 必须加索引的查询模式

```sql
-- 如果看到这样的查询频繁执行，一定要加索引
SELECT * FROM tickets WHERE status = 'open' ORDER BY created_at DESC;
-- 需要: idx_tickets_status + idx_tickets_created

SELECT * FROM tickets WHERE client LIKE '%集宁%';
-- 需要: idx_tickets_client

SELECT * FROM history WHERE ticket_id = 123;
-- 需要: idx_history_ticket（已有）
```

检查缺少索引的方法：
```bash
curl "http://localhost:5052/api/v1/system/maintenance?action=analyze"
```

### 3.3 事务保护

```python
# ❌ 部分写入：收入记录和工单状态更新不在同一事务
db_execute("INSERT INTO income_records ...")
db_execute("UPDATE tickets SET billing_status = 'paid' WHERE id = ?", (id,))
# 如果第二步失败，钱记上了但工单还是未结算

# ✅ 原子操作
with db_transaction() as conn:
    conn.execute("INSERT INTO income_records ...")
    conn.execute("UPDATE tickets SET billing_status = 'paid' WHERE id = ?", (id,))
    conn.execute("INSERT INTO history ...")
    # 全部成功才提交，任何一步失败自动回滚
```

---

## 四、测试规范

### 4.1 必须写测试的场景

```python
# 1. 每个 API 端点至少一个成功路径测试
def test_get_ticket_success(self):
    resp = self.client.get("/api/v1/tickets/1")
    assert resp.status_code == 200

# 2. 每个业务逻辑至少一个边界条件测试
def test_create_ticket_missing_client(self):
    resp = self.client.post("/api/v1/tickets/", json={"content": "test"})
    assert resp.status_code == 400

# 3. 每个状态流转至少一个非法流转测试
def test_transition_invalid(self):
    resp = self.client.put("/api/v1/tickets/1/status", json={"status": "archived"})
    assert resp.status_code == 400  # open 不能直接到 archived
```

### 4.2 测试隔离

```python
# ✅ 每个测试类使用独立的测试数据库
@pytest.fixture(autouse=True)
def setup_db(self):
    """每个测试前重建表，确保无数据污染"""
    db_execute("DELETE FROM tickets")
    db_execute("DELETE FROM history")
    # 插入干净的测试数据
```

### 4.3 新功能的必备验收条件

在合并代码前，确认以下清单：

- [ ] API 返回正确的状态码（200/201/400/404/500）
- [ ] 错误情况返回友好的错误信息
- [ ] 测试覆盖率 > 80%（新增代码）
- [ ] 不做 N+1 查询
- [ ] 涉及写操作的有事务保护
- [ ] 添加了必要的数据库索引
- [ ] 代码通过 pylint/flake8（分数 > 8/10）

---

## 五、常见陷阱

### 5.1 fetch 请求中 Cookie 丢失

```javascript
// ❌ SameSite=Lax + fetch 在某些浏览器不发送 Cookie
fetch('/api/v1/tickets/')

// ✅ 使用绝对路径（同源）并确保 samesite 配置正确
// 后端: resp.set_cookie(..., samesite="Lax")
```

### 5.2 Django/Flask 模板与 JS 模板冲突

```javascript
// ❌ Jinja2 会尝试解析 {{ }}
var data = {{ ticket_data | tojson }};

// ✅ 使用 tojson 过滤器安全输出
var data = {{ ticket_data | tojson }};
```

### 5.3 showToast 签名混淆

```javascript
// ✅ 统一使用: showToast(message, type, duration)
showToast('操作成功', 'success')     // 正确
showToast('加载失败', 'danger')      // 正确
showToast('提示信息', 'info', 3000)  // 自定义时长
```

### 5.4 API 路径冲突

```python
# ❌ 新旧 API 在同一路径冲突（旧 RESTx 优先）
# 旧: routes/api/tickets.py → @ns.route("/") → /api/v1/tickets/
# 新: api/v1/tickets.py → Blueprint → /api/v1/tickets/

# ✅ 新功能用新的 Blueprint 路径
# 新: api/v1/tickets_v2.py → /api/v2/tickets/
# 或确保旧路由不再使用
```

---

## 六、开发工作流

### 6.1 每日开发 checklist

```bash
# 1. 拉取最新代码
git pull

# 2. 运行全部测试，确保通过
cd /path/to/new-ticket-system
python3 -m pytest tests/ -q

# 3. 健康检查
curl http://localhost:5052/api/v1/health

# 4. 开发新功能
#    - 先写 Repository 方法
#    - 再写 Service 业务逻辑  
#    - 最后写 API 端点

# 5. 提交前再次运行测试
python3 -m pytest tests/ -q

# 6. 提交
git add -A
git commit -m "feat: 添加 xxx 功能"
```

### 6.2 发布流程

```bash
# 完整发布检查
bash scripts/health_check.sh          # 系统健康检查
python3 -m pytest tests/ -v           # 全部测试
curl "http://localhost:5052/api/v1/system/maintenance?action=full"  # 数据库维护
```

---

## 七、学习资源

### 7.1 必读

| 主题 | 资源 |
|------|------|
| Python 风格指南 | PEP 8 (Google Python Style Guide) |
| Flask 最佳实践 | Flask 官方文档的 "Patterns for Flask" 章节 |
| SQL 优化 | `EXPLAIN QUERY PLAN` — SQLite 官方文档 |
| 测试 | pytest 官方文档 (fixtures, parametrize, monkeypatch) |

### 7.2 本系统架构文档

| 文档 | 位置 | 内容 |
|------|------|------|
| 架构方案 | `ARCHITECTURE.md` | 总体设计、分层、技术选型 |
| 工程指南 | `docs/engineering-guide.md` | 👈 本文，日常编码规范 |
| 设计系统 | `static/css/design.css` | CSS 变量、组件样式、响应式断点 |

---

> **最后一段话**：代码质量不是靠一个人把关出来的，是靠团队每个人写代码时的习惯。
> 每写一行代码前问自己：**"三个月后的我，或者接手我代码的同事，能一眼看懂这段代码在做什么吗？"**
> 如果答案是否定的，就先花两分钟把它写清楚。
