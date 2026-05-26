"""
===== 博通工单管理系统 — 完整测试数据集 =====

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
from infrastructure.di.service_locator import resolve_service
finance_service = resolve_service("finance_service")
ticket_svc = resolve_service("ticket_service")
inventory_service = resolve_service("inventory_service")

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
    ("集宁一中", "交互智能平板", "Seewo", "B86EB", "SN-SW-2024001", now - timedelta(days=180)),
    ("集宁一中", "交互智能平板", "Seewo", "B86EB", "SN-SW-2024002", now - timedelta(days=160)),
    ("集宁京能电力", "安防摄像头", "Hikvision", "DS-2CD3T86G2", "SN-HK-2023001", now - timedelta(days=365)),
    ("集宁京能电力", "交换机", "Huawei", "S5735S-L24T4X-A", "SN-HW-2024001", now - timedelta(days=90)),
    ("蜗牛电竞网吧", "服务器", "Dell", "R750xs", "SN-DL-2023002", now - timedelta(days=400)),
    ("蜗牛电竞网吧", "显示器", "AOC", "27G2SP", "SN-AOC-2024005", now - timedelta(days=30)),
    ("乌兰察布市蒙古族中学", "投影仪", "Epson", "CB-2155W", "SN-EP-2023003", now - timedelta(days=500)),
    ("益民劳务有限公司", "台式电脑", "Lenovo", "ThinkCentre M730q", "SN-LN-2024006", now - timedelta(days=60)),
    ("王利平", "笔记本电脑", "Dell", "Latitude 5440", "SN-DL-2024007", now - timedelta(days=15)),
    ("王利平", "打印机", "HP", "LaserJet MFP M227fdn", "SN-HP-2023010", now - timedelta(days=200)),
]

for client, device_type, brand, model, sn, install_date in equipment_list:
    c = db_query_one("SELECT id FROM clients WHERE name = ?", (client,))
    if not c:
        continue
    existing = db_query_one("SELECT id FROM equipment WHERE serial_no = ?", (sn,))
    if existing:
        continue
    db_execute("""INSERT INTO equipment 
        (name, type, brand, model, serial_no, client, install_date, warranty_expire, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (device_type, device_type, brand, model, sn, client,
         install_date.strftime("%Y-%m-%d"),
         (install_date + timedelta(days=365*3)).strftime("%Y-%m-%d"), today_ts))

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
    ("二毛姐", "维修", "家中电脑运行缓慢", "completed", 180, "电脑清灰升级"),
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
    if existing:
        continue
    db_execute("INSERT INTO service_fees (name, fee_type, unit_price, description) VALUES (?,?,?,?)",
               (name, fee_type, price, desc))
print(f"   ✅ 已有 {db_query_one('SELECT COUNT(*) as c FROM service_fees')['c']} 个服务项目")

# ============================================================
# 6. 生成收入记录（关联工单结算）
# ============================================================
print("6️⃣  创建收入记录 ...")
income_records = [
    # (client, amount, method, source_type, source_id, description)
    ("集宁一中", 1680, "对公", "ticket", created_tickets[0], f"工单{created_tickets[0]} 一体机维修收款"),
    ("王利平", 150, "微信", "ticket", created_tickets[7], f"工单{created_tickets[7]} 打印机安装收款"),
    ("益民劳务有限公司", 350, "微信", "ticket", created_tickets[5], f"工单{created_tickets[5]} 电脑维修收款"),
]

for client, amount, method, src_type, src_id, desc in income_records:
    # 随机过去1-7天的日期作为收款日期
    paid_dt = now - timedelta(days=len(income_records)*2, hours=len(income_records))
    existing = db_query_one(
        "SELECT id FROM income_records WHERE source_type=? AND source_id=? AND amount=?",
        (src_type, src_id, amount))
    if existing:
        continue
    finance_service.record_ticket_income(client, amount, method, src_id,
                                        paid_dt.strftime("%Y-%m-%d %H:%M"), desc)
print(f"   ✅ 已创建 {len(income_records)} 条收入记录")

# ============================================================
# 7. 创建销售记录（包含完整支付流程）
# ============================================================
print("7️⃣  创建销售记录 ...")
sales_plans = [
    # (goods_id, client, quantity, amount, payment_method)
    (2, "集宁一中", 1, 240, "对公"),     # 加速器20客户端
    (3, "蜗牛电竞网吧", 5, 750, "微信"),  # OPS风扇x5
    (5, "王利平", 2, 80, "微信"),         # 电源适配器x2
    (6, "集宁京能电力", 10, 260, "对公"), # 公牛插板x10
    (9, "蜗牛电竞网吧", 3, 90, "微信"),   # 监控电源x3
]

