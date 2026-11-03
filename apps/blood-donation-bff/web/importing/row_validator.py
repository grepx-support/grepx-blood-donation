# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from validation import check
from .donor_row import DonorRow

class RowValidator:
    """Shared donor rules + the one rule that needs the database (duplicate email)."""
    def __init__(self, donors): self.donors = donors

    def validate(self, data):
        _, errors = check(DonorRow, data)
        if "email" not in errors and self.donors.by_email(str(data.get("email", "")).strip().lower()):
            errors["email"] = "Already registered"
        return errors

    @staticmethod
    def clean(data): return DonorRow(**{k: data.get(k) for k in DonorRow.model_fields})
