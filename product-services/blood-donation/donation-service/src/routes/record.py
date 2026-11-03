# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""RECORD — staff record a donation by hand (e.g. given elsewhere)."""
from datetime import date

from grepx_service import RequestContext, local_today

from dto import DONATIONS_TABLE, PEOPLE_TABLE, EVENTS_TABLE, DonationField as F, ReasonCode
from .common import refresh_stats


def handle(ctx: RequestContext) -> None:
    donor_id = ctx.text(F.DONOR_ID)
    if not ctx.read.accepted_one(PEOPLE_TABLE, donor_id):
        return ctx.reject(ReasonCode.UNKNOWN_DONOR)
    try:
        day = date.fromisoformat(ctx.text(F.DONATED_ON) or local_today().isoformat())
    except ValueError:
        return ctx.reject(ReasonCode.INVALID_DATE)
    if day > local_today():
        return ctx.reject(ReasonCode.INVALID_DATE)
    units = int(ctx.get(F.UNITS, 1))
    if not 1 <= units <= 3:
        return ctx.reject(ReasonCode.INVALID_UNITS)
    drive = ctx.read.accepted_one(EVENTS_TABLE, ctx.text(F.DRIVE_ID)) if ctx.text(F.DRIVE_ID) else None
    ctx.emitter.submit(DONATIONS_TABLE, ctx.key, "ACCEPTED", {
        F.DONATION_ID.value: ctx.key, F.DONOR_ID.value: donor_id, F.DRIVE_ID.value: ctx.text(F.DRIVE_ID),
        F.DRIVE_TITLE.value: (drive or {}).get("title", ""), F.VENUE.value: (drive or {}).get("venue", ""),
        F.DONATED_ON.value: day.isoformat(), F.UNITS.value: units, F.TENANT_ID.value: ctx.text(F.TENANT_ID)})
    refresh_stats(ctx.emitter, ctx.read, donor_id)
    ctx.accept({F.DONATION_ID: ctx.key})
