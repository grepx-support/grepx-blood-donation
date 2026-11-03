# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

from datetime import date, timedelta
from grepx_service import local_today
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from ui.nav import go_next
from repos import DriveRepo, InterestRepo, DonationRepo, NotificationLogRepo, SlotRepo, ReportRepo, TaskRepo, DonorRepo
from tasks.playbook import PlaybookService, phases, playbook
from flask_login import current_user
from repos.donor_query import DonorCriteria, DonorQuery
from messaging.recipient import Recipient
from flask import current_app
from services.slot_planner import SlotPlanner
from services.drive_cloner import DriveCloner
from automessages import AutoPolicy
from services.attendance_service import AttendanceService, STATUSES, NotDriveDay, DAY_ONLY, is_drive_day
from messaging.messenger import Messenger
from messaging.audiences import AUDIENCES
from messaging.channels import CHANNELS
from messaging.events import bus
from security import permission_required
from media import MediaService
from integrations.catalog import SOCIAL
from repos import SocialPostRepo, CertificateRepo, VoucherRepo
from routes.social import default_caption, publish_drive, flash_results
from services.drive_gallery import DriveGallery

bp = Blueprint("drives", __name__, url_prefix="/admin/drives")
drives, interests = DriveRepo(), InterestRepo()

@bp.route("/")
@permission_required("manage_drives")
def index(): return render_template("admin/drives.html", drives=drives.all())

@bp.route("/new", methods=["GET", "POST"])
@permission_required("manage_drives")
def new():
    if request.method == "POST":
        f = request.form
        problem = _check_details(f)
        slots = _plan(f) if f.get("use_slots") and not problem else []
        if problem or slots is None:
            if problem: flash(problem, "error")
            return _new_form(f.get("copy_images_from"))
        capacity = sum(c for *_, c in slots) or int(f.get("capacity") or 100)
        time_slot = f"{f['slot_start']} – {f['slot_end']}" if slots else f.get("time_slot", "").strip()
        i = drives.create(f["title"].strip(), f["venue"].strip(), f["drive_date"], time_slot, f.get("description", "").strip(), capacity, None)
        SlotRepo().replace(i, slots)
        _, problems = gallery().add(drives.by_id(i), request.files.getlist("images"), [f.get("image_url", "")])
        for p in problems: flash(p, "warning")
        src = drives.by_id(f.get("copy_images_from") or 0)
        if src and not any(x.filename for x in request.files.getlist("images")) and not f.get("image_url"):
            drives.set_images(i, src["images"], src["image_url"])  # started from another drive: reuse its pictures
        future = f["drive_date"] >= local_today().isoformat()
        bus.publish("drive.created", drive=drives.by_id(i), announce=bool(f.get("announce")) and future)
        if f.get("announce") and future: flash("Donors are being told about the new drive (email / WhatsApp). 📣", "info")
        nets = [n for n in f.getlist("social") if n in SOCIAL]
        if nets and current_user.can("notify"): d = drives.by_id(i); flash_results(publish_drive(d, nets, default_caption(d)))
        if f.get("add_checklist"):
            who = f.get("checklist_assignee") or None
            n = PlaybookService(TaskRepo()).apply(drives.by_id(i), current_user, who or None)
            flash(f"Added the {n}-task drive checklist to Planning. 📋", "info")
        if f["drive_date"] < local_today().isoformat():
            flash("Saved as a past drive. It won't show on the website (see Drives → Past).", "warning")
        else:
            flash(f"Drive published{f' with {len(slots)} time slots' if slots else ''}! Now let your donors know. 📣", "celebrate")
        return redirect(url_for("drives.manage", i=i))
    return _new_form(request.args.get("from"))

def _new_form(src_id=None):
    """New drive form, optionally pre-filled from an existing drive (copy)."""
    src = drives.by_id(src_id) if src_id else None
    return render_template("admin/drive_new.html", lesson=ReportRepo().latest_with_lessons(), tomorrow=_tomorrow(), limit=_limit(), social=SOCIAL,
                           src=src, src_slots=SlotRepo().for_drive(src["id"]) if src else [], all_drives=drives.all(),
                           announce_default=AutoPolicy.enabled("drive_announcement"), suggested=DriveCloner.suggested_date(src) if src else _tomorrow())

