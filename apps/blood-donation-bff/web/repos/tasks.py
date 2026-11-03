"""Tasks (task-service): the original rows (status, drive_id, assignee/creator names) built from task-service state."""
from __future__ import annotations
import grepx_contracts as gc

from . import _nexus as nx

TASK_REQ, TASK_SVC = gc.task.REQUESTS, gc.task.SERVICE
FIELDS = ("title", "description", "due_at", "assignee_id", "drive_id", "important", "remind", "status", "phase")


TASK_COLUMNS = {"title": "", "description": None, "due_at": None, "created_by": None, "phase": None, "reminded_at": None, "created": None}


def _task(t: dict) -> dict:
    t = {**TASK_COLUMNS, **t}
    who = nx.one(gc.people.PEOPLE, t.get("assignee_id")) if t.get("assignee_id") else None
    creator = nx.one(gc.people.PEOPLE, t.get("created_by")) if t.get("created_by") else None
    drive_id = t.get("ref_id") if t.get("ref_type") == "event" else None
    d = nx.one(gc.event.EVENTS, drive_id) if drive_id else None
    return {**t, "status": t.get("state") or "todo", "drive_id": drive_id or None, "assignee_id": t.get("assignee_id") or None,
            "assignee": (who or {}).get("name"), "assignee_photo": (who or {}).get("photo_id"), "creator": (creator or {}).get("name"),
            "drive_title": (d or {}).get("title"), "drive_date": (d or {}).get("drive_date"),
            "important": 1 if t.get("important") else 0, "remind": 1 if t.get("remind") else 0}


def _order(t: dict):
    return (t["status"] == "done", not t.get("due_at"), t.get("due_at") or "", -int(t.get("important") or 0))


def _fields(f: dict) -> dict:
    """Original column names -> task-service fields."""
    out = {k: f[k] for k in FIELDS if k in f and k not in ("drive_id", "status")}
    if "status" in f:
        out["state"] = f["status"]
    if "drive_id" in f:
        d = nx.one(gc.event.EVENTS, f["drive_id"]) if f["drive_id"] else None
        out.update(ref_type="event" if d else "", ref_id=f["drive_id"] or "", ref_label=(d or {}).get("title", ""))
    for flag in ("important", "remind"):
        if flag in out:
            out[flag] = bool(int(out[flag] or 0))
    if "assignee_id" in out:
        p = nx.one(gc.people.PEOPLE, out["assignee_id"]) if out["assignee_id"] else None
        out.update(assignee_id=out["assignee_id"] or "", assignee_name=(p or {}).get("name", ""),
                   assignee_email=(p or {}).get("email", ""), assignee_phone=(p or {}).get("phone", ""))
    return out


def _manager() -> bool:
    try:
        from flask_login import current_user
        return bool(current_user.is_admin or current_user.can("manage_tasks"))
    except Exception:
        return False


class TaskRepo:
    def _all(self):
        return [_task(t) for t in nx.table(gc.task.TASKS)]

    def find(self, user, everyone=False, drive_id=None, who=None):
        rows = self._all()
        if not (user.is_admin and everyone):
            rows = [t for t in rows if t["assignee_id"] in (user.id, None) or t.get("created_by") == user.id]
        if drive_id:
            rows = [t for t in rows if t["drive_id"] == str(drive_id)]
        if who == "unassigned":
            rows = [t for t in rows if not t["assignee_id"]]
        elif who:
            rows = [t for t in rows if t["assignee_id"] == str(who)]
        return sorted(rows, key=_order)

    def visible_to(self, user, everyone=False):
        return self.find(user, everyone)

    def by_id(self, i):
        t = nx.one(gc.task.TASKS, i)
        return _task(t) if t else None

    def for_assignee(self, i):
        return sorted((t for t in self._all() if t["assignee_id"] == str(i)), key=_order)

    def for_drive(self, drive_id):
        return sorted((t for t in self._all() if t["drive_id"] == str(drive_id)), key=_order)

    def titles_for_drive(self, drive_id):
        return {t["title"] for t in self.for_drive(drive_id)}

    def create(self, created_by, **f):
        v = nx.command(TASK_REQ, TASK_SVC, {"action": "CREATE", "actor_id": created_by, **_fields(f)})
        return v.fields.get("task_id")

    def update(self, i, **f):
        nx.command(TASK_REQ, TASK_SVC, {"action": "UPDATE", "task_id": i, "actor_id": nx.actor(), "actor_is_manager": _manager(),
                                        "reminded_at": "", **_fields(f)})

    def set_status(self, i, status):
        nx.command(TASK_REQ, TASK_SVC, {"action": "CHANGE_STATUS", "task_id": i, "state": status, "actor_id": nx.actor(),
                                        "actor_is_manager": _manager()})

    def assign(self, i, user_id):
        """Picking up a task yourself is task-service's CLAIM (anyone may take an unassigned task); others: an edit."""
        if user_id and str(user_id) == nx.actor():
            p = nx.one(gc.people.PEOPLE, user_id) or {}
            nx.command(TASK_REQ, TASK_SVC, {"action": "CLAIM", "task_id": i, "actor_id": user_id, "assignee_name": p.get("name", ""),
                                            "assignee_email": p.get("email", ""), "assignee_phone": p.get("phone", "")})
        else:
            self.update(i, assignee_id=user_id or "")

    def delete(self, i):
        nx.command(TASK_REQ, TASK_SVC, {"action": "DELETE", "task_id": i, "actor_id": nx.actor(), "actor_is_manager": _manager()})

    def delete_many(self, ids):
        for i in ids:
            self.delete(i)

    def due_for_reminder(self, horizon, cooldown):
        return []                                   # task-service sends task reminders itself (scheduler tick)

    def mark_reminded(self, i, when):
        pass


class TaskEventRepo:
    """The audit trail task-service keeps on each task ("events")."""
    def add(self, task_id, by_id, action, detail=""):
        pass                                        # task-service records events as it applies each change

    def for_tasks(self, ids):
        names: dict = {}
        out = {}
        for i in ids or []:
            t = nx.one(gc.task.TASKS, i) or {}
            for e in reversed(list(t.get("events") or [])):
                by = e.get("by") or ""
                if by not in names:
                    names[by] = (nx.one(gc.people.PEOPLE, by) or {}).get("name") if by else None
                out.setdefault(i, []).append({"who": names[by] or "System", "action": e.get("action", ""),
                                              "detail": e.get("detail", ""), "at": (e.get("at") or "")[:16].replace("T", " ")})
        return out

    def delete_for(self, task_id):
        pass                                        # the trail lives on the task in task-service
