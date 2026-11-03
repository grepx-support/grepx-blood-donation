# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""SAVE_SEGMENT / DELETE_SEGMENT — a saved donor group: a name plus the grid filter (query string). The group stays
current because the filter is applied to today's donors whenever it is opened."""
from grepx_service import RequestContext, new_key, now_iso

from dto import SEGMENTS_TABLE


def save(ctx: RequestContext) -> None:
    name, query = ctx.text("name")[:80], ctx.text("query")[:1000]
    if not name:
        return ctx.reject("MISSING_NAME")
    segment_id = ctx.text("segment_id") or new_key()[:12]
    ctx.emitter.submit(SEGMENTS_TABLE, segment_id, "ACCEPTED", {"segment_id": segment_id, "name": name, "query": query,
                                                                "created_by": ctx.text("actor_id"), "created": now_iso()})
    ctx.accept({"segment_id": segment_id})


def delete(ctx: RequestContext) -> None:
    segment_id = ctx.text("segment_id")
    if not ctx.read.accepted_one(SEGMENTS_TABLE, segment_id):
        return ctx.reject("UNKNOWN_SEGMENT")
    ctx.emitter.submit(SEGMENTS_TABLE, segment_id, "DELETED", {"segment_id": segment_id})
    ctx.accept()
