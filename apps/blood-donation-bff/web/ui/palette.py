# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

from flask import url_for
from repos import DriveRepo
from .menu import menu_for

class PaletteBuilder:
    """Items for the Ctrl+K command palette, tailored to the signed-in user."""
    def __init__(self, user): self.user = user

    def items(self):
        out = [self._item("Home", "public.index", "home", "Pages"), self._item("Am I eligible?", "public.eligibility", "stethoscope", "Pages")]
        if self.user.is_authenticated:
            out.append(self._item("My donor dashboard", "donor.dashboard", "heart", "Pages"))
        else:
            out += [self._item("Log in", "auth.login", "log-in", "Account"), self._item("Become a donor", "auth.register", "user-plus", "Account")]
        out += [{"label": m.label, "url": url_for(m.endpoint), "icon": m.icon, "group": "Workspace"} for m in menu_for(self.user)]
        out += [{"label": d["title"], "hint": d["drive_date"], "url": url_for("public.drive", i=d["id"]), "icon": "calendar-heart",
                 "group": "Upcoming drives"} for d in DriveRepo().upcoming()[:6]]
        return out

    @staticmethod
    def _item(label, endpoint, icon, group): return {"label": label, "url": url_for(endpoint), "icon": icon, "group": group}
