# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

from flask import current_app
from dates import days_ago
from .recipient import Recipient

class Audience:
    """Who a broadcast goes to. Add a segment = add a subclass to AUDIENCES. The SQL lives in DonorRepo."""
    key = label = ""
    def rows(self): return []
    def recipients(self): return [Recipient.from_row(r) for r in self.rows()]

def _donors():
    from repos import DonorRepo
    return DonorRepo()

class RoleAudience(Audience):
    def __init__(self, role, label): self.key, self.label, self.role = role, label, role
    def rows(self): return _donors().by_role(self.role)

class BloodGroupAudience(Audience):
    def __init__(self, group): self.key, self.label, self.group = f"group:{group}", f"Donors {group}", group
    def rows(self): return _donors().donors_in_group(self.group)

class EligibleDonors(Audience):
    key, label = "eligible", "Donors eligible now"
    def rows(self): return _donors().donors_eligible(days_ago(current_app.config["DONATION_GAP_DAYS"]))

AUDIENCES = {a.key: a for a in [RoleAudience("donor", "All donors"), EligibleDonors(), RoleAudience("volunteer", "Volunteers"),
             RoleAudience("admin", "Admins")] + [BloodGroupAudience(g) for g in ("O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+")]}
