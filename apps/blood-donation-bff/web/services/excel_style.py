# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from io import BytesIO
from openpyxl.styles import Font, PatternFill

class SheetStyler:
    """Shared look for every workbook we hand out (bold red header, frozen row, filters)."""
    HEADER = PatternFill("solid", fgColor="E11D48")

    def style(self, ws, widths=22):
        for cell in ws[1]:
            cell.font, cell.fill = Font(bold=True, color="FFFFFF"), self.HEADER
        for col in ws.iter_cols(min_row=1, max_row=1):
            ws.column_dimensions[col[0].column_letter].width = widths
        ws.freeze_panes = "A2"
        ws.parent.properties.creator = ws.parent.properties.lastModifiedBy = "GrepX Private Limited (grepx.sg)"

    @staticmethod
    def to_stream(wb):
        buf = BytesIO(); wb.save(buf); buf.seek(0); return buf
