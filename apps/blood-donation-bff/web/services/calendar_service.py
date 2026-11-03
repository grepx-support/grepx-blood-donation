# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Drives, bookings and tasks as calendar events (rendering: grepx_bff.calendar)."""
from datetime import datetime, timedelta

from grepx_bff.calendar import IcsEvent

class EventFactory:
    """Turns drives, bookings and tasks into calendar events."""
    @staticmethod
    def drive(d, slot_start=None, slot_end=None):
        day = datetime.strptime(d["drive_date"], "%Y-%m-%d")
        if slot_start:
            start = datetime.combine(day, datetime.strptime(slot_start, "%H:%M").time())
            end = datetime.combine(day, datetime.strptime(slot_end, "%H:%M").time())
            title = f"🩸 {d['title']} ({slot_start})"
        else:
            start, end, title = day.date(), day.date() + timedelta(days=1), f"🩸 {d['title']}"
        return IcsEvent(f"drive-{d['id']}", title, start, end, d["venue"], d["time_slot"] or "Thank you for donating!")

    @staticmethod
    def task(t):
        start = datetime.strptime(t["due_at"], "%Y-%m-%dT%H:%M")
        title = ("⚠️ " if t["important"] else "") + t["title"] + (" ✓" if t["status"] == "done" else "")
        return IcsEvent(f"task-{t['id']}", title, start, start + timedelta(minutes=30), "", t["description"] or "")
