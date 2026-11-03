"""Targeted-invitation filters over the donor-service and donation-service data (same rules as before)."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DonorCriteria:
    """Filters for targeted invitations. Every field is optional."""
    groups: list = field(default_factory=list)
    sex: str = ""
    eligible_only: bool = False
    min_donations: int = 0
    not_since_days: int = 0
    age_min: int = 0
    age_max: int = 0
    exclude_drive: str | None = None

    @classmethod
    def from_args(cls, a, drive_id=None):
        num = lambda k: int(a.get(k) or 0)
        return cls(a.getlist("group"), a.get("sex", ""), bool(a.get("eligible")), num("min_donations"),
                   num("not_since_days"), num("age_min"), num("age_max"), drive_id if a.get("not_booked") else None)


class DonorQuery:
    """Each filter narrows the donor list (role donor only), sorted by name."""
    def __init__(self, gap_days=90): self.gap = gap_days

    def run(self, c):
        from dates import days_ago, years_ago
        from .donors import DonorRepo
        from .drives import _registrations
        rows = DonorRepo().search()
        keep = lambda f: [d for d in rows if f(d)]  # noqa: E731
        last = lambda d: d.get("last_donation") or "1900-01-01"  # noqa: E731
        if c.groups: rows = keep(lambda d: d.get("blood_group") in c.groups)
        if c.sex: rows = keep(lambda d: d.get("sex") == c.sex)
        if c.eligible_only: rows = keep(lambda d: last(d) <= days_ago(self.gap))
        if c.min_donations: rows = keep(lambda d: d["total"] >= c.min_donations)
        if c.not_since_days: rows = keep(lambda d: last(d) <= days_ago(c.not_since_days))
        if c.age_min: rows = keep(lambda d: bool(d.get("dob")) and d["dob"] <= years_ago(c.age_min))
        if c.age_max: rows = keep(lambda d: bool(d.get("dob")) and d["dob"] > years_ago(c.age_max + 1))
        if c.exclude_drive:
            booked = {r.get("donor_id") for r in _registrations(drive_id=c.exclude_drive) if r.get("donor_id")}
            rows = keep(lambda d: d["id"] not in booked)
        return rows
