# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from datetime import date, datetime
from openpyxl import load_workbook

HEADERS = ["Name", "Email", "Phone", "Blood Group", "Sex", "Weight (kg)", "Date of Birth"]
KEYS = ["name", "email", "phone", "blood_group", "sex", "weight", "dob"]

class HeaderError(Exception): pass

class ExcelReader:
    def read(self, stream):
        rows = load_workbook(stream, read_only=True, data_only=True).active.iter_rows(values_only=True)
        head = [str(c or "").strip() for c in next(rows, ())][:len(HEADERS)]
        if head != HEADERS: raise HeaderError("Headers must be exactly: " + ", ".join(HEADERS))
        for n, r in enumerate(rows, start=2):
            cells = (list(r) + [None] * len(KEYS))[:len(KEYS)]
            if any(c not in (None, "") for c in cells): yield n, dict(zip(KEYS, map(self._cell, cells)))

    @staticmethod
    def _cell(c):
        if c is None: return ""
        if isinstance(c, (datetime, date)): return c.strftime("%Y-%m-%d")
        if isinstance(c, float) and c.is_integer(): return str(int(c))
        return str(c).strip()
