---
name: xlsx-export
description: "Export ticket, financial, and inventory data to professional Excel files. Invoke when user asks to export data to Excel, create spreadsheets from system data, or generate xlsx reports."
---

# XLSX Export for Botong Ticket System

Export ticket system data to professional Excel spreadsheets — ticket lists, financial reports, inventory summaries, and client statements.

## When to Use

- User asks to export ticket list to Excel
- User needs a financial report in xlsx format
- User wants to export inventory data
- User requests any spreadsheet output from system data

## Library Selection

| Task | Library | Reason |
|------|---------|--------|
| Data analysis / bulk export | pandas | Fast, concise |
| Formatted reports with formulas | openpyxl | Cell-level control |
| Simple CSV export | pandas → `to_csv(encoding='utf-8-sig')` | Excel-compatible |

## CSV Encoding Rules

**CRITICAL**: Always use `utf-8-sig` (UTF-8 with BOM) for CSV files opened in Excel:

```python
df.to_csv('output.csv', encoding='utf-8-sig')  # BOM included — Excel recognises UTF-8
```

| Target | Encoding |
|--------|----------|
| Excel (any platform) | `utf-8-sig` |
| macOS Numbers.app | `utf-8` (no BOM) |
| Command-line tools | `utf-8` (no BOM) |
| Unknown / general | `utf-8-sig` |

## Export Templates

### Ticket List Export

```python
import pandas as pd
from datetime import datetime

def export_tickets(tickets):
    rows = []
    for t in tickets:
        rows.append({
            '工单编号': t.ticket_no,
            '客户名称': t.client_name,
            '服务类型': t.service_type,
            '状态': t.status,
            '创建时间': t.created_at.strftime('%Y-%m-%d %H:%M'),
            '完工时间': t.completed_at.strftime('%Y-%m-%d %H:%M') if t.completed_at else '',
            '劳务收入': t.labor_fee,
            '材料费用': t.material_fee,
            '交通费用': t.travel_fee,
            '折扣': t.discount,
            '合计': t.total_amount,
        })
    df = pd.DataFrame(rows)
    df.to_excel('tickets_export.xlsx', index=False, sheet_name='工单列表')
```

### Financial Report with Formulas

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

wb = Workbook()
ws = wb.active
ws.title = "财务报表"

header_font = Font(bold=True, color='FFFFFF', size=11)
header_fill = PatternFill('solid', fgColor='2E4057')
header_align = Alignment(horizontal='center', vertical='center')
thin_border = Border(
    left=Side(style='thin', color='CCCCCC'),
    right=Side(style='thin', color='CCCCCC'),
    top=Side(style='thin', color='CCCCCC'),
    bottom=Side(style='thin', color='CCCCCC'),
)

headers = ['项目', '收入', '成本', '利润', '利润率']
for col, header in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=header)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = header_align
    cell.border = thin_border

row = 2
for item in financial_items:
    ws.cell(row=row, column=1, value=item.name).border = thin_border
    ws.cell(row=row, column=2, value=item.revenue).border = thin_border
    ws.cell(row=row, column=3, value=item.cost).border = thin_border
    ws.cell(row=row, column=4).border = thin_border
    ws[f'D{row}'] = f'=B{row}-C{row}'
    ws.cell(row=row, column=5).border = thin_border
    ws[f'E{row}'] = f'=IF(B{row}=0,0,D{row}/B{row})'
    ws[f'E{row}'].number_format = '0.0%'
    row += 1

ws.cell(row=row, column=1, value='合计').font = Font(bold=True)
ws[f'B{row}'] = f'=SUM(B2:B{row-1})'
ws[f'C{row}'] = f'=SUM(C2:C{row-1})'
ws[f'D{row}'] = f'=SUM(D2:D{row-1})'
ws[f'E{row}'] = f'=IF(B{row}=0,0,D{row}/B{row})'
ws[f'E{row}'].number_format = '0.0%'

ws.column_dimensions['A'].width = 20
ws.column_dimensions['B'].width = 15
ws.column_dimensions['C'].width = 15
ws.column_dimensions['D'].width = 15
ws.column_dimensions['E'].width = 12

wb.save('financial_report.xlsx')
```

### Inventory Export

```python
def export_inventory(items):
    rows = []
    for item in items:
        rows.append({
            '商品名称': item.name,
            '分类': item.category,
            '规格': item.specification,
            '单位': item.unit,
            '进价': item.purchase_price,
            '售价': item.selling_price,
            '库存数量': item.quantity,
            '库存金额': item.purchase_price * item.quantity,
            '仓库': item.warehouse_name,
        })
    df = pd.DataFrame(rows)
    df['进价'] = df['进价'].apply(lambda x: f'¥{x:.2f}')
    df['售价'] = df['售价'].apply(lambda x: f'¥{x:.2f}')
    df['库存金额'] = df['库存金额'].apply(lambda x: f'¥{x:.2f}')
    df.to_excel('inventory_export.xlsx', index=False, sheet_name='库存明细')
```

## Financial Model Color Coding

| Color | Usage | RGB |
|-------|-------|-----|
| Blue text | Hardcoded inputs | 0,0,255 |
| Black text | Formulas and calculations | 0,0,0 |
| Green text | Cross-sheet references | 0,128,0 |
| Yellow background | Key assumptions | 255,255,0 |

## Number Formatting

| Type | Format |
|------|--------|
| Currency | `¥#,##0.00` |
| Percentage | `0.0%` |
| Zero display | `¥#,##0.00;(¥#,##0.00);"-"` |
| Negative | Parentheses `(123)` not minus `-123` |

## Formula Rules

- **ALWAYS use Excel formulas** instead of hardcoded Python calculations
- Place assumptions in separate cells, reference them in formulas
- Use `=SUM()`, `=AVERAGE()`, `=IF()` for dynamic spreadsheets
- Verify formulas with edge cases (zero values, negative numbers)

## Integration Pattern

Export functionality should be called from API layer using existing `toolsApi.exportXxx()` + `downloadBlob()` pattern:

```python
@api_bp.route('/api/v1/tickets/export', methods=['GET'])
def export_tickets():
    tickets = ticket_service.list_tickets()
    df = build_tickets_dataframe(tickets)
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, sheet_name='工单列表')
    buffer.seek(0)
    return send_file(buffer, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name='tickets_export.xlsx')
```

## Key Reminders

| Rule | Why |
|------|-----|
| Use `utf-8-sig` for CSV | Excel needs BOM to recognize UTF-8 |
| Use formulas not hardcoded values | Spreadsheets stay dynamic |
| All amounts from AmountCalculator | Consistency with backend |
| Use `Decimal` for financial data | Avoid float precision errors |
| Set column widths explicitly | Auto-width often too narrow for Chinese |
| Blue = input, Black = formula | Financial model convention |
