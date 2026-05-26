from typing import Dict, Any


class SupplierService:

    def __init__(self, supplier_repo=None, supplier_svc=None):
        self._supplier_repo = supplier_repo
        self._supplier_svc = supplier_svc

    def _get_supplier_repo(self):
        if self._supplier_repo:
            return self._supplier_repo
        if self._supplier_svc:
            return self._supplier_svc
        raise RuntimeError("SupplierService: supplier_repo not injected")

    def get_supplier_performance_summary(self) -> Dict[str, Any]:
        repo = self._get_supplier_repo()
        stats = repo.get_supplier_performance()
        total_spent = sum(float(s.get("total_spent", 0) or 0) for s in stats)
        total_unpaid = sum(float(s.get("unpaid_amount", 0) or 0) for s in stats)
        summary = f"共 {len(stats)} 家供应商，累计采购 ¥{total_spent:.2f}，未付 ¥{total_unpaid:.2f}"
        return {
            "stats": stats,
            "total_spent": round(total_spent, 2),
            "total_unpaid": round(total_unpaid, 2),
            "summary": summary,
        }

    def list_suppliers(self):
        return self._get_supplier_repo().list_suppliers()

    def create_supplier(self, data: dict):
        return self._get_supplier_repo().create_supplier(data)

    def get_supplier(self, sup_id: int):
        return self._get_supplier_repo().get_supplier(sup_id)

    def update_supplier(self, sup_id: int, **fields):
        return self._get_supplier_repo().update_supplier(sup_id, **fields)

    def delete_supplier(self, sup_id: int):
        return self._get_supplier_repo().delete_supplier(sup_id)

    def get_supplier_performance(self):
        return self._get_supplier_repo().get_supplier_performance()
