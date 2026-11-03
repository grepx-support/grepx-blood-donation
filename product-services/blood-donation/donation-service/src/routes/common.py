# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Donation projection + per-donor stats (recomputed from the donations — never stored as a trusted counter)."""
from datetime import date

from grepx_service import Emitter, Reader, local_today

from domain import donor_status
from dto import DONATIONS_TABLE, STATS_TABLE


def refresh_stats(emitter: Emitter, read: Reader, donor_id: str, today: date | None = None) -> dict:
    rows = read.accepted(DONATIONS_TABLE, donor_id=donor_id)
    stats = donor_status([r["donated_on"] for r in rows], today or local_today())
    emitter.submit(STATS_TABLE, donor_id, "ACCEPTED", {"donor_id": donor_id, **stats})
    return stats
