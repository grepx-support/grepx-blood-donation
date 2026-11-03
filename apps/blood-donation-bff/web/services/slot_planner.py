# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

from datetime import datetime, timedelta

class SlotPlanner:
    """Splits opening hours into equal slots, e.g. 10:00–17:00 every 30 min with 6 places each."""
    def plan(self, start, end, minutes, capacity):
        t, stop, step, out = self._t(start), self._t(end), timedelta(minutes=int(minutes)), []
        if step.total_seconds() <= 0 or int(capacity) <= 0: raise ValueError("slot length and places must be positive")
        while t + step <= stop:
            out.append((t.strftime("%H:%M"), (t + step).strftime("%H:%M"), int(capacity))); t += step
        if not out: raise ValueError("end time must be after start time")
        return out

    @staticmethod
    def _t(hhmm): return datetime.strptime(hhmm, "%H:%M")
