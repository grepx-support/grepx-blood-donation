# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

from ui.site import site_url
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort, Response, session
from ui.nav import go_back, flash_form_errors
from flask_login import current_user, login_required
from repos import DriveRepo, InterestRepo, StatsRepo, DonorRepo, WidgetAccessRepo, SlotRepo, ReferralRepo
from services.reminder_service import ReminderService
from grepx_bff.calendar import IcsCalendar
from services.calendar_service import EventFactory
from services.booking_service import BookingService, SlotFull, SlotRequired
from services.referral_service import ReferralService
from analytics.service import AnalyticsService
from repos import eligibility
from repos._nexus import RepoError
from validation import ContactForm, check

bp = Blueprint("public", __name__)
drives, interests = DriveRepo(), InterestRepo()

@bp.route("/")
def index():
    up = drives.upcoming()
    reminder = None
    if current_user.is_authenticated and current_user.role == "donor":
        reminder = ReminderService(DonorRepo(), current_app.config["DONATION_GAP_DAYS"]).message_for(current_user.id)
    widgets = AnalyticsService(WidgetAccessRepo()).for_audience("public")
    return render_template("public/index.html", drives=up, next_drive=up[0] if up else None, stats=StatsRepo().summary(),
                           urgent=current_app.config["URGENT_GROUPS"], reminder=reminder, widgets=widgets)

@bp.route("/drive/<i>")
def drive(i):
    d = drives.by_id(i) or abort(404)
    booking = interests.find(i, current_user.id) if current_user.is_authenticated else None
    from services.drive_gallery import DriveGallery
    return render_template("public/drive.html", d=d, booking=booking, slots=SlotRepo().for_drive(i), images=DriveGallery.images(d))

@bp.route("/drive/<i>/calendar.ics")
def drive_ics(i):
    d = drives.by_id(i) or abort(404)
    b = interests.find(i, current_user.id) if current_user.is_authenticated else None
    event = EventFactory.drive(d, b["slot_start"] if b else None, b["slot_end"] if b else None)
    return Response(IcsCalendar(current_app.config["ORG_NAME"]).render([event]), mimetype="text/calendar",
                    headers={"Content-Disposition": f"attachment; filename=drive-{i}.ics"})

@bp.post("/drive/<i>/interest")
def interest(i):
    drives.by_id(i) or abort(404)
    form, errors = check(ContactForm, request.form)
    if errors:
        flash_form_errors(errors)
        return go_back(url_for("public.drive", i=i))
    interests.add(i, current_user.id if current_user.is_authenticated else None, form.name, form.phone, form.email)
    flash("Thank you! We've noted your interest and will keep you posted. 💚", "success")
    return go_back(url_for("public.drive", i=i))

@bp.post("/drive/<i>/confirm")
@login_required
def confirm(i):
    try: slot = BookingService(interests, SlotRepo()).book(i, current_user, request.form.get("slot_id"))
    except SlotRequired:
        flash("Pick a time slot so you don't have to queue. ⏱️", "info")
        return redirect(url_for("public.drive", i=i) + "#book")
    except SlotFull:
        flash("Sorry, that slot just filled up — please pick another.", "warning")
        return redirect(url_for("public.drive", i=i) + "#book")
    when = f" at {slot['starts_at']}" if slot else ""
    flash(f"You're booked{when} — see you there! 🎉", "celebrate")
    return redirect(url_for("public.drive", i=i))

@bp.post("/drive/<i>/cancel")
@login_required
def cancel(i):
    interests.cancel(i, current_user.id)
    flash("Registration cancelled. We hope to see you at another drive.", "info")
    return go_back(url_for("public.drive", i=i))

@bp.route("/eligibility", methods=["GET", "POST"], endpoint="eligibility")
def eligibility_check():
    result = None
    if request.method == "POST":
        try: result = eligibility.check(request.form.to_dict())
        except RepoError: flash("Please fill in valid values.", "warning")
    return render_template("public/eligibility.html", result=result)

@bp.route("/join/<code>")
def join(code):
    ref = ReferralService(DonorRepo(), ReferralRepo(), site_url()).referrer(code)
    if ref:
        session["ref"] = code.upper()
        flash(f"{ref['name'].split()[0]} invited you to become a blood donor. Welcome! 💚", "success")
    return redirect(url_for("auth.register"))
