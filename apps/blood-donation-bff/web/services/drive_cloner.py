# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The date the "repeat this drive" form suggests (the copy itself is event-service CLONE: repos.DriveRepo.clone)."""
from datetime import date, timedelta
from grepx_service import local_today

class DriveCloner:
    @staticmethod
    def suggested_date(d):
        """A week after the original (or a week from today if that is already past)."""
        base = max(date.fromisoformat(d["drive_date"]), local_today() - timedelta(days=7))
        return (base + timedelta(days=7)).isoformat()
