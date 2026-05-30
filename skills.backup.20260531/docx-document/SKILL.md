---
name: docx-document
description: "Generate Word documents for service agreements, maintenance reports, and formal letters. Invoke when user asks to create .docx files, service contracts, or formatted documents from ticket system data."
---

# DOCX Document Generator for Botong Ticket System

Generate professional Word documents — service agreements, maintenance reports, formal letters, and project documentation.

## When to Use

- User asks to generate a service agreement (包年服务协议)
- User needs a maintenance report in Word format
- User wants to create a formal letter or proposal
- User requests any .docx output from system data

## Quick Reference

| Task | Approach |
|------|----------|
| Create new document | Use `python-docx` library |
| Read existing document | `python-docx` or `pandoc` |
| Edit template | Load with `python-docx`, modify, save |

## Setup

```bash
pip install python-docx
```

## Document Templates

### Service Agreement (包年服务协议)

```python
from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

doc = Document()

style = doc.styles['Normal']
font = style.font
font.name = 'SimSun'
font.size = Pt(12)
style.element.rPr.rFonts.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia', 'SimSun')

title = doc.add_heading('', level=0)
run = title.add_run('IT运维服务协议')
run.font.size = Pt(22)
run.font.color.rgb = RGBColor(0x2E, 0x40, 0x57)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph('')
doc.add_paragraph(f'甲方：{client_name}')
doc.add_paragraph(f'乙方：博通IT运维服务')
doc.add_paragraph(f'协议编号：{agreement_no}')
doc.add_paragraph(f'签订日期：{sign_date}')
doc.add_paragraph('')

doc.add_heading('一、服务内容', level=1)
doc.add_paragraph(f'服务期限：{start_date} 至 {end_date}')
doc.add_paragraph(f'服务费用：¥{annual_fee:.2f}/年')
doc.add_paragraph(f'包含服务项目：{service_items}')

doc.add_heading('二、双方权利义务', level=1)
doc.add_paragraph('甲方应及时提供必要的协助和配合...')
doc.add_paragraph('乙方应按照约定提供专业、及时的IT运维服务...')

doc.add_heading('三、服务响应', level=1)
table = doc.add_table(rows=4, cols=3)
table.style = 'Light Grid Accent 1'
table.alignment = WD_TABLE_ALIGNMENT.CENTER

headers = ['故障级别', '响应时间', '解决时间']
for i, header in enumerate(headers):
    table.rows[0].cells[i].text = header

data = [
    ['紧急故障', '30分钟内', '4小时内'],
    ['一般故障', '2小时内', '8小时内'],
    ['常规服务', '4小时内', '24小时内'],
]
for row_idx, row_data in enumerate(data, 1):
    for col_idx, value in enumerate(row_data):
        table.rows[row_idx].cells[col_idx].text = value

doc.add_paragraph('')
doc.add_paragraph(f'甲方签章：________________    日期：________________')
doc.add_paragraph(f'乙方签章：________________    日期：________________')

doc.save('service_agreement.docx')
```

### Maintenance Report (维护报告)

```python
def generate_maintenance_report(ticket, client, items, materials):
    doc = Document()

    doc.add_heading('IT运维服务报告', level=0).alignment = WD_ALIGN_PARAGRAPH.CENTER

    info_table = doc.add_table(rows=4, cols=4)
    info_data = [
        ['客户名称', client.name, '工单编号', ticket.ticket_no],
        ['联系人', client.contact, '联系电话', client.phone],
        ['服务日期', ticket.created_at.strftime('%Y-%m-%d'), '完工日期',
         ticket.completed_at.strftime('%Y-%m-%d') if ticket.completed_at else ''],
        ['技术员', ', '.join(i.technician_name for i in items), '服务类型', ticket.service_type],
    ]
    for r, row_data in enumerate(info_data):
        for c, value in enumerate(row_data):
            cell = info_table.rows[r].cells[c]
            cell.text = value
            if c % 2 == 0:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.bold = True

    doc.add_heading('故障描述', level=1)
    doc.add_paragraph(ticket.description or '无')

    doc.add_heading('处理过程', level=1)
    for item in items:
        doc.add_paragraph(
            f'{item.technician_name} - {item.service_name} - '
            f'工时{item.hours}h - ¥{item.fee_amount:.2f}',
            style='List Bullet'
        )

    doc.add_heading('使用材料', level=1)
    if materials:
        mat_table = doc.add_table(rows=len(materials) + 1, cols=5)
        for i, h in enumerate(['材料名称', '规格', '数量', '单价', '金额']):
            mat_table.rows[0].cells[i].text = h
        for r, m in enumerate(materials, 1):
            mat_table.rows[r].cells[0].text = m.goods_name
            mat_table.rows[r].cells[1].text = m.specification or ''
            mat_table.rows[r].cells[2].text = str(m.quantity)
            mat_table.rows[r].cells[3].text = f'¥{m.unit_price:.2f}'
            mat_table.rows[r].cells[4].text = f'¥{m.total:.2f}'

    doc.add_heading('费用明细', level=1)
    doc.add_paragraph(f'劳务费用：¥{ticket.labor_fee:.2f}')
    doc.add_paragraph(f'材料费用：¥{ticket.material_fee:.2f}')
    doc.add_paragraph(f'交通费用：¥{ticket.travel_fee:.2f}')
    doc.add_paragraph(f'折扣：-¥{ticket.discount:.2f}')
    p = doc.add_paragraph(f'合计：¥{ticket.total_amount:.2f}')
    for run in p.runs:
        run.bold = True
        run.font.size = Pt(14)

    doc.save(f'report_{ticket.ticket_no}.docx')
```

## Chinese Font Configuration

```python
from docx.oxml.ns import qn

def set_chinese_font(doc, font_name='SimSun'):
    style = doc.styles['Normal']
    style.font.name = font_name
    style.element.rPr.rFonts.set(qn('w:eastAsia'), font_name)
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            run.font.name = font_name
            run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)
```

## Common Patterns

### Page Setup

```python
from docx.shared import Cm

section = doc.sections[0]
section.page_width = Cm(21)
section.page_height = Cm(29.7)
section.top_margin = Cm(2.54)
section.bottom_margin = Cm(2.54)
section.left_margin = Cm(3.17)
section.right_margin = Cm(3.17)
```

### Header/Footer

```python
section = doc.sections[0]
header = section.header
header_para = header.paragraphs[0]
header_para.text = '博通IT运维服务'
header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

footer = section.footer
footer_para = footer.paragraphs[0]
footer_para.text = f'第 {{PAGE}} 页'
footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
```

## Key Reminders

| Rule | Why |
|------|-----|
| Set Chinese font on both `font.name` and `rFonts.eastAsia` | python-docx needs both for CJK |
| Use `List Bullet` style for bullet lists | Never use unicode bullets manually |
| All amounts from AmountCalculator | Consistency with backend |
| Use `Decimal` for financial data | Avoid float precision errors |
| Set table style explicitly | Default tables look unprofessional |
| Bold header cells in info tables | Improves readability |
