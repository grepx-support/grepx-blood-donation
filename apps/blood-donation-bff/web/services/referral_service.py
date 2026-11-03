# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

class ReferralService:
    """Invite links and the leaderboard. Points are referral-service's (referral_scores)."""

    def __init__(self, donors, referrals, site): self.donors, self.referrals, self.site = donors, referrals, site

    def code_for(self, donor_id):
        """donor-service gives every donor a code when they register."""
        return (self.donors.by_id(donor_id) or {}).get("ref_code") or ""

    def link_for(self, donor_id): return f"{self.site}/join/{self.code_for(donor_id)}"
    def referrer(self, code): return self.donors.by_column("ref_code", (code or "").upper())

    def attach(self, new_donor_id, code):
        ref = self.referrer(code)
        if ref and ref["id"] != new_donor_id:
            self.donors.set_column(new_donor_id, "referred_by", ref["id"]); return ref
        return None

    def summary(self, donor_id):
        s = self.referrals.stats_for(donor_id)
        return {**s, "rank": self.referrals.rank_of(donor_id),
                "link": self.link_for(donor_id)}

    def leaderboard(self, n=10):
        return [{k: r[k] for k in ("name", "joined", "donated", "points")} for r in self.referrals.leaderboard(n)]
