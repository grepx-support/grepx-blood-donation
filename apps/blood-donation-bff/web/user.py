# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from flask_login import UserMixin, AnonymousUserMixin
from permissions import STAFF_ROLES
from repos import DonorRepo, PermissionRepo, StaffRoleRepo

class User(UserMixin):
    """Adapter: wraps a donor row so Flask-Login and templates can use attributes."""
    def __init__(self, row, perms):
        self.row, self.perms, self.id = row, perms, row["id"]

    def __getattr__(self, key):
        try: return self.row[key]
        except (IndexError, KeyError): raise AttributeError(key)

    @property
    def is_admin(self): return self.row["role"] == "admin"
    @property
    def is_staff(self): return self.row["role"] in STAFF_ROLES
    @property
    def first_name(self): return self.row["name"].split()[0]
    def can(self, perm): return self.is_admin or perm in self.perms

    @classmethod
    def load(cls, uid):
        row = DonorRepo().by_id(uid)
        if not row: return None
        if not row: return None
        role_perms = StaffRoleRepo().perms_for(row["staff_role_id"]) if row["role"] == "volunteer" else set()
        return cls(row, PermissionRepo().get(uid) | role_perms)  # volunteer role functions + personal extras

class Guest(AnonymousUserMixin):
    is_admin = is_staff = False
    def can(self, perm): return False
