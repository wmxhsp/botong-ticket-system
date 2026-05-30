"""
博通工单系统 - 简化版测试数据生成器
用于生成核心业务数据以支持系统测试
"""
import sys, os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.persistence.legacy_db import db_execute, db_query, db_query_one

now = datetime.now()
today = now.strftime("%Y-%m-%d")
today_ts = now.isoformat()

def generate_test_data():
    """生成核心测试数据"""

    # ============================================================
    # 1. 确保基础数据完整
    # ============================================================
    print("1️⃣  确保客户数据完整 ...")
    clients = [
        ("集宁一中", "0474-1234567", "学校-集宁区", 45),
        ("乌兰察布市蒙古族中学", "0474-2345678", "学校-集宁区", 60),
        ("集宁京能电力", "0474-3456789", "企业-集宁区", 30),
        ("兴和县寻梦网吧", "0474-4567890", "网吧-兴和县", 15),
        ("蜗牛电竞网吧", "0474-5678901", "网吧-集宁区", 15),
        ("益民劳务有限公司", "0474-6789012", "企业-集宁区", 30),
        ("王利平", "15924455769", "个人-集宁区", 7),
        ("二毛姐", "15847451234", "个人-集宁区", 7),
    ]

    client_ids = {}
    for name, phone, notes, terms in clients:
        existing = db_query_one("SELECT id FROM clients WHERE name = ?", (name,))
        if existing:
            client_ids[name] = existing['id']
            db_execute("UPDATE clients SET phone=?, notes=?, payment_terms=? WHERE id=?",
                       (phone, notes, terms, existing['id']))
        else:
            cid = db_execute("INSERT INTO clients (name, phone, notes, payment_terms, created_at) VALUES (?,?,?,?,?)",
                           (name, phone, notes, terms, today_ts))
            client_ids[name] = cid

    print(f"   ✅ 已确保 {len(clients)} 个客户")

    # ============================================================
    # 2. 生成商品类别和商品
    # ============================================================
    print("2️⃣  创建商品数据 ...")
    # 商品类别
    categories = ["网络设备", "电脑配件", "办公耗材", "监控设备", "线材"]
    cat_ids = {}
    for i, cat_name in enumerate(categories):
        existing = db_query_one("SELECT id FROM goods_categories WHERE name = ?", (cat_name,))
        if existing:
            cat_ids[cat_name] = existing['id']
        else:
            cid = db_execute("INSERT INTO goods_categories (name) VALUES (?)", (cat_name,))
            cat_ids[cat_name] = cid

    # 商品
    goods_data = [
        ("TP-LINK千兆路由器", cat_ids["网络设备"], 285, 200, 3),
        ("超五类网线305米箱", cat_ids["线材"], 420, 300, 2),
        ("海康威视摄像头", cat_ids["监控设备"], 180, 120, 5),
        ("电脑电源500W", cat_ids["电脑配件"], 250, 180, 3),
        ("22寸显示器", cat_ids["电脑配件"], 650, 500, 2),
        ("HDMI线2米", cat_ids["线材"], 25, 15, 10),
        ("VGA线1.5米", cat_ids["线材"], 18, 10, 10),
        ("联想电源适配器", cat_ids["电脑配件"], 40, 25, 5),
        ("公牛插板", cat_ids["办公耗材"], 26, 18, 20),
        ("监控电源", cat_ids["监控设备"], 30, 20, 10),
    ]

    goods_ids = {}
    for name, cat_id, sell_price, cost_price, min_stock in goods_data:
        existing = db_query_one("SELECT id FROM goods WHERE name = ?", (name,))
        if existing:
            goods_ids[name] = existing['id']
            db_execute("UPDATE goods SET selling_price=?, cost_price=?, min_stock=? WHERE id=?",
                       (sell_price, cost_price, min_stock, existing['id']))
        else:
            gid = db_execute("""INSERT INTO goods (name, category_id, selling_price, cost_price, min_stock, unit, created_at)
                               VALUES (?,?,?,?,?,'个',?)""",
                            (name, cat_id, sell_price, cost_price, min_stock, today_ts))
            goods_ids[name] = gid

    print(f"   ✅ 已确保 {len(goods_data)} 个商品")

    # ============================================================
    # 3. 生成供应商
    # ============================================================
    print("3️⃣  创建供应商数据 ...")
    suppliers = [
        ("京东电脑办公专营店", "张经理", "13800138000", "对公"),
        ("海康威视授权经销商", "李经理", "13900139000", "对公"),
        ("TP-LINK官方代理", "王经理", "13700137000", "对公"),
    ]

    supplier_ids = {}
    for name, contact, phone, payment_terms in suppliers:
        existing = db_query_one("SELECT id FROM suppliers WHERE name = ?", (name,))
        if existing:
            supplier_ids[name] = existing['id']
        else:
            sid = db_execute("""INSERT INTO suppliers (name, contact, phone, payment_terms, created_at)
                               VALUES (?,?,?,?,?)""",
                           (name, contact, phone, payment_terms, today_ts))
            supplier_ids[name] = sid

    print(f"   ✅ 已确保 {len(suppliers)} 个供应商")

    # ============================================================
    # 4. 生成技术员
    # ============================================================
    print("4️⃣  创建技术员数据 ...")
    technicians = [
        ("苏鹏", "13811112222", "supeng@botong.cn", "hourly", 60, 50, "高级工程师"),
        ("王浩博", "13822223333", "wanghb@botong.cn", "hourly", 45, 35, "中级工程师"),
        ("李学平", "13833334444", "lixp@botong.cn", "hourly", 50, 40, "中级工程师"),
        ("小赵", "13844445555", "xiaozhao@botong.cn", "hourly", 30, 25, "初级工程师"),
    ]

    tech_ids = {}
    for name, phone, email, billing_type, cost_rate, hourly_rate, skill_level in technicians:
        existing = db_query_one("SELECT id FROM technicians WHERE name = ?", (name,))
        if existing:
            tech_ids[name] = existing['id']
            db_execute("""UPDATE technicians SET phone=?, email=?, billing_type=?,
                          cost_rate=?, hourly_rate=?, skill_level=? WHERE id=?""",
                       (phone, email, billing_type, cost_rate, hourly_rate, skill_level, existing['id']))
        else:
            tid = db_execute("""INSERT INTO technicians (name, phone, email, billing_type, cost_rate, hourly_rate, skill_level, created_at)
                               VALUES (?,?,?,?,?,?,?,?)""",
                           (name, phone, email, billing_type, cost_rate, hourly_rate, skill_level, today_ts))
            tech_ids[name] = tid

    print(f"   ✅ 已确保 {len(technicians)} 个技术员")

    # ============================================================
    # 5. 生成工单（覆盖各种状态）
    # ============================================================
    print("5️⃣  创建工单数据 ...")
    ticket_plans = [
        # (client, title, status, total, priority)
        ("集宁一中", "教室一体机维修", "closed", 1680, "H"),
        ("集宁一中", "投影仪维修", "pending_payment", 520, "M"),
        ("集宁京能电力", "交换机端口维修", "in_progress", 450, "H"),
        ("蜗牛电竞网吧", "网吧无盘安装", "pending_parts", 3600, "H"),
        ("蜗牛电竞网吧", "月度巡检", "open", 2000, "L"),
        ("益民劳务有限公司", "财务电脑维修", "closed", 350, "M"),
        ("王利平", "笔记本维修", "pending_client", 280, "M"),
        ("王利平", "打印机安装", "closed", 150, "L"),
        ("乌兰察布市蒙古族中学", "广播系统维修", "in_progress", 1200, "M"),
        ("二毛姐", "电脑清灰升级", "completed", 180, "L"),
        ("集宁京能电力", "机房巡检", "open", 2000, "M"),
        ("蜗牛电竞网吧", "显卡更换", "pending_payment", 850, "H"),
    ]

    ticket_ids = []
    for client, title, status, total, priority in ticket_plans:
        existing = db_query_one("SELECT id FROM tickets WHERE client=? AND title=? ORDER BY id DESC LIMIT 1",
                               (client, title))
        if existing:
            tid = existing['id']
        else:
            tid = db_execute("""INSERT INTO tickets (client, title, status, total, priority, created_at)
                               VALUES (?,?,?,?,?,?)""",
                           (client, title, status, total, priority, today_ts))
        ticket_ids.append(tid)

    print(f"   ✅ 已创建/确保 {len(ticket_ids)} 个工单")

    # ============================================================
    # 6. 生成库存数据
    # ============================================================
    print("6️⃣  创建库存数据 ...")
    inventory_count = 0
    for goods_name, qty in [
        ("TP-LINK千兆路由器", 5),
        ("超五类网线305米箱", 3),
        ("海康威视摄像头", 8),
        ("电脑电源500W", 10),
        ("22寸显示器", 4),
        ("HDMI线2米", 2),  # 低库存预警
        ("VGA线1.5米", 1),  # 低库存预警
        ("联想电源适配器", 10),
        ("公牛插板", 25),
        ("监控电源", 15),
    ]:
        if goods_name not in goods_ids:
            continue
        gid = goods_ids[goods_name]

        # 检查是否已有库存
        existing = db_query_one("SELECT id FROM inventory_items WHERE goods_id=?", (gid,))
        if existing:
            db_execute("UPDATE inventory_items SET quantity=? WHERE id=?", (qty, existing['id']))
        else:
            db_execute("""INSERT INTO inventory_items (goods_id, quantity, location, min_stock, created_at)
                          VALUES (?,?,?,?,?)""",
                      (gid, qty, "主库房", 2, today_ts))

        inventory_count += 1

    print(f"   ✅ 已确保 {inventory_count} 个库存项")

    # ============================================================
    # 7. 生成收入记录
    # ============================================================
    print("7️⃣  创建收入记录 ...")
    income_data = [
        ("集宁一中", 1680, "对公", "工单收款-一体机维修"),
        ("王利平", 150, "微信", "工单收款-打印机安装"),
        ("益民劳务有限公司", 350, "微信", "工单收款-电脑维修"),
    ]

    for client, amount, method, desc in income_data:
        db_execute("""INSERT INTO income_records (client, amount, payment_method, description, received_at, created_at)
                      VALUES (?,?,?,?,?,?)""",
                  (client, amount, method, desc, today, today_ts))

    print(f"   ✅ 已创建 {len(income_data)} 条收入记录")

    # ============================================================
    # 8. 生成支出记录
    # ============================================================
    print("8️⃣  创建支出记录 ...")
    expense_data = [
        ("配件采购", "京东", 450, "采购网线水晶头"),
        ("交通费", "", 120, "外出维修油费"),
        ("维修工具", "五金店", 85, "螺丝刀套装"),
        ("办公用品", "晨光文具", 165, "打印纸墨盒"),
        ("通信费", "中国移动", 58, "工作手机话费"),
    ]

    for cat, vendor, amount, desc in expense_data:
        db_execute("""INSERT INTO expense_records (category, vendor, amount, description, paid_at, created_at)
                      VALUES (?,?,?,?,?,?)""",
                  (cat, vendor, amount, desc, today, today_ts))

    print(f"   ✅ 已创建 {len(expense_data)} 条支出记录")

    # ============================================================
    # 9. 生成待办事项
    # ============================================================
    print("9️⃣  创建待办事项 ...")
    todo_data = [
        ("处理工单-集宁一中投影仪", "H", "work", today + " 17:00"),
        ("采购配件-蜗牛网吧触摸框", "M", "work", today + " 15:00"),
        ("回访客户-益民劳务电脑维修", "L", "work", today + " 10:00"),
        ("月度报表汇总", "M", "work", (now + timedelta(days=2)).strftime("%Y-%m-%d") + " 18:00"),
        ("跟进蜗牛网吧续费", "H", "work", (now + timedelta(days=1)).strftime("%Y-%m-%d") + " 12:00"),
    ]

    for title, priority, category, due_date in todo_data:
        existing = db_query_one("SELECT id FROM todos WHERE title=?", (title,))
        if not existing:
            db_execute("""INSERT INTO todos (title, priority, category, due_date, created_at)
                          VALUES (?,?,?,?,?)""",
                      (title, priority, category, due_date, today_ts))

    print(f"   ✅ 已创建 {len(todo_data)} 条待办")

    # ============================================================
    # 10. 生成服务项目
    # ============================================================
    print("🔟  创建服务项目 ...")
    fees_data = [
        ("上门维修", 60, "上门技术服务"),
        ("系统安装", 80, "操作系统及软件安装"),
        ("网络维护", 50, "网络故障排查维护"),
        ("投影机清洗", 80, "投影机深度清洗"),
        ("数据恢复", 150, "硬盘数据恢复"),
    ]

    for name, price, desc in fees_data:
        existing = db_query_one("SELECT id FROM service_fees WHERE name=?", (name,))
        if not existing:
            db_execute("""INSERT INTO service_fees (name, unit_price, description, created_at)
                          VALUES (?,?,?,?)""",
                      (name, price, desc, today_ts))

    print(f"   ✅ 已确保服务项目数据")

    # ============================================================
    # 最终统计
    # ============================================================
    print("\n" + "="*60)
    print("📊 测试数据生成完毕！最终数据量：")
    print("="*60)

    for table in ["clients", "tickets", "goods", "inventory_items", "suppliers",
                  "technicians", "service_fees", "income_records", "expense_records", "todos"]:
        try:
            count = db_query_one(f"SELECT COUNT(*) as c FROM {table}")["c"]
            print(f"  {table}: {count}")
        except Exception as e:
            print(f"  {table}: 查询失败 ({str(e)[:30]})")

    print("\n✅ 测试数据创建完成!")

if __name__ == "__main__":
    generate_test_data()
