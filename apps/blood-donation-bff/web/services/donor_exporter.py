# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

from openpyxl import Workbook
from importing.excel_reader import HEADERS
from .excel_style import SheetStyler

class DonorExporter:
    def build(self, donors):
        wb = Workbook(); ws = wb.active; ws.title = "Donors"
        ws.append(HEADERS + ["Donations", "Last donation"])
        for d in donors:
            ws.append([d["name"], d["email"], d["phone"], d["blood_group"], d["sex"], d["weight"], d["dob"], d["total"], d["last_donation"]])
        styler = SheetStyler(); styler.style(ws); ws.auto_filter.ref = ws.dimensions
        return styler.to_stream(wb)
