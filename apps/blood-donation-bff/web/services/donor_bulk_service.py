# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from repos import DonorRepo

class DonorBulkService:
    """Apply one change to many donors at once (chunked, so 20,000 rows are fine)."""
    FIELDS = {"blood_group": ("", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"), "sex": ("Male", "Female"),
              "role": ("donor", "volunteer")}

    def update(self, ids, changes):
        sets = {k: v for k, v in changes.items() if k in self.FIELDS and v is not None and v != "__keep__"}
        for k, v in sets.items():
            if v not in self.FIELDS[k]: raise ValueError(f"Invalid value for {k}")
        if not sets or not ids: return 0
        DonorRepo().bulk_set(ids, {k: v or None for k, v in sets.items()})
        return len(ids)
