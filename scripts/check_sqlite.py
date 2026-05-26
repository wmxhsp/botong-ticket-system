#!/usr/bin/env python3
"""检查 SQLite 数据库结构和数据"""
import sqlite3
import sys

DB_PATH = "/Users/supeng/Documents/botong-ticket-system/tickets.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 列出所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    print("=== 数据库表 ===")
    for t in tables:
        name = t[0]
        cursor.execute(f"SELECT COUNT(*) FROM [{name}]")
        count = cursor.fetchone()[0]
        print(f"  {name}: {count} 行")
    print()

    # 列出关键表结构
    key_tables = ["tickets", "clients", "technicians", "inventory", "finance_records"]
    for table_name in key_tables:
        try:
            cursor.execute(f"PRAGMA table_info([{table_name}])")
            cols = cursor.fetchall()
            print(f"=== {table_name} 字段 ===")
            for c in cols:
                print(f"  {c[1]} ({c[2]})")
            print()
        except Exception as e:
            print(f"{table_name}: {e}")

    conn.close()
    print("SQLite 数据库检查完成!")

if __name__ == "__main__":
    main()
