# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

from openpyxl import Workbook
from openpyxl.worksheet.datavalidation import DataValidation
from services.excel_style import SheetStyler
from .excel_reader import HEADERS

class ExcelTemplate:
    """Template with dropdowns, so admins make fewer mistakes before uploading."""
    def build(self):
        wb = Workbook(); ws = wb.active; ws.title = "Donors"
        ws.append(HEADERS)
        ws.append(["Jane Tan", "jane@example.com", "91234567", "O+", "Female", 58, "1995-04-12"])
        for rng, values in (("D2:D2000", "A+,A-,B+,B-,AB+,AB-,O+,O-"), ("E2:E2000", "Male,Female")):
            dv = DataValidation(type="list", formula1=f'"{values}"', allow_blank=True); dv.add(rng); ws.add_data_validation(dv)
        styler = SheetStyler(); styler.style(ws)
        return styler.to_stream(wb)
