from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from src.exporters.csv_exporter import HEADERS, _LIST_FIELDS, _cell
from src.models import Company


def export_excel(companies: list[Company], path: str) -> str:
    output_path = Path(path).with_suffix(".xlsx")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "Companies"

    header_row = [label for _, label in HEADERS]
    ws.append(header_row)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    ws.freeze_panes = "A2"

    for company in companies:
        ws.append([_cell(company, field) for field, _ in HEADERS])

    for col_idx, _ in enumerate(HEADERS, start=1):
        col_letter = get_column_letter(col_idx)
        max_len = max(
            len(str(ws.cell(row=row, column=col_idx).value or ""))
            for row in range(1, ws.max_row + 1)
        )
        ws.column_dimensions[col_letter].width = min(max_len + 2, 60)

    wb.save(output_path)
    return str(output_path)
