# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

"""People on a drive: open anyone's details from the board, move them to another time, change donors per slot."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from repos import InterestRepo, SlotRepo, DriveRepo
from services.attendee_profile import AttendeeProfile
from services.slot_allocation import SlotAllocator, SlotCapacity, SlotError
from messaging.events import bus
from security import permission_required
from ui.htmx import is_htmx, with_toast

bp = Blueprint("attendees", __name__, url_prefix="/admin/drives/<i>")
staff_view, organiser = permission_required("manage_drives", "checkin"), permission_required("manage_drives")

def _back(i, anchor=""): return redirect(url_for("drives.manage", i=i) + anchor)

@bp.route("/people/<iid>")
@staff_view
def panel(i, iid):
    p = AttendeeProfile(iid)
    if not p.exists() or p.booking["drive_id"] != i: abort(404)
    return render_template("admin/_attendee.html", drive_id=i, **p.context())

@bp.post("/people/<iid>/slot")
@organiser
def move_slot(i, iid):
    try: r = SlotAllocator(InterestRepo(), SlotRepo(), bus).reassign(iid, request.form.get("slot_id"), bool(request.form.get("notify")))
    except SlotError as e: flash(str(e), "error"); return _back(i)
    when = f"{r.slot['starts_at']}–{r.slot['ends_at']}" if r.slot else "no fixed time"
    flash(f"{r.person['name']} moved to {when}." + (" That slot is now over its capacity." if r.over_capacity else ""),
          "warning" if r.over_capacity else "success")
    return _back(i)

@bp.post("/slots/<sid>/capacity")
@organiser
def capacity(i, sid):
    try:
        slot, n = SlotCapacity(SlotRepo(), DriveRepo()).change(sid, request.form.get("value"), request.form.get("delta", 0))
        msg, kind = f"{slot['starts_at']} now takes {n} donor{'s' if n != 1 else ''}.", "success"
    except (SlotError, ValueError) as e: msg, kind = str(e) or "Enter a number.", "warning"
    if is_htmx(): return with_toast(redirect(url_for("drives.manage", i=i)), msg, kind)
    flash(msg, kind); return _back(i, "#slots-card")

@bp.post("/slots/capacity")
@organiser
def capacity_all(i):
    try:
        kept = SlotCapacity(SlotRepo(), DriveRepo()).set_all(i, request.form.get("value", ""))
        flash(f"Every slot now takes {request.form['value']} donors." + (f" {kept} slot(s) kept higher because more people are already booked." if kept else ""), "success")
    except (SlotError, ValueError) as e: flash(str(e) or "Enter a number.", "error")
    return _back(i, "#slots-card")
