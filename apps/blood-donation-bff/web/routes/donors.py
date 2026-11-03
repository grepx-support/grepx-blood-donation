# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

import json
from datetime import date
from grepx_service import local_today
from urllib.parse import parse_qs, urlencode
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app, abort, make_response
from services.profile_photo import photo_service
from ui.nav import go_back, id_list, flash_form_errors
from flask_login import current_user
from werkzeug.datastructures import MultiDict
from repos import DonorRepo, DonationRepo, DriveRepo, InterestRepo, DonorGridRepo, DonorGridQuery, SegmentRepo, NotificationLogRepo, ImportRepo
from services.reminder_service import ReminderService
from services.donor_exporter import DonorExporter
from services.donor_bulk_service import DonorBulkService
from importing.excel_reader import KEYS, HEADERS, HeaderError
from importing.row_validator import RowValidator
from importing.import_service import ImportService
from importing.excel_reader import ExcelReader
from messaging.events import bus
from messaging.messenger import Messenger
from messaging.recipient import Recipient
from messaging.channels import CHANNELS
from security import permission_required
from validation import WalkInForm, check

bp = Blueprint("donors", __name__, url_prefix="/admin/donors")
guard = permission_required("manage_donors")
donors = DonorRepo()
GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

def grid_repo(): return DonorGridRepo(current_app.config["DONATION_GAP_DAYS"])

