from datetime import datetime
from typing import List, Dict, Optional

from infrastructure.persistence.legacy_db import db_execute, db_query, db_query_one


class ServiceFeeRepo:

    def list_fees(self) -> List[Dict]:
        try:
            items = db_query("""
                SELECT sf.*, COALESCE(t.cnt, 0) as usage_count
                FROM service_fees sf
                LEFT JOIN (SELECT service_fee_id, COUNT(*) as cnt FROM tickets WHERE service_fee_id IS NOT NULL GROUP BY service_fee_id) t
                ON sf.id = t.service_fee_id
                ORDER BY sf.fee_type, sf.name
            """)
        except Exception:
            items = []
        return items

    def create_fee(self, data: Dict) -> Dict:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        fee_type = data.get("fee_type", "hourly")
        db_execute("INSERT INTO service_fees (name, fee_type, unit_price, cost_price, description, active, created_at, updated_at) VALUES (?,?,?,?,?,1,?,?)",
                   (data["name"], fee_type, float(data["unit_price"]),
                    float(data.get("cost_price", 0)), data.get("description", ""), now, now))
        return {"message": f"已创建服务项目: {data['name']}"}

    def get_fee(self, fee_id: int) -> Optional[Dict]:
        fee = db_query_one("SELECT * FROM service_fees WHERE id = ?", (fee_id,))
        return fee

    def update_fee(self, fee_id: int, **fields) -> Dict:
        updates = []
        params = []
        for field in ["name", "fee_type", "unit_price", "cost_price", "description", "active"]:
            if field in fields:
                updates.append(f"{field} = ?")
                params.append(fields[field])
        if not updates:
            return {"error": "没有可更新的字段"}
        params.append(fee_id)
        db_execute(f"UPDATE service_fees SET {', '.join(updates)}, updated_at=datetime('now','localtime') WHERE id=?", tuple(params))
        return {"message": "已更新"}

    def delete_fee(self, fee_id: int) -> Dict:
        db_execute("DELETE FROM service_fees WHERE id = ?", (fee_id,))
        return {"message": "已删除"}
