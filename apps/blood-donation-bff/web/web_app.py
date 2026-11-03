# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The original LifeFlow web site (server-rendered pages), running on the microservices.

Same routes, templates, CSS and JS as before; the data layer (repos/) reads Nexus state tables and sends every
change as a request to the owning service. Mounted by the blood-donation BFF at "/" (the JSON API stays at /api/v1).
"""
import os
from datetime import datetime
from grepx_service import local_today

from flask import Flask, flash, redirect, request, url_for
from flask_login import current_user
from flask_wtf.csrf import CSRFError

from config import Config
from extensions import csrf, login_manager
from repos import _nexus
from routes import BLUEPRINTS
from security import SessionGuard
from ui import filters
from ui.menu import menu_for
from ui.palette import PaletteBuilder
from ui.site import site_url
from user import Guest, User


def _context():
    return {"menu": menu_for(current_user), "palette": PaletteBuilder(current_user).items(),
            "today_iso": local_today().isoformat(), "now_iso": datetime.now().strftime("%Y-%m-%dT%H:%M")}


def create_web_app(gateway, config=Config) -> Flask:
    _nexus.GW = gateway
    here = os.path.dirname(os.path.abspath(__file__))
    app = Flask(__name__, root_path=here, template_folder="templates", static_folder="static")
    app.config.from_object(config)
    login_manager.init_app(app)
    csrf.init_app(app)
    app.register_error_handler(CSRFError, _expired_form)
    app.register_error_handler(_nexus.RepoError, _refused)
    login_manager.user_loader(User.load)
    login_manager.anonymous_user = Guest
    SessionGuard(app, login_manager)
    app.context_processor(lambda: {"org": app.config["ORG_NAME"], "wa_number": app.config["WHATSAPP_NUMBER"],
                                   "company": app.config["COMPANY_NAME"], "company_url": app.config["COMPANY_URL"],
                                   "year": local_today().year, "site": site_url()})
    app.context_processor(_context)
    filters.register(app)
    for bp in BLUEPRINTS:
        app.register_blueprint(bp)
    _wire_events()
    return app


def _wire_events():
    """Only events no service handles itself: welcome, thanks, certificates, referrals, slot moves, task
    assignments and reminders are sent by their services (sending them here too would send them twice)."""
    from messaging.events import bus
    from messaging.subscribers import on_drive_created
    if on_drive_created not in bus._subs.get("drive.created", []):
        bus.subscribe("drive.created", on_drive_created)


def _refused(e):
    """A service said no (or isn't connected yet): show why and go back, like the original's flash messages."""
    flash(str(e), "warning")
    back = request.referrer or ""
    return redirect(back if back.startswith(request.host_url) else url_for("public.index"))


def _expired_form(e):
    flash("That page was out of date (you logged in or out in another tab, or it was open a long time). "
          "Nothing was saved — please try again. Tip: use a private window to test a second account.", "warning")
    if request.headers.get("HX-Request"):
        return "", 200, {"HX-Refresh": "true"}
    back = request.referrer or ""
    return redirect(back if back.startswith(request.host_url) else url_for("auth.login"))
