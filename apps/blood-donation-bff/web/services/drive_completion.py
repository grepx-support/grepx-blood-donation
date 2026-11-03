# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Closing a drive: event-service marks it completed; booking-service turns anyone still Interested /
Confirmed into a no-show; recognition-service issues certificates (and the optional voucher offer) and thanks each donor."""
import grepx_contracts as gc
import time
from dataclasses import dataclass, field

from dates import today
from repos import _nexus as nx


class CannotComplete(ValueError): pass


@dataclass
class CompletionResult:
    no_shows: int = 0
    certificates: list = field(default_factory=list)
    vouchers: int = 0
    vouchers_short: int = 0
    notified: int = 0


def offer_fields(offer) -> dict:
    """VoucherOffer -> the offer recognition-service understands."""
    if not offer:
        return {}
    return {"title": offer.title, "partner": offer.partner, "details": offer.details, "code": offer.shared_code,
            "codes": list(offer.codes), "expires_on": offer.expires_on}


class DriveCompletion:
    def __init__(self, drives, interests, donations, certificates, vouchers, bus=None):
        self.drives, self.interests, self.donations, self.certs, self.vouchers = drives, interests, donations, certificates, vouchers

    def complete(self, drive, user_id, close_open=True, notify=True, offer=None):
        if drive["drive_date"] > today(): raise CannotComplete("A drive can be completed on or after its date.")
        open_before = sum(1 for p in self.interests.for_drive(drive["id"]) if p["status"] in ("interested", "confirmed"))
        donors = self.donors(drive["id"])
        had = {c["id"] for c in self.certs.for_drive(drive["id"])}
        try:
            nx.command(gc.event.REQUESTS, gc.event.SERVICE, {"action": "COMPLETE", "drive_id": drive["id"], "actor_id": user_id,
                                                           "voucher": offer_fields(offer)})
        except nx.RepoError as e:
            raise CannotComplete(str(e)) from e
        new = self._wait_for_certificates(drive["id"], had, len(donors))
        r = CompletionResult(no_shows=open_before, certificates=new, notified=len(new))
        if offer:
            r.vouchers = sum(1 for d in donors if self.vouchers.has(drive["id"], d))
            r.vouchers_short = len(donors) - r.vouchers
        return r

    def reopen(self, drive):
        nx.command(gc.event.REQUESTS, gc.event.SERVICE, {"action": "REOPEN", "drive_id": drive["id"], "actor_id": nx.actor()})

    def reward(self, drive_id, offer=None):
        """After completion: certificates for donations recorded later, plus an extra voucher offer (recognition-service)."""
        v = nx.command(gc.recognition.REQUESTS, gc.recognition.SERVICE, {"action": "ISSUE", "drive_id": drive_id, "voucher": offer_fields(offer)})
        return int(v.fields.get("certificates") or 0), int(v.fields.get("vouchers") or 0), int(v.fields.get("vouchers_short") or 0)

    def donors(self, drive_id):
        out = {}
        for d in self.donations.for_drive(drive_id): out.setdefault(d["donor_id"], d["donated_on"])
        return out

    def _wait_for_certificates(self, drive_id, had, expected, seconds=5.0):
        """recognition-service reacts to the completed drive; wait briefly so the page can say how many were issued."""
        deadline = time.time() + seconds
        while True:
            now = {c["id"] for c in self.certs.for_drive(drive_id)} - had
            if len(now) + len(had) >= expected or time.time() > deadline:
                return sorted(now)
            time.sleep(0.2)
            cache = nx._cache()
            if cache is not None: cache.clear()
