# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

from ui.site import site_url
from flask import Blueprint, render_template, current_app, request, redirect, url_for, flash
from services.profile_photo import photo_service
from ui.nav import go_back, flash_form_errors
from flask_login import login_required, current_user
from repos import DonorRepo, DonationRepo, InterestRepo, DriveRepo, WidgetAccessRepo, ReferralRepo, TaskRepo, CertificateRepo, VoucherRepo
from tasks.service import STATUSES
from services.referral_service import ReferralService
from services.calendar_feed import CalendarFeed
from services.reminder_service import ReminderService
from services.badges import badges_for
from analytics.service import AnalyticsService
from validation import DonorForm, check
from validation.rules import PASSWORD_MIN

bp = Blueprint("donor", __name__)

@bp.route("/dashboard")
@login_required
def dashboard():
    uid = current_user.id
    history, mine = DonationRepo().for_donor(uid), InterestRepo().mine(uid)
    mine_ids = {m["id"] for m in mine}
    cfg = current_app.config
    referrals = ReferralService(DonorRepo(), ReferralRepo(), site_url())
    feed = CalendarFeed(DonorRepo(), TaskRepo(), InterestRepo(), DriveRepo(), cfg["ORG_NAME"]).token_for(uid)
    return render_template("donor/dashboard.html", history=history, mine=mine, badges=badges_for(len(history)),
                           status=ReminderService(DonorRepo(), current_app.config["DONATION_GAP_DAYS"]).status(uid),
                           recommended=[d for d in DriveRepo().upcoming() if d["id"] not in mine_ids][:3],
                           widgets=AnalyticsService(WidgetAccessRepo()).for_audience("donor"),
                           invite=referrals.summary(uid), leaders=referrals.leaderboard(5),
                           feed_url=f"{site_url()}/calendar/{feed}.ics",
                           my_tasks=[t for t in TaskRepo().for_assignee(uid) if t["status"] != "done"], statuses=STATUSES,
                           certificates=CertificateRepo().for_donor(uid), vouchers=VoucherRepo().for_donor(uid))

@bp.post("/profile/photo")
@login_required
def photo():
    from media import MediaRejected
    try: photo_service().set(current_user.id, request.files.get("photo")); flash("Looking good! Your photo is updated. 📸", "success")
    except (MediaRejected, AttributeError) as e: flash(str(e) or "Please choose a photo.", "error")
    return go_back(url_for("donor.profile"))

@bp.post("/profile/photo/remove")
@login_required
def photo_remove():
    photo_service().remove(current_user.id); flash("Photo removed.", "info")
    return go_back(url_for("donor.profile"))

@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        f, repo = request.form, DonorRepo()
        form, errors = check(DonorForm, f)
        if f.get("password") and len(f["password"]) < PASSWORD_MIN: errors["password"] = f"at least {PASSWORD_MIN} characters"
        if errors:
            flash_form_errors(errors); return render_template("donor/profile.html", errors=errors)
        other = repo.by_email(form.email)
        try:
            if other and other["id"] != current_user.id: raise ValueError
            repo.update_profile(current_user.id, **form.values())
            if f.get("password"): repo.set_password(current_user.id, f["password"])
            flash("Your details are saved. ✅", "success")
            return redirect(url_for("donor.dashboard"))
        except Exception:
            flash("That email is already used by another account.", "error")
    return render_template("donor/profile.html")
