# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

"""Decorator pattern: stack access rules on any route."""
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import login_required, current_user

def _guard(check, message):
    def deco(view):
        @wraps(view)
        @login_required
        def wrapper(*a, **k):
            if not check(current_user):
                flash(message, "warning"); return redirect(url_for("public.index"))
            return view(*a, **k)
        return wrapper
    return deco

staff_required = _guard(lambda u: u.is_staff, "That area is for staff only.")
admin_required = _guard(lambda u: u.is_admin, "Admins only.")
def permission_required(*perms):
    return _guard(lambda u: any(u.can(p) for p in perms), "You don't have access to that function.")


# ---------------------------------------------------------------------------------------------
# Session hardening: no cached private pages (Back after logout shows the login page), idle logout
# for staff, fresh session on login, secure cookies and standard security headers.
import time
from datetime import timedelta
from flask import request, session
from flask_login import logout_user

PRIVATE_PREFIXES = ("/admin", "/dashboard", "/profile", "/calendar/")

class SessionGuard:
    def __init__(self, app, login_manager):
        self.app, self.idle = app, app.config["STAFF_IDLE_MINUTES"] * 60
        login_manager.session_protection = "strong"
        app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", REMEMBER_COOKIE_HTTPONLY=True,
                          REMEMBER_COOKIE_SAMESITE="Lax", REMEMBER_COOKIE_DURATION=timedelta(days=7),
                          PERMANENT_SESSION_LIFETIME=timedelta(hours=12))
        app.before_request(self.check_idle)
        app.after_request(self.headers)

    def check_idle(self):
        if request.path.startswith("/static/") or not current_user.is_authenticated: return None
        now, last = time.time(), session.get("seen")
        if current_user.is_staff and last and now - last > self.idle:
            logout_user(); session.clear()
            flash(f"You were logged out after {self.idle // 60} minutes of inactivity.", "info")
            return redirect(url_for("auth.login", next=request.path if request.method == "GET" else None))
        session["seen"] = now; session.permanent = True
        return None

    @staticmethod
    def headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if not request.path.startswith("/static/") and (current_user.is_authenticated or request.path.startswith(PRIVATE_PREFIXES)):
            resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private, max-age=0"
            resp.headers["Pragma"] = "no-cache"; resp.headers["Expires"] = "0"
        return resp
