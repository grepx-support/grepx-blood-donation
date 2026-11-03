"""Reacts to bookings (booking-service): 'attended' at an event is a donation - record it (and say thank you);
leaving 'attended' voids it. Donations keep the blood product's own names (donor_id, drive_id, donated_on)."""

from grepx_config.deployment import link
from grepx_service import Emitter, Reader, notify

from dto import DONATIONS_TABLE, EVENTS_TABLE
from routes.common import refresh_stats

ATTENDED = "attended"


def handle_booking(app, row, cfg) -> str:
    f = row.fields
    if f.get("status") != "ACCEPTED" or not f.get("person_id"):
        return "ignored"
    emitter, read = Emitter(app, cfg, cause=row), Reader(app.client)
    key, donor = f"reg-{row.key}", f["person_id"]
    existing = read.accepted_one(DONATIONS_TABLE, key)
    if f.get("state") == ATTENDED and existing is None:
        event = read.accepted_one(EVENTS_TABLE, f["event_id"]) or {}
        emitter.submit(DONATIONS_TABLE, key, "ACCEPTED", {"donation_id": key, "donor_id": donor, "drive_id": f["event_id"],
                                                          "drive_title": event.get("title", ""), "venue": event.get("venue", ""),
                                                          "donated_on": event.get("event_date", ""), "units": 1,
                                                          "registration_id": row.key, "tenant_id": f.get("tenant_id", "")})
        refresh_stats(emitter, read, donor)
        notify(emitter, "donation_thanks", email=f.get("email", ""), phone=f.get("phone", ""), ref=key,
               values={"first_name": (f.get("name") or "").split(" ")[0], "link": link(cfg, "dashboard")}, user_id=donor)
        return "recorded"
    if f.get("state") != ATTENDED and existing is not None:
        emitter.submit(DONATIONS_TABLE, key, "VOIDED", {"donor_id": donor})
        refresh_stats(emitter, read, donor)
        return "voided"
    return "unchanged"
