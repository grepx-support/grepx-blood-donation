# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from datetime import datetime
from flask import Blueprint, render_template
from flask_login import current_user
from repos import DriveRepo, StatsRepo, TaskRepo, WidgetAccessRepo
from analytics.service import AnalyticsService
from security import staff_required

bp = Blueprint("admin", __name__, url_prefix="/admin")

@bp.route("/")
@staff_required
def home():
    tasks = [t for t in TaskRepo().visible_to(current_user) if t["assignee_id"] == current_user.id and t["status"] != "done"]
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    charts = AnalyticsService(WidgetAccessRepo()).for_audience(current_user.role, kinds={"chart"})[:2]
    return render_template("admin/home.html", stats=StatsRepo().summary(), drives=DriveRepo().upcoming()[:5],
                           tasks=tasks[:6], overdue=sum(1 for t in tasks if t["due_at"] and t["due_at"] < now), charts=charts, now=now)
