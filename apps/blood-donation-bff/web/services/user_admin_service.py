# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

import secrets
from permissions import ROLES
from validation import UserForm, check, summary
from validation.rules import PASSWORD_MIN

class UserError(Exception): pass

class UserAdminService:
    """Admin-side account management for anyone: donor, volunteer or admin. The email is the login name."""
    MIN_PASSWORD = PASSWORD_MIN

    def __init__(self, donors): self.donors = donors

    def create(self, f):
        u = self._clean(f); email = u.email
        if self.donors.by_email(email): raise UserError(f"{email} is already registered.")
        password, generated = self._password(f.get("password"))
        uid = self.donors.create(u.name, email, u.phone or "-", password,
                                 f.get("blood_group") or None, f.get("sex") or None, None, None, self._role(f.get("role")))
        return self.donors.by_id(uid), password if generated else None

    def update(self, uid, f, acting_user):
        user = self.donors.by_id(uid) or self._missing()
        u = self._clean(f); email = u.email
        other = self.donors.by_email(email)
        if other and other["id"] != uid: raise UserError(f"{email} belongs to another account.")
        role = "admin" if uid == acting_user.id else self._role(f.get("role"))  # never demote yourself by accident
        self.donors.update_profile(uid, name=u.name, email=email, phone=u.phone or user["phone"],
                                   blood_group=user["blood_group"], sex=user["sex"], weight=user["weight"], dob=user["dob"])
        self.donors.set_role(uid, role)
        return self.donors.by_id(uid)

    def reset_password(self, uid, new_password=None):
        self.donors.by_id(uid) or self._missing()
        password, generated = self._password(new_password)
        self.donors.set_password(uid, password)
        return password if generated else None

    def _password(self, given):
        given = (given or "").strip()
        if not given: return secrets.token_urlsafe(9), True
        if len(given) < self.MIN_PASSWORD: raise UserError(f"Passwords need at least {self.MIN_PASSWORD} characters.")
        return given, False

    @staticmethod
    def _clean(f):
        u, errors = check(UserForm, f)
        if errors: raise UserError("Please fix: " + summary(errors))
        return u

    @staticmethod
    def _email(v):
        v = (v or "").strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]: raise UserError("Please enter a valid email (it is the login name).")
        return v

    @staticmethod
    def _name(f):
        n = (f.get("name") or "").strip()
        if len(n) < 2: raise UserError("Please enter the person's name.")
        return n

    @staticmethod
    def _role(r): return r if r in ROLES else "donor"

    @staticmethod
    def _missing(): raise UserError("That user no longer exists.")
