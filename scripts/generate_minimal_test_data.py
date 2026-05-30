"""
博通工单系统 - 简化测试数据生成器
只生成核心表的数据，避免字段不匹配问题
"""
import sys, os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.persistence.legacy_db import db_execute, db_query, db_query_one

now = datetime.now()
today = now.strftime("%Y-%m-%d")
today_ts = now.isoformat()

def generate_minimal_test_data():
    """生成最小测试数据集"""

    print("1️⃣  确保客户数据完整 ...")
    clients = [
        ("集宁一中", "0474-1234567", "学校-集宁区", 45),
        ("集宁京能电力", "0474-3456789", "企业-集宁区", 30),
        ("蜗牛电竞网吧", "0474-5678901", "网吧-集宁区", 15),
        ("王利平", "15924455769", "个人-集宁区", 7),
    ]
    for name, phone, notes, terms in clients:
        existing = db_query_one("SELECT id FROM clients WHERE name = ?", (name,))
        if existing:
            db_execute("UPDATE clients SET phone=?, notes=?, payment_terms=? WHERE id=?",
                       (phone, notes, terms, existing['id']))
        else:
            db_execute("INSERT INTO clients (name, phone, notes, payment_terms, created_at) VALUES (?,?,?,?,?)",
                      (name, phone, notes, terms, today_ts))
    print(f"   ✅ 已确保 {len(clients)} 个客户")

    print("2️⃣  创建工单数据 ...")
    ticket_plans = [
        ("集宁一中", "教室一体机维修", "closed", 1680, "H"),
        ("集宁京能电力", "交换机端口维修", "in_progress", 450, "H"),
        ("蜗牛电竞网吧", "月度巡检", "open", 2000, "L"),
        ("王利平", "笔记本维修", "pending_client", 280, "M"),
    ]
    for client, title, status, total, priority in ticket_plans:
        existing = db_query_one("SELECT id FROM tickets WHERE client=? AND title=? ORDER BY id DESC LIMIT 1", (client, title))
        if not existing:
            db_execute("INSERT INTO tickets (client, title, status, total, priority, created_at) VALUES (?,?,?,?,?,?)",
                      (client, title, status, total, priority, today_ts))
    print(f"   ✅ 已创建/确保 {len(ticket_plans)} 个工单")

    print("3️⃣  创建收入记录 ...")
    income_data = [
        ("集宁一中", 1680, "对公", "工单收款-一体机维修"),
        ("王利平", 150, "微信", "工单收款-打印机安装"),
    ]
    for client, amount, method, desc in income_data:
        db_execute("INSERT INTO income_records (client, amount, payment_method, description, received_at, created_at) VALUES (?,?,?,?,?,?)",
                  (client, amount, method, desc, today, today_ts))
    print(f"   ✅ 已创建 {len(income_data)} 条收入记录")

    print("4️⃣  创建支出记录 ...")
    expense_data = [
        ("配件采购", "京东", 450, "采购网线水晶头"),
        ("交通费", "", 120, "外出维修油费"),
    ]
    for cat, vendor, amount, desc in expense_data:
        db_execute("INSERT INTO expense_records (category, vendor, amount, description, paid_at, created_at) VALUES (?,?,?,?,?,?)",
                  (cat, vendor, amount, desc, today, today_ts))
    print(f"   ✅ 已创建 {len(expense_data)} 条支出记录")

    print("5️⃣  创建待办事项 ...")
    todo_data = [
        ("处理工单-集宁一中投影仪", "H", "work", today + " 17:00"),
        ("月度报表汇总", "M", "work", (now + timedelta(days=2)).strftime("%Y-%m-%d") + " 18:00"),
    ]
    for title, priority, category, due_date in todo_data:
        existing = db_query_one("SELECT id FROM todos WHERE title=?", (title,))
        if not existing:
            db_execute("INSERT INTO todos (title, priority, category, due_date, created_at) VALUES (?,?,?,?,?)",
                      (title, priority, category, due_date, today_ts))
    print(f"   ✅ 已创建 {len(todo_data)} 条待办")

    print("\n" + "="*60)
    print("📊 测试数据生成完毕！")
    print("="*60)
    for table in ["clients", "tickets", "income_records", "expense_records", "todos"]:
        try:
            count = db_query_one(f"SELECT COUNT(*) as c FROM {table}")["c"]
            print(f"  {table}: {count}")
        except:
            print(f"  {table}: 查询失败")
    print("\n✅ 完成!")

if __name__ == "__main__":
    generate_minimal_test_data()
