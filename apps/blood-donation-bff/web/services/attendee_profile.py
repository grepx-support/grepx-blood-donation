# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

"""Everything an organiser needs about one person on a drive, in one place (read-only view model)."""
from flask import current_app
from repos import DonorRepo, DonationRepo, InterestRepo, SlotRepo
from services.reminder_service import ReminderService

class AttendeeProfile:
    def __init__(self, interest_id):
        self.booking = InterestRepo().by_id(interest_id)
        self.donor = DonorRepo().with_stats(self.booking["donor_id"]) if self.booking and self.booking["donor_id"] else None

    def exists(self): return self.booking is not None

    def context(self):
        b, d = self.booking, self.donor
        slots = SlotRepo().for_drive(b["drive_id"])
        return dict(b=b, donor=d, slots=slots, slot=next((s for s in slots if s["id"] == b["slot_id"]), None),
                    eligibility=ReminderService(DonorRepo(), current_app.config["DONATION_GAP_DAYS"]).status(d["id"]) if d else None,
                    history=DonationRepo().for_donor(d["id"])[:5] if d else [],
                    other_drives=[x for x in InterestRepo().mine(d["id"]) if x["id"] != b["drive_id"]] if d else [])
