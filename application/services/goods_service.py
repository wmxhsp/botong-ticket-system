from typing import Dict, Any


class GoodsService:

    def __init__(self, goods_repo=None, goods_svc=None):
        self._goods_repo = goods_repo
        self._goods_svc = goods_svc

    def _get_goods_repo(self):
        if self._goods_repo:
            return self._goods_repo
        if self._goods_svc:
            return self._goods_svc
        return None

    def list_with_summary(self, mode: str = None, q: str = None) -> Dict[str, Any]:
        repo = self._get_goods_repo()
        items = repo.list_goods(mode=mode, q=q)
        count = len(items)
        if items:
            low_stock = sum(1 for g in items if g.get("stock", 0) <= g.get("min_stock", 0))
            items_str = "、".join(f"{g.get('name','?')}(库存{g.get('stock',0)})" for g in items[:8])
            suffix = f"，等{count}种" if count > 8 else ""
            summary = f"共 {count} 种商品：{items_str}{suffix}"
            if low_stock:
                summary += f"，{low_stock} 种库存不足"
        else:
            summary = "暂无商品"
        return {"goods": items, "summary": summary}

    def list_goods(self, mode: str = None, q: str = None):
        return self._get_goods_repo().list_goods(mode=mode, q=q)

    def get_goods(self, goods_id: int):
        return self._get_goods_repo().get_goods(goods_id)

    def create_goods(self, data: dict):
        return self._get_goods_repo().create_goods(data)

    def update_goods(self, goods_id: int, **fields):
        return self._get_goods_repo().update_goods(goods_id, **fields)

    def delete_goods(self, goods_id: int):
        return self._get_goods_repo().delete_goods(goods_id)

    def get_inventory_overview(self):
        return self._get_goods_repo().get_inventory_overview()

    def list_categories(self):
        return self._get_goods_repo().list_categories()

    def get_category(self, category_id: int):
        return self._get_goods_repo().get_category(category_id)

    def create_category(self, name: str, icon: str = "", sort_order: int = 99):
        return self._get_goods_repo().create_category(name, icon, sort_order)

    def update_category(self, category_id: int, **fields):
        return self._get_goods_repo().update_category(category_id, **fields)

    def delete_category(self, category_id: int):
        return self._get_goods_repo().delete_category(category_id)

    def list_types(self, category_id: int = None):
        return self._get_goods_repo().list_types(category_id)

    def create_type(self, category_id: int, name: str, sort_order: int = 99):
        return self._get_goods_repo().create_type(category_id, name, sort_order)

    def update_type(self, type_id: int, **fields):
        return self._get_goods_repo().update_type(type_id, **fields)

    def delete_type(self, type_id: int):
        return self._get_goods_repo().delete_type(type_id)
