import re
import logging

logger = logging.getLogger(__name__)

_PINYIN_MAP = {
    '张': 'zh', '王': 'w', '李': 'l', '赵': 'zh', '刘': 'l', '陈': 'ch',
    '杨': 'y', '黄': 'h', '周': 'zh', '吴': 'w', '徐': 'x', '孙': 's',
    '马': 'm', '胡': 'h', '朱': 'zh', '郭': 'g', '何': 'h', '林': 'l',
    '罗': 'l', '高': 'g', '梁': 'l', '宋': 's', '唐': 't', '许': 'x',
    '韩': 'h', '冯': 'f', '邓': 'd', '曹': 'c', '彭': 'p', '曾': 'z',
    '肖': 'x', '田': 't', '董': 'd', '潘': 'p', '袁': 'y', '蔡': 'c',
    '蒋': 'j', '余': 'y', '杜': 'd', '叶': 'y', '程': 'ch', '苏': 's',
    '魏': 'w', '吕': 'l', '丁': 'd', '任': 'r', '沈': 'sh', '姚': 'y',
    '卢': 'l', '傅': 'f', '钟': 'zh', '崔': 'c', '谭': 't',
    '蒙': 'm', '古': 'g', '族': 'z', '中': 'zh', '学': 'x',
    '北': 'b', '京': 'j', '能': 'n', '源': 'y',
    '电': 'd', '脑': 'n', '打': 'd', '印': 'y', '机': 'j',
    '服': 'f', '务': 'w', '器': 'q', '投': 't', '影': 'y',
    '空': 'k', '调': 't', '网': 'w', '络': 'l', '监': 'j',
    '控': 'k', '门': 'm', '禁': 'j', '摄': 's', '像': 'x',
    '头': 't', '电': 'd', '话': 'h', '手': 'sh', '箱': 'x',
    '大': 'd', '厦': 's', '楼': 'l', '公': 'g', '司': 's',
    '院': 'y', '校': 'x', '店': 'd', '厂': 'ch', '部': 'b',
    '办': 'b', '室': 'sh', '维': 'w', '修': 'x', '安': 'a',
    '装': 'zh', '保': 'b', '养': 'y', '培': 'p', '训': 'x',
    '普': 'p', '通': 't', '紧': 'j', '急': 'j',
    '本': 'b', '月': 'y', '下': 'x', '年': 'n',
}


