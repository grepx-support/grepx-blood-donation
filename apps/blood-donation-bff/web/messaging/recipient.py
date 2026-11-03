# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from dataclasses import dataclass

@dataclass(frozen=True)
class Recipient:
    """Anyone we can message: donor, volunteer or admin. 'role' picks the template variant."""
    id: int | None
    name: str
    email: str
    phone: str
    role: str = "donor"

    @property
    def first_name(self): return (self.name or "there").split()[0]

    @classmethod
    def from_row(cls, row):
        return cls(row["id"], row["name"], row["email"], row["phone"], row["role"] or "donor")
