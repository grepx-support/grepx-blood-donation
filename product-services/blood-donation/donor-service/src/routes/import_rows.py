"""STAGE_IMPORT_ROW / UPDATE_IMPORT_ROW — Excel rows held for review (fix, ignore) before they become donors.
The row data and its validation errors are stored as given; status: valid | error | ignored | imported | skipped."""
from grepx_service import RequestContext, now_iso, state_of

from dto import IMPORT_ROWS_TABLE

STATUSES = ("valid", "error", "ignored", "imported", "skipped")


def stage(ctx: RequestContext) -> None:
    batch, row_no = ctx.text("batch"), int(ctx.get("row_no", 0) or 0)
    if not batch or ctx.text("row_status") not in STATUSES:
        return ctx.reject("INVALID_ROW")
    row_id = f"{batch}-{row_no:05d}"
    ctx.emitter.submit(IMPORT_ROWS_TABLE, row_id, "ACCEPTED", {"row_id": row_id, "batch": batch, "row_no": row_no,
                                                               "data": dict(ctx.get("data", {})), "errors": dict(ctx.get("errors", {})),
                                                               "row_status": ctx.text("row_status"), "created": now_iso()})
    ctx.accept({"row_id": row_id})


def update(ctx: RequestContext) -> None:
    row = ctx.read.accepted_one(IMPORT_ROWS_TABLE, ctx.text("row_id"))
    if row is None:
        return ctx.reject("UNKNOWN_ROW")
    changes = {k: ctx.get(k) for k in ("data", "errors") if ctx.get(k) is not None}
    if ctx.text("row_status"):
        if ctx.text("row_status") not in STATUSES:
            return ctx.reject("INVALID_ROW")
        changes["row_status"] = ctx.text("row_status")
    keep = state_of(row)
    ctx.emitter.submit(IMPORT_ROWS_TABLE, row["_key"], "ACCEPTED", {**keep, **changes})
    ctx.accept({"row_id": row["_key"]})
