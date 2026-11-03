# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from flask import Blueprint, render_template, request, redirect, url_for, flash
from ui.nav import go_back
from flask_login import current_user
from repos import DonorRepo
from permissions import ROLES
from services.user_admin_service import UserAdminService, UserError
from security import admin_required

bp = Blueprint("users", __name__, url_prefix="/admin/users")
def service(): return UserAdminService(DonorRepo())
def _back(): return redirect(url_for("users.index", q=request.args.get("q", ""), role=request.args.get("role", "")))

@bp.route("/")
@admin_required
def index():
    q, role = request.args.get("q", "").strip().lower(), request.args.get("role", "")
    users = DonorRepo().accounts(q, role)
    return render_template("admin/users.html", users=users, roles=ROLES, q=q, role=role)

@bp.post("/new")
@admin_required
def create():
    try:
        user, generated = service().create(request.form)
        flash(f"Account created for {user['name']} — login: {user['email']}" +
              (f" · temporary password: {generated}  (share it privately; they can change it in My details)" if generated else ""), "success")
    except UserError as e: flash(str(e), "error")
    return _back()

@bp.post("/<i>")
@admin_required
def update(i):
    try: user = service().update(i, request.form, current_user); flash(f"Saved {user['name']} ({user['role']}).", "success")
    except UserError as e: flash(str(e), "error")
    return _back()

@bp.post("/<i>/send-reset")
@admin_required
def send_reset(i):
    """Email the person a one-time link so they choose their own password (nobody else ever sees it)."""
    from routes.auth import send_reset_link
    who = DonorRepo().by_id(i)
    if not who or "@no-email.local" in (who["email"] or ""): flash("This person has no email address. Set a password for them instead.", "warning")
    else: send_reset_link(who); flash(f"Reset link sent to {who['email']} (valid for 1 hour).", "success")
    return go_back(url_for("users.index"))

@bp.post("/<i>/password")
@admin_required
def password(i):
    try:
        generated = service().reset_password(i, request.form.get("password"))
        who = DonorRepo().by_id(i)
        flash(f"Password reset for {who['email']}" + (f" — new temporary password: {generated}" if generated else "."), "success")
    except UserError as e: flash(str(e), "error")
    return _back()