for gid, client, qty, amount, method in sales_plans:
    try:
        result = inventory_service.record_sale(
            goods_id=gid, client=client, quantity=qty,
            payment_method=method, amount=amount,
            notes=f"批量销售-{client}"
        )
        print(f"   → 销售 {result.get('sale_id','?')}: {client} x{qty}")
    except Exception as e:
        print(f"   ⚠️ 销售失败 {gid} {client}: {e}")
        # 库存不足时，强制写入纯收入
        finance_service.record_quick_income(
            client, amount, method,
            f"销售 {gid} x{qty} (库存不足)", now.isoformat())

# ============================================================
# 8. 创建采购单 + 入库
# ============================================================
print("8️⃣  创建采购单和入库 ...")
purchase_data = [
    ("默认供货商", "联想电源适配器采购", 40, 10, 20.0),  # (vendor, desc, item_count unit_cost)
    ("默认供货商", "公牛插板补货", 26, 20, 15.0),
    ("默认供货商", "监控电源采购", 30, 10, 15.0),
]

for i, (vendor, desc, unit_price, qty, unit_cost) in enumerate(purchase_data):
    po_no = f"PO-SEED-{today.replace('-','')}-{i}"
    try:
        po_id = db_execute("""INSERT INTO purchase_orders (po_no, vendor, purchase_date, status, notes, total_amount, payment_status, created_at)
                          VALUES (?,?,?,?,?,?,?,?)""",
                         (po_no, vendor, today, "completed", desc, unit_cost*qty, "unpaid", today_ts))
        g = db_query_one("SELECT id, name FROM goods ORDER BY id LIMIT 1 OFFSET ?", (i,))
        if g:
            db_execute("""INSERT INTO purchase_items (po_id, goods_id, goods_name, quantity, unit_cost, total_cost)
                          VALUES (?,?,?,?,?,?)""",
                         (po_id, g["id"], g["name"], qty, unit_cost, unit_cost*qty))
        print(f"   → 采购单 {po_no}: {desc} x{qty} = ¥{unit_cost*qty:.0f}")
    except Exception as e:
        print(f"   ⚠️ 采购失败 {desc}: {str(e)[:80]}")

# ============================================================
# 8.5 采购入库 → 生成库存
# ============================================================
print("8.5️⃣  采购入库生成库存 ...")
stock_count = 0
for i, (vendor, desc, unit_price, qty, unit_cost) in enumerate(purchase_data):
    g = db_query_one("SELECT id, name, is_bulk FROM goods ORDER BY id LIMIT 1 OFFSET ?", (i,))
    if g:
        gid = g["id"]
        try:
            items = reg.inventory_svc.add_inventory(
                goods_id=gid,
                quantity=qty,
                location="主库房",
                notes=f"采购入库: {desc}",
            )
            stock_count += len(items) if items else 0
            print(f"   → 入库 {g['name']} x{qty} (库存项: {len(items) if items else 0})")
        except Exception as e:
            print(f"   ⚠️ 入库失败 {g['name']}: {str(e)[:80]}")
print(f"   ✅ 已创建 {stock_count} 个库存项")

# ============================================================
# 8.6 补充更多商品 + 库存（覆盖预警场景）
# ============================================================
print("8.6️⃣  补充商品库存（含预警）...")
extra_goods = [
    ("TP-LINK千兆路由器", 285, 12, 3),
    ("超五类网线305米箱", 420, 5, 2),
    ("海康威视摄像头", 180, 8, 1),
    ("电脑电源500W", 250, 15, 5),
    ("22寸显示器", 650, 4, 4),
]
stock_count2 = 0
for name, price, base_qty, low_threshold in extra_goods:
    g = db_query_one("SELECT id FROM goods WHERE name = ?", (name,))
    if not g:
        gid = db_execute(
            "INSERT INTO goods (name, selling_price, cost_price, unit, category) "
            "VALUES (?, ?, ?, '个', '网络设备')",
            (name, price, price * 0.7))
    else:
        gid = g["id"]

    # 创建库存（低于阈值的商品制造低库存预警）
    qty = min(base_qty, low_threshold + 1)
    try:
        items = reg.inventory_svc.add_inventory(
            goods_id=gid, quantity=qty, location="主库房",
            notes=f"初始入库 {name}")
        stock_count2 += len(items) if items else 0
        print(f"   → {name} x{qty} (预警阈值: {low_threshold})")
    except Exception as e:
        print(f"   ⚠️ {name}: {str(e)[:60]}")
