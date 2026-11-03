# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from dates import today

STATUSES = {"interested": "Interested", "confirmed": "Confirmed", "donated": "Donated", "no_show": "No-show", "not_eligible": "Not eligible"}
DAY_ONLY = ("donated", "no_show")  # can only be set (or undone) on the drive day itself

class NotDriveDay(ValueError): pass

def is_drive_day(drive): return drive["drive_date"] == today()

class AttendanceService:
    """Moves an attendee between statuses. booking-service applies the rules (drive day only, completed drives
    locked) and donation-service keeps the donation history in step with "donated"."""
    def __init__(self, interests, donations, bus=None): self.interests, self.donations, self.bus = interests, donations, bus

    def move(self, interest_id, status):
        from repos import RepoError
        if status not in STATUSES: raise ValueError(status)
        row = self.interests.by_id(interest_id)
        if not row: raise LookupError(interest_id)
        if row.get("drive_status") == "completed":
            raise NotDriveDay("This drive is completed. Reopen it first to change attendance.")
        if (status in DAY_ONLY or row["status"] in DAY_ONLY) and row["status"] != status and row["drive_date"] != today():
            raise NotDriveDay(f"Donated and No-show can only be marked on the drive day ({row['drive_date']}).")
        try:
            self.interests.set_status(interest_id, status)
        except RepoError as e:
            if e.reason in ("NOT_DRIVE_DAY", "DRIVE_CLOSED"):
                raise NotDriveDay(f"Donated and No-show can only be marked on the drive day ({row['drive_date']}).") from e
            raise
        return f"{row['name']} → {STATUSES[status]}"
