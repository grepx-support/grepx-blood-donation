# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

STATUSES = {"todo": "To do", "in_progress": "In progress", "blocked": "Blocked", "done": "Done"}

class TaskService:
    """Task rules + an audit trail (TaskEventRepo) so you can see who changed what, and when."""
    def __init__(self, repo, policy, bus, events=None):
        from repos import TaskEventRepo
        self.repo, self.policy, self.bus, self.events = repo, policy, bus, events or TaskEventRepo()

    @property
    def me(self): return self.policy.user

    def create(self, form):
        data = self._clean(form)
        task_id = self.repo.create(self.me.id, **data)
        self.events.add(task_id, self.me.id, "created", self._assignee_text(task_id))
        if data["assignee_id"]: self.bus.publish("task.assigned", task=self.repo.by_id(task_id), by=self.me)
        return task_id

    def update(self, task_id, form):
        old = self._editable(task_id)
        data = self._clean(form)
        self.repo.update(task_id, **data)
        new = self.repo.by_id(task_id)
        for field, label in (("status", "status"), ("assignee_id", "assigned"), ("due_at", "due date")):
            if old[field] != new[field]: self.events.add(task_id, self.me.id, label, self._describe(field, new))
        if data["assignee_id"] and data["assignee_id"] != old["assignee_id"]:
            self.bus.publish("task.assigned", task=new, by=self.me)

    def move(self, task_id, status):
        if status not in STATUSES: raise ValueError(status)
        task = self._editable(task_id); self.repo.set_status(task_id, status)
        self.events.add(task_id, self.me.id, "status", STATUSES[status])
        return f"“{task['title']}” → {STATUSES[status]}"

    def claim(self, task_id):
        task = self.repo.by_id(task_id)
        if not task or not self.policy.can_claim(task): raise PermissionError(task_id)
        self.repo.assign(task_id, self.me.id)
        self.events.add(task_id, self.me.id, "picked up", self.me.name)
        return task

    def delete_many(self, ids):
        """Deletes the tasks this person may edit; returns (deleted, skipped)."""
        ok = [i for i in ids if (t := self.repo.by_id(i)) and self.policy.can_edit(t)]
        for i in ok: self.events.delete_for(i)
        self.repo.delete_many(ok)
        return len(ok), len(ids) - len(ok)

    def delete(self, task_id):
        self._editable(task_id); self.repo.delete(task_id); self.events.delete_for(task_id)

    def _editable(self, task_id):
        task = self.repo.by_id(task_id)
        if not task or not self.policy.can_edit(task): raise PermissionError(task_id)
        return task

    def _assignee_text(self, task_id):
        t = self.repo.by_id(task_id); return f"assigned to {t['assignee']}" if t["assignee"] else "unassigned"

    @staticmethod
    def _describe(field, t):
        if field == "status": return STATUSES.get(t["status"], t["status"])
        if field == "assignee_id": return t["assignee"] or "Unassigned"
        return (t["due_at"] or "no due date").replace("T", " ")

    @staticmethod
    def _existing(uid):
        from repos import DonorRepo
        return uid if uid and DonorRepo().by_id(uid) else None

    def _clean(self, f):
        status = f.get("status", "todo")
        return {"title": f["title"].strip(), "description": f.get("description", "").strip(), "due_at": f.get("due_at") or None,
                "assignee_id": self._existing(self.policy.assignee(f.get("assignee_id"))), "drive_id": f.get("drive_id") or None,
                "important": int(bool(f.get("important"))), "remind": int(bool(f.get("remind"))),
                "status": status if status in STATUSES else "todo", "phase": f.get("phase") or None}
