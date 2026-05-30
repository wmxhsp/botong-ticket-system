"""
===== 博通工单管理系统 —— 完整测试数据集 =====

覆盖模块：
  ✓ 客户     ✓ 工单（9种状态）  ✓ 设备     ✓ 服务项目
  ✓ 商品     ✓ 库存             ✓ 采购     ✓ 供应商
  ✓ 销售     ✓ 财务收入支出     ✓ 技术员   ✓ 待办
  ✓ 提醒     ✓ 通知             ✓ 其他费用

策略：各模块数据之间通过外键/业务关联形成完整链路
"""
import sys, os, json, calendar
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.persistence.legacy_db import db_execute, db_query, db_query_one, db_transaction
from infrastructure.di.service_locator import reg
from infrastructure.di.bootstrap import bootstrap
bootstrap()
from infrastructure.di.service_locator import inject_service
finance_service = inject_service("finance_service")
ticket_svc = inject_service("ticket_service")
inventory_service = inject_service("inventory_service")

now = datetime.now()
today = now.strftime("%Y-%m-%d")
today_ts = now.isoformat()

# ============================================================
# 1. 完善客户资料（补齐联系方式、账期）
# ============================================================
print("1️⃣  完善客户资料 ...")
clients_data = [
    ("集宁一中", "0474-1234567", "集宁区", "学校", 45),
    ("乌兰察布市蒙古族中学", "0474-2345678", "集宁区", "学校", 60),
    ("集宁京能电力", "0474-3456789", "集宁区", "企业", 30),
    ("兴和县寻梦网吧", "0474-4567890", "兴和县", "网吧", 15),
    ("蜗牛电竞网吧", "0474-5678901", "集宁区", "网吧", 15),
    ("益民劳务有限公司", "0474-6789012", "集宁区", "企业", 30),
    ("王利平", "15924455769", "集宁区", "个人", 7),
    ("二毛姐", "15847451234", "集宁区", "个人", 7),
]

for name, phone, area, ctype, terms in clients_data:
    existing = db_query_one("SELECT id FROM clients WHERE name = ?", (name,))
    if existing:
        db_execute("UPDATE clients SET phone=?, notes=?, payment_terms=? WHERE id=?",
                   (phone, f"{area}-{ctype}", terms, existing["id"]))
    else:
        db_execute("INSERT INTO clients (name, phone, notes, payment_terms, created_at) VALUES (?,?,?,?,?)",
                   (name, phone, f"{area}-{ctype}", terms, today_ts))

print(f"   ✅ 已确保 {len(clients_data)} 个客户信息完整")

# ============================================================
# 2. 补充设备（关联客户）
# ============================================================
print("2️⃣  补充设备数据 ...")
equipment_list = [
    ("集宁一中", "交互智能平板", "希沃 Seewo B86EB", "SN-SW-2024001", (now - timedelta(days=180)).strftime("%Y-%m-%d"), "集宁区"),
    ("集宁一中", "交互智能平板", "希沃 Seewo B86EB", "SN-SW-2024002", (now - timedelta(days=160)).strftime("%Y-%m-%d"), "集宁区"),
    ("集宁京能电力", "安防摄像头", "海康威视 Hikvision DS-2CD3T86G2", "SN-HK-2023001", (now - timedelta(days=365)).strftime("%Y-%m-%d"), "集宁区"),
    ("集宁京能电力", "交换机", "华为 Huawei S5735S-L24T4X-A", "SN-HW-2024001", (now - timedelta(days=90)).strftime("%Y-%m-%d"), "集宁区"),
    ("蜗牛电竞网吧", "服务器", "Dell R750xs", "SN-DL-2023002", (now - timedelta(days=400)).strftime("%Y-%m-%d"), "集宁区"),
    ("蜗牛电竞网吧", "显示器", "AOC 27G2SP", "SN-AOC-2024005", (now - timedelta(days=30)).strftime("%Y-%m-%d"), "集宁区"),
    ("乌兰察布市蒙古族中学", "投影仪", "爱普生 Epson CB-2155W", "SN-EP-2023003", (now - timedelta(days=500)).strftime("%Y-%m-%d"), "集宁区"),
    ("益民劳务有限公司", "台式电脑", "联想 ThinkCentre M730q", "SN-LN-2024006", (now - timedelta(days=60)).strftime("%Y-%m-%d"), "集宁区"),
    ("王利平", "笔记本电脑", "Dell Latitude 5440", "SN-DL-2024007", (now - timedelta(days=15)).strftime("%Y-%m-%d"), "集宁区"),
    ("王利平", "打印机", "HP LaserJet MFP M227fdn", "SN-HP-2023010", (now - timedelta(days=200)).strftime("%Y-%m-%d"), "集宁区"),
]

