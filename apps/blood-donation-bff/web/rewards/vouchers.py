# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from dataclasses import dataclass, field

@dataclass
class VoucherOffer:
    """A partner's thank-you (e.g. a free coffee). Either one shared code for everyone, or a list of unique codes."""
    title: str
    partner: str = ""
    details: str = ""
    shared_code: str = ""
    codes: list = field(default_factory=list)
    expires_on: str = ""

    @classmethod
    def from_form(cls, f):
        if not f.get("voucher_on") or not f.get("voucher_title", "").strip(): return None
        codes = [c.strip() for c in f.get("voucher_codes", "").replace(",", "\n").splitlines() if c.strip()]
        return cls(f["voucher_title"].strip()[:120], f.get("voucher_partner", "").strip()[:120], f.get("voucher_details", "").strip(),
                   f.get("voucher_shared", "").strip()[:120], codes, f.get("voucher_expires", "").strip()[:10])

    def allocate(self, donor_ids):
        """[(donor_id, code)] — unique codes go out in order until they run out; a shared code goes to everyone."""
        if self.codes: return list(zip(donor_ids, self.codes))
        return [(d, self.shared_code) for d in donor_ids]
