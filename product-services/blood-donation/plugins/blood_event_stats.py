# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Blood product figures added to the generic event report (config plugins.event_report).

Plugin interface:  extras(read, event, attended) -> dict      read = a Reader; attended = the bookings marked attended
"""
from collections import Counter

import grepx_contracts as gc

DONATIONS, PEOPLE = gc.donation.DONATIONS, gc.people.PEOPLE


def extras(read, event: dict, attended: list[dict]) -> dict:
    ids = sorted({b.get("person_id") for b in attended if b.get("person_id")})
    if not ids:
        return {"units": 0, "first_timers": 0, "blood_groups": {}}
    history = read.accepted(DONATIONS, donor_id=ids)
    here = [d for d in history if d.get("drive_id") == event["_key"]]
    first: dict = {}
    for d in history:
        on = d.get("donated_on") or ""
        if d.get("donor_id") not in first or on < first[d.get("donor_id")]:
            first[d.get("donor_id")] = on
    donors = {d["_key"]: d for d in read.accepted(PEOPLE, transaction_id=ids)}
    return {"units": sum(int(d.get("units") or 1) for d in here),
            "first_timers": sum(1 for d in here if (d.get("donated_on") or "") <= first.get(d.get("donor_id"), "")),
            "blood_groups": dict(Counter((donors.get(b.get("person_id")) or {}).get("blood_group") or "Unknown" for b in attended).most_common())}
