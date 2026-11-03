# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The signed-in person: dashboard, profile, photo, calendar link, bookings."""

import grepx_contracts as gc
from fastapi import APIRouter, Depends, UploadFile
from grepx_service import local_today, new_key

from grepx_bff.errors import ApiError
from grepx_bff.security import Principal, current_user, gateway
from views import PUBLIC_DONOR, clean, drive_view, upcoming

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/dashboard")
def dashboard(user: Principal = Depends(current_user), gw=Depends(gateway)):
    donor = gw.one(gc.people.PEOPLE, user.user_id) or {}
    stats = clean(gw.one(gc.donation.DONOR_STATS, user.user_id)) or {"count": 0, "ready": True, "first": True, "badges": []}
    mine = []
    for r in gw.rows(gc.booking.BOOKINGS, donor_id=user.user_id):
        d = gw.one(gc.event.EVENTS, r.get("drive_id", ""))
        if d and r.get("state") in ("interested", "confirmed") and d.get("drive_date", "") >= local_today().isoformat():
            mine.append({**clean(r), "drive": drive_view(gw, d)})
    booked = {m["drive_id"] for m in mine}
    leaders = sorted(gw.rows(gc.referral.REFERRAL_SCORES), key=lambda s: -int(s.get("points") or 0))[:10]
    return {
        "donor": clean(donor, PUBLIC_DONOR), "card": {"number": f"BC-{user.user_id[:6].upper()}", "qr": f"LIFEFLOW:DONOR:{user.user_id}"},
        "stats": stats, "registrations": mine, "recommended": [drive_view(gw, d) for d in upcoming(gw) if d["_key"] not in booked][:4],
        "history": sorted((clean(d) for d in gw.rows(gc.donation.DONATIONS, donor_id=user.user_id)), key=lambda d: d["donated_on"], reverse=True),
        "certificates": [clean(c) for c in gw.rows(gc.recognition.CERTIFICATES, donor_id=user.user_id)],
        "vouchers": [clean(v) for v in gw.rows(gc.recognition.VOUCHERS, donor_id=user.user_id)],
        "invite": {"link": f"{gw.site}/join/{donor.get('ref_code', '')}", **(clean(gw.one(gc.referral.REFERRAL_SCORES, user.user_id)) or {"points": 0})},
        "leaderboard": [{"name": (s.get("name") or "").split(" ")[0], "points": s.get("points"), "me": s["_key"] == user.user_id} for s in leaders],
        "tasks": [clean(t) for t in gw.rows(gc.task.TASKS, assignee_id=user.user_id) if t.get("state") != "done"],
        "calendar_url": f"{gw.site}/api/v1/calendar/{donor.get('cal_token', '')}.ics",
    }


@router.patch("/profile")
def profile(body: dict, user: Principal = Depends(current_user), gw=Depends(gateway)):
    allowed = {k: v for k, v in body.items() if k in ("name", "email", "phone", "blood_group", "sex", "weight", "dob")}
    gw.command(gc.people.REQUESTS, gc.people.SERVICE, {"action": "UPDATE", "donor_id": user.user_id, **allowed})
    return dashboard(user, gw)


def store_upload(gw, file: UploadFile, kind: str, owner: str) -> str:
    data = file.file.read()
    if len(data) > 15 * 1024 * 1024:
        raise ApiError("TOO_LARGE", 413)
    staged = f"staging/{new_key()}"
    gw.storage.put(staged, data)
    return gw.command(gc.media.REQUESTS, gc.media.SERVICE, {"action": "PROCESS", "staged_key": staged, "kind": kind, "owner_id": owner}).fields["media_id"]


@router.post("/photo")
def photo(file: UploadFile, user: Principal = Depends(current_user), gw=Depends(gateway)):
    media_id = store_upload(gw, file, "avatar", user.user_id)
    gw.command(gc.people.REQUESTS, gc.people.SERVICE, {"action": "SET_PHOTO", "donor_id": user.user_id, "photo_id": media_id})
    return {"photo_id": media_id}


@router.post("/calendar/reset")
def calendar_reset(user: Principal = Depends(current_user), gw=Depends(gateway)):
    gw.command(gc.people.REQUESTS, gc.people.SERVICE, {"action": "RESET_CAL_TOKEN", "donor_id": user.user_id})
    return {"calendar_url": f"{gw.site}/api/v1/calendar/{gw.one(gc.people.PEOPLE, user.user_id)['cal_token']}.ics"}


@router.post("/drives/{drive_id}/book")
def book(drive_id: str, body: dict, user: Principal = Depends(current_user), gw=Depends(gateway)):
    return gw.command(gc.booking.REQUESTS, gc.booking.SERVICE, {"action": "BOOK", "drive_id": drive_id, "donor_id": user.user_id,
                                                                        "slot_id": body.get("slot_id", "")}).fields


@router.post("/drives/{drive_id}/cancel")
def cancel(drive_id: str, user: Principal = Depends(current_user), gw=Depends(gateway)):
    return gw.command(gc.booking.REQUESTS, gc.booking.SERVICE, {"action": "CANCEL", "drive_id": drive_id, "donor_id": user.user_id}).fields


@router.post("/tasks/{task_id}/status")
def my_task(task_id: str, body: dict, user: Principal = Depends(current_user), gw=Depends(gateway)):
    return gw.command(gc.task.REQUESTS, gc.task.SERVICE, {"action": "CHANGE_STATUS", "task_id": task_id, "state": body.get("state"),
                                                        "actor_id": user.user_id}).fields