print(f"   ✅ 已补充 {stock_count2} 个库存项")

# 低库存预警商品（库存为0或极少）
alert_goods = [
    ("HDMI线2米", 25, "线材", 10),
    ("VGA线", 18, "线材", 10),
]
for name, price, cat, min_qty in alert_goods:
    g = db_query_one("SELECT id FROM goods WHERE name = ?", (name,))
    if not g:
        gid = db_execute(
            "INSERT INTO goods (name, selling_price, cost_price, unit, category) "
            "VALUES (?, ?, ?, '条', ?)",
            (name, price, price * 0.6, cat))
        # 只创建1个库存（远低于阈值）
        reg.inventory_svc.add_inventory(goods_id=gid, quantity=1, location="主库房",
                                         notes="少量库存，即将用完")
        print(f"   ⚠️ 预警商品: {name} 仅剩 1 个 (建议补货)")
    else:
        print(f"   → {name} 已存在")

# 耗材类（散装商品）
bulk_goods = [
    ("焊锡丝", 15, "克", 200),
    ("热缩管", 0.5, "米", 100),
]
for name, price, unit, qty in bulk_goods:
    g = db_query_one("SELECT id FROM goods WHERE name = ?", (name,))
    if not g:
        gid = db_execute(
            "INSERT INTO goods (name, selling_price, cost_price, unit, category, is_bulk) "
            "VALUES (?, ?, ?, ?, '耗材', 1)",
            (name, price, price * 0.5, unit))
        reg.inventory_svc.add_inventory(goods_id=gid, quantity=qty, location="耗材柜",
                                         notes=f"初始库存 {name}")
        print(f"   → 散装: {name} x{qty}{unit}")
    else:
        print(f"   → {name} 已存在")

# ============================================================
# 9. 创建业务支出记录
# ============================================================
print("9️⃣  创建业务支出记录 ...")
expenses_data = [
    ("采购", "京东", 450, "采购网线、水晶头等耗材"),
    ("交通费", "", 120, "本月外出维修油费"),
    ("维修工具", "五金店", 85, "螺丝刀套装"),
    ("办公用品", "晨光文具", 165, "打印纸、墨盒"),
    ("通信费", "中国移动", 58, "工作手机话费"),
]

for cat, vendor, amount, desc in expenses_data:
    paid_dt = now - timedelta(days=len(expenses_data))
    finance_service.add_expense(category=cat, vendor=vendor, amount=amount,
                                 description=desc, paid_at=paid_dt.strftime("%Y-%m-%d"),
                                 related_ticket_id=None)
print(f"   ✅ 已创建 {len(expenses_data)} 条业务支出")

# ============================================================
# 10. 其他费用（分类覆盖）
# ============================================================
print("🔟  创建其他费用记录 ...")
personal_expenses = [
    ("餐费", 35, "微信", "午餐-刀削面"),
    ("餐费", 42, "支付宝", "晚餐-火锅"),
    ("交通费", 15.5, "微信", "打车回家"),
    ("购物", 128, "美团", "超市日用品"),
    ("房租", 1200, "微信", "5月房租"),
    ("水电费", 85, "微信", "5月水电"),
    ("通信费", 39, "微信", "话费充值"),
    ("娱乐", 56, "支付宝", "电影票"),
    ("医疗", 68, "微信", "药店买药"),
]

for cat, amount, pay_type, desc in personal_expenses:
    paid_dt = now - timedelta(days=len(personal_expenses))
    db_execute("""INSERT INTO expense_records 
        (category, vendor, amount, paid_at, description, is_personal, payment_type)
        VALUES (?, ?, ?, ?, ?, 1, ?)""",
        (cat, "", amount, paid_dt.strftime("%Y-%m-%d"), desc, pay_type))
print(f"   ✅ 已创建 {len(personal_expenses)} 条其他费用")

