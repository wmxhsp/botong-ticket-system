from datetime import datetime
from typing import List, Dict, Optional, Tuple

from infrastructure.persistence.legacy_db import db_execute, db_query, db_query_one


class StatsRepo:

    _ALLOWED_DATE_FIELDS = {"created_at", "received_at", "paid_at", "updated_at"}

    def _date_cond(self, field: str, date_from: str, date_to: str) -> Tuple[List[str], List[str]]:
        if field not in self._ALLOWED_DATE_FIELDS:
            raise ValueError(f"Invalid date field: {field}")
        clauses, params = [], []
        if date_from:
            clauses.append(f"{field} >= ?")
            params.append(date_from)
        if date_to:
            clauses.append(f"{field} <= ?")
            params.append(f"{date_to} 23:59:59")
        return clauses, params

    def get_overview(self, date_from: str = "", date_to: str = "") -> Dict:
        t_where, t_params = self._date_cond("created_at", date_from, date_to)
        t_where_sql = " AND ".join(t_where) if t_where else "1=1"
        total_tickets = db_query_one(
            f"SELECT COUNT(*) as c FROM tickets WHERE {t_where_sql}",
            tuple(t_params))

        i_where, i_params = self._date_cond("received_at", date_from, date_to)
        i_where_sql = " AND ".join(i_where) if i_where else "1=1"
        total_income = db_query_one(
            f"SELECT COALESCE(SUM(amount),0) as t FROM income_records WHERE {i_where_sql}",
            tuple(i_params))

        e_where, e_params = self._date_cond("paid_at", date_from, date_to)
        e_where_sql = " AND ".join(e_where) if e_where else "1=1"
        total_expense = db_query_one(
            f"SELECT COALESCE(SUM(amount),0) as t FROM expense_records WHERE {e_where_sql}",
            tuple(e_params))

        total_inc = total_income["t"] if total_income else 0
        total_exp = total_expense["t"] if total_expense else 0

        total_clients = db_query_one("SELECT COUNT(*) as c FROM clients")["c"] or 0

        status_dist = db_query(
            f"SELECT status, COUNT(*) as c FROM tickets WHERE {t_where_sql} GROUP BY status ORDER BY c DESC",
            tuple(t_params))

        monthly_tickets = db_query(
            f"SELECT substr(created_at,1,7) as ym, COUNT(*) as cnt FROM tickets WHERE {t_where_sql} GROUP BY ym ORDER BY ym DESC LIMIT 6",
            tuple(t_params))
        monthly_tickets.reverse()

        service_type_dist = db_query(
            f"SELECT service_type, COUNT(*) as c FROM tickets WHERE {t_where_sql} AND service_type IS NOT NULL AND service_type != '' GROUP BY service_type ORDER BY c DESC",
            tuple(t_params))

        return {
            "total_tickets": total_tickets["c"] if total_tickets else 0,
            "total_income": total_inc,
            "total_expense": total_exp,
            "total_profit": total_inc - total_exp,
            "total_clients": total_clients,
            "status_distribution": status_dist,
            "monthly_tickets": monthly_tickets,
            "service_type_dist": service_type_dist,
        }

    def get_monthly_income_trend(self) -> List[Dict]:
        monthly_income = []
        today = datetime.now()
        prev_income = None
        for i in range(5, -1, -1):
            m = today.month - i
            yr = today.year
            while m <= 0:
                m += 12
                yr -= 1
            ym = f"{yr}-{m:02d}"
            inc = db_query_one(
                "SELECT COALESCE(SUM(amount),0) as t FROM income_records WHERE received_at LIKE ?",
                (ym + '%',))
            exp = db_query_one(
                "SELECT COALESCE(SUM(amount),0) as t FROM expense_records WHERE paid_at LIKE ?",
                (ym + '%',))
            income = inc["t"] if inc else 0
            expense = exp["t"] if exp else 0
            growth = None
            if prev_income is not None and prev_income > 0:
                growth = round((income - prev_income) / prev_income * 100, 1)
            prev_income = income
            monthly_income.append({
                "month": ym,
                "income": income,
                "expense": expense,
                "income_growth": growth
            })
        return monthly_income

    def get_client_ranking(self, date_from: str = "", date_to: str = "") -> List[Dict]:
        i_where, i_params = self._date_cond("received_at", date_from, date_to)
        i_where_sql = " AND ".join(i_where) if i_where else "1=1"
        return db_query(
            f"SELECT client, COUNT(*) as cnt, COALESCE(SUM(amount),0) as total FROM income_records WHERE {i_where_sql} GROUP BY client ORDER BY total DESC",
            tuple(i_params))

    def get_ticket_count(self, date_from: str = "", date_to: str = "") -> int:
        t_where, t_params = self._date_cond("created_at", date_from, date_to)
        t_where_sql = " AND ".join(t_where) if t_where else "1=1"
        result = db_query_one(
            f"SELECT COUNT(*) as c FROM tickets WHERE {t_where_sql}",
            tuple(t_params))
        return result["c"] if result else 0

    def get_income_total(self, date_from: str = "", date_to: str = "") -> float:
        i_where, i_params = self._date_cond("received_at", date_from, date_to)
        i_where_sql = " AND ".join(i_where) if i_where else "1=1"
        result = db_query_one(
            f"SELECT COALESCE(SUM(amount),0) as t FROM income_records WHERE {i_where_sql}",
            tuple(i_params))
        return result["t"] if result else 0

    def get_expense_total(self, date_from: str = "", date_to: str = "") -> float:
        e_where, e_params = self._date_cond("paid_at", date_from, date_to)
        e_where_sql = " AND ".join(e_where) if e_where else "1=1"
        result = db_query_one(
            f"SELECT COALESCE(SUM(amount),0) as t FROM expense_records WHERE {e_where_sql}",
            tuple(e_params))
        return result["t"] if result else 0

    def get_client_count(self) -> int:
        result = db_query_one("SELECT COUNT(*) as c FROM clients")
        return result["c"] if result else 0

    def get_status_distribution(self, date_from: str = "", date_to: str = "") -> List[Dict]:
        t_where, t_params = self._date_cond("created_at", date_from, date_to)
        t_where_sql = " AND ".join(t_where) if t_where else "1=1"
        return db_query(
            f"SELECT status, COUNT(*) as c FROM tickets WHERE {t_where_sql} GROUP BY status ORDER BY c DESC",
            tuple(t_params))

    def get_monthly_ticket_counts(self, date_from: str = "", date_to: str = "") -> List[Dict]:
        t_where, t_params = self._date_cond("created_at", date_from, date_to)
        t_where_sql = " AND ".join(t_where) if t_where else "1=1"
        result = db_query(
            f"SELECT substr(created_at,1,7) as ym, COUNT(*) as cnt FROM tickets WHERE {t_where_sql} GROUP BY ym ORDER BY ym DESC LIMIT 6",
            tuple(t_params))
        result.reverse()
        return result
