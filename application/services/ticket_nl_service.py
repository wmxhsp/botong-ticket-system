import re
import json
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TicketNlService:
    STATUS_NAMES = {
        "open": "待处理", "in-progress": "进行中", "pending-payment": "待结算",
        "closed": "已完成", "cancelled": "已取消",
    }

    def __init__(self, ticket_service=None, client_service=None,
                 finance_service=None, equipment_service=None,
                 reminder_service=None):
        self._ticket_service = ticket_service
        self._client_service = client_service
        self._finance_service = finance_service
        self._equipment_service = equipment_service
        self._reminder_service = reminder_service

    def execute_nl_command(self, text):
        command = (text or "").strip()
        if not command:
            return {"error": "请输入命令"}
        cmd = command.lower()
        try:
            m = re.search(r"创建工单[：\s]*(.+?)维修(.+)", command)
            if m:
                return self._nl_create_ticket(m.group(1).strip(), m.group(2).strip())
            m = re.search(r"新建工单[：\s]*(.+)", command)
            if m:
                return self._nl_create_ticket(m.group(1).strip(), command)
            m = re.search(r"创建客户[：\s]*(.+?)(?:电话[：\s]*(\d+))?$", command)
            if m:
                return self._nl_create_client(m.group(1).strip(), m.group(2) or "")
            if re.search(r"(查看|显示|列出|查询|找).*工单", cmd):
                return self._nl_list_tickets(cmd)
            elif re.search(r"待处理|未处理|待办", cmd) and re.search(r"工单|订单|任务", cmd):
                return self._nl_list_tickets(cmd, status="open")
            elif re.search(r"进行中", cmd) and re.search(r"工单|订单|任务", cmd):
                return self._nl_list_tickets(cmd, status="in-progress")
            elif re.search(r"待结算|未收款|未结算", cmd):
                return self._nl_list_tickets(cmd, status="pending-payment")
            elif re.search(r"(已完成|完工)", cmd) and re.search(r"工单|订单", cmd):
                return self._nl_list_tickets(cmd, status="closed")
            elif re.search(r"逾期|超期|过期", cmd) and re.search(r"工单|订单|任务", cmd):
                return self._nl_overdue_tickets()
            elif re.search(r"(今天|今日).*工单|今日新增", cmd):
                return self._nl_today_tickets()
            elif re.search(r"多少.*工单|工单.*多少|一共.*工单|工单总数", cmd):
                return self._nl_ticket_count()
            elif re.search(r"(查看|显示|列出|查询|找).*客户", cmd):
                return self._nl_list_clients()
            elif re.search(r"(查看|显示|列出).*设备", cmd):
                return self._nl_list_equipment()
            elif re.search(r"(查看|显示|查).*通知|最近通知|未读通知", cmd):
                return self._nl_notifications()
            elif re.search(r"(本月|这个月).*(收入|财务|利润|支出)", cmd):
                return self._nl_finance_summary()
            elif re.search(r"(统计|分析|报表|汇总|概览)", cmd):
                return self._nl_stats()
            elif re.search(r"(帮助|help|功能|用法|命令)", cmd):
                return {"message": "我支持以下命令：<br>"
                    "• 查看/待处理/进行中/待结算/已完成工单<br>"
                    "• 逾期工单 / 今日工单 / 工单总数<br>"
                    "• 创建工单 客户XXX 维修XXX<br>"
                    "• 查看客户 / 创建客户 名称<br>"
                    "• 查看设备<br>"
                    "• 本月收入 / 财务汇总<br>"
                    "• 通知 / 未读通知<br>"
                    "• 统计 / 分析报表"}
            else:
                return {"error": f"抱歉，我不理解「{command}」。试试输入「帮助」查看支持的命令。"}
        except Exception as e:
            logger.error(f"NL command error: {e}")
            return {"error": f"处理失败: {str(e)}"}

    def _nl_create_ticket(self, client, description):
        try:
            data = {"client": client, "content": description, "description": description}
            result = self._ticket_service.create_ticket(data)
            ticket_id = result.get("id") or result.get("ticket", {}).get("id", "")
            return {"message": f"✅ 工单已创建<br>客户: {client}<br>内容: {description[:50]}",
                    "action_url": f"/tickets/{ticket_id}"}
        except Exception as e:
            return {"error": f"创建失败: {e}"}

    def _nl_create_client(self, name, phone=""):
        client_svc = self._client_service
        try:
            existing = client_svc.get_client(name) if client_svc and hasattr(client_svc, 'get_client') else None
            if existing:
                return {"message": f"客户「{name}」已存在", "action_url": f"/clients/{name}"}
            client_svc.create_client(name=name, phone=phone)
            return {"message": f"✅ 客户已创建<br>名称: {name}<br>电话: {phone or '无'}",
                    "action_url": "/clients"}
        except Exception as e:
            return {"error": f"创建失败: {e}"}

    def _nl_overdue_tickets(self):
        rows = self._ticket_service.get_overdue_tickets(limit=10)
        if not rows:
            return {"message": "✅ 无逾期工单"}
        html = "<div style='font-size:12px'>"
        for r in rows:
            sn = self.STATUS_NAMES.get(r.get("status", ""), r.get("status", ""))
            html += (f"<div style='padding:6px 0;border-bottom:1px solid var(--bt-gray-100)'>"
                     f"<strong>#{r['id']}</strong> {r['client']} "
                     f"<span style='color:#ef4444'>{sn}</span>"
                     f" <span style='color:var(--bt-text-muted);font-size:11px'>截止:{r.get('completion_date','')}</span></div>")
        html += "</div>"
        return {"message": f"⚠️ 找到 {len(rows)} 条逾期工单：<br>" + html, "action_url": "/tickets"}

    def _nl_today_tickets(self):
        today = datetime.now().strftime("%Y-%m-%d")
        data = self._ticket_service.list_tickets(date_from=today, page=1, per_page=10)
        rows = data.get("tickets", []) if isinstance(data, dict) else data
        if not rows:
            return {"message": "今日暂无新工单"}
        html = "<div style='font-size:12px'>"
        for r in rows:
            sn = self.STATUS_NAMES.get(r.get("status", ""), r.get("status", ""))
            html += (f"<div style='padding:6px 0;border-bottom:1px solid var(--bt-gray-100)'>"
                     f"<strong>#{r['id']}</strong> {r['client']} <span style='color:var(--bt-text-muted)'>({sn})</span></div>")
        html += "</div>"
        return {"message": f"今日新增 {len(rows)} 条工单：<br>" + html, "action_url": "/tickets"}

    def _nl_ticket_count(self):
        stats = self._ticket_service.get_status_stats()
        total = sum(stats.values())
        html = f"<div style='font-size:14px;padding:8px 0'>总工单: <strong>{total}</strong></div>"
        for status, count in stats.items():
            sn = self.STATUS_NAMES.get(status, status)
            html += f"<div style='padding:4px 0'>{sn}: {count}</div>"
        return {"message": html, "action_url": "/tickets"}

    def _nl_list_equipment(self):
        equip_svc = self._equipment_service
        if not equip_svc:
            return {"error": "设备服务不可用"}
        data = equip_svc.list_equipment(page=1, page_size=8)
        rows = data.get("items", data) if isinstance(data, dict) else data
        if not rows:
            return {"message": "暂无设备"}
        html = "<div style='font-size:12px'>"
        for r in rows:
            html += (f"<div style='padding:6px 0;border-bottom:1px solid var(--bt-gray-100)'>"
                     f"<strong>{r['name']}</strong>"
                     f"{' · ' + r['brand'] if r.get('brand') else ''}"
                     f" <span style='color:var(--bt-text-muted)'>{r.get('serial_no', '') or ''}</span></div>")
        html += "</div>"
        return {"message": f"设备列表 ({len(rows)} 台)：<br>" + html, "action_url": "/equipment"}

    def _nl_list_tickets(self, cmd, status=None):
        data = self._ticket_service.list_tickets(status=status, page=1, per_page=5)
        rows = data.get("tickets", []) if isinstance(data, dict) else data
        if not rows:
            return {"message": "暂无工单"}
        html = "<div style='font-size:12px'>"
        for r in rows:
            sn = self.STATUS_NAMES.get(r.get("status", ""), r.get("status", ""))
            html += (f"<div style='padding:6px 0;border-bottom:1px solid var(--bt-gray-100)'>"
                     f"<strong>#{r['id']}</strong> {r['client']} "
                     f"<span style='color:var(--bt-text-muted)'>¥{float(r.get('total', 0) or 0):.0f}</span>"
                     f" <span style='font-size:11px;color:var(--bt-text-muted)'>({sn})</span></div>")
        html += "</div>"
        return {"message": f"找到 {len(rows)} 条工单：<br>" + html,
                "action_url": "/tickets" + (f"?status={status}" if status else "")}

    def _nl_list_clients(self):
        client_svc = self._client_service
        rows = client_svc.list_clients()[:5] if client_svc and hasattr(client_svc, 'list_clients') else []
        if not rows:
            return {"message": "暂无客户"}
        html = "<div style='font-size:12px'>"
        for r in rows:
            html += (f"<div style='padding:6px 0;border-bottom:1px solid var(--bt-gray-100)'>"
                     f"<strong>{r['name']}</strong>"
                     f"{' · ' + r['phone'] if r.get('phone') else ''}"
                     f"{' · ' + r['contact'] if r.get('contact') else ''}</div>")
        html += "</div>"
        return {"message": f"最近客户 ({len(rows)} 条)：<br>" + html, "action_url": "/clients"}

    def _nl_notifications(self):
        try:
            svc = self._reminder_service
            notes = svc.get_all_notifications(limit=5) if svc and hasattr(svc, 'get_all_notifications') else []
        except Exception:
            notes = []
        if not notes:
            return {"message": "暂无通知"}
        html = "<div style='font-size:12px'>"
        for r in notes[:5]:
            html += (f"<div style='padding:6px 0;border-bottom:1px solid var(--bt-gray-100)'>"
                     f"{r.get('title', r.get('message', ''))} "
                     f"<span style='color:var(--bt-text-muted);font-size:11px'>{str(r.get('created_at','') or '')[:10]}</span></div>")
        html += "</div>"
        return {"message": f"最近通知 ({len(notes[:5])} 条)：<br>" + html}

    def _nl_finance_summary(self):
        finance_svc = self._finance_service
        if not finance_svc:
            return {"error": "财务服务不可用"}
        month = datetime.now().strftime("%Y-%m")
        month_start = month + "-01"
        today = datetime.now().strftime("%Y-%m-%d")
        inc = finance_svc.get_monthly_income(month_start, today)
        exp = finance_svc.get_monthly_expense(month_start, today)
        profit = inc - exp
        profit_color = "#10b981" if profit >= 0 else "#ef4444"
        return {"message": (f"<b>{month}</b> 财务概况：<br>"
                        f"收入：<b style='color:#10b981'>¥{inc:.2f}</b><br>"
                        f"支出：<b style='color:#ef4444'>¥{exp:.2f}</b><br>"
                        f"利润：<b style='color:{profit_color}'>¥{profit:.2f}</b>"),
                        "action_url": "/finance"}

    def _nl_stats(self):
        stats = self._ticket_service.get_status_stats()
        total = sum(stats.values())
        open_count = stats.get("open", 0)
        client_svc = self._client_service
        clients = client_svc.list_clients() if client_svc and hasattr(client_svc, 'list_clients') else []
        return {"message": f"系统概览：<br>"
                        f"总工单：<b>{total}</b> 单<br>"
                        f"总客户：<b>{len(clients)}</b> 个<br>"
                        f"待处理：<b>{open_count}</b> 单",
                        "action_url": "/stats"}
