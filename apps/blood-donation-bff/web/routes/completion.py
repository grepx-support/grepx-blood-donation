# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Completing a drive (organisers) and the public certificate pages (anyone with the link can verify)."""
from flask import Blueprint, Response, render_template, request, url_for, flash, abort, current_app
from flask_login import current_user
from repos import DriveRepo, InterestRepo, DonationRepo, CertificateRepo, VoucherRepo, MediaRepo
from services.drive_completion import DriveCompletion, CannotComplete
from rewards import CertificateRenderer, VoucherOffer
from repos import _nexus as _nx
from messaging.events import bus
from security import permission_required
from ui.nav import go_back
from ui.site import site_url

bp = Blueprint("completion", __name__)
organiser = permission_required("manage_drives")

def service():
    return DriveCompletion(DriveRepo(), InterestRepo(), DonationRepo(), CertificateRepo(), VoucherRepo(), bus)

def _drive(i): return DriveRepo().by_id(i) or abort(404)
def _back(i): return go_back(url_for("drives.manage", i=i))

@bp.post("/admin/drives/<i>/complete")
@organiser
def complete(i):
    f = request.form
    try:
        r = service().complete(_drive(i), current_user.id, bool(f.get("close_open")), bool(f.get("notify")), VoucherOffer.from_form(f))
    except CannotComplete as e:
        flash(str(e), "warning"); return _back(i)
    parts = [f"{len(r.certificates)} certificate{'s' if len(r.certificates) != 1 else ''} issued"]
    if r.notified: parts.append(f"{r.notified} donor{'s' if r.notified != 1 else ''} thanked by email + WhatsApp")
    if r.vouchers: parts.append(f"{r.vouchers} voucher{'s' if r.vouchers != 1 else ''} given")
    if r.no_shows: parts.append(f"{r.no_shows} marked no-show")
    flash("Drive completed 🎉 " + " · ".join(parts) + ".", "celebrate")
    if r.vouchers_short: flash(f"{r.vouchers_short} donor(s) got no voucher because the codes ran out. Add more codes and send again.", "warning")
    return _back(i)

@bp.post("/admin/drives/<i>/reopen")
@organiser
def reopen(i):
    service().reopen(_drive(i)); flash("Drive reopened. Attendance can be changed again; certificates already sent stay valid.", "info")
    return _back(i)

@bp.post("/admin/drives/<i>/rewards")
@organiser
def rewards(i):
    """After completion: certificates for donations recorded later, extra vouchers (recognition-service thanks each donor)."""
    d = _drive(i)
    new, given, short = service().reward(i, VoucherOffer.from_form(request.form))
    flash(f"{new} new certificate(s), {given} voucher(s), {new} donor(s) messaged." + (f" {short} without a code (ran out)." if short else ""), "success")
    return _back(d["id"])

def _unsent(i): return {c["id"] for c in CertificateRepo().for_drive(i) if not c["sent_at"]}

# ---- public certificate pages --------------------------------------------------------------------------
def _cert(code):
    c = CertificateRepo().by_code(code) if code.isalnum() and len(code) == 32 else None
    return c or abort(404)

@bp.route("/certificate/<code>")
def view(code):
    c = _cert(code)
    return render_template("public/certificate.html", c=c, png=f"{site_url()}{url_for('completion.image', code=code)}",
                           link=f"{site_url()}{url_for('completion.view', code=code)}")

@bp.route("/certificate/<code>.png")
def image(code):
    c = _cert(code)
    photo = None
    if c["photo_id"]:
        m = MediaRepo().by_id(c["photo_id"]); photo = _nx.GW.storage.get(m["key"]) if m else None
    png = CertificateRenderer(current_app.config["ORG_NAME"]).render(dict(c), f"{site_url().split('://')[-1]}/certificate/{code[:8]}…", photo)
    return Response(png, mimetype="image/png", headers={"Cache-Control": "public, max-age=3600",
                                                         "Content-Disposition": f'inline; filename="certificate-{code[:8]}.png"'})