@bp.route("/<i>")
@permission_required("manage_drives")
def manage(i):
    d = drives.by_id(i) or abort(404)
    people = interests.for_drive(i)
    board = {k: [p for p in people if p["status"] == k] for k in STATUSES}
    return render_template("admin/drive.html", d=d, board=board, statuses=STATUSES, audiences=AUDIENCES, channels=CHANNELS,
                           slots=SlotRepo().for_drive(i), locked=SlotRepo().has_bookings(i), images=DriveGallery.images(d),
                           social=SOCIAL, social_posts=SocialPostRepo().for_drive(i), caption=default_caption(d),
                           certificates=CertificateRepo().for_drive(i), vouchers=VoucherRepo().for_drive(i),
                           clone_date=DriveCloner.suggested_date(d),
                           drive_day=is_drive_day(d), day_only=DAY_ONLY,
                           limit=_limit(), **_task_overview(d))

def _task_overview(d):
    tasks = TaskRepo().for_drive(d["id"])
    grouped = [(p, [t for t in tasks if (t["phase"] or "Other") == p]) for p in phases() + ("Other",)]
    return {"drive_tasks": tasks, "task_phases": [(p, ts) for p, ts in grouped if ts], "staff": DonorRepo().staff(),
            "checklist_missing": len(PlaybookService(TaskRepo()).missing(d)), "checklist_total": len(playbook())}

@bp.post("/<i>/checklist")
@permission_required("manage_drives")
def checklist(i):
    d = drives.by_id(i) or abort(404)
    who = request.form.get("assignee_id") or None
    n = PlaybookService(TaskRepo()).apply(d, current_user, who or None)
    flash(f"Added {n} checklist tasks to “{d['title']}”. Assign them on the planner. 📋" if n else "The checklist is already on this drive.", "success" if n else "info")
    return go_next(url_for("drives.manage", i=i) + "#drive-tasks")

def _limit(): return current_app.config["DRIVE_IMAGE_LIMIT"]
def gallery(): return DriveGallery(MediaService(), _limit())

def _check_details(f):
    """Title, venue, a real date and a whole-number capacity. Returns a message or None."""
    if len(f.get("title", "").strip()) < 3: return "Please give the drive a title (3+ characters)."
    if len(f.get("venue", "").strip()) < 3: return "Please enter the venue."
    try: date.fromisoformat(f.get("drive_date", ""))
    except ValueError: return "Please pick a valid date."
    cap = f.get("capacity", "").strip()
    if not f.get("use_slots") and cap and not (cap.isdigit() and 0 < int(cap) <= 100000): return "Capacity must be a whole number above 0."
    return None

# ---- repeat a drive on another date
@bp.post("/<i>/clone")
@permission_required("manage_drives")
def clone(i):
    d, f = drives.by_id(i) or abort(404), request.form
    try: when = date.fromisoformat(f.get("drive_date", "")).isoformat()
    except ValueError: flash("Pick a date for the copy.", "error"); return redirect(url_for("drives.manage", i=i))
    new = drives.clone(d["id"], when, f.get("title"), bool(f.get("copy_slots")), bool(f.get("add_checklist")))
    flash(f"Copy created for {date.fromisoformat(when):%a %d %b %Y}. Check the details, then announce it. ✨", "celebrate")
    return redirect(url_for("drives.manage", i=new))

