# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, abort
from flask_login import current_user
from repos import ReportRepo, DriveRepo, InterestRepo, TaskRepo
from repos.report_repo import RETRO_FIELDS
from services.report_builder import DriveReportBuilder
from services.report_exporter import ReportExporter
from security import permission_required

bp = Blueprint("reports", __name__, url_prefix="/admin/reports")
guard = permission_required("reports")
repo = ReportRepo()

@bp.route("/")
@guard
def index(): return render_template("admin/reports.html", drives=repo.all())

@bp.route("/<i>")
@guard
def view(i):
    d = DriveRepo().by_id(i) or abort(404)
    if not repo.get(i): repo.save_stats(i, DriveReportBuilder().build(i), current_user.id)
    return render_template("admin/report.html", d=d, r=repo.get(i))

@bp.post("/<i>")
@guard
def save(i):
    repo.save_retro(i, current_user.id, **{k: request.form.get(k, "").strip() for k in RETRO_FIELDS})
    flash("Report saved. Future drives will show these lessons. 📝", "success")
    return redirect(url_for("reports.view", i=i))

@bp.post("/<i>/refresh")
@guard
def refresh(i):
    repo.save_stats(i, DriveReportBuilder().build(i), current_user.id)
    flash("Numbers refreshed from the latest data.", "info")
    return redirect(url_for("reports.view", i=i))

@bp.post("/<i>/task")
@guard
def to_task(i):
    TaskRepo().create(current_user.id, title=request.form["title"][:120], description=f"Retro action from drive #{i}",
                      assignee_id=current_user.id, status="todo", important=0, remind=0)
    flash("Action added to your planner. ✅", "success")
    return redirect(url_for("reports.view", i=i))

@bp.route("/<i>/export.xlsx")
@guard
def export(i):
    r = repo.get(i) or abort(404)
    return send_file(ReportExporter().build(r, InterestRepo().for_drive(i)), as_attachment=True, download_name=f"drive-{i}-report.xlsx")
