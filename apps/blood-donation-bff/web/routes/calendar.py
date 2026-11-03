# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from flask import Blueprint, Response, abort, current_app, flash
from ui.nav import go_back
from flask_login import login_required, current_user
from repos import DonorRepo, TaskRepo, InterestRepo, DriveRepo
from services.calendar_feed import CalendarFeed

bp = Blueprint("calendar", __name__)
def feed(): return CalendarFeed(DonorRepo(), TaskRepo(), InterestRepo(), DriveRepo(), current_app.config["ORG_NAME"])

@bp.route("/calendar/<token>.ics")
def ics(token):
    """Private subscription feed (Google Calendar → 'From URL'). The secret token is the only key."""
    body = feed().render(token) or abort(404)
    return Response(body, mimetype="text/calendar", headers={"Cache-Control": "no-cache"})

@bp.post("/calendar/reset")
@login_required
def reset():
    feed().token_for(current_user.id, reset=True)
    flash("New calendar link created. The old link stops working.", "info")
    return go_back("/")