# ---- pictures + details ------------------------------------------------------------------------------
@bp.post("/<i>/images")
@permission_required("manage_drives")
def images(i):
    d = drives.by_id(i) or abort(404)
    g, act, url = gallery(), request.form.get("action", "add"), request.form.get("url", "")
    if act == "remove": g.remove(d, url); flash("Picture removed.", "info")
    elif act == "cover": g.make_cover(d, url); flash("Cover picture changed. 🖼️", "success")
    else:
        added, problems = g.add(d, request.files.getlist("images"), [request.form.get("image_url", "")])
        for p in problems: flash(p, "warning")
        if added: flash(f"{added} picture{'s' if added > 1 else ''} added. 🖼️", "success")
        elif not problems: flash("Choose a picture first.", "info")
    return redirect(url_for("drives.manage", i=i) + "#pictures")

@bp.post("/<i>/edit")
@permission_required("manage_drives")
def edit(i):
    d, f = drives.by_id(i) or abort(404), request.form
    problem = _check_details({**f, "use_slots": "1" if d["slot_count"] else f.get("use_slots", "")})
    if problem: flash(problem, "error")
    else:
        drives.update(i, f["title"].strip(), f["venue"].strip(), f["drive_date"], f.get("description", "").strip(),
                      None if d["slot_count"] else f.get("time_slot", "").strip(), None if d["slot_count"] else int(f.get("capacity") or d["capacity"]))
        flash("Drive details saved." + (" It's in the past, so it no longer shows on the website." if f["drive_date"] < local_today().isoformat() else ""), "success")
    return redirect(url_for("drives.manage", i=i))

def _tomorrow(): return (local_today() + timedelta(days=1)).isoformat()

def _plan(f):
    try: return SlotPlanner().plan(f["slot_start"], f["slot_end"], f["slot_minutes"], f["slot_capacity"])
    except (ValueError, KeyError) as e: flash(f"Time slots: {e}", "error"); return None

@bp.post("/<i>/slots")
@permission_required("manage_drives")
def slots(i):
    if SlotRepo().has_bookings(i): flash("Slots already have bookings, so they can't be changed.", "warning")
    elif (planned := _plan(request.form)) is not None:
        SlotRepo().replace(i, planned); flash(f"{len(planned)} time slots ready. Donors can now book a time. ⏱️", "success")
    return redirect(url_for("drives.manage", i=i))

@bp.post("/move")
@permission_required("manage_drives", "checkin")
def move():
    body = request.get_json()
    try: return jsonify(message=AttendanceService(interests, DonationRepo(), bus).move(str(body["id"]), body["status"]))
    except NotDriveDay as e: return jsonify(message=str(e)), 400
    except (ValueError, LookupError, KeyError): return jsonify(message="Could not move"), 400

@bp.post("/<i>/notify")
@permission_required("notify")
def notify(i):
    d = drives.by_id(i) or abort(404)
    people = {r.id: r for key in request.form.getlist("audience") if key in AUDIENCES for r in AUDIENCES[key].recipients()}
    n = Messenger(NotificationLogRepo()).send("drive_announcement", people.values(), request.form.getlist("channels"), drive_id=i, drive=d)
    flash(f"{n} messages sent to {len(people)} people. 🚀", "success")
    return redirect(url_for("drives.manage", i=i))

@bp.route("/<i>/invite", methods=["GET", "POST"])
@permission_required("notify")
def invite(i):
    d = drives.by_id(i) or abort(404)
    if request.method == "POST":
        ids = {str(x) for x in request.form.getlist("donor") if x}
        people = [Recipient.from_row(r) for r in DonorQuery().run(DonorCriteria()) if r["id"] in ids]
        n = Messenger(NotificationLogRepo()).send("drive_invitation", people, request.form.getlist("channels"), drive_id=i,
                                                   drive=d, note=request.form.get("note", "").strip())
        flash(f"Invitations sent: {n} messages to {len(people)} donors. 💌", "celebrate")
        return redirect(url_for("drives.manage", i=i))
    crit = DonorCriteria.from_args(request.args, i) if request.args else DonorCriteria(eligible_only=True, exclude_drive=i)
    found = DonorQuery(current_app.config["DONATION_GAP_DAYS"]).run(crit)
    return render_template("admin/invite.html", d=d, found=found, c=crit, channels=CHANNELS,
                           groups=["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