def _grid_context(g):
    repo, wait = grid_repo(), ReminderService(donors, current_app.config["DONATION_GAP_DAYS"]).wait_days
    total = repo.count(g)
    rows = [dict(r, wait=wait(r["last_donation"])) for r in repo.page(g)]
    return {"g": g, "rows": rows, "total": total, "pages": max(1, -(-total // g.per)), "qs": urlencode(g.args(page=1), doseq=True)}

@bp.route("/")
@guard
def index():
    g = DonorGridQuery.from_args(request.args)
    return render_template("admin/donors.html", **_grid_context(g), groups=GROUPS, facets=grid_repo().facets(),
                           segments=SegmentRepo().all(), drives=DriveRepo().upcoming(), channels=CHANNELS, keys=KEYS,
                           headers=dict(zip(KEYS, HEADERS)), stats=_status_counts())

@bp.route("/rows")
@guard
def rows():
    g = DonorGridQuery.from_args(request.args)
    resp = make_response(render_template("admin/_donor_rows.html", **_grid_context(g)))
    resp.headers["HX-Replace-Url"] = url_for("donors.index") + "?" + urlencode(g.args(), doseq=True)  # shareable, back-button friendly
    return resp

def _status_counts():
    repo = grid_repo()
    return {s: repo.count(DonorGridQuery(status=s)) for s in ("eligible", "waiting", "new")} | {"all": repo.count(DonorGridQuery())}

def _selected_ids(form):
    """Either the ticked ids, or every donor matching the filters the admin was looking at."""
    if form.get("scope") == "all":
        return grid_repo().ids(DonorGridQuery.from_args(MultiDict(parse_qs(form.get("qs", "")))))
    return id_list(form.get("ids"))

def _back(): return redirect(url_for("donors.index") + ("?" + request.form.get("qs") if request.form.get("qs") else ""))

# ---- add ---------------------------------------------------------------------------------------------
@bp.post("/add")
@guard
def add():
    svc = ImportService(ExcelReader(), RowValidator(donors), ImportRepo(), donors)
    try: batch = svc.stage_rows([{k: request.form.get(k, "") for k in KEYS}])
    except HeaderError as e: flash(str(e), "error"); return _back()
    rows = ImportRepo().parsed(batch)
    if rows and rows[0]["status"] == "valid":
        svc.commit(batch); flash(f"Donor {request.form.get('name')} added. 🎉", "celebrate"); return _back()
    flash("Please fix the highlighted fields.", "warning")
    return redirect(url_for("imports.review", batch=batch))

@bp.post("/add-many")
@guard
def add_many():
    try:
        rows = json.loads(request.form.get("rows") or "[]")
        batch = ImportService(ExcelReader(), RowValidator(donors), ImportRepo(), donors).stage_rows(rows)
    except (ValueError, HeaderError) as e: flash(str(e) or "Could not read the grid.", "error"); return _back()
    return redirect(url_for("imports.review", batch=batch))

# ---- bulk actions on the selection ------------------------------------------------------------------
@bp.post("/bulk/edit")
@guard
def bulk_edit():
    ids = _selected_ids(request.form)
    try: n = DonorBulkService().update(ids, {k: request.form.get(k) for k in DonorBulkService.FIELDS})
    except ValueError as e: flash(str(e), "error"); return _back()
    flash(f"Updated {n} donors." if n else "Nothing to change — pick at least one field.", "success" if n else "info")
    return _back()

@bp.post("/bulk/message")
@permission_required("notify")
def bulk_message():
    people = [Recipient.from_row(r) for r in _rows_for(_selected_ids(request.form))]
    n = Messenger(NotificationLogRepo()).send("broadcast", people, request.form.getlist("channels"),
                                              subject=request.form["subject"], message=request.form["message"])
    flash(f"Sent {n} messages to {len(people)} donors. 📣", "success"); return _back()

@bp.post("/bulk/invite")
@permission_required("notify")
def bulk_invite():
    d = DriveRepo().by_id(request.form["drive_id"]) or abort(404)
    people = [Recipient.from_row(r) for r in _rows_for(_selected_ids(request.form))]
    n = Messenger(NotificationLogRepo()).send("drive_invitation", people, request.form.getlist("channels"), drive_id=d["id"],
                                              drive=d, note=request.form.get("note", "").strip())
    flash(f"Invited {len(people)} donors to {d['title']} ({n} messages). 💌", "celebrate"); return _back()

@bp.post("/bulk/export")
@guard
def bulk_export():
    rows = _rows_for(_selected_ids(request.form), with_stats=True)
    return send_file(DonorExporter().build(rows), as_attachment=True, download_name=f"donors-{local_today()}.xlsx")

def _rows_for(ids, with_stats=False): return donors.many(ids, with_stats)

@bp.route("/export.xlsx")
@guard
def export():
    g = DonorGridQuery.from_args(request.args)
    return send_file(DonorExporter().build(_rows_for(grid_repo().ids(g), with_stats=True)), as_attachment=True,
                     download_name=f"donors-{local_today()}.xlsx")

# ---- saved groups ------------------------------------------------------------------------------------
@bp.post("/segments")
@guard
def save_segment():
    name = request.form.get("name", "").strip()
    if name: SegmentRepo().add(name, request.form.get("qs", ""), current_user.id); flash(f"Saved group “{name}”.", "success")
    return _back()

@bp.post("/segments/<i>/delete")
@guard
def delete_segment(i):
    SegmentRepo().delete(i); flash("Group removed.", "info"); return _back()

# ---- one donor ---------------------------------------------------------------------------------------
@bp.route("/<i>")
@guard
def profile(i):
    d = donors.with_stats(i) or abort(404)
    status = ReminderService(donors, current_app.config["DONATION_GAP_DAYS"]).status(i)
    from repos import PermissionRepo, StaffRoleRepo
    from permissions import PERMS, ROLES
    vr = StaffRoleRepo().all()
    return render_template("admin/donor.html", d=d, history=DonationRepo().for_donor(i), drives=DriveRepo().all(),
                           status=status, upcoming=InterestRepo().mine(i), today=local_today().isoformat(),
                           access_user={**dict(d), "perms": sorted(PermissionRepo().get(i))}, perms=PERMS, roles=ROLES,
                           vroles=vr, role_perms={r["id"]: r["perm_list"] for r in vr},
                           role_name=next((r["name"] for r in vr if r["id"] == d["staff_role_id"]), None))

@bp.post("/<i>/photo")
@guard
def photo(i):
    from media import MediaRejected
    donors.by_id(i) or abort(404)
    try: photo_service().set(i, request.files.get("photo")); flash("Photo updated.", "success")
    except (MediaRejected, AttributeError) as e: flash(str(e) or "Please choose a photo.", "error")
    return redirect(url_for("donors.profile", i=i))

@bp.post("/<i>/photo/remove")
@guard
def photo_remove(i):
    donors.by_id(i) or abort(404); photo_service().remove(i); flash("Photo removed.", "info")
    return redirect(url_for("donors.profile", i=i))

@bp.post("/<i>/donation")
@guard
def add_donation(i):
    try: on = date.fromisoformat(request.form.get("donated_on", ""))
    except ValueError: on = None
    if not on or on > local_today():
        flash("Please pick the donation date (it can't be in the future).", "error"); return redirect(url_for("donors.profile", i=i))
    DonationRepo().add(i, on.isoformat(), request.form.get("drive_id") or None)
    bus.publish("donation.recorded", donor_id=i)
    flash("Donation recorded — thank-you message sent. 💚", "celebrate")
    return redirect(url_for("donors.profile", i=i))

@bp.post("/<i>/edit")
@guard
def edit(i):
    current = donors.by_id(i) or abort(404)
    form, errors = check(WalkInForm, request.form)
    if errors:
        flash_form_errors(errors, "Not saved. Please fix: ")
        return go_back(url_for("donors.profile", i=i))
    v = form.values(); v["email"] = v["email"] or current["email"]
    other = donors.by_email(v["email"])
    if other and other["id"] != i: flash("That email is already used by another donor.", "error")
    else: donors.update_profile(i, **v); flash("Donor details saved.", "success")
    return go_back(url_for("donors.profile", i=i))
