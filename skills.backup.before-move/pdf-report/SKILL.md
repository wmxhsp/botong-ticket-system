---
name: pdf-report
description: "Generate PDF invoices, settlement reports, and financial reports for the ticket system. Invoke when user asks to create PDF from ticket data, generate invoices, export settlement sheets, or produce financial reports."
---

# PDF Report Generator for Botong Ticket System

Generate professional PDF documents from ticket system data — invoices, settlement reports, financial summaries, and service reports.

## When to Use

- User asks to generate a PDF invoice from a ticket
- User wants a settlement report (结算单) for a completed ticket
- User needs a financial summary report
- User requests any PDF output from ticket/financial data

## Architecture

All PDF generation uses **reportlab** with Chinese font support. The project runs on macOS (STHeiti/Songti fonts available).

```
Ticket data → AmountCalculator → PDF template → reportlab rendering → .pdf file
```

## Mandatory Rules

### 1. Chinese Font Setup — ALWAYS First

Every reportlab script MUST call `setup_chinese_pdf()` before any other reportlab operation:

```python
import platform
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def setup_chinese_pdf():
    system = platform.system()
    if system == 'Darwin':
        candidates = [
            ('/System/Library/Fonts/STHeiti Light.ttc', 'STHeiti', 0),
            ('/System/Library/Fonts/STHeiti Medium.ttc', 'STHeitiMedium', 0),
            ('/System/Library/Fonts/Supplemental/Songti.ttc', 'Songti', 0),
        ]
    elif system == 'Windows':
        import os
        windir = os.environ.get('WINDIR', 'C:\\Windows')
        candidates = [
            (os.path.join(windir, 'Fonts', 'msyh.ttc'), 'MicrosoftYaHei', 0),
            (os.path.join(windir, 'Fonts', 'simhei.ttf'), 'SimHei', 0),
        ]
    else:
        candidates = [
            ('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', 'NotoSansCJK', 0),
        ]
    cn_font = None
    for font_path, font_name, idx in candidates:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path, subfontIndex=idx))
                cn_font = font_name
                break
            except Exception:
                continue
    if cn_font is None:
        raise RuntimeError(f"No CJK font found on {system}")
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        if isinstance(style, ParagraphStyle):
            style.fontName = cn_font
    return cn_font, styles
```

### 2. NEVER Use Helvetica/Times-Roman for Chinese

These Latin-only fonts cause Chinese characters to render as blank boxes silently (no error, just broken output).

### 3. All Amounts Must Come from AmountCalculator

Never compute fees inline. Always use `domain/amount_calculator.py`:

```python
from domain.amount_calculator import AmountCalculator

calc = AmountCalculator()
labor_fee = calc.calc_labor_fee(billing_type, hours, days, package_cost, fee_rate)
labor_cost = calc.calc_labor_cost(billing_type, hours, days, package_cost, cost_rate_lookup)
material_fee = calc.calc_material_fee(materials)
total = calc.calc_total(labor_fee, material_fee, travel_fee, discount)
```

## Document Templates

### Invoice (结算单)

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER

cn_font, styles = setup_chinese_pdf()

title_style = ParagraphStyle('CnTitle', parent=styles['Title'], fontSize=20, alignment=TA_CENTER)
body_style = ParagraphStyle('CnBody', parent=styles['Normal'], fontSize=11, leading=18)

doc = SimpleDocTemplate("settlement.pdf", pagesize=A4)

header_data = [
    [Paragraph('客户名称', styles['Normal']), Paragraph(client_name, styles['Normal']),
     Paragraph('工单编号', styles['Normal']), Paragraph(ticket_no, styles['Normal'])],
    [Paragraph('服务日期', styles['Normal']), Paragraph(service_date, styles['Normal']),
     Paragraph('完工日期', styles['Normal']), Paragraph(completion_date, styles['Normal'])],
]

service_header = [
    Paragraph('服务项目', styles['Normal']),
    Paragraph('技术员', styles['Normal']),
    Paragraph('计费模式', styles['Normal']),
    Paragraph('工时/天数', styles['Normal']),
    Paragraph('费率', styles['Normal']),
    Paragraph('金额', styles['Normal']),
]

