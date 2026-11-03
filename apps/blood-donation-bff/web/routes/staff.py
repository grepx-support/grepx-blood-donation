# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

from flask import Blueprint, render_template, request, redirect, url_for, flash
from ui.nav import go_next
from flask_login import current_user
from repos import DonorRepo, PermissionRepo, StaffRoleRepo
from permissions import PERMS, ROLES
from security import admin_required
from ui.htmx import is_htmx, with_toast

bp = Blueprint("staff", __name__, url_prefix="/admin/staff")
donors, perms, roles = DonorRepo(), PermissionRepo(), StaffRoleRepo()

def _page(q):
    users = [{**dict(u), "perms": sorted(perms.get(u["id"]))} for u in donors.users(q)]
    vr = roles.all()
    return render_template("admin/staff.html", users=users, perms=PERMS, roles=ROLES, q=q, vroles=vr,
                           role_perms={r["id"]: r["perm_list"] for r in vr})

@bp.route("/")
@admin_required
def index(): return _page(request.args.get("q", ""))

@bp.post("/<i>")
@admin_required
def save(i):
    """Set someone's account type (donor / volunteer / admin), their volunteer role, and any extra functions."""
    role = request.form.get("role", "donor") if i != current_user.id else "admin"
    role = role if role in ROLES else "donor"
    donors.set_role(i, role)
    vrole = request.form.get("staff_role_id", "")
    donors.set_staff_role(i, vrole if role == "volunteer" and vrole and roles.by_id(vrole) else None)
    perms.set(i, [p for p in request.form.getlist("perm") if p in PERMS] if role == "volunteer" else [])
    name = donors.by_id(i)["name"]
    if is_htmx(): return with_toast(_page(request.args.get("q", "")), f"Access updated for {name}")
    flash(f"Access updated for {name}", "success")
    return go_next(url_for("staff.index", q=request.args.get("q", "")))

@bp.post("/new")
@admin_required
def create():
    """Add a volunteer (or admin) in one step: account + volunteer role. Extra functions can be switched on after."""
    from services.user_admin_service import UserAdminService, UserError
    f = request.form
    try: user, temp = UserAdminService(donors).create({**f, "role": f.get("role") if f.get("role") in ("volunteer", "admin") else "volunteer"})
    except UserError as e:
        flash(str(e), "error"); return redirect(url_for("staff.index"))
    vrole = f.get("staff_role_id", "")
    if user["role"] == "volunteer" and vrole and roles.by_id(vrole): donors.set_staff_role(user["id"], vrole)
    flash(f"{user['name']} added as {user['role']} — login: {user['email']}" +
          (f" · temporary password: {temp} (share it privately; they can change it in My details)" if temp else ""), "success")
    return redirect(url_for("staff.index") + f"#staff-{user['id']}")

# ---- volunteer roles ---------------------------------------------------------------------------------
def _role_form():
    f = request.form
    return f.get("name", "").strip(), f.get("description", "").strip(), [p for p in f.getlist("perm") if p in PERMS]

@bp.post("/roles")
@admin_required
def role_create():
    name, desc, ps = _role_form()
    if not name: flash("Give the role a name.", "error")
    else: roles.create(name, desc, ps); flash(f"Role “{name}” created.", "success")
    return redirect(url_for("staff.index") + "#roles")

@bp.post("/roles/<i>")
@admin_required
def role_update(i):
    name, desc, ps = _role_form()
    roles.update(i, name or "Untitled role", desc, ps); flash(f"Role “{name}” saved — everyone with this role is updated.", "success")
    return redirect(url_for("staff.index") + "#roles")

@bp.post("/roles/<i>/delete")
@admin_required
def role_delete(i):
    r = roles.by_id(i)
    if r: roles.delete(i); flash(f"Role “{r['name']}” deleted. Its volunteers keep only their extra functions.", "info")
    return redirect(url_for("staff.index") + "#roles")
