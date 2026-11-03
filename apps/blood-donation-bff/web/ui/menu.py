# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

class MenuItem:
    """One sidebar entry; decides for itself whether a user may see it."""
    def __init__(self, label, icon, endpoint, perm=None, admin_only=False):
        self.label, self.icon, self.endpoint, self.perm, self.admin_only = label, icon, endpoint, perm, admin_only
        self.blueprint = endpoint.split(".")[0]

    def visible(self, user):
        if self.admin_only: return user.is_admin
        return self.perm is None or user.can(self.perm)

    ALIASES = {"donors": ("imports.",)}  # pages that live under another menu item

    def is_active(self, endpoint):
        endpoint = endpoint or ""
        if any(endpoint.startswith(a) for a in self.ALIASES.get(self.blueprint, ())): return True
        return endpoint == self.endpoint or (self.blueprint != "admin" and endpoint.startswith(self.blueprint + "."))

MENU = [MenuItem("Overview", "layout-dashboard", "admin.home"),
        MenuItem("Drives", "calendar-heart", "drives.index", "manage_drives"),
        MenuItem("Planning", "square-kanban", "tasks.index"),
        MenuItem("Analytics", "chart-pie", "analytics.index"),
        MenuItem("Check-in", "scan-line", "checkin.index", "checkin"),
        MenuItem("Donors", "users", "donors.index", "manage_donors"),
        MenuItem("Messages", "send", "messages.index", "view_log"),
        MenuItem("Reports & retros", "file-chart-column", "reports.index", "reports"),
        MenuItem("Users & passwords", "key-round", "users.index", admin_only=True),
        MenuItem("Volunteers & admins", "shield-check", "staff.index", admin_only=True),
        MenuItem("Integrations", "plug", "integrations.index", admin_only=True)]

def menu_for(user):
    return [m for m in MENU if m.visible(user)] if user.is_authenticated and user.is_staff else []