class SearchService:

    def __init__(self, ticket_service=None, equipment_service=None,
                 client_service=None, goods_service=None,
                 supplier_service=None, service_fee_service=None,
                 todo_service=None, reminder_service=None):
        self._ticket_service = ticket_service
        self._equipment_service = equipment_service
        self._client_service = client_service
        self._goods_service = goods_service
        self._supplier_service = supplier_service
        self._service_fee_service = service_fee_service
        self._todo_service = todo_service
        self._reminder_service = reminder_service

    def _get_ticket_service(self):
        return self._ticket_service

    def _get_equipment_service(self):
        return self._equipment_service

    def _get_client_service(self):
        return self._client_service

    def _get_goods_service(self):
        return self._goods_service

    def _get_supplier_service(self):
        return self._supplier_service

    def _get_service_fee_service(self):
        return self._service_fee_service

    def _get_todo_service(self):
        return self._todo_service

    def _get_reminder_service(self):
        return self._reminder_service

    @staticmethod
    def _get_pinyin_initials(text):
        result = ""
        for ch in text:
            if '\u4e00' <= ch <= '\u9fff':
                result += _PINYIN_MAP.get(ch, ch.lower())
            else:
                result += ch.lower()
        return result

    @staticmethod
    def _pinyin_fuzzy_match(query, text):
        if not query or not text:
            return False
        q_py = SearchService._get_pinyin_initials(query.lower())
        t_py = SearchService._get_pinyin_initials(text.lower())
        return q_py in t_py

    @staticmethod
    def _highlight(text, keyword):
        if not keyword or not text:
            return text
        try:
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            return pattern.sub(lambda m: f"**{m.group(0)}**", str(text))
        except Exception:
            return str(text)

    def global_search(self, query):
        q = (query or "").strip()
        if not q or len(q) < 1:
            return {"results": {
                "tickets": [], "equipment": [], "clients": [],
                "goods": [], "suppliers": [], "service_fees": [],
                "todos": [], "notifications": []
            }}

        results = {}
        q_lower = q.lower()
        q_py = self._get_pinyin_initials(q_lower)

        ticket_svc = self._get_ticket_service()
        equip_svc = self._get_equipment_service()
        client_svc = self._get_client_service()

        tickets = ticket_svc.search_tickets(q, 8)
        seen_ticket_ids = {t["id"] for t in tickets}
        if q_py != q_lower:
            try:
                all_tickets = ticket_svc.search_tickets("", 100)
                for t in all_tickets:
                    if t["id"] not in seen_ticket_ids and (
                        self._pinyin_fuzzy_match(q, t.get("client", "")) or
                        self._pinyin_fuzzy_match(q, t.get("content", "") or t.get("description", ""))
                    ):
                        tickets.append(t)
                        seen_ticket_ids.add(t["id"])
                        if len(tickets) >= 10:
                            break
            except Exception:
                pass

        results["tickets"] = [
            {"id": t["id"], "ticket_no": self._highlight(t["ticket_no"], q),
             "client": self._highlight(t["client"], q), "status": t["status"],
             "status_name": ticket_svc.STATUS_NAMES.get(t["status"], t["status"]),
             "description": self._highlight((t.get("content") or t.get("description") or "")[:60], q),
             "url": f"/tickets/{t['id']}"}
            for t in tickets
        ]

        equipment = equip_svc.search_equipment(q, 6)
        seen_equip_ids = {e["id"] for e in equipment}
        if q_py != q_lower:
            try:
                all_equip = equip_svc.list_equipment(page=1, page_size=100).get("items", [])
                for e in all_equip:
                    if e["id"] not in seen_equip_ids and (
                        self._pinyin_fuzzy_match(q, e.get("name", "")) or self._pinyin_fuzzy_match(q, e.get("client", ""))
                    ):
                        equipment.append(e)
                        seen_equip_ids.add(e["id"])
                        if len(equipment) >= 8:
                            break
            except Exception:
                pass

        results["equipment"] = [
            {"id": e["id"], "name": self._highlight(e["name"], q),
             "serial_no": self._highlight(e.get("serial_no", "") or "", q),
             "model": e.get("model", ""), "client": self._highlight(e.get("client", ""), q),
             "location": e.get("location", ""), "url": f"/equipment/{e['id']}"}
            for e in equipment
        ]

        clients = client_svc.search_clients(q, 5) if hasattr(client_svc, 'search_clients') else []
        seen_client_names = {c["name"] for c in clients}
        if q_py != q_lower:
            try:
                all_clients = client_svc.list_clients() if hasattr(client_svc, 'list_clients') else []
                for c in all_clients:
                    cname = c.get("name", "")
                    if cname not in seen_client_names and self._pinyin_fuzzy_match(q, cname):
                        clients.append(c)
                        seen_client_names.add(cname)
                        if len(clients) >= 8:
                            break
            except Exception:
                pass
        results["clients"] = [
            {"name": self._highlight(c["name"], q), "contact": self._highlight(c.get("contact", ""), q),
             "phone": c.get("phone", ""), "url": f"/clients/{c['name']}"}
            for c in clients
        ]

        results["goods"] = []
        try:
            goods_svc = self._get_goods_service()
            if goods_svc and hasattr(goods_svc, 'search_goods'):
                goods = goods_svc.search_goods(q, 8)
            elif goods_svc and hasattr(goods_svc, 'list_goods'):
                all_goods = goods_svc.list_goods()
                goods = [g for g in all_goods if q.lower() in (g.get("name", "") or "").lower() or q.lower() in (g.get("category", "") or "").lower()][:8]
            else:
                goods = []
            if q_py != q_lower and not goods:
                try:
                    all_goods = goods_svc.list_goods() if goods_svc and hasattr(goods_svc, 'list_goods') else []
                    goods = [g for g in all_goods if self._pinyin_fuzzy_match(q, g.get("name", ""))][:8]
                except Exception:
                    pass
            results["goods"] = [
                {"id": g["id"], "name": self._highlight(g["name"], q), "category": g.get("category", ""),
                 "unit": g.get("unit", ""), "price": g.get("selling_price", g.get("retail_price", 0))}
                for g in goods
            ]
        except Exception as e:
            logger.warning(f"Goods search failed: {e}")

        results["suppliers"] = []
        try:
            supplier_svc = self._get_supplier_service()
            if supplier_svc and hasattr(supplier_svc, 'search_suppliers'):
                suppliers = supplier_svc.search_suppliers(q, 5)
            elif supplier_svc and hasattr(supplier_svc, 'list_suppliers'):
                all_sup = supplier_svc.list_suppliers()
                suppliers = [s for s in all_sup if q.lower() in (s.get("name", "") or "").lower() or q.lower() in (s.get("contact", "") or "").lower()][:5]
            else:
                suppliers = []
            if q_py != q_lower and not suppliers:
                try:
                    all_sup = supplier_svc.list_suppliers() if supplier_svc and hasattr(supplier_svc, 'list_suppliers') else []
                    suppliers = [s for s in all_sup if self._pinyin_fuzzy_match(q, s.get("name", ""))][:5]
                except Exception:
                    pass
            results["suppliers"] = [
                {"id": s["id"], "name": self._highlight(s["name"], q), "contact": s.get("contact", ""), "phone": s.get("phone", "")}
                for s in suppliers
            ]
        except Exception as e:
            logger.warning(f"Supplier search failed: {e}")

        results["service_fees"] = []
        try:
            fee_svc = self._get_service_fee_service()
            if fee_svc and hasattr(fee_svc, 'search_fees'):
                fees = fee_svc.search_fees(q, 5)
            elif fee_svc and hasattr(fee_svc, 'list_service_fees'):
                all_fees = fee_svc.list_service_fees()
                fees = [f for f in all_fees if q.lower() in (f.get("name", "") or "").lower()][:5]
            else:
                fees = []
            if q_py != q_lower and not fees:
                try:
                    all_fees = fee_svc.list_service_fees() if fee_svc and hasattr(fee_svc, 'list_service_fees') else []
                    fees = [f for f in all_fees if self._pinyin_fuzzy_match(q, f.get("name", ""))][:5]
                except Exception:
                    pass
            results["service_fees"] = [
                {"id": f["id"], "name": self._highlight(f["name"], q), "type": f.get("type", f.get("fee_type", "")),
                 "price": f.get("unit_price", 0), "cost": f.get("cost", f.get("cost_price", 0))}
                for f in fees
            ]
        except Exception as e:
            logger.warning(f"Service fee search failed: {e}")

        results["todos"] = []
        try:
            todo_svc = self._get_todo_service()
            if todo_svc and hasattr(todo_svc, 'search_todos'):
                todos = todo_svc.search_todos(q, 5)
            elif todo_svc and hasattr(todo_svc, 'list_todos'):
                all_todos = todo_svc.list_todos()
                todos = [t for t in all_todos if q.lower() in (t.get("title", "") or "").lower()][:5]
            else:
                todos = []
            results["todos"] = [
                {"id": t["id"], "title": self._highlight(t["title"], q), "due_date": t.get("due_date", ""),
                 "status": "completed" if t.get("done") else "pending", "url": "/todos"}
                for t in todos
            ]
        except Exception as e:
            logger.warning(f"Todo search failed: {e}")

        results["notifications"] = []
        try:
            reminder_svc = self._get_reminder_service()
            if reminder_svc and hasattr(reminder_svc, 'get_all_notifications'):
                all_notes = reminder_svc.get_all_notifications(limit=100)
                notes = [n for n in all_notes if q.lower() in (n.get("title", "") or "").lower() or q.lower() in (n.get("content", "") or "").lower()][:5]
                results["notifications"] = [
                    {"id": n["id"], "title": self._highlight(n.get("title", ""), q),
                     "message": self._highlight((n.get("content", "") or "")[:50], q),
                     "unread": not n.get("read", True), "created_at": n.get("created_at", "")}
                    for n in notes
                ]
        except Exception as e:
            logger.warning(f"Notification search failed: {e}")

        count_map = {k: len(v) for k, v in results.items()}
        parts = [f"{c} 条{v}" for v, c in zip(
            ["工单", "设备", "客户", "商品", "供应商", "服务项目", "待办", "通知"],
            [count_map.get(k, 0) for k in ["tickets", "equipment", "clients", "goods",
                                            "suppliers", "service_fees", "todos", "notifications"]]
        ) if c > 0]
        summary = f"搜索「{q}」找到 {', '.join(parts)}" if parts else f"搜索「{q}」无匹配结果"
        if not parts and q_py != q_lower:
            summary += "（已尝试拼音模糊匹配）"

        return {"results": results, "summary": summary, "total": sum(count_map.values())}
