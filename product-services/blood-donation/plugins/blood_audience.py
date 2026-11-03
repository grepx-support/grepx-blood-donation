"""Blood product audiences and invite filters, loaded by the generic campaign-service (config plugins.audience). Pure.

Plugin interface:  STATS_TABLE                      per-person figures the filters need (row key = person id)
                   audience(name, people, stats, roles, today, member_role) -> list | None   (None = not mine)
                   matches(person, stats, filters, today) -> bool
Audiences added here: eligible (may donate again today) | group:<blood group>.
Filters: groups, sex, eligible_only, min_donations, not_since_days, age_min, age_max.
"""
from __future__ import annotations

from datetime import date, timedelta

import grepx_contracts as gc

STATS_TABLE = gc.donation.DONOR_STATS
BLOOD_GROUPS = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")


def _eligible(stats: dict, today: date) -> bool:
    return not stats or stats.get("next_eligible", "") <= today.isoformat()


def audience(name: str, people: list[dict], stats: dict, roles: dict, today: date, member_role: str):
    if name == "eligible":
        return [p for p in people if roles.get(p["_key"], member_role) == member_role and _eligible(stats.get(p["_key"], {}), today)]
    if name.startswith("group:") and name[6:] in BLOOD_GROUPS:
        return [p for p in people if p.get("blood_group") == name[6:]]
    return None


def _age(dob: str, today: date) -> int | None:
    if not dob:
        return None
    born = date.fromisoformat(dob)
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def matches(donor: dict, stats: dict, f: dict, today: date) -> bool:
    groups = f.get("groups") or []
    if groups and (donor.get("blood_group") or "unknown") not in groups:
        return False
    if f.get("sex") and donor.get("sex") != f["sex"]:
        return False
    if f.get("eligible_only") and not _eligible(stats, today):
        return False
    if int(f.get("min_donations") or 0) > int(stats.get("count") or 0):
        return False
    if f.get("not_since_days") and stats.get("last") and stats["last"] > (today - timedelta(days=int(f["not_since_days"]))).isoformat():
        return False
    age = _age(donor.get("dob", ""), today)
    if (f.get("age_min") and (age is None or age < int(f["age_min"]))) or (f.get("age_max") and (age is None or age > int(f["age_max"]))):
        return False
    return True
