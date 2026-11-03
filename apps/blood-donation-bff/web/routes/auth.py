# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

import grepx_contracts as gc
from ui.site import site_url
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, session
from ui.nav import go_next, flash_form_errors
from flask_login import login_user, logout_user, current_user
from repos import DonorRepo, RepoError
from user import User
from validation import RegisterForm, check

bp = Blueprint("auth", __name__)
donors = DonorRepo()

def _home(user): return url_for("admin.home") if user.is_staff else url_for("donor.dashboard")

@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated: return redirect(_home(current_user))
    if request.method == "POST":
        try: uid = donors.verify_password(request.form["email"], request.form["password"])   # auth-service checks it
        except RepoError as e:
            current_app.logger.warning("login unavailable: %s", e.reason)
            flash(f"Sign-in is not available right now ({e.reason}). Please try again in a minute.", "error")
            return render_template("auth/login.html")
        user = User.load(uid) if uid else None
        if user:
            session.clear()  # fresh session on every login (prevents session fixation)
            login_user(user, remember=bool(request.form.get("remember")) and not user.is_staff)
            flash(f"Welcome back, {user.first_name}!", "success")
            return go_next(_home(user))
        flash("That email and password don't match.", "error")
    return render_template("auth/login.html")

@bp.route("/register", methods=["GET", "POST"])
def register():
    drive_id = request.values.get("drive")
    if request.method == "POST":
        form, errors = check(RegisterForm, request.form)
        if errors:
            flash_form_errors(errors)
            return render_template("auth/register.html", drive_id=drive_id, ref=session.get("ref"), errors=errors)
        v = form.values()
        try:   # donor-service creates the profile (and credits the referrer), auth-service the login; donor-service sends the welcome
            if donors.by_email(v["email"]): raise RepoError("EMAIL_TAKEN")
            uid = donors.register(v["name"], v["email"], v["phone"], form.password, v["blood_group"], v["sex"], v["weight"], v["dob"],
                                  invite_code=(donors.by_column("ref_code", session.pop("ref", None)) or {}).get("ref_code", ""), link=f"{site_url()}{url_for('donor.dashboard')}")
        except RepoError as e:
            flash("That email is already registered — try logging in." if e.reason == "EMAIL_TAKEN" else str(e), "warning")
            return render_template("auth/register.html", drive_id=drive_id)
        login_user(User.load(uid))
        flash("Welcome to the family! Your donor account is ready. 🩸", "celebrate")
        return redirect(url_for("public.drive", i=drive_id) if drive_id else url_for("donor.dashboard"))
    return render_template("auth/register.html", drive_id=drive_id, ref=session.get("ref"))

@bp.route("/logout")
def logout():
    logout_user(); session.clear(); flash("You're logged out. See you soon!", "info")
    return redirect(url_for("public.index"))


# ---- forgotten password ---------------------------------------------------------------------------------
def send_reset_link(row):
    """auth-service emails a one-time reset link (valid 1 hour). Used by the forgot page and by admins."""
    from repos import _nexus as nx
    nx.command(gc.auth.REQUESTS, gc.auth.SERVICE, {"action": "RESET_REQUEST", "email": row["email"],
                                                 "link_base": f"{site_url()}/reset"})
    return True

@bp.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        import time
        email = request.form.get("email", "").strip().lower()
        last = session.get("reset_at", 0)
        if time.time() - last < 60:
            flash("Please wait a minute before asking again.", "warning")
        else:
            session["reset_at"] = time.time()
            row = donors.by_email(email)
            if row and "@no-email.local" not in row["email"]: send_reset_link(row)
            # same answer either way, so nobody can find out which emails are registered
            flash("If that email is registered, a reset link is on its way (check spam too). It works for 1 hour.", "info")
            return redirect(url_for("auth.login"))
    return render_template("auth/forgot.html")

@bp.route("/reset/<token>", methods=["GET", "POST"])
def reset(token):
    from validation.rules import PASSWORD_MIN
    from repos import _nexus as nx
    row = None                                   # auth-service checks the token when the new password is sent
    if request.method == "POST":
        pw, again = request.form.get("password", ""), request.form.get("password2", "")
        if len(pw) < PASSWORD_MIN: flash(f"Passwords need at least {PASSWORD_MIN} characters.", "error")
        elif pw != again: flash("The two passwords don't match.", "error")
        else:
            v = nx.command(gc.auth.REQUESTS, gc.auth.SERVICE, {"action": "RESET_CONFIRM", "token_enc": nx.GW.box.seal(token),
                                                              "password_enc": nx.GW.box.seal(pw)}, ok_only=False)
            if not v.ok:
                flash("That link isn't valid any more (links work once, for 1 hour). Ask for a new one.", "error")
                return redirect(url_for("auth.forgot"))
            logout_user(); session.clear()
            flash("Password changed. Log in with your new password. 🔐", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth/reset.html", who=row)

