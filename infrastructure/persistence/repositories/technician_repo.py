from datetime import datetime
from typing import List, Dict, Optional, Any

from infrastructure.persistence.legacy_db import db_execute, db_query, db_query_one
from domain.exceptions import TechnicianNotFoundError


class TechnicianRepo:

    def list_technicians(self) -> List[Dict]:
        items = db_query("SELECT * FROM technicians ORDER BY status, name")
        for t in items:
            name = t["name"]
            stats = db_query_one(
                "SELECT COUNT(DISTINCT ticket_id) as cnt, COALESCE(SUM(hours),0) as total_hours, "
                "COALESCE(SUM(line_total),0) as total_revenue, COALESCE(SUM(line_cost),0) as total_cost "
                "FROM ticket_service_items WHERE technician_name=?",
                (name,)
            )
            t["ticket_count"] = stats["cnt"] if stats else 0
            t["total_hours"] = stats["total_hours"] if stats else 0
            t["labor_revenue"] = float(stats["total_revenue"] if stats else 0)
            t["labor_cost"] = float(stats["total_cost"] if stats else 0)
            t["profit_contribution"] = t["labor_revenue"] - t["labor_cost"]
        return items

    def create_technician(self, data: dict) -> Dict:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        db_execute(
            "INSERT INTO technicians (name, phone, skills, cost_rate, billing_type, daily_rate, package_rate, daily_cost_rate, package_cost, status, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                data["name"],
                data.get("phone", ""),
                data.get("skills", ""),
                float(data.get("cost_rate", 0)),
                data.get("billing_type", "hourly"),
                float(data.get("daily_rate", 0)),
                float(data.get("package_rate", 0)),
                float(data.get("daily_cost_rate", 0)),
                float(data.get("package_cost", 0)),
                data.get("status", "active"),
                now,
                now,
            ),
        )
        return {"message": f"已创建: {data['name']}"}

    def get_summary(self) -> Dict[str, Any]:
        total = db_query_one("SELECT COUNT(*) as c FROM technicians") or {"c": 0}
        active = db_query_one(
            "SELECT COUNT(*) as c FROM technicians WHERE status='active'"
        ) or {"c": 0}
        total_hours = db_query_one(
            "SELECT COALESCE(SUM(hours),0) as h FROM ticket_service_items"
        ) or {"h": 0}
        avg_cost_rate = db_query_one(
            "SELECT COALESCE(AVG(cost_rate),0) as r FROM technicians WHERE status='active'"
        ) or {"r": 0}
        return {
            "total": total["c"],
            "active": active["c"],
            "total_hours": total_hours["h"],
            "avg_cost_rate": avg_cost_rate["r"],
        }

    def get_stats(self, date_from: str = "", date_to: str = "") -> Dict[str, Any]:
        clauses, params = [], []
        if date_from:
            clauses.append("t.created_at >= ?")
            params.append(date_from)
        if date_to:
            clauses.append("t.created_at <= ?")
            params.append(f"{date_to} 23:59:59")
        where_sql = " AND ".join(clauses) if clauses else "1=1"

        rows = db_query(f"""
            SELECT
                si.technician_name as name,
                COUNT(DISTINCT t.id) as ticket_count,
                COALESCE(SUM(si.hours), 0) as total_hours,
                COALESCE(SUM(si.line_total), 0) as total_revenue,
                COALESCE(SUM(si.line_cost), 0) as total_cost,
                COALESCE(SUM(si.line_total), 0) - COALESCE(SUM(si.line_cost), 0) as total_profit
            FROM ticket_service_items si
            JOIN tickets t ON t.id = si.ticket_id
            WHERE si.technician_name IS NOT NULL AND si.technician_name != ''
              AND {where_sql}
            GROUP BY si.technician_name
            ORDER BY total_profit DESC
        """, tuple(params) if params else ())

        summary = self.get_summary()
        return {
            "technicians": rows or [],
            "summary": summary
        }

    def get_profit_ranking(self, date_from: str = "", date_to: str = "") -> Dict[str, Any]:
        clauses, params = [], []
        if date_from:
            clauses.append("t.created_at >= ?")
            params.append(date_from)
        if date_to:
            clauses.append("t.created_at <= ?")
            params.append(f"{date_to} 23:59:59")
        where_sql = " AND ".join(clauses) if clauses else "1=1"

        rows = db_query(f"""
            SELECT
                si.technician_name as name,
                COUNT(DISTINCT t.id) as ticket_count,
                COALESCE(SUM(si.hours), 0) as total_hours,
                COALESCE(SUM(si.line_total), 0) as total_revenue,
                COALESCE(SUM(si.line_cost), 0) as total_cost,
                COALESCE(SUM(si.line_total), 0) - COALESCE(SUM(si.line_cost), 0) as total_profit,
                CASE WHEN COALESCE(SUM(si.line_total), 0) > 0
                    THEN ROUND((COALESCE(SUM(si.line_total), 0) - COALESCE(SUM(si.line_cost), 0)) / COALESCE(SUM(si.line_total), 0) * 100, 1)
                    ELSE 0 END as profit_margin
            FROM ticket_service_items si
            JOIN tickets t ON t.id = si.ticket_id
            WHERE si.technician_name IS NOT NULL AND si.technician_name != ''
              AND {where_sql}
            GROUP BY si.technician_name
            ORDER BY total_profit DESC
        """, tuple(params) if params else ())

        tech_list = rows or []
        for i, t in enumerate(tech_list):
            t["rank"] = i + 1
            tech = db_query_one("SELECT id, phone, skills, status, billing_type, cost_rate, daily_rate, package_rate, daily_cost_rate, package_cost FROM technicians WHERE name = ?", (t["name"],))
            if tech:
                t["id"] = tech["id"]
                t["phone"] = tech["phone"]
                t["skills"] = tech["skills"]
                t["status"] = tech["status"]
                t["billing_type"] = tech["billing_type"]
                t["cost_rate"] = tech["cost_rate"]
                t["daily_rate"] = tech["daily_rate"]
                t["package_rate"] = tech["package_rate"]
                t["daily_cost_rate"] = tech["daily_cost_rate"]
                t["package_cost"] = tech["package_cost"]
            else:
                t["id"] = None
                t["status"] = "unknown"

        total_revenue = sum(float(r.get("total_revenue", 0)) for r in tech_list)
        total_cost = sum(float(r.get("total_cost", 0)) for r in tech_list)
        total_profit = total_revenue - total_cost

        return {
            "ranking": tech_list,
            "summary": {
                "total_technicians": len(tech_list),
                "total_revenue": round(total_revenue, 2),
                "total_cost": round(total_cost, 2),
                "total_profit": round(total_profit, 2),
                "avg_profit_margin": round(total_profit / total_revenue * 100, 1) if total_revenue > 0 else 0,
            }
        }

    def get_technician(self, tech_id: int) -> Dict:
        tech = db_query_one("SELECT * FROM technicians WHERE id = ?", (tech_id,))
        if not tech:
            raise TechnicianNotFoundError(f"技术人员 #{tech_id} 不存在")
        return tech

    def update_technician(self, tech_id: int, **fields) -> Dict:
        tech = self.get_technician(tech_id)

        allowed_fields = ["name", "phone", "skills", "status", "cost_rate", "billing_type", "daily_rate", "package_rate", "daily_cost_rate", "package_cost"]
        updates = []
        params = []

        for f in allowed_fields:
            if f in fields:
                updates.append(f"{f} = ?")
                params.append(fields[f])

        if not updates:
            return tech

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        params.extend([now, tech_id])
        db_execute(
            f"UPDATE technicians SET {', '.join(updates)}, updated_at=? WHERE id=?",
            tuple(params),
        )
        return self.get_technician(tech_id)

    def delete_technician(self, tech_id: int) -> bool:
        self.get_technician(tech_id)
        db_execute("DELETE FROM technicians WHERE id = ?", (tech_id,))
        return True

    def get_technician_by_name(self, name: str) -> Optional[Dict]:
        return db_query_one("SELECT * FROM technicians WHERE name = ?", (name,))

    def get_technician_tickets(self, name: str) -> Dict[str, Any]:
        tickets = db_query(
            """
            SELECT t.id, t.ticket_no, t.client, t.status, t.description as content,
                   t.time_spent, t.created_at, si.hours as tech_hours, si.line_cost as cost_amount
            FROM ticket_service_items si
            JOIN tickets t ON si.ticket_id = t.id
            WHERE si.technician_name = ?
            ORDER BY t.created_at DESC
            """,
            (name,),
        )
        seen = set()
        unique_tickets = []
        for t in (tickets or []):
            if t["id"] not in seen:
                seen.add(t["id"])
                unique_tickets.append(t)
        return {
            "technician_name": name,
            "tickets": unique_tickets,
            "total_tickets": len(unique_tickets),
        }
