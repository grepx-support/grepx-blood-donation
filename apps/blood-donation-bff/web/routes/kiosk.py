# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""On-site walk-in page anyone can use at the venue (donor, volunteer, or a tablet at the door).
Privacy: people are found only by an exact phone number or email, never by browsing names."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from flask_login import current_user
from repos import DriveRepo, DonorRepo, InterestRepo
from services.walkin_service import WalkInService, InvalidDetails
from messaging.events import bus

bp = Blueprint("kiosk", __name__, url_prefix="/drive/<i>/here")
def walkins(): return WalkInService(DonorRepo(), InterestRepo(), bus)
def _mask(s): return (s[:2] + "•••" + s[-3:]) if s and len(s) > 5 else "•••"

@bp.route("/")
def index(i):
    d = DriveRepo().by_id(i) or abort(404)
    found_id = session.get("kiosk_found", {}).get(str(i))
    found = DonorRepo().by_id(found_id) if found_id else None
    me = InterestRepo().find(i, current_user.id) if current_user.is_authenticated else None
    return render_template("public/kiosk.html", d=d, found=found, me=me, mask=_mask)

@bp.post("/find")
def find(i):
    donor = DonorRepo().find_exact(request.form.get("contact", ""))
    if donor: session["kiosk_found"] = {str(i): donor["id"]}
    else: flash("No donor found with that phone or email — register below in 10 seconds.", "info")
    return redirect(url_for("kiosk.index", i=i) + ("#found" if donor else "#new"))

@bp.post("/checkin")
def checkin(i):
    found_id = session.get("kiosk_found", {}).get(str(i))
    if current_user.is_authenticated and request.form.get("me"): found_id = current_user.id
    if not found_id: return redirect(url_for("kiosk.index", i=i))
    donor = walkins().check_in(i, DonorRepo().by_id(found_id), source="kiosk")
    session.pop("kiosk_found", None)
    flash(f"Welcome, {donor['name'].split()[0]}! You're checked in — please take a seat. 🩸", "celebrate")
    return redirect(url_for("kiosk.index", i=i))

@bp.post("/new")
def new(i):
    try: donor, created = walkins().register_and_check_in(i, request.form, source="kiosk")
    except InvalidDetails as e:
        flash(f"Please check your details: {e}", "error"); return redirect(url_for("kiosk.index", i=i) + "#new")
    flash(f"Welcome{' to the family' if created else ' back'}, {donor['name'].split()[0]}! You're checked in. 🩸", "celebrate")
    return redirect(url_for("kiosk.index", i=i))
