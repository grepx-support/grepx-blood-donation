"""Smaller repositories: pictures (media-service), social posts (campaign-service), drive reports (event-report-service),
the message log (notification-service), settings and analytics visibility (settings-service)."""
from __future__ import annotations
import grepx_contracts as gc

from grepx_auth import is_sealed

from . import _nexus as nx


class MediaRepo:
    def add(self, *a, **k): pass
    def all(self): return [{**m, "id": m["id"]} for m in nx.table(gc.media.MEDIA)]
    def by_id(self, mid): return nx.one(gc.media.MEDIA, mid)
    def delete(self, mid):
        nx.command(gc.media.REQUESTS, gc.media.SERVICE, {"action": "DELETE", "media_id": mid}, ok_only=False)


class SocialPostRepo:
    """Every attempt to post a drive, as logged by campaign-service."""
    def add(self, *a, **k): pass                    # campaign-service records each attempt itself

    def for_drive(self, drive_id):
        rows = [{**p, "status": p.get("post_status"), "error": p.get("error") or None, "permalink": p.get("permalink") or None}
                for p in nx.where(gc.campaign.SOCIAL_POSTS, drive_id=drive_id)]
        return sorted(rows, key=lambda p: p.get("created") or "", reverse=True)


class ReportRepo:
    """Drive reports and retrospectives: event-report-service computes the numbers (SNAPSHOT) and keeps the retro text."""
    REQ, SVC = gc.event_report.REQUESTS, gc.event_report.SERVICE

    def get(self, drive_id):
        r = nx.one(gc.event_report.EVENT_REPORTS, drive_id)
        if not r:
            return None
        return {**r, "stats": dict(r.get("stats") or {}), "rating": int(r.get("rating") or 0) or None,
                "updated_at": (r.get("updated_at") or "")[:16].replace("T", " ")}

    def save_stats(self, drive_id, stats, user_id):
        nx.command(self.REQ, self.SVC, {"action": "SNAPSHOT", "drive_id": drive_id, "actor_id": user_id})

    def save_retro(self, drive_id, user_id, **f):
        fields = {k: (f.get(k) or "") for k in ("went_well", "to_improve", "actions", "notes")}
        nx.command(self.REQ, self.SVC, {"action": "SAVE_RETRO", "drive_id": drive_id, "actor_id": user_id,
                                        "rating": int(f.get("rating") or 0), **fields})

    def all(self):
        from .drives import DriveRepo
        out = []
        for d in DriveRepo().all():
            r = nx.one(gc.event_report.EVENT_REPORTS, d["id"]) or {}
            out.append({**d, "rating": int(r.get("rating") or 0) or None, "updated_at": (r.get("updated_at") or "")[:16].replace("T", " "),
                        "has_report": 1 if r.get("stats") else 0})
        return out

    def latest_with_lessons(self):
        rows = []
        for r in nx.table(gc.event_report.EVENT_REPORTS):
            if (r.get("to_improve") or "").strip() or (r.get("actions") or "").strip():
                d = nx.one(gc.event.EVENTS, r["id"]) or {}
                rows.append({**r, "title": d.get("title") or r.get("title"), "drive_date": d.get("drive_date") or ""})
        return max(rows, key=lambda r: r["drive_date"], default=None)


class NotificationLogRepo:
    """Every message notification-service handled (its request rows are the delivery log)."""
    STATUS = {"SENT": "sent", "LOGGED": "logged", "FAILED": "failed", "SKIPPED": "skipped"}

    def add(self, *a, **k): pass                    # notification-service records each delivery itself

    def _rows(self):
        out = []
        for n in nx.table(gc.notification.NOTIFICATIONS):
            d = nx.one(gc.event.EVENTS, n.get("drive_id")) if n.get("drive_id") else None
            out.append({**n, "status": self.STATUS.get(n.get("delivery"), "failed"), "event": n.get("event") or n.get("template"),
                        "created": (n.get("sent_at") or n.get("occurred_at") or "")[:16].replace("T", " "),
                        "drive_id": n.get("drive_id") or None, "title": (d or {}).get("title")})
        return sorted(out, key=lambda n: n["created"], reverse=True)

    def by_channel(self):
        counts: dict = {}
        for n in self._rows():
            c = counts.setdefault(n.get("channel"), {"channel": n.get("channel"), "sent": 0, "failed": 0})
            c["sent"] += n["status"] == "sent"
            c["failed"] += n["status"] == "failed"
        return list(counts.values())

    def recent(self, n=500):
        return self._rows()[:n]


class WidgetAccessRepo:
    """Which audiences may see which analytics widget (a setting in settings-service). '_none' = hidden from everyone."""
    NAME = "analytics.widget_access"

    def all(self):
        import json
        raw = (nx.one(gc.settings.APP_SETTINGS, self.NAME) or {}).get("value") or ""
        try:
            saved = json.loads(raw) if raw else {}
        except ValueError:
            saved = {}
        return {w: {a for a in audiences if a != "_none"} for w, audiences in saved.items()}

    def replace(self, matrix):
        import json
        SettingsRepo().set(self.NAME, json.dumps({w: sorted(a or {"_none"}) for w, a in matrix.items()}))


class SettingsRepo:
    """Admin-editable settings: settings-service owns them (secrets arrive and stay sealed)."""
    def all(self):
        return {r["id"]: r.get("value") or "" for r in nx.table(gc.settings.APP_SETTINGS)}

    def set(self, name, value):
        nx.command(gc.settings.REQUESTS, gc.settings.SERVICE, {"action": "SET", "name": name, "value": value or "",
                                                             "secret": is_sealed(value), "actor_id": nx.actor()})

    def delete(self, name):
        nx.command(gc.settings.REQUESTS, gc.settings.SERVICE, {"action": "DELETE", "name": name, "actor_id": nx.actor()})
