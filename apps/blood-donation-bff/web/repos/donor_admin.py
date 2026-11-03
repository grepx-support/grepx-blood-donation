"""Donor administration: the donor grid (filters, sorting, paging), saved segments and Excel import staging.
Donors, segments and import rows all belong to donor-service; donation counts come from donation-service."""
from __future__ import annotations
import grepx_contracts as gc

from dataclasses import dataclass, field

from dates import days_ago

from . import _nexus as nx
from .donors import _all, _matches, _with_stats

DONOR_REQ, DONOR_SVC = gc.donor.REQUESTS, gc.donor.SERVICE
SORTS = {"name": "name", "group": "blood_group", "donations": "total", "last": "last_donation", "created": "created"}


@dataclass
class DonorGridQuery:
    q: str = ""
    groups: list = field(default_factory=list)
    status: str = ""          # eligible | waiting | new
    sex: str = ""
    min_donations: int = 0
    people: str = "donor"     # donor | volunteer | admin | all
    sort: str = "name"
    desc: bool = False
    page: int = 1
    per: int = 50

    @classmethod
    def from_args(cls, a):
        num = lambda k, d: max(0, int(a.get(k) or d)) if str(a.get(k) or d).isdigit() else d  # noqa: E731
        return cls(a.get("q", "").strip(), [g for g in a.getlist("group") if g], a.get("status", ""), a.get("sex", ""),
                   num("min_donations", 0), a.get("people") if a.get("people") in ("volunteer", "admin", "all") else "donor",
                   a.get("sort", "name") if a.get("sort") in SORTS else "name", a.get("dir") == "desc",
                   max(1, num("page", 1)), min(200, max(10, num("per", 50))))

    def args(self, **override):
        d = {"q": self.q, "group": self.groups, "status": self.status, "sex": self.sex, "min_donations": self.min_donations or "",
             "people": "" if self.people == "donor" else self.people,
             "sort": self.sort, "dir": "desc" if self.desc else "", "page": self.page, "per": self.per}
        d.update(override)
        return {k: v for k, v in d.items() if v not in ("", None, [])}


class DonorGridRepo:
    def __init__(self, gap_days=90): self.gap = gap_days

    def _rows(self, g):
        cutoff = days_ago(self.gap)
        roles = {r["id"]: r.get("name") for r in nx.table(gc.access.STAFF_ROLES)}
        out = []
        for p in _all():
            if g.people != "all" and p["role"] != g.people:
                continue
            if not _matches(p, g.q):
                continue
            if g.groups and (p.get("blood_group") or "") not in ["" if x == "unknown" else x for x in g.groups]:
                continue
            if g.sex and p.get("sex") != g.sex:
                continue
            p = _with_stats(p)
            if g.min_donations and p["total"] < g.min_donations:
                continue
            if g.status == "new" and p["total"]:
                continue
            if g.status == "eligible" and not (p["last_donation"] and p["last_donation"] <= cutoff):
                continue
            if g.status == "waiting" and not (p["last_donation"] and p["last_donation"] > cutoff):
                continue
            out.append({**p, "staff_role": roles.get(p.get("staff_role_id"))})
        key = SORTS[g.sort]
        return sorted(out, key=lambda r: ((r.get(key) if r.get(key) is not None else (0 if key == "total" else "")),
                                          str(r["id"])), reverse=g.desc)

    def count(self, g): return len(self._rows(g))

    def page(self, g):
        start = (g.page - 1) * g.per
        return self._rows(g)[start:start + g.per]

    def ids(self, g): return [r["id"] for r in self._rows(g)]

    def facets(self):
        counts: dict = {}
        for p in _all():
            if p["role"] == "donor":
                k = p.get("blood_group") or "unknown"
                counts[k] = counts.get(k, 0) + 1
        return counts


class SegmentRepo:
    """Saved donor groups = a name + the filter query string (they stay current as donors change)."""
    def all(self):
        return sorted(nx.table(gc.donor.DONOR_SEGMENTS), key=lambda s: (s.get("name") or "").lower())

    def add(self, name, qs, by):
        v = nx.command(DONOR_REQ, DONOR_SVC, {"action": "SAVE_SEGMENT", "name": name[:80], "query": qs[:1000], "actor_id": by})
        return v.fields.get("segment_id")

    def delete(self, i):
        nx.command(DONOR_REQ, DONOR_SVC, {"action": "DELETE_SEGMENT", "segment_id": i})


class ImportRepo:
    """Excel rows held for review in donor-service until they are imported."""
    def add(self, batch, no, data, errors, status):
        v = nx.command(DONOR_REQ, DONOR_SVC, {"action": "STAGE_IMPORT_ROW", "batch": batch, "row_no": int(no), "data": data or {},
                                              "errors": errors or {}, "row_status": status})
        return v.fields.get("row_id")

    def update(self, i, data, errors, status):
        nx.command(DONOR_REQ, DONOR_SVC, {"action": "UPDATE_IMPORT_ROW", "row_id": i, "data": data or {}, "errors": errors or {},
                                          "row_status": status})

    def set_status(self, i, status):
        nx.command(DONOR_REQ, DONOR_SVC, {"action": "UPDATE_IMPORT_ROW", "row_id": i, "row_status": status})

    def parsed(self, batch):
        rows = sorted(nx.where(gc.donor.IMPORT_ROWS, batch=batch), key=lambda r: int(r.get("row_no") or 0))
        return [dict(id=r["id"], no=int(r.get("row_no") or 0), status=r.get("row_status"), data=dict(r.get("data") or {}),
                     errors=dict(r.get("errors") or {})) for r in rows]
