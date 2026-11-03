# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from ui.site import site_url
from flask import abort, Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from ui.nav import go_back, id_list
from flask_login import current_user
from repos import TaskRepo, DonorRepo, DriveRepo, InterestRepo, TaskEventRepo
from tasks.playbook import phases, playbook
from services.calendar_feed import CalendarFeed
from tasks.policy import TaskPolicy
from tasks.service import TaskService, STATUSES
from messaging.events import bus
from security import staff_required, permission_required

bp = Blueprint("tasks", __name__, url_prefix="/admin/tasks")
repo = TaskRepo()
def service(): return TaskService(repo, TaskPolicy(current_user), bus)

@bp.route("/")
@staff_required
def index():
    a = request.args
    everyone = a.get("scope") == "all" and current_user.is_admin
    rows = repo.find(current_user, everyone, a.get("drive") or None, a.get("who") or None)
    from tasks.playbook import PlaybookService
    pb, items = PlaybookService(repo), playbook()
    drive_checklists = [(d, len(items) - len(pb.missing(d)), len(items),
                         sum(1 for t in repo.for_drive(d["id"]) if t["status"] == "done"), len(pb.checklist_tasks(d, only_open=True)))
                        for d in DriveRepo().upcoming()]
    history = TaskEventRepo().for_tasks([t["id"] for t in rows])
    tasks = [dict(t, history=history.get(t["id"], [])) for t in rows]
    return render_template("admin/tasks.html", tasks=tasks, statuses=STATUSES, phases=phases(), staff=DonorRepo().staff(),
                           drives=DriveRepo().upcoming(), all_drives=DriveRepo().all(), everyone=everyone,
                           can_assign=TaskPolicy(current_user).can_assign_others(), feed_url=_feed_url(),
                           f_drive=a.get("drive", ""), f_who=a.get("who", ""), drive_checklists=drive_checklists, playbook=items)

def _feed_url():
    cfg = current_app.config
    token = CalendarFeed(DonorRepo(), repo, InterestRepo(), DriveRepo(), cfg["ORG_NAME"]).token_for(current_user.id)
    return f"{site_url()}/calendar/{token}.ics"

@bp.post("/")
@staff_required
def create():
    service().create(request.form); flash("Task created. ✅", "success")
    return go_back(url_for("tasks.index"))

@bp.post("/<i>")
@staff_required
def update(i):
    try: service().update(i, request.form); flash("Task updated.", "success")
    except PermissionError: flash("You can only edit your own tasks.", "error")
    return go_back(url_for("tasks.index"))

@bp.route("/people")
@staff_required
def people():
    """Search anyone (admin, volunteer or donor) to assign a task to. Staff are listed first."""
    rows = DonorRepo().people(request.args.get("q", "").strip())
    return jsonify([{"id": r["id"], "name": r["name"], "role": r["role"],
                     "email": "" if "no-email.local" in r["email"] else r["email"]} for r in rows])

@bp.post("/<i>/claim")
@staff_required
def claim(i):
    try: t = service().claim(i); flash(f"You picked up “{t['title']}”. 💪", "success")
    except PermissionError: flash("Someone already picked up that task.", "warning")
    return go_back(url_for("tasks.index"))

@bp.post("/<i>/delete")
@staff_required
def delete(i):
    try: service().delete(i); flash("Task deleted.", "info")
    except PermissionError: flash("You can only delete your own tasks.", "error")
    return redirect(url_for("tasks.index"))

@bp.post("/bulk-delete")
@staff_required
def bulk_delete():
    ids = id_list(request.form.get("ids"))
    done, skipped = service().delete_many(ids)
    flash(f"Deleted {done} task{'s' if done != 1 else ''}." + (f" {skipped} skipped (not yours to delete)." if skipped else ""), "info" if done else "warning")
    return go_back(url_for("tasks.index"))

@bp.post("/checklist/<drive_id>/remove")
@permission_required("manage_tasks", "manage_drives")
def remove_checklist(drive_id):
    """Remove a drive's standard checklist in one go (all of it, or only the tasks nobody started)."""
    from tasks.playbook import PlaybookService
    d = DriveRepo().by_id(drive_id)
    if not d: abort(404)
    n = PlaybookService(repo).remove(d, only_open=request.form.get("which") == "open")
    flash(f"Removed {n} checklist task{'s' if n != 1 else ''} from {d['title']}. You can add the checklist again any time.", "info")
    return go_back(url_for("tasks.index"))

@bp.post("/move")
@staff_required
def move():
    body = request.get_json()
    try: return jsonify(message=service().move(str(body["id"]), body["status"]))
    except (PermissionError, ValueError, KeyError): return jsonify(message="Not allowed"), 400

@bp.route("/events.json")
@staff_required
def events():
    colors = {"todo": "#f59e0b", "in_progress": "#0ea5e9", "blocked": "#dc2626", "done": "#16a34a"}
    out = [{"title": ("⚠️ " if t["important"] else "") + t["title"], "start": t["due_at"], "color": colors.get(t["status"])}
           for t in repo.visible_to(current_user, current_user.is_admin) if t["due_at"]]
    out += [{"title": "🩸 " + d["title"], "start": d["drive_date"], "allDay": True, "color": "#e11d48",
             "url": url_for("public.drive", i=d["id"])} for d in DriveRepo().all()]
    return jsonify(out)
