"""People: donor profiles (donor-service), login (auth-service), role and permissions (access-service)."""
from __future__ import annotations
import grepx_contracts as gc

from typing import Optional

from dates import days_ago

from . import _nexus as nx

PERSON_REQ, PERSON_SVC = gc.people.REQUESTS, gc.people.SERVICE  # the donor record itself (+ blood fields)
ACCESS_REQ, ACCESS_SVC = gc.access.REQUESTS, gc.access.SERVICE
AUTH_REQ, AUTH_SVC = gc.auth.REQUESTS, gc.auth.SERVICE
_ROLE_ORDER = {"admin": 0, "volunteer": 1}
DONOR_COLUMNS = {"name": "", "email": "", "phone": "", "blood_group": None, "sex": None, "weight": None, "dob": None, "ref_code": None,
                 "referred_by": None, "cal_token": None, "photo_id": None, "created": None}


def _person(d: dict) -> dict:
    """A donor row in the original shape: role / staff_role_id from access-service, stats from donations."""
    access = nx.one(gc.access.USER_ACCESS, d["id"]) or {}
    d = {**DONOR_COLUMNS, **d}
    return {**d, "role": access.get("role") or "donor", "staff_role_id": access.get("staff_role_id") or None,
            "password_hash": "", "weight": d.get("weight") or None}


def _with_stats(p: dict) -> dict:
    mine = [x for x in nx.table(gc.donation.DONATIONS) if x.get("donor_id") == p["id"]]
    return {**p, "last_donation": max((x.get("donated_on", "") for x in mine), default=None), "total": len(mine)}


def _all() -> list[dict]:
    return [_person(d) for d in nx.table(gc.people.PEOPLE)]


def _matches(p: dict, q: str) -> bool:
    q = (q or "").strip().lower()
    if not q:
        return True
    digits = "".join(ch for ch in q if ch.isdigit())
    return q in (p.get("name") or "").lower() or q in (p.get("email") or "").lower() or bool(
        digits and digits in "".join(ch for ch in p.get("phone") or "" if ch.isdigit()))


def _by_role_then_name(p: dict):
    return _ROLE_ORDER.get(p["role"], 2), (p.get("name") or "").lower()


