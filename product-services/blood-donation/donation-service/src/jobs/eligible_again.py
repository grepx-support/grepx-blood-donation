# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Reacts to scheduler ticks (job eligible-again): tell donors whose waiting period ends today."""
from datetime import date

from grepx_service import Emitter, Reader, local_today, notify, now_iso

from dto import PEOPLE_TABLE, STATS_TABLE
from grepx_config.deployment import link

JOB = "eligible-again"


def handle_tick(app, row, cfg, today: date | None = None) -> int:
    if row.fields.get("job") != JOB or row.fields.get("status") != "NEW":
        return 0
    emitter, read, sent = Emitter(app, cfg, cause=row), Reader(app.client), 0
    today = today or local_today()
    for stats in read.accepted(STATS_TABLE, next_eligible=today.isoformat()):
        donor = read.accepted_one(PEOPLE_TABLE, stats["_key"])
        if not donor or not stats.get("count"):
            continue
        notify(emitter, "eligible_again", email=donor.get("email", ""), phone=donor.get("phone", ""), ref=f"eligible-{donor['_key']}-{today}",
               values={"first_name": donor.get("name", "").split(" ")[0], "link": link(cfg, "events")}, user_id=donor["_key"])
        sent += 1
    emitter.submit("ticks", row.key, "ACCEPTED", {**row.fields, "processed_at": now_iso(), "count": sent})
    return sent
