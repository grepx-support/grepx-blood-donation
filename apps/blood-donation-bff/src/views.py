"""Read models assembled for screens (composition only — no business decisions)."""
from __future__ import annotations
import grepx_contracts as gc


from grepx_service import local_today

from grepx_bff.views import clean, media_url  # noqa: F401  (re-exported for product routers)

PUBLIC_DONOR = ("donor_id", "name", "email", "phone", "blood_group", "sex", "weight", "dob", "photo_id", "ref_code", "source", "created")


def drive_view(gw, drive: dict) -> dict:
    regs = gw.rows(gc.booking.BOOKINGS, drive_id=drive["_key"])
    slots = sorted(gw.rows(gc.slot.SLOTS, drive_id=drive["_key"]), key=lambda s: s.get("starts_at", ""))
    holding = [r for r in regs if r.get("state") not in ("no_show", "not_eligible", "cancelled")]
    capacity = sum(int(s.get("capacity") or 0) for s in slots) or int(drive.get("capacity") or 0)
    view = clean(drive)
    view.update({"going": len(holding), "donated": sum(1 for r in regs if r.get("state") == "donated"), "capacity": capacity,
                 "image_url": media_url(gw, drive.get("image_url", "")), "images": [media_url(gw, i) for i in drive.get("images") or []],
                 "slots": [{**clean(s, ("starts_at", "ends_at", "capacity")), "booked": sum(1 for r in holding if r.get("slot_id") == s["_key"])} for s in slots]})
    return view


def upcoming(gw) -> list[dict]:
    today = local_today().isoformat()
    return sorted((d for d in gw.rows(gc.event.EVENTS, state="open") if d.get("drive_date", "") >= today), key=lambda d: d["drive_date"])


def mask_phone(phone: str) -> str:
    return f"{phone[:3]} ••••{phone[-4:]}" if phone else ""
