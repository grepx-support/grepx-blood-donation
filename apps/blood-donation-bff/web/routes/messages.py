# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

import grepx_contracts as gc
from flask import Blueprint, render_template, request, redirect, url_for, flash
from repos import NotificationLogRepo
from messaging.audiences import AUDIENCES
from messaging.channels import CHANNELS
from messaging.messenger import Messenger
from security import permission_required, admin_required
from flask_login import current_user
from messaging.recipient import Recipient
from repos import DonorRepo

bp = Blueprint("messages", __name__, url_prefix="/admin/messages")

@bp.route("/")
@permission_required("view_log", "notify")
def index():
    setup = {k: (ch.configured(), ch.setup_hint) for k, ch in CHANNELS.items()}
    from ui.site import configured
    import re
    link_warning = None if configured() and not re.match(r"https?://[\d.]+(:\d+)?$", configured()) else (
        "SITE_URL is not set in .env, so reminders sent in the background may carry a wrong link." if not configured() else
        "Links use a bare IP address. WhatsApp often doesn't make those clickable — point a domain (e.g. blood.grepx.sg) at the server and set SITE_URL=https://that-domain.")
    return render_template("admin/messages.html", rows=NotificationLogRepo().recent(), audiences=AUDIENCES, channels=CHANNELS, setup=setup,
                           link_warning=link_warning)

@bp.post("/test")
@admin_required
def test():
    """Send one test message to yourself and show the real error if the provider refuses it."""
    ch = CHANNELS.get(request.form.get("channel", ""))
    if not ch: return redirect(url_for("messages.index"))
    me = Recipient.from_row(DonorRepo().by_id(current_user.id))
    if not ch.configured():
        flash(f"{ch.key.capitalize()} is not set up yet: open {ch.setup_hint} (admin menu).", "warning")
        return redirect(url_for("messages.index"))
    from repos import _nexus as nx          # the real path: notification-service delivers and logs it
    v = nx.command(gc.notification.NOTIFICATIONS, gc.notification.SERVICE, {
        "action": "SEND", "template": "staff_message", "channel": ch.key, "recipient": ch.address(me), "auto": False,
        "values": {"subject": "Test message", "text": "It works! Your blood camp can send messages. 🩸"}, "event": "test",
        "user_id": str(current_user.id)}, ok_only=False)
    if v.ok and v.fields.get("delivery") == "SENT":
        flash(f"Test {ch.key} sent to {ch.address(me)}. Check it arrived.", "success")
    elif v.ok and v.fields.get("delivery") == "LOGGED":
        flash(f"{ch.key.capitalize()} is not set up in the notification service yet — the message was only logged.", "warning")
    else:  # show the provider's own words (wrong password, unverified number…)
        flash(f"{ch.key.capitalize()} failed: {v.fields.get('error') or v.fields.get('reason') or 'unknown error'}", "error")
    return redirect(url_for("messages.index"))

@bp.post("/broadcast")
@permission_required("notify")
def broadcast():
    f = request.form
    people = {r.id: r for key in f.getlist("audience") if key in AUDIENCES for r in AUDIENCES[key].recipients()}
    n = Messenger(NotificationLogRepo()).send("broadcast", people.values(), f.getlist("channels"), subject=f["subject"], message=f["message"])
    flash(f"Broadcast sent: {n} messages to {len(people)} people. 📣", "success")
    return redirect(url_for("messages.index"))
