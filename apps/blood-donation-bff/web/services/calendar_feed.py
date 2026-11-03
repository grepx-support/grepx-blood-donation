# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

import secrets
from grepx_bff.calendar import IcsCalendar
from .calendar_service import EventFactory

class CalendarFeed:
    """Private subscription feed per person: their tasks (staff), their booked drives, and all drives for staff."""
    def __init__(self, donors, tasks, interests, drives, org):
        self.donors, self.tasks, self.interests, self.drives, self.org = donors, tasks, interests, drives, org

    def token_for(self, donor_id, reset=False):
        row = self.donors.by_id(donor_id)
        if row["cal_token"] and not reset: return row["cal_token"]
        token = secrets.token_urlsafe(18); self.donors.set_column(donor_id, "cal_token", token)
        return token

    def render(self, token):
        row = self.donors.by_column("cal_token", token)
        if not row: return None
        events = [EventFactory.drive(b, b["slot_start"], b["slot_end"]) for b in self.interests.mine(row["id"])]
        if row["role"] != "donor":
            booked = {b["id"] for b in self.interests.mine(row["id"])}
            events += [EventFactory.drive(d) for d in self.drives.all() if d["id"] not in booked]
            events += [EventFactory.task(t) for t in self.tasks.for_assignee(row["id"]) if t["due_at"]]
        return IcsCalendar(self.org).render(events, f"{self.org} · {row['name'].split()[0]}")
