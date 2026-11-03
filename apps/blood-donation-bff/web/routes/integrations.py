# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

"""Admin: connect social media, email and SMS/WhatsApp accounts from the app (no server access needed)."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from integrations import settings, save_settings
from integrations.catalog import CATALOG, BY_KEY, SECRET_KEYS, TESTS
from security import admin_required

bp = Blueprint("integrations", __name__, url_prefix="/admin/integrations")

@bp.route("/")
@admin_required
def index():
    from repos.settings_repo import SettingsRepo
    saved = SettingsRepo().all()
    groups = {}
    for i in CATALOG: groups.setdefault(i.group, []).append(i)
    import os
    env = {f.key for i in CATALOG for f in i.fields if os.getenv(f.key)}  # really set in .env (not just a built-in default)
    return render_template("admin/integrations.html", groups=groups, saved=saved, values=settings(), secret_keys=SECRET_KEYS, env=env)

@bp.post("/<key>")
@admin_required
def save(key):
    i = BY_KEY.get(key) or abort(404)
    if request.form.get("disconnect"):
        save_settings({f.key: "__clear__" for f in i.fields}); flash(f"{i.label} disconnected here (anything in .env still applies).", "info")
    else:
        save_settings({f.key: request.form.get(f.key, "") for f in i.fields}, SECRET_KEYS)
        flash(f"{i.label} saved." + (" Press Test to check it works." if i.configured() else " Some fields are still missing."), "success")
    return redirect(url_for("integrations.index") + f"#{key}")

@bp.post("/<key>/test")
@admin_required
def test(key):
    i = BY_KEY.get(key) or abort(404)
    if not i.configured(): flash(f"Fill in {i.label} first.", "warning")
    else:
        from repos._nexus import RepoError, command
        try: flash("✅ " + command(*TESTS[key]).fields.get("message", "Connected"), "success")
        except RepoError as e: flash(f"{i.label}: {e}", "error")
    return redirect(url_for("integrations.index") + f"#{key}")
