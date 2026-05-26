import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PurchaseService:

    def __init__(self, purchase_repo=None, inventory_service=None, finance_service=None):
        self._repo = purchase_repo
        self._inventory_service = inventory_service
        self._finance_service = finance_service

    def _get_repo(self):
        return self._repo

    def _get_inventory_svc(self):
        return self._inventory_service

    def _get_finance_svc(self):
        return self._finance_service

    def list_purchase_orders(self):
        return self._get_repo().list_purchase_orders()

    def get_purchase_order(self, po_id):
        return self._get_repo().get_purchase_order(po_id)

    def get_purchase_items(self, po_id):
        return self._get_repo().get_purchase_items(po_id)

    def get_purchase_item(self, item_id):
        return self._get_repo().get_purchase_item(item_id)

    def get_purchase_stats(self):
        return self._get_repo().get_purchase_stats()

    def get_unpaid_orders(self):
        return self._get_repo().get_unpaid_orders()

    def delete_purchase_order(self, po_id):
        return self._get_repo().delete_purchase_order(po_id)

    def count_purchase_orders(self):
        return self._get_repo().count_purchase_orders()

    def complete_purchase_order(self, po_id, now=None):
        now = now or datetime.now().strftime("%Y-%m-%d %H:%M")
        repo = self._get_repo()
        inv_svc = self._get_inventory_svc()
        fin_svc = self._get_finance_svc()
        po_no = repo.get_po_no(po_id)
        items = repo.get_purchase_items(po_id)

        repo.update_purchase_status(po_id, "completed")
        for item in items:
            remaining = item["quantity"] - item.get("received_qty", 0)
            if remaining > 0:
                for i in range(remaining):
                    serial = f"{item['goods_name'][:4]}{now.replace('-','').replace(' ','').replace(':','')[-8:]}-{i+1:02d}"
                    inv_svc.create_inventory_item(
                        goods_id=item["goods_id"], serial_no=serial,
                        batch_no=po_no, location="库房", status="in_stock",
                        purchase_order_id=po_id, unit_cost=item["unit_cost"],
                        received_at=now, created_at=now
                    )
                repo.update_item_received_qty(item["id"], item["quantity"])
                total = remaining * item["unit_cost"]
                fin_svc.add_expense(
                    category="采购", vendor="", amount=total,
                    description=f"采购 {item['goods_name']} x{remaining} (单号{po_no})",
                    paid_at=now
                )

        for item in items:
            try:
                inv_svc.update_weighted_cost(item["goods_id"])
            except Exception as e:
                logger.warning(f"更新加权成本失败: {e}")

    def list_with_summary(self):
        orders = self._get_repo().list_purchase_orders()
        count = len(orders)
        if orders:
            draft_count = sum(1 for o in orders if o.get("status") == "draft")
            received_count = sum(1 for o in orders if o.get("status") in ("completed", "partial"))
            vendors = set(o.get("vendor", "") for o in orders)
            summary = f"共 {count} 单采购（{draft_count} 单草稿，{received_count} 单已收货），供应商：{'、'.join(v for v in vendors if v)[:30]}"
        else:
            summary = "暂无采购单"
        return {"orders": orders, "summary": summary}

    def receive_and_stock(self, item_id, receive_qty):
        repo = self._get_repo()
        item = repo.get_purchase_item(item_id)
        if not item:
            return None
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        po_no = repo.get_po_no(item["po_id"])
        remaining = item["quantity"] - item["received_qty"]
        actual_qty = min(receive_qty, remaining)
        inv_svc = self._get_inventory_svc()
        fin_svc = self._get_finance_svc()

        for i in range(actual_qty):
            serial = f"{item['goods_name'][:4]}{now.replace('-','').replace(' ','').replace(':','')[-8:]}-{i+1:02d}"
            inv_svc.create_inventory_item(
                goods_id=item["goods_id"], serial_no=serial,
                batch_no=po_no, location="库房", status="in_stock",
                purchase_order_id=item["po_id"], unit_cost=item["unit_cost"],
                received_at=now, created_at=now
            )

        new_received = item["received_qty"] + actual_qty
        repo.update_received_qty(item_id, new_received)

        summary = repo.get_po_summary(item["po_id"])
        total_qty = summary.get("total_qty", 0) or 0
        total_recv = summary.get("total_recv", 0) or 0
        new_po_status = "completed" if total_recv >= total_qty else "partial"
        repo.update_purchase_status(item["po_id"], new_po_status)

        cost = actual_qty * item["unit_cost"]
        fin_svc.add_expense(
            category="采购", vendor="", amount=cost,
            description=f"采购 {item['goods_name']} x{actual_qty} (单号{po_no})",
            paid_at=now
        )

        try:
            inv_svc.update_weighted_cost(item["goods_id"])
        except Exception as e:
            logger.warning(f"更新加权成本失败: {e}")

        return {"message": f"已收货 {item['goods_name']} x{actual_qty}"}

    def process_payment(self, po_id, amount, method="银行转账"):
        repo = self._get_repo()
        po = repo.get_purchase_order(po_id)
        if not po:
            return None
        if po.get("payment_status") == "paid":
            return {"error": "该采购单已全部付款"}
        total = float(po.get("total_amount", 0) or 0)
        if total <= 0:
            items = repo.get_purchase_items(po_id)
            total = sum(float(i.get("total_cost", 0) or 0) for i in items)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        if amount <= 0 or amount >= total:
            amount = total
            new_status = "paid"
        else:
            new_status = "partial"
        repo.confirm_payment(po_id, amount=amount, method=method, status=new_status, now=now)
        summary = f"采购单 {po.get('po_no', '')} 已付款 ¥{amount:.2f}（{method}），状态：{'全额付款' if new_status == 'paid' else '部分付款'}"
        return {"message": summary, "summary": summary, "payment_status": new_status, "amount_paid": amount}

    def create_with_summary(self, vendor, items, notes="", auto_receive=False):
        repo = self._get_repo()
        po_count = repo.count_purchase_orders()
        po_no = f"PO-{datetime.now().strftime('%Y%m%d')}-{po_count + 1:03d}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        if auto_receive:
            result = self._create_and_complete(repo, po_no, vendor, now, notes, items)
            item_count = len(items)
            summary = f"采购单 {po_no} 已创建并入库：{vendor}，共 {item_count} 种商品"
            return {"message": f"采购单 {po_no} 已创建并入库", "summary": summary, "po_no": po_no, "id": result["id"]}
        else:
            result = repo.create_purchase_order(
                po_no=po_no, vendor=vendor, purchase_date=now,
                notes=notes, items=items)
            item_count = len(items)
            summary = f"采购单 {po_no} 已创建（草稿）：{vendor}，共 {item_count} 种商品"
            return {"message": f"采购单 {po_no} 已创建（草稿）", "summary": summary, "po_no": po_no, "id": result["id"]}

    def _create_and_complete(self, repo, po_no, vendor, now, notes, items):
        inv_svc = self._get_inventory_svc()
        fin_svc = self._get_finance_svc()
        result = repo.create_and_complete_order(po_no, vendor, now, notes, items)
        po_items = repo.get_purchase_items(result["id"])
        for item in po_items:
            remaining = item["quantity"] - item.get("received_qty", 0)
            if remaining > 0:
                for i in range(remaining):
                    serial = f"{item['goods_name'][:4]}{now.replace('-','').replace(' ','').replace(':','')[-8:]}-{i+1:02d}"
                    inv_svc.create_inventory_item(
                        goods_id=item["goods_id"], serial_no=serial,
                        batch_no=po_no, location="库房", status="in_stock",
                        purchase_order_id=result["id"], unit_cost=item["unit_cost"],
                        received_at=now, created_at=now
                    )
                repo.update_item_received_qty(item["id"], item["quantity"])
                inv_svc.update_weighted_cost(item["goods_id"])
                total = remaining * item["unit_cost"]
                fin_svc.add_expense(
                    category="采购", vendor=vendor, amount=total,
                    description=f"采购 {item['goods_name']} x{remaining} (单号{po_no})",
                    paid_at=now)
        return result
