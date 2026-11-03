# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from repos import WidgetAccessRepo
from analytics.service import AnalyticsService
from security import staff_required, admin_required

bp = Blueprint("analytics", __name__, url_prefix="/admin/analytics")
service = lambda: AnalyticsService(WidgetAccessRepo())

@bp.route("/")
@staff_required
def index(): return render_template("admin/analytics.html", widgets=service().for_audience(current_user.role))

@bp.route("/access", methods=["GET", "POST"])
@admin_required
def access():
    if request.method == "POST":
        service().save(request.form); flash("Analytics access updated for every audience.", "success")
        return redirect(url_for("analytics.access"))
    rows, audiences = service().matrix()
    return render_template("admin/analytics_access.html", rows=rows, audiences=audiences)
