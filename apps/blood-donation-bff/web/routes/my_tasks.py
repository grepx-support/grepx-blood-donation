# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

from flask import Blueprint, request, redirect, url_for, flash
from ui.nav import go_back
from flask_login import login_required, current_user
from repos import TaskRepo
from tasks.policy import TaskPolicy
from tasks.service import TaskService
from messaging.events import bus

bp = Blueprint("my_tasks", __name__, url_prefix="/my-tasks")

@bp.post("/<i>/status")
@login_required
def status(i):
    """Anyone with a task assigned (including donors) can move it along from their dashboard."""
    task = TaskRepo().by_id(i)
    if not task or task["assignee_id"] != current_user.id:
        flash("That task isn't assigned to you.", "error"); return redirect(url_for("donor.dashboard"))
    try: msg = TaskService(TaskRepo(), TaskPolicy(current_user), bus).move(i, request.form.get("status", ""))
    except (ValueError, PermissionError): flash("Could not update that task.", "error")
    else: flash(msg, "success")
    return go_back(url_for("donor.dashboard"))