material_header = [
    Paragraph('材料名称', styles['Normal']),
    Paragraph('规格', styles['Normal']),
    Paragraph('数量', styles['Normal']),
    Paragraph('单价', styles['Normal']),
    Paragraph('金额', styles['Normal']),
]

story = [
    Paragraph("博通IT运维服务结算单", title_style),
    Spacer(1, 12),
    Table(header_data, colWidths=[80, 120, 80, 120]),
    Spacer(1, 20),
    Paragraph("服务明细", ParagraphStyle('H2', parent=styles['Heading2'], fontSize=14)),
    Table([service_header] + service_rows, colWidths=[100, 60, 60, 60, 60, 80]),
    Spacer(1, 20),
    Paragraph("材料明细", ParagraphStyle('H2', parent=styles['Heading2'], fontSize=14)),
    Table([material_header] + material_rows, colWidths=[100, 80, 60, 80, 80]),
    Spacer(1, 20),
    Paragraph(f"劳务收入: ¥{labor_fee:.2f}", body_style),
    Paragraph(f"材料费用: ¥{material_fee:.2f}", body_style),
    Paragraph(f"交通费用: ¥{travel_fee:.2f}", body_style),
    Paragraph(f"折扣: -¥{discount:.2f}", body_style),
    Paragraph(f"合计: ¥{total:.2f}", ParagraphStyle('Total', parent=body_style, fontSize=14, fontName=cn_font)),
]

doc.build(story)
```

### Financial Summary Report

```python
story = [
    Paragraph("财务汇总报告", title_style),
    Paragraph(f"报告期间: {start_date} ~ {end_date}", body_style),
    Spacer(1, 12),
    Paragraph("收入统计", ParagraphStyle('H2', parent=styles['Heading2'])),
    Table(income_data, colWidths=[150, 100, 100]),
    Spacer(1, 12),
    Paragraph("支出统计", ParagraphStyle('H2', parent=styles['Heading2'])),
    Table(expense_data, colWidths=[150, 100, 100]),
    Spacer(1, 12),
    Paragraph("利润分析", ParagraphStyle('H2', parent=styles['Heading2'])),
    Table(profit_data, colWidths=[150, 100, 100]),
]
```

## Table Styling

```python
common_table_style = TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E4057')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('FONTNAME', (0, 0), (-1, -1), cn_font),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
])
```

## Canvas API Pattern

For precise positioning (headers, footers, watermarks):

```python
from reportlab.pdfgen import canvas

c = canvas.Canvas("output.pdf", pagesize=A4)
width, height = A4

c.setFont(cn_font, 10)
c.drawString(30, 30, f"博通IT运维 · 第 {page_num} 页")

c.save()
```

## Integration with Ticket System

PDF generation should be triggered from the application service layer:

```python
class TicketService:
    def generate_settlement_pdf(self, ticket_id):
        ticket = self.ticket_repo.get_by_id(ticket_id)
        client = self.client_repo.get_by_id(ticket.client_id)
        items = self.service_item_repo.get_by_ticket(ticket_id)
        materials = self.material_repo.get_by_ticket(ticket_id)

        calc = AmountCalculator()
        labor_fee = calc.calc_labor_fee(...)
        material_fee = calc.calc_material_fee(materials)
        total = calc.calc_total(labor_fee, material_fee, travel_fee, discount)

        pdf_path = self._render_settlement_pdf(ticket, client, items, materials, total)
        return pdf_path
```

## Key Reminders

| Rule | Why |
|------|-----|
| Always call `setup_chinese_pdf()` first | Without it, Chinese renders as blank boxes |
| Use `Paragraph(text, styles['Normal'])` for table cells | `TableStyle FONTNAME` is ignored for Paragraph cells |
| All amounts from `AmountCalculator` | No scattered fee calculations |
| Use `Decimal` for financial calculations | Avoid float precision errors |
| Wrap cell text in `Paragraph` | Required for CJK text in tables |
| Set `c.setFont(cn_font, size)` before every Canvas draw | Font is NOT inherited between draw calls |
