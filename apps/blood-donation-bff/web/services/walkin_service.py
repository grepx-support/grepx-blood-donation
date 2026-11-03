# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

import grepx_contracts as gc
import secrets
from validation import WalkInForm, check, summary

class InvalidDetails(ValueError): pass

class WalkInService:
    """Walk-ins: find a registered donor, or quick-register a new one, then check them in to the drive."""
    def __init__(self, donors, interests, bus=None): self.donors, self.interests, self.bus = donors, interests, bus

    def check_in(self, drive_id, donor, source="walkin"):
        """Arrived = confirmed (booking-service never moves Donated / No-show backwards)."""
        from repos import _nexus as nx
        nx.command(gc.booking.REQUESTS, gc.booking.SERVICE, {"action": "CHECK_IN", "drive_id": drive_id, "donor_id": donor["id"],
                                                                     "name": donor["name"], "phone": donor["phone"], "email": donor["email"],
                                                                     "source": source})
        return donor

    def register(self, form):
        """Quick register (no password needed now — they can reset it later). Returns (donor, created)."""
        clean, errors = check(WalkInForm, form)
        if errors: raise InvalidDetails(summary(errors))
        v = clean.values()
        existing = (v["email"] and self.donors.find_exact(v["email"])) or self.donors.find_exact(v["phone"])
        if existing: return existing, False
        email = v["email"] or f"walkin-{secrets.token_hex(4)}@no-email.local"
        uid = self.donors.create(v["name"], email, v["phone"], "",
                                 v["blood_group"], v["sex"], v["weight"], v["dob"])
        donor = self.donors.by_id(uid)
        return donor, True

    def register_and_check_in(self, drive_id, form, source="walkin"):
        donor, created = self.register(form)
        self.check_in(drive_id, donor, source)
        return donor, created
