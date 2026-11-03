# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

"""Drive posters and publishing drives to social media (Facebook, Instagram, LinkedIn, X, Telegram)."""
import grepx_contracts as gc
import time
from flask import Blueprint, Response, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import current_user
from repos import DriveRepo, MediaRepo
from media.service import is_media_id
from services.poster import PosterRenderer
from integrations.catalog import SOCIAL
from security import permission_required
from ui.site import site_url

bp = Blueprint("social", __name__)

def default_caption(d):
    return render_template("messages/social_post/caption.j2", drive=d, org=current_app.config["ORG_NAME"]).strip()

def _cover_bytes(d):
    """The drive's cover picture from the shared storage media-service writes to (None if there is none)."""
    from repos import _nexus as nx
    ref = d["image_url"]
    row = MediaRepo().by_id(ref) if is_media_id(ref) else None
    return nx.GW.storage.get(row["key"]) if row else None

@bp.route("/drive/<i>/poster.jpg")
def poster(i):
    """Public on purpose: Facebook and Instagram download it from here."""
    d = DriveRepo().by_id(i) or abort(404)
    return Response(_poster_bytes(d), mimetype="image/jpeg", headers={"Cache-Control": "public, max-age=300"})

def publish_drive(d, networks, caption):
    """campaign-service posts the drive (it reads the network credentials and logs every attempt).
    Returns {network: (ok, link_or_error)} for the drive page."""
    from repos import _nexus as nx
    image = f"{site_url()}{url_for('social.poster', i=d['id'])}?v={int(time.time())}"
    link = f"{site_url()}{url_for('public.drive', i=d['id'])}"
    v = nx.command(gc.campaign.REQUESTS, gc.campaign.SERVICE, {"action": "PUBLISH_SOCIAL", "drive_id": d["id"], "networks": list(networks),
                                                             "caption": caption, "image_url": image, "link": link,
                                                             "actor_id": str(current_user.id)}, ok_only=False)
    if not v.ok:
        return {n: (False, v.fields.get("reason") or "could not publish") for n in networks}
    return {k: (bool(r.get("ok")), r.get("info") or "") for k, r in dict(v.fields.get("results") or {}).items()}

def _poster_bytes(d):
    return PosterRenderer(current_app.config["ORG_NAME"]).render(d, _cover_bytes(d), site_url().split("://", 1)[-1])

def flash_results(results):
    for key, (ok, info) in results.items():
        label = SOCIAL[key].label
        flash(f"Posted to {label}. 🎉" if ok else f"{label}: {info}", "success" if ok else "error")

@bp.post("/admin/drives/<i>/social")
@permission_required("notify")
def publish(i):
    d = DriveRepo().by_id(i) or abort(404)
    networks = [n for n in request.form.getlist("network") if n in SOCIAL]
    if not networks: flash("Pick at least one social network.", "info")
    else: flash_results(publish_drive(d, networks, request.form.get("caption", "").strip() or default_caption(d)))
    return redirect(url_for("drives.manage", i=i) + "#social")
