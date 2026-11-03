# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""When can a donor give again, and which badges have they earned. Pure."""
from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Iterable

GAP_DAYS = int(os.environ.get("DONATION_GAP_DAYS", "90"))
BADGES = (("First Drop", 1, "droplet"), ("Life Saver", 3, "heart-pulse"), ("Regular Hero", 5, "shield-check"),
          ("Legend", 10, "crown"), ("Platinum", 25, "gem"))


def donor_status(donated_on: Iterable[str], today: date) -> dict:
    days = sorted(donated_on)
    count = len(days)
    if not days:
        return {"count": 0, "lives": 0, "last": "", "next_eligible": today.isoformat(), "ready": True, "days_left": 0, "pct": 100,
                "first": True, "badges": []}
    last = date.fromisoformat(days[-1])
    nxt = last + timedelta(days=GAP_DAYS)
    left = max(0, (nxt - today).days)
    return {"count": count, "lives": count * 3, "last": last.isoformat(), "next_eligible": nxt.isoformat(), "ready": left == 0,
            "days_left": left, "pct": round(100 * (GAP_DAYS - left) / GAP_DAYS), "first": False,
            "badges": [name for name, need, _ in BADGES if count >= need]}
