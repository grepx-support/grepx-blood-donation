# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

from openpyxl import Workbook
from .excel_style import SheetStyler

class ReportExporter:
    """Drive report → Excel (summary, retro, slots, attendees)."""
    def build(self, report, people):
        s, wb, styler = report["stats"], Workbook(), SheetStyler()
        ws = wb.active; ws.title = "Summary"; ws.append(["Metric", "Value"])
        for k in ("registered", "confirmed", "donated", "no_show", "not_eligible", "walk_ins", "units", "show_rate", "fill_rate", "first_timers"):
            ws.append([k.replace("_", " ").title(), s.get(k)])
        for g, n in s.get("blood_groups", {}).items(): ws.append([f"Donated {g}", n])
        styler.style(ws, 26)
        retro = wb.create_sheet("Retro"); retro.append(["Section", "Notes"])
        for k in ("went_well", "to_improve", "actions", "notes", "rating"): retro.append([k.replace("_", " ").title(), report.get(k) or ""])
        styler.style(retro, 60)
        slots = wb.create_sheet("Slots"); slots.append(["Time", "Booked", "Capacity"])
        for x in s.get("slots", []): slots.append([x["time"], x["booked"], x["capacity"]])
        styler.style(slots)
        att = wb.create_sheet("Attendees"); att.append(["Name", "Phone", "Email", "Status", "Slot", "Source"])
        for p in people: att.append([p["name"], p["phone"], p["email"], p["status"], p["slot_start"], p["source"]])
        styler.style(att)
        return styler.to_stream(wb)
