# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from repos import DriveRepo, InterestRepo, DonationRepo, DonorRepo
from services.attendance_service import AttendanceService, STATUSES, NotDriveDay, is_drive_day
from services.walkin_service import WalkInService, InvalidDetails
from messaging.events import bus
from security import permission_required
from ui.htmx import is_htmx, with_toast

bp = Blueprint("checkin", __name__, url_prefix="/admin/checkin")
guard = permission_required("checkin")
drives, interests = DriveRepo(), InterestRepo()
def walkins(): return WalkInService(DonorRepo(), interests, bus)

def _page(drive_id):
    upcoming = drives.upcoming() or drives.all()[:5]
    d = drives.by_id(drive_id) if drive_id else (upcoming[0] if upcoming else None)
    people = interests.for_drive(d["id"]) if d else []
    return render_template("admin/checkin.html", d=d, drives=upcoming, people=people, statuses=STATUSES, drive_day=bool(d) and is_drive_day(d))

@bp.route("/")
@guard
def index(): return _page(request.args.get("drive"))

@bp.post("/<drive_id>/mark/<iid>/<status>")
@guard
def mark(drive_id, iid, status):
    try: msg, kind = AttendanceService(interests, DonationRepo(), bus).move(iid, status), "success"
    except NotDriveDay as e: msg, kind = str(e), "warning"
    if is_htmx(): return with_toast(_page(drive_id), msg, kind)
    flash(msg, kind); return redirect(url_for("checkin.index", drive=drive_id))

@bp.route("/<drive_id>/lookup")
@guard
def lookup(drive_id):
    q = request.args.get("q", "").strip()
    found = DonorRepo().lookup(q) if len(q) >= 2 else []
    booked = {p["donor_id"]: p["status"] for p in interests.for_drive(drive_id)}
    return render_template("admin/_lookup.html", found=found, q=q, booked=booked, drive_id=drive_id)

@bp.post("/<drive_id>/walkin")
@guard
def walkin(drive_id):
    f = request.form
    if f.get("donor_id"):
        donor = walkins().check_in(drive_id, DonorRepo().by_id(f["donor_id"]))
        msg = f"{donor['name']} checked in ✓"
    else:
        try: donor, created = walkins().register_and_check_in(drive_id, f)
        except InvalidDetails as e:
            if is_htmx(): return with_toast(_page(drive_id), f"Not registered. {e}", "error")
            flash(f"Not registered. {e}", "error"); return redirect(url_for("checkin.index", drive=drive_id))
        msg = f"{donor['name']} {'registered and ' if created else ''}checked in ✓ 🙌"
    if is_htmx(): return with_toast(_page(drive_id), msg)
    flash(msg, "success")
    return redirect(url_for("checkin.index", drive=drive_id))

@bp.post("/<drive_id>/scan")
@guard
def scan(drive_id):
    m = re.fullmatch(r"LIFEFLOW:DONOR:([0-9A-Za-z_-]+)", (request.get_json() or {}).get("code", ""))
    donor = DonorRepo().by_id(m.group(1)) if m else None
    if not donor: return jsonify(message="That QR code isn't a donor card."), 404
    walkins().check_in(drive_id, donor, source="online")
    return jsonify(message=f"{donor['name']} ({donor['blood_group'] or '?'}) checked in ✓")
