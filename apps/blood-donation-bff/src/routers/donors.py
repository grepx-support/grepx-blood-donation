# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Staff donor management: grid with filters, add, edit, record donations, bulk import."""

import grepx_contracts as gc
from grepx_service import local_today

from fastapi import APIRouter, Depends

from grepx_bff.security import Principal, gateway, require
from views import PUBLIC_DONOR, clean

router = APIRouter(prefix="/admin/donors", tags=["donors"])


@router.get("")
def grid(q: str = "", group: str = "", status: str = "", sex: str = "", sort: str = "name", page: int = 1, per: int = 25,
         user: Principal = Depends(require("manage_donors")), gw=Depends(gateway)):
    stats = {s["_key"]: s for s in gw.rows(gc.donation.DONOR_STATS)}
    today, out = local_today().isoformat(), []
    for d in gw.rows(gc.people.PEOPLE):
        s = stats.get(d["_key"], {})
        state = "new" if not s.get("count") else ("eligible" if s.get("next_eligible", "") <= today else "waiting")
        text = f"{d.get('name', '')} {d.get('email', '')} {d.get('phone', '')}".lower()
        if (q and q.lower() not in text) or (group and (d.get("blood_group") or "unknown") != group) or (status and status != state) or (sex and d.get("sex") != sex):
            continue
        out.append({**clean(d, PUBLIC_DONOR), "donations": s.get("count", 0), "last": s.get("last", ""), "eligibility": state})
    out.sort(key=lambda r: (str(r.get(sort) or ""), r.get("name", "")))
    per = max(10, min(200, per))
    return {"total": len(out), "page": page, "rows": out[(page - 1) * per: page * per]}


@router.post("")
def add(body: dict, user: Principal = Depends(require("manage_donors")), gw=Depends(gateway)):
    return gw.command(gc.people.REQUESTS, gc.people.SERVICE, {"action": "CREATE", "source": "staff", **body}).fields


@router.get("/{donor_id}")
def profile(donor_id: str, user: Principal = Depends(require("manage_donors")), gw=Depends(gateway)):
    return {"donor": clean(gw.one(gc.people.PEOPLE, donor_id), PUBLIC_DONOR), "stats": clean(gw.one(gc.donation.DONOR_STATS, donor_id)),
            "access": clean(gw.one(gc.access.USER_ACCESS, donor_id)), "registrations": [clean(r) for r in gw.rows(gc.booking.BOOKINGS, donor_id=donor_id)],
            "donations": [clean(d) for d in gw.rows(gc.donation.DONATIONS, donor_id=donor_id)]}


@router.patch("/{donor_id}")
def edit(donor_id: str, body: dict, user: Principal = Depends(require("manage_donors")), gw=Depends(gateway)):
    return gw.command(gc.people.REQUESTS, gc.people.SERVICE, {"action": "UPDATE", "donor_id": donor_id, **body}).fields


@router.post("/{donor_id}/donations")
def record(donor_id: str, body: dict, user: Principal = Depends(require("manage_donors")), gw=Depends(gateway)):
    return gw.command(gc.donation.REQUESTS, gc.donation.SERVICE, {"action": "RECORD", "donor_id": donor_id, **body}).fields


@router.post("/import")
def bulk_import(rows: list[dict], user: Principal = Depends(require("bulk_import")), gw=Depends(gateway)):
    """Each row is its own request; the verdicts become the review list (imported / skipped with reason)."""
    results = []
    for i, row in enumerate(rows, 1):
        v = gw.command(gc.people.REQUESTS, gc.people.SERVICE, {"action": "CREATE", "source": "import", **row}, ok_only=False)
        results.append({"row": i, "ok": v.ok, "reason": "" if v.ok else v.reason, "donor_id": v.fields.get("donor_id", "")})
    return {"imported": sum(r["ok"] for r in results), "results": results}
