# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

"""Admin: which automatic messages go out, over which channels, and in whose words."""
import grepx_contracts as gc
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from automessages import AUTO, BY_KEY, AutoPolicy
from integrations import setting, save_settings
from messaging.channels import CHANNELS
from security import admin_required

bp = Blueprint("automessages", __name__, url_prefix="/admin/messages/automatic")

SAMPLE = {"first_name": "Aisha", "name": "Aisha Rahman", "link": "https://your-site/…", "drive_title": "Orchard Lifeline Drive",
          "drive_date": "Sat, 14 Nov 2026", "drive_time": "10:00 – 17:00", "venue": "ION Orchard Atrium", "slot_time": "10:30–11:00",
          "voucher": "🎁 Free kopi (Ya Kun) – code HERO2026", "friend": "Daniel"}

@bp.route("/")
@admin_required
def index():
    rows = [dict(a=a, on=AutoPolicy.enabled(a.key), channels=AutoPolicy.channels(a.key) or a.channels,
                 subject=setting(f"auto.{a.key}.subject"), text=setting(f"auto.{a.key}.text")) for a in AUTO]
    return render_template("admin/automessages.html", rows=rows, channels=CHANNELS, sample=SAMPLE)

@bp.post("/<key>")
@admin_required
def save(key):
    a, f = BY_KEY.get(key) or abort(404), request.form
    custom = f.get("wording") == "custom"
    save_settings({f"auto.{key}.enabled": "1" if f.get("enabled") else "0",
                   f"auto.{key}.channels": ",".join(c for c in f.getlist("channels") if c in CHANNELS) or "__clear__",
                   f"auto.{key}.subject": f.get("subject", "") if custom else "__clear__",
                   f"auto.{key}.text": f.get("text", "") if custom else "__clear__"})
    from repos import _nexus as nx   # the services that send this message themselves follow template-service's settings
    nx.command(gc.template.REQUESTS, gc.template.SERVICE, {"action": "SAVE", "template_key": key, "enabled": bool(f.get("enabled")),
                                                 "channels": [c for c in f.getlist("channels") if c in CHANNELS] or list(a.channels),
                                                 "subject": f.get("subject", "") if custom else "", "text": f.get("text", "") if custom else ""},
               ok_only=False)
    flash(f"“{a.label}” saved — {'on' if f.get('enabled') else 'off'}{', your own wording' if custom and f.get('text', '').strip() else ', built-in design'}.", "success")
    return redirect(url_for("automessages.index") + f"#{key}")
