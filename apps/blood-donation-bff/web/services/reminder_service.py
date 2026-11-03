# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from datetime import datetime, timedelta
from grepx_service import local_today

class ReminderService:
    def __init__(self, donors, gap_days=90): self.donors, self.gap = donors, gap_days

    def next_eligible(self, donor_id):
        last = self.donors.last_donation(donor_id)
        return datetime.strptime(last, "%Y-%m-%d").date() + timedelta(days=self.gap) if last else None

    def wait_days(self, last):
        """Days until eligible for a 'YYYY-MM-DD' last donation (0 = ready, None = never donated)."""
        if not last: return None
        return max(0, (datetime.strptime(last, "%Y-%m-%d").date() + timedelta(days=self.gap) - local_today()).days)

    def status(self, donor_id):
        nxt = self.next_eligible(donor_id)
        left = max(0, (nxt - local_today()).days) if nxt else 0
        return {"ready": left == 0, "days_left": left, "next": nxt, "first": nxt is None,
                "pct": round((self.gap - left) / self.gap * 100), "message": self._message(nxt, left)}

    @staticmethod
    def _message(nxt, left):
        if nxt is None: return "Ready for your first donation? Pick an upcoming drive below."
        if left == 0: return "You're eligible to donate again. Join an upcoming drive!"
        return f"You can donate again in {left} days (on {nxt:%d %b %Y})."

    def message_for(self, donor_id): return self.status(donor_id)["message"]
