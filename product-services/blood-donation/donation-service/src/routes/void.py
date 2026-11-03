# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""VOID — remove a donation recorded by mistake."""
from grepx_service import RequestContext

from dto import DONATIONS_TABLE, DonationField as F, ReasonCode
from .common import refresh_stats


def handle(ctx: RequestContext) -> None:
    donation = ctx.read.accepted_one(DONATIONS_TABLE, ctx.text(F.DONATION_ID))
    if donation is None:
        return ctx.reject(ReasonCode.UNKNOWN_DONATION)
    ctx.emitter.submit(DONATIONS_TABLE, donation["_key"], "VOIDED", {F.DONOR_ID.value: donation[F.DONOR_ID.value]})
    refresh_stats(ctx.emitter, ctx.read, donation[F.DONOR_ID.value])
