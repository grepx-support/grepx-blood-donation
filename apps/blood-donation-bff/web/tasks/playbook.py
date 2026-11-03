# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

"""The standard drive checklist. Its items live in checklist-service (seeded from product-services/<p>/catalog/playbook.yaml);
checklist-service creates and removes the tasks. This module only reads the template and asks."""
import grepx_contracts as gc
from types import SimpleNamespace

from repos import _nexus as nx

TEMPLATE_KEY = "blood-drive-playbook"
REQUESTS, SERVICE = gc.checklist.REQUESTS, gc.checklist.SERVICE


def playbook() -> list:
    """The template's items as objects (phase, title, days, details, time, important), in template order."""
    row = nx.one(gc.checklist.CHECKLIST_TEMPLATES, TEMPLATE_KEY) or {}
    return [SimpleNamespace(**{"time": "09:00", "important": False, "details": "", **item}) for item in row.get("items") or []]


def phases() -> tuple:
    return tuple(dict.fromkeys(i.phase for i in playbook()))


class PlaybookService:
    """Adds / removes the standard checklist for one drive. Running it twice never duplicates tasks."""
    def __init__(self, repo, events=None): self.repo = repo

    def missing(self, drive):
        have = self.repo.titles_for_drive(drive["id"])
        return [i for i in playbook() if i.title not in have]

    def checklist_tasks(self, drive, only_open=False):
        titles = {i.title for i in playbook()}
        return [t for t in self.repo.for_drive(drive["id"]) if t["title"] in titles and not (only_open and t["status"] != "todo")]

    def apply(self, drive, by_user, assignee_id=None):
        who = nx.one(gc.people.PEOPLE, assignee_id) or {} if assignee_id else {}
        v = nx.command(REQUESTS, SERVICE, {"action": "APPLY", "template_key": TEMPLATE_KEY, "ref_type": "event", "ref_id": drive["id"],
                                           "ref_label": drive["title"], "base_date": drive["drive_date"], "actor_id": str(by_user.id),
                                           "assignee_id": assignee_id or "", "assignee_name": who.get("name", ""),
                                           "assignee_email": who.get("email", ""), "assignee_phone": who.get("phone", "")})
        return int(v.fields.get("created") or 0)

    def remove(self, drive, only_open=False):
        v = nx.command(REQUESTS, SERVICE, {"action": "REMOVE", "template_key": TEMPLATE_KEY, "ref_id": drive["id"],
                                           "only_open": bool(only_open), "actor_id": nx.actor()})
        return int(v.fields.get("removed") or 0)
