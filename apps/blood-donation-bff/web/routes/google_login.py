# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Continue with Google — for donors, volunteers and admins alike.
Existing account (any role) -> signed straight in; the role is the account's own, Google never grants one.
No account yet -> a short "finish signing up" form (phone, blood group …), then donor-service creates the donor
and auth-service links the Google login (no password needed)."""
import grepx_contracts as gc
import secrets

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import login_user

from integrations.sign_in import AUTHORIZE_URL, TOKEN_URL, google_client, google_enabled
from repos import DonorRepo, RepoError
from repos import _nexus as nx
from ui.nav import flash_form_errors
from ui.site import site_url
from user import User
from validation import DonorForm, check

bp = Blueprint("google_login", __name__)
donors = DonorRepo()
AUTH_REQ, AUTH_SVC = gc.auth.REQUESTS, gc.auth.SERVICE


def _auth(action, id_token_enc, **extra):
    return nx.command(AUTH_REQ, AUTH_SVC, {"action": action, "provider": "google", "id_token_enc": id_token_enc, **extra})


def _sign_in(uid, welcome):
    user = User.load(uid) or abort(403)
    session.clear()  # fresh session on every login (prevents session fixation)
    login_user(user)
    flash(welcome.format(name=user.first_name), "success")
    return user


@bp.route("/login/google")
def start():
    if not google_enabled():
        flash("Google sign-in is not set up yet.", "warning")
        return redirect(url_for("auth.login"))
    url, state = google_client().create_authorization_url(AUTHORIZE_URL, nonce=secrets.token_urlsafe(16), prompt="select_account")
    session["google_state"] = state
    return redirect(url)


@bp.route("/login/google/callback")
def callback():
    if request.args.get("error") or request.args.get("state") != session.pop("google_state", None):
        flash("Google sign-in was cancelled. Please try again.", "warning")
        return redirect(url_for("auth.login"))
    try:
        token = google_client().fetch_token(TOKEN_URL, code=request.args.get("code", ""))
        verdict = _auth("LOGIN_EXTERNAL", nx.GW.box.seal(token["id_token"]))
    except RepoError as e:
        current_app.logger.warning("google sign-in refused: %s", e.reason)
        flash("Google sign-in did not work for this account. Please log in with your email and password.", "error")
        return redirect(url_for("auth.login"))
    except Exception as e:  # network / Google answered with an error
        current_app.logger.warning("google token exchange failed: %s", e)
        flash("Could not reach Google just now. Please try again.", "error")
        return redirect(url_for("auth.login"))
    f = verdict.fields
    if f.get("registered"):
        user = _sign_in(f["user_id"], "Welcome back, {name}!")
        return redirect(url_for("admin.home") if user.is_staff else url_for("donor.dashboard"))
    session["google_signup"] = {"id_token_enc": nx.GW.box.seal(token["id_token"]), "email": f["email"], "name": f.get("name", "")}
    return redirect(url_for("google_login.finish"))


@bp.route("/register/google", methods=["GET", "POST"])
def finish():
    """First Google sign-in: the email is Google's (verified); ask only what a donor record needs."""
    info = session.get("google_signup") or {}
    if not info:
        return redirect(url_for("auth.register"))
    if request.method == "POST":
        form, errors = check(DonorForm, {**request.form.to_dict(), "email": info["email"]})
        if errors:
            flash_form_errors(errors)
            return render_template("auth/register.html", google=info, errors=errors)
        v = form.values()
        try:
            uid = donors.register(v["name"], info["email"], v["phone"], "", v["blood_group"], v["sex"], v["weight"], v["dob"],
                                  invite_code=(donors.by_column("ref_code", session.get("ref")) or {}).get("ref_code", ""),
                                  link=f"{site_url()}{url_for('donor.dashboard')}")
            _auth("LINK_EXTERNAL", info["id_token_enc"], user_id=uid)
        except RepoError as e:
            flash("That email is already registered — log in with Google again." if e.reason == "EMAIL_TAKEN" else str(e), "warning")
            return render_template("auth/register.html", google=info)
        _sign_in(uid, "Welcome to the family, {name}! Your donor account is ready. 🩸")
        return redirect(url_for("donor.dashboard"))
    return render_template("auth/register.html", google=info)