class DonorRepo:
    def by_id(self, i) -> Optional[dict]:
        d = nx.one(gc.people.PEOPLE, i)
        return _person(d) if d else None

    def by_email(self, e) -> Optional[dict]:
        e = (e or "").strip().lower()
        found = [d for d in nx.table(gc.people.PEOPLE) if (d.get("email") or "").lower() == e] if e else []
        return _person(found[0]) if found else None

    def with_stats(self, i):
        p = self.by_id(i)
        return _with_stats(p) if p else None

    def search(self, q="", group=""):
        return sorted((_with_stats(p) for p in _all() if p["role"] == "donor" and (not group or p.get("blood_group") == group)
                       and _matches(p, q)), key=lambda p: (p.get("name") or "").lower())

    def users(self, q=""):
        return sorted((p for p in _all() if (p["role"] != "donor" and not q) or (q and _matches(p, q))), key=_by_role_then_name)

    # ---- writes: each one is a request to the service that owns the data --------------------------------------
    def register(self, name, email, phone, password, group="", sex="", weight=None, dob="", role="donor",
                 source="online", invite_code="", link="") -> str:
        """Create the donor profile and its login (a saga: donor-service, then auth-service), then the role."""
        sealed = nx.GW.box.seal(password)
        v = nx.command(PERSON_REQ, PERSON_SVC, {"action": "CREATE", "name": name, "email": (email or "").lower(), "phone": phone,
                                              "blood_group": group or "", "sex": sex or "", "weight": weight, "dob": dob or "",
                                              "source": source, "invite_code": invite_code or "", "link": link,
                                              "allow_no_email": source != "online"})
        uid = v.fields["donor_id"]
        if password:
            nx.command(AUTH_REQ, AUTH_SVC, {"action": "REGISTER", "user_id": uid, "email": (email or "").lower(), "password_enc": sealed})
        if role and role != "donor":
            self.set_role(uid, role)
        return uid

    def create(self, name, email, phone, pw_hash, group, sex, weight, dob, role="donor"):
        """Original signature: here pw_hash is the plain password (auth-service hashes it)."""
        return self.register(name, email, phone, pw_hash, group, sex, weight, dob, role, source="staff")

    def verify_password(self, email, password) -> Optional[str]:
        """auth-service checks the password; the user id, None for wrong credentials, RepoError when it can't answer."""
        v = nx.command(AUTH_REQ, AUTH_SVC, {"action": "LOGIN", "email": (email or "").strip().lower(),
                                           "password_enc": nx.GW.box.seal(password or "")}, ok_only=False)
        if v.ok:
            return v.fields.get("user_id")
        if v.reason == "INVALID_CREDENTIALS":
            return None
        raise nx.RepoError(v.reason or "SERVICE_UNAVAILABLE", str(v.fields.get("detail") or ""))

    def set_role(self, i, role):
        nx.command(ACCESS_REQ, ACCESS_SVC, {"action": "SET_ROLE", "user_id": i, "role": role, "actor_id": nx.actor()})

    def set_staff_role(self, i, role_id):
        nx.command(ACCESS_REQ, ACCESS_SVC, {"action": "SET_STAFF_ROLE", "user_id": i, "staff_role_id": role_id or "",
                                            "actor_id": nx.actor()})

    def set_password(self, i, password):
        """Original took a hash; here the plain password goes (sealed) to auth-service."""
        p = self.by_id(i) or {}
        nx.command(AUTH_REQ, AUTH_SVC, {"action": "SET_PASSWORD", "user_id": i, "email": p.get("email", ""),
                                       "password_enc": nx.GW.box.seal(password)})

    def last_donation(self, i):
        return max((x.get("donated_on", "") for x in nx.table(gc.donation.DONATIONS) if x.get("donor_id") == str(i)), default=None)

    def eligible_today(self, gap):
        day = days_ago(gap)
        return [p for p in (_with_stats(p) for p in _all() if p["role"] == "donor") if p["last_donation"] == day]

    def staff(self):
        return sorted((p for p in _all() if p["role"] != "donor"), key=lambda p: (p.get("name") or "").lower())

    def by_column(self, column, value):
        assert column in ("ref_code", "cal_token")
        if not value:
            return None
        found = [d for d in nx.table(gc.people.PEOPLE) if str(d.get(column) or "").lower() == str(value).lower()]
        return _person(found[0]) if found else None

    def set_column(self, i, column, value):
        assert column in ("ref_code", "cal_token", "referred_by", "photo_id")
        if column == "photo_id":
            nx.command(PERSON_REQ, PERSON_SVC, {"action": "SET_PHOTO", "donor_id": i, "photo_id": value or ""})
        elif column == "cal_token":
            nx.command(PERSON_REQ, PERSON_SVC, {"action": "RESET_CAL_TOKEN", "donor_id": i})
        # ref_code / referred_by are set by donor-service when the profile is created

    def find_exact(self, contact):
        c = (contact or "").strip().lower()
        digits = "".join(ch for ch in c if ch.isdigit())
        for d in nx.table(gc.people.PEOPLE):
            phone = "".join(ch for ch in (d.get("phone") or "") if ch.isdigit())
            if (d.get("email") or "").lower() == c or (len(digits) >= 8 and phone.endswith(digits[-8:])):
                return _person(d)
        return None

    def lookup(self, q, limit=8):
        return sorted((_with_stats(p) for p in _all() if _matches(p, q)), key=lambda p: (p.get("name") or "").lower())[:limit]

    def by_role(self, role):
        return [p for p in _all() if p["role"] == role]

    def donors_in_group(self, group):
        return [p for p in _all() if p["role"] == "donor" and p.get("blood_group") == group]

    def donors_eligible(self, since_day):
        return [p for p in (_with_stats(p) for p in _all() if p["role"] == "donor") if (p["last_donation"] or "1900-01-01") <= since_day]

    def accounts(self, q="", role="", limit=300):
        return sorted((p for p in _all() if (not role or p["role"] == role) and _matches(p, q)), key=_by_role_then_name)[:limit]

    def people(self, q="", limit=20):
        return sorted((p for p in _all() if (not q and p["role"] != "donor") or (q and _matches(p, q))), key=_by_role_then_name)[:limit]

    def many(self, ids, with_stats=False):
        wanted = {str(i) for i in ids}
        rows = [p for p in _all() if p["id"] in wanted]
        return sorted((_with_stats(p) if with_stats else p for p in rows), key=lambda p: (p.get("name") or "").lower())

    def bulk_set(self, ids, values):
        """One change for many people (admins are never changed in bulk): role -> access-service, the rest -> donor-service."""
        role = values.get("role")
        profile = {k: (v or "") for k, v in values.items() if k != "role"}
        for i in ids:
            p = self.by_id(i)
            if not p or p["role"] == "admin":
                continue
            if profile:
                nx.command(PERSON_REQ, PERSON_SVC, {"action": "UPDATE", "donor_id": i, **profile})
            if role and role != p["role"]:
                self.set_role(i, role)

    EDITABLE = ("name", "email", "phone", "blood_group", "sex", "weight", "dob")

    def update_profile(self, i, **f):
        changes = {k: (f[k] if f[k] not in ("", None) else "") for k in self.EDITABLE if k in f}
        nx.command(PERSON_REQ, PERSON_SVC, {"action": "UPDATE", "donor_id": i, **changes})