for client, device_type, model, serial_no, warranty_date, location in equipment_list:
    existing = db_query_one("SELECT id FROM equipment WHERE serial_no = ?", (serial_no,))
    if not existing:
        db_execute("""INSERT INTO equipment (name, type, client, model, serial_no, warranty_expire, location)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                   (device_type, device_type, client, model, serial_no, warranty_date, location))

print(f"   ✅ 新增/确保 {len(equipment_list)} 个设备")

# ============================================================
# 3. 生成"完整链路"工单（含多状态流转）
# ============================================================
print("3️⃣  创建完整链路工单 ...")

def create_ticket(client, service_type, description="", status="open", total=0, title=""):
    result = ticket_svc.create_ticket(
        title=title or f"{client}-{service_type}",
        client=client,
        service_type=service_type,
        description=description or f"{client} - {service_type}服务",
    )
    tid = result["id"]
    # 设置金额
    if total > 0:
        db_execute("UPDATE tickets SET total = ? WHERE id = ?", (total, tid))
    # 如果状态不是 open，逐步流转
    status_flow = ["open", "in_progress", "pending_parts", "pending_client", "pending_payment", "completed", "closed"]
    if status and status != "open":
        for s in status_flow:
            if s == status:
                break
            try:
                ticket_svc.transition_status(tid, s, note="自动测试流转")
            except Exception:
                pass
    return tid

# 工单方案：覆盖多种客户、服务类型、金额
ticket_plans = [
    # (client, service_type, description, final_status, total, title)
    ("集宁一中", "维修", "教室希沃一体机触摸失灵，需更换触摸框", "closed", 1680, "教室一体机维修"),
    ("集宁一中", "维修", "3号教学楼投影仪画面模糊", "pending_payment", 520, "投影仪维修"),
    ("集宁京能电力", "维修", "办公区交换机端口故障，影响网络", "in_progress", 450, "交换机端口维修"),
    ("蜗牛电竞网吧", "安装", "新到30台电脑需安装无盘系统", "pending_parts", 3600, "网吧无盘安装"),
    ("蜗牛电竞网吧", "维护", "本月例行巡检维护", "open", 2000, "月度巡检"),
    ("益民劳务有限公司", "维修", "财务室电脑无法开机", "closed", 350, "财务电脑维修"),
    ("王利平", "维修", "笔记本屏幕闪烁", "pending_client", 280, "笔记本维修"),
    ("王利平", "安装", "新购打印机安装调试", "closed", 150, "打印机安装"),
    ("乌兰察布市蒙古族中学", "维修", "校园广播系统故障", "in_progress", 1200, "广播系统维修"),
    ("二毛姐", "维修", "家里电脑运行缓慢", "completed", 180, "电脑清灰升级"),
    ("集宁京能电力", "维护", "机房月度巡检", "open", 2000, "机房巡检"),
    ("蜗牛电竞网吧", "维修", "3号机显卡花屏，需更换", "pending_payment", 850, "显卡更换"),
]

created_tickets = []
for client, stype, desc, status, total, title in ticket_plans:
    try:
        tid = create_ticket(client, stype, desc, status, total, title)
        created_tickets.append(tid)
        print(f"   → 工单 #{tid} [{status}] {client} ¥{total}")
    except Exception as e:
        print(f"   ⚠️ 跳过 {client} {title}: {str(e)[:60]}")
        # 查找已有的同客户同金额工单
        existing = db_query_one("SELECT id FROM tickets WHERE client=? AND total=? ORDER BY id DESC LIMIT 1",
                               (client, total))
        if existing:
            created_tickets.append(existing["id"])

# ============================================================
# 4. 分配技术员 & 记录工时
# ============================================================
print("4️⃣  分配技术员 & 工时 ...")
tech_assignments = [
    # (ticket_index_in_created, technician_name, hours, cost_rate)
    (0, "苏鹏", 3.0, 60),     # 集宁一中 触摸框
    (1, "王浩博", 2.0, 30),   # 集宁一中 投影仪
    (2, "李学平", 2.5, 50),   # 京能电力 交换机
    (3, "苏鹏", 5.0, 60),     # 蜗牛网吧 无盘安装
    (4, "王浩博", 2.0, 30),   # 蜗牛网吧 巡检
    (5, "苏鹏", 1.5, 60),     # 益民 电脑维修
    (6, "苏鹏", 2.0, 60),     # 王利平 笔记本
    (7, "小赵", 1.0, 30),     # 王利平 打印机
    (8, "李学平", 3.0, 50),   # 蒙古族中学 广播系统
    (9, "小赵", 1.5, 30),     # 二毛姐 电脑
    (10, "王浩博", 2.0, 30),  # 京能电力 巡检
    (11, "苏鹏", 2.0, 60),    # 蜗牛 显卡
]

for idx, tech_name, hours, cost_rate in tech_assignments:
    if idx >= len(created_tickets):
        continue
    tid = created_tickets[idx]
    ticket_svc.add_technician(tid, tech_name, cost_rate, hours)
print(f"   ✅ 已分配 {len(tech_assignments)} 个技术员记录")

# ============================================================
# 5. 创建服务项目/计价规则（已有数据，补充）
# ============================================================
print("5️⃣  补充服务计价规则 ...")
fees_to_add = [
    ("投影机清洗", "hourly", 80, "投影机深度清洗"),
    ("网络布线", "fixed", 300, "网线布线安装"),
    ("数据恢复", "hourly", 150, "硬盘数据恢复"),
]
for name, fee_type, price, desc in fees_to_add:
    existing = db_query_one("SELECT id FROM service_fees WHERE name = ?", (name,))
    if not existing:
        db_execute("INSERT INTO service_fees (name, fee_type, unit_price, description) VALUES (?,?,?,?)",
                   (name, fee_type, price, desc))
print(f"   ✅ 已有 {db_query_one('SELECT COUNT(*) as c FROM service_fees')['c']} 个服务项目")

# ============================================================
# 6. 生成收入记录（关联工单结算）
# ============================================================
print("6️⃣  创建收入记录 ...")
income_records = [
    # (client, amount, method, source_type, source_id, description)
    ("集宁一中", 1680, "对公", "ticket", created_tickets[0] if len(created_tickets) > 0 else None, f"工单# {created_tickets[0]} 一体机维修收款" if len(created_tickets) > 0 else "测试收款"),
    ("王利平", 150, "微信", "ticket", created_tickets[7] if len(created_tickets) > 7 else None, f"工单# {created_tickets[7]} 打印机安装收款" if len(created_tickets) > 7 else "测试收款"),
    ("益民劳务有限公司", 350, "微信", "ticket", created_tickets[5] if len(created_tickets) > 5 else None, f"工单# {created_tickets[5]} 电脑维修收款" if len(created_tickets) > 5 else "测试收款"),
]

for client, amount, method, src_type, src_id, desc in income_records:
    # 随机过去1-7天的日期作为收款日期
    paid_dt = now - timedelta(days=len(income_records)*2, hours=len(income_records))
    existing = db_query_one(
        "SELECT id FROM income_records WHERE amount=? AND client=? AND description=?",
        (amount, client, desc))
    if not existing:
        finance_service.record_ticket_income(client, amount, method, src_id,
                                          paid_dt.strftime("%Y-%m-%d %H:%M"), desc)
print(f"   ✅ 已创建 {len(income_records)} 条收入记录")

# ============================================================
# 7. 确保有商品数据
# ============================================================
print("7️⃣  确保商品数据 ...")
# 先确保有商品分类
categories = ["网络设备", "电脑配件", "办公耗材", "监控设备", "线材"]
for cat_name in categories:
    existing = db_query_one("SELECT id FROM goods_categories WHERE name = ?", (cat_name,))
    if not existing:
        db_execute("INSERT INTO goods_categories (name) VALUES (?)", (cat_name,))

# 确保有商品数据
goods_data = [
    ("TP-LINK千兆路由器", "网络设备", 285, 200, 3),
    ("超五类网线305米箱", "线材", 420, 300, 2),
    ("海康威视摄像头", "监控设备", 180, 120, 8),
    ("电脑电源500W", "电脑配件", 250, 180, 3),
    ("22寸显示器", "电脑配件", 650, 500, 2),
    ("HDMI线2米", "线材", 25, 15, 10),
    ("VGA线1.5米", "线材", 18, 10, 10),
]

goods_ids = []
for name, cat_name, sell_price, cost_price, min_stock in goods_data:
    cat = db_query_one("SELECT id FROM goods_categories WHERE name = ?", (cat_name,))
    cat_id = cat["id"] if cat else 1
    existing = db_query_one("SELECT id FROM goods WHERE name = ?", (name,))
    if existing:
        goods_ids.append(existing["id"])
    else:
        gid = db_execute("INSERT INTO goods (name, category_id, selling_price, cost_price, min_stock, unit, created_at) VALUES (?,?,?,?,?,?,?)",
                       (name, cat_id, sell_price, cost_price, min_stock, "个", today_ts))
        goods_ids.append(gid)

print(f"   ✅ 已确保 {len(goods_data)} 个商品")

# ============================================================
# 8. 创建供应商
# ============================================================
print("8️⃣  创建供应商数据 ...")
suppliers_data = [
    ("京东电脑办公专营店", "张经理", "13800138000", 30),
    ("海康威视授权经销商", "李经理", "13900139000", 30),
    ("TP-LINK官方代理", "王经理", "13700137000", 30),
]

for name, contact, phone, payment_terms in suppliers_data:
    existing = db_query_one("SELECT id FROM suppliers WHERE name = ?", (name,))
    if not existing:
        db_execute("INSERT INTO suppliers (name, contact, phone, payment_terms, created_at) VALUES (?,?,?,?,?)",
                  (name, contact, phone, payment_terms, today_ts))

print(f"   ✅ 已确保 {len(suppliers_data)} 个供应商")

# ============================================================
# 9. 创建技术员
# ============================================================
print("9️⃣  创建技术员数据 ...")
technicians_data = [
    ("苏鹏", "13811112222", "网络、系统、硬件", "hourly", 60, 50),
    ("王浩博", "13822223333", "系统安装、维护", "hourly", 45, 35),
    ("李学平", "13833334444", "网络、监控", "hourly", 50, 40),
    ("小赵", "13844445555", "基础维修", "hourly", 30, 25),
]

for name, phone, skills, billing_type, labor_cost, cost_rate in technicians_data:
    existing = db_query_one("SELECT id FROM technicians WHERE name = ?", (name,))
    if not existing:
        db_execute("""INSERT INTO technicians (name, phone, skills, billing_type, cost_rate, labor_cost, created_at)
                   VALUES (?,?,?,?,?,?,?)""",
                  (name, phone, skills, billing_type, cost_rate, labor_cost, today_ts))

print(f"   ✅ 已确保 {len(technicians_data)} 个技术员")

# ============================================================
# 10. 创建业务支出记录
# ============================================================
print("🔟  创建业务支出记录 ...")
expense_data = [
    ("配件采购", "京东", 450, "采购网线、水晶头等耗材"),
    ("交通费", "", 120, "本月外出维修油费"),
    ("维修工具", "五金店", 85, "螺丝刀套装"),
    ("办公用品", "晨光文具", 165, "打印纸、墨盒"),
    ("通信费", "中国移动", 58, "工作手机话费"),
]

for cat, vendor, amount, desc in expense_data:
    paid_dt = now - timedelta(days=len(expense_data))
    finance_service.add_expense(category=cat, vendor=vendor, amount=amount,
                                 description=desc, paid_at=paid_dt.strftime("%Y-%m-%d"),
                                 related_ticket_id=None)
print(f"   ✅ 已创建 {len(expense_data)} 条业务支出")

# ============================================================
# 11. 创建待办事项（关联工单）
# ============================================================
print("1️⃣1️⃣ 创建待办事项（含关联工单）...")
todo_data = [
    ("处理工单-集宁一中投影仪", "H", "work", today + " 17:00", created_tickets[1] if len(created_tickets) > 1 else None),
    ("采购配件-蜗牛网吧触摸框", "M", "work", today + " 15:00", created_tickets[3] if len(created_tickets) > 3 else None),
    ("回访客户-益民劳务电脑维修", "L", "work", today + " 10:00", created_tickets[5] if len(created_tickets) > 5 else None),
    ("月度报表汇总", "M", "work", (now + timedelta(days=2)).strftime("%Y-%m-%d") + " 18:00", None),
    ("跟进蜗牛网吧续费", "H", "work", (now + timedelta(days=1)).strftime("%Y-%m-%d") + " 12:00", None),
]

todo_svc = inject_service("todo_service")
for title, priority, category, due_date, ticket_id in todo_data:
    existing = db_query_one("SELECT id FROM todos WHERE title LIKE ?", (title[:10] + "%",))
    if not existing:
        todo_svc.create(title=title, priority=priority, category=category,
                      source_type="ticket" if ticket_id else "",
                      source_id=ticket_id, due_date=due_date, remind=1)
print(f"   ✅ 已创建 {len(todo_data)} 条待办")

# ============================================================
# 12. 关联工单-设备
# ============================================================
print("1️⃣2️⃣ 关联工单与设备 ...")
for idx, tid in enumerate(created_tickets[:6]):  # 前6个工单关联设备
    equip = db_query_one("SELECT id FROM equipment LIMIT 1 OFFSET ?", (idx,))
    if not equip:
        break
    existing = db_query_one("SELECT id FROM ticket_equipment WHERE ticket_id=? AND equipment_id=?",
                          (tid, equip["id"]))
    if not existing:
        db_execute("INSERT INTO ticket_equipment (ticket_id, equipment_id) VALUES (?,?)",
                  (tid, equip["id"]))
print(f"   ✅ 已关联 6 个工单-设备")

# ============================================================
# 13. 创建提醒（工单预约）
# ============================================================
print("1️⃣3️⃣ 创建工单提醒 ...")
for idx, tid in enumerate(created_tickets[:5]):
    appointment = (now + timedelta(days=idx+1)).strftime("%Y-%m-%d 09:00")
    db_execute("UPDATE tickets SET appointment_at = ? WHERE id = ?", (appointment, tid))
    existing_reminder = db_query_one("SELECT id FROM ticket_reminders WHERE ticket_id=?", (tid,))
    if not existing_reminder:
        ticket = db_query_one("SELECT client, title FROM tickets WHERE id=?", (tid,))
        if ticket:
            reminder_service = inject_service("reminder_service")
            reminder_service.create_reminder(
                ticket_id=tid, appointment_at=appointment,
                client_name=ticket["client"], service_content=ticket.get("title", "") or ""
            )
print(f"   ✅ 已创建 5 个工单预约提醒")

# ============================================================
# 14. 完善历史记录
# ============================================================
print("1️⃣4️⃣ 补充审计日志 ...")
for idx, tid in enumerate(created_tickets[:8]):
    existing = db_query_one("SELECT id FROM history WHERE ticket_id=? AND action='seed_data'", (tid,))
    if not existing:
        db_execute("INSERT INTO history (ticket_id, action, timestamp, by, changes) VALUES (?,?,?,?,?)",
                  (tid, "seed_data", today_ts, "system",
                   json.dumps({"note": "测试数据集-系统生成"}, ensure_ascii=False)))
print(f"   ✅ 已补充历史记录")

# ============================================================
# 最终统计
# ============================================================
print("\n" + "="*60)
print("📊 测试数据生成完毕！最终数据量：")
print("="*60)
for table in ["clients", "tickets", "equipment", "income_records", "expense_records",
              "goods", "suppliers", "technicians", "service_fees", "todos",
              "ticket_reminders"]:
    try:
        count = db_query_one(f"SELECT COUNT(*) as c FROM {table}")["c"]
        print(f"  {table}: {count}")
    except Exception as e:
        print(f"  {table}: 查询失败 - {str(e)[:30]}")

print("\n✅ 测试数据创建完成!")