# ============================================================
# 11. 创建待办事项（关联工单）
# ============================================================
print("1️⃣1️⃣ 创建待办事项（含关联工单）...")
todo_data = [
    ("处理工单-集宁一中投影仪", "H", created_tickets[1] if len(created_tickets) > 1 else None, today + " 17:00"),
    ("采购配件-蜗牛网吧触摸框", "M", created_tickets[3] if len(created_tickets) > 3 else None, today + " 15:00"),
    ("回访客户-益民劳务电脑维修", "L", created_tickets[5] if len(created_tickets) > 5 else None, today + " 10:00"),
    ("月度报表汇总", "M", None, (now + timedelta(days=2)).strftime("%Y-%m-%d") + " 18:00"),
    ("跟进蜗牛网吧续费", "H", None, (now + timedelta(days=1)).strftime("%Y-%m-%d") + " 12:00"),
]

todo_svc = resolve_service("todo_service")
for title, priority, ticket_id, due_date in todo_data:
    existing = db_query_one("SELECT id FROM todos WHERE title LIKE ?", (title[:10] + "%",))
    if existing:
        continue
    todo_svc.create(title=title, priority=priority, source_type="ticket" if ticket_id else "",
                    source_id=ticket_id, due_date=due_date, category="work", remind=1)
print(f"   ✅ 已创建 {len(todo_data)} 条待办")

# ============================================================
# 12. 设置预算
# ============================================================
print("1️⃣2️⃣ 设置个人月度预算 ...")
budgets = [
    ("餐费", 1500, today[:7]),
    ("房租", 1200, today[:7]),
    ("交通费", 300, today[:7]),
    ("购物", 500, today[:7]),
    ("娱乐", 200, today[:7]),
]
for cat, budget, month in budgets:
    existing = db_query_one("SELECT id FROM expense_budgets WHERE category=? AND month=?",
                            (cat, month))
    if existing:
        db_execute("UPDATE expense_budgets SET budget_amount=? WHERE id=?", (budget, existing["id"]))
    else:
        db_execute("INSERT INTO expense_budgets (category, month, budget_amount) VALUES (?,?,?)",
                   (cat, month, budget))
print(f"   ✅ 已设置 {len(budgets)} 个预算")

# ============================================================
# 13. 关联工单-设备
# ============================================================
print("1️⃣3️⃣ 关联工单与设备 ...")
for i, tid in enumerate(created_tickets[:6]):  # 前6个工单关联设备
    equip = db_query_one("SELECT id FROM equipment LIMIT 1 OFFSET ?", (i,))
    if not equip:
        break
    existing = db_query_one("SELECT id FROM ticket_equipment WHERE ticket_id=? AND equipment_id=?",
                            (tid, equip["id"]))
    if existing:
        continue
    db_execute("INSERT INTO ticket_equipment (ticket_id, equipment_id) VALUES (?,?)",
               (tid, equip["id"]))
print(f"   ✅ 已关联 6 个工单-设备")

# ============================================================
# 14. 创建提醒（工单预约）
# ============================================================
print("1️⃣4️⃣ 创建工单提醒 ...")
for i, tid in enumerate(created_tickets[:5]):
    appointment = (now + timedelta(days=i+1)).strftime("%Y-%m-%d 09:00")
    db_execute("UPDATE tickets SET appointment_at = ? WHERE id = ?", (appointment, tid))
    existing_reminder = db_query_one("SELECT id FROM ticket_reminders WHERE ticket_id=?", (tid,))
    if existing_reminder:
        continue
    ticket = db_query_one("SELECT client, title FROM tickets WHERE id=?", (tid,))
    if ticket:
        reminder_service = resolve_service("reminder_service")
        reminder_service.create_reminder(
            ticket_id=tid, appointment_at=appointment,
            client_name=ticket["client"], service_content=ticket.get("title", "") or ""
        )
print(f"   ✅ 已创建 5 个工单预约提醒")

# ============================================================
# 15. 完善历史记录
# ============================================================
print("1️⃣5️⃣ 补充审计日志 ...")
for i, tid in enumerate(created_tickets[:8]):
    existing = db_query_one("SELECT id FROM history WHERE ticket_id=? AND action='seed_data'", (tid,))
    if existing:
        continue
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
              "goods", "inventory_items", "purchase_orders", "sales_records",
              "suppliers", "technicians", "service_fees", "todos", "notifications",
              "ticket_reminders", "expense_categories", "expense_budgets"]:
    count = db_query_one(f"SELECT COUNT(*) as c FROM {table}")["c"]
    print(f"  {table}: {count}")

print("\n✅ 测试数据创建完成!")
