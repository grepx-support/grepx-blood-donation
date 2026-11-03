# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Public pages: drives, impact numbers, certificates, invite links, private calendar feeds."""

import grepx_contracts as gc
from datetime import date, datetime, timedelta

from grepx_service import local_today

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from grepx_bff.calendar import IcsCalendar, IcsEvent
from grepx_bff.errors import ApiError
from grepx_bff.security import gateway, optional_user
from views import clean, drive_view, upcoming

router = APIRouter(tags=["public"])


@router.get("/drives")
def drives(gw=Depends(gateway)):
    return [drive_view(gw, d) for d in upcoming(gw)]


@router.get("/drives/{drive_id}")
def drive(drive_id: str, user=Depends(optional_user), gw=Depends(gateway)):
    d = gw.one(gc.event.EVENTS, drive_id)
    if d is None:
        raise ApiError("UNKNOWN_DRIVE", 404)
    view = drive_view(gw, d)
    view["my_registration"] = clean(gw.one(gc.booking.BOOKINGS, f"{drive_id}-{user.user_id}")) if user else None
    return view


@router.get("/stats")
def stats(gw=Depends(gateway)):
    donations = len(gw.rows(gc.donation.DONATIONS))
    groups = {}
    for d in gw.rows(gc.people.PEOPLE):
        groups[d.get("blood_group") or "Unknown"] = groups.get(d.get("blood_group") or "Unknown", 0) + 1
    return {"donors": len(gw.rows(gc.people.PEOPLE)), "donations": donations, "lives": donations * 3, "drives": len(upcoming(gw)),
            "blood_groups": groups, "urgent": ["O-", "B-", "A-"]}


@router.get("/certificates/{code}")
def certificate(code: str, gw=Depends(gateway)):
    cert = gw.one(gc.recognition.CERTIFICATES, code)
    if cert is None:
        raise ApiError("UNKNOWN_CERTIFICATE", 404)
    return {**clean(cert), "number": code[:8].upper(), "verify_url": f"{gw.site}/certificate/{code}"}


@router.get("/join/{ref_code}")
def join(ref_code: str, gw=Depends(gateway)):
    found = gw.rows(gc.people.PEOPLE, ref_code=ref_code)
    return {"valid": bool(found), "invite_code": ref_code if found else ""}


@router.get("/calendar/{token}.ics")
def calendar(token: str, gw=Depends(gateway)):
    donor = (gw.rows(gc.people.PEOPLE, cal_token=token) or [None])[0]
    if donor is None:
        raise ApiError("UNKNOWN_CALENDAR", 404)
    events = []
    for r in gw.rows(gc.booking.BOOKINGS, donor_id=donor["_key"]):
        d = gw.one(gc.event.EVENTS, r.get("drive_id", ""))
        if d and r.get("state") in ("interested", "confirmed") and d.get("drive_date", "") >= local_today().isoformat():
            events.append(_event(r["_key"], f"🩸 {d.get('title')}", d["drive_date"], r.get("slot_start", ""), r.get("slot_end", ""), d.get("venue", "")))
    for t in gw.rows(gc.task.TASKS, assignee_id=donor["_key"]):
        if t.get("due_at") and t.get("state") != "done":
            day, time = t["due_at"].split("T")
            events.append(_event(t["_key"], f"📋 {t.get('title')}", day, time[:5], time[:5]))
    return Response(IcsCalendar().render(events), media_type="text/calendar")


def _event(uid: str, title: str, day: str, start: str, end: str, location: str = "") -> IcsEvent:
    d = date.fromisoformat(day)
    if not start:
        return IcsEvent(uid, title, d, d + timedelta(days=1), location)
    at = lambda hm: datetime.combine(d, datetime.strptime(hm, "%H:%M").time())  # noqa: E731
    return IcsEvent(uid, title, at(start), at(end or start), location)