class PermissionRepo:
    def get(self, i):
        access = nx.one(gc.access.USER_ACCESS, i) or {}
        return set(access.get("perms") or [])

    def set(self, i, perms):
        current = self.get(i)
        for p in set(perms) ^ current:
            nx.command(ACCESS_REQ, ACCESS_SVC, {"action": "SET_PERMISSION", "user_id": i, "perm": p, "enabled": p in perms,
                                                "actor_id": nx.actor()})


class StaffRoleRepo:
    """Volunteer roles: a name and a set of functions (permissions) — access-service."""
    def all(self):
        members = {}
        for a in nx.table(gc.access.USER_ACCESS):
            if a.get("role") == "volunteer" and a.get("staff_role_id"):
                members[a["staff_role_id"]] = members.get(a["staff_role_id"], 0) + 1
        rows = [{**r, "members": members.get(r["id"], 0), "perm_list": list(r.get("perms") or []),
                 "perms": ",".join(r.get("perms") or [])} for r in nx.table(gc.access.STAFF_ROLES)]
        return sorted(rows, key=lambda r: (r.get("name") or "").lower())

    def by_id(self, i):
        r = nx.one(gc.access.STAFF_ROLES, i)
        return {**r, "perms": ",".join(r.get("perms") or [])} if r else None

    def perms_for(self, i):
        r = nx.one(gc.access.STAFF_ROLES, i) if i else None
        return set(r.get("perms") or []) if r else set()

    def create(self, name, description, perms):
        v = nx.command(ACCESS_REQ, ACCESS_SVC, {"action": "SAVE_ROLE", "name": name[:80], "description": description[:255],
                                                "perms": list(perms), "actor_id": nx.actor()})
        return v.fields.get("role_id")

    def update(self, i, name, description, perms):
        nx.command(ACCESS_REQ, ACCESS_SVC, {"action": "SAVE_ROLE", "role_id": i, "name": name[:80], "description": description[:255],
                                            "perms": list(perms), "actor_id": nx.actor()})

    def delete(self, i):
        nx.command(ACCESS_REQ, ACCESS_SVC, {"action": "DELETE_ROLE", "role_id": i, "actor_id": nx.actor()})
