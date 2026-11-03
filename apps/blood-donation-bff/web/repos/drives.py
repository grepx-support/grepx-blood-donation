"""Drives (event-service), slots (slot-service) and bookings — the original "interests" (booking-service)."""
from __future__ import annotations
import grepx_contracts as gc

import json

from dates import today

from . import _nexus as nx

DRIVE_REQ, DRIVE_SVC = gc.event.REQUESTS, gc.event.SERVICE
SLOT_REQ, SLOT_SVC = gc.slot.REQUESTS, gc.slot.SERVICE
REG_REQ, REG_SVC = gc.booking.REQUESTS, gc.booking.SERVICE
LIVE = ("interested", "confirmed", "donated", "no_show", "not_eligible")      # a cancelled registration is gone (original deleted it)


def _registrations(**eq) -> list[dict]:
    return [r for r in nx.where(gc.booking.BOOKINGS, **eq) if r.get("state") in LIVE]


DRIVE_COLUMNS = {"title": "", "venue": "", "drive_date": "", "time_slot": None, "description": None, "capacity": 100,
                 "image_url": None, "images": None, "status": "open", "completed_at": None, "completed_by": None}
INTEREST_COLUMNS = {"drive_id": None, "donor_id": None, "name": "", "phone": "", "email": "", "status": "interested", "slot_id": None,
                    "source": "online", "reminded_at": None, "created": None}


def _drive(d: dict) -> dict:
    """A drive in the original shape (status, images as JSON text, counts)."""
    d = {**DRIVE_COLUMNS, **{k: v for k, v in d.items() if v not in (None, "") or k not in DRIVE_COLUMNS}}
    regs = _registrations(drive_id=d["id"])
    images = d.get("images") or []
    return {**d, "status": d.get("state") or "open", "images": json.dumps(images) if isinstance(images, list) else images,
            "image_url": d.get("image_url") or (images[0] if isinstance(images, list) and images else ""),
            "capacity": int(d.get("capacity") or 0) or 100,
            "going": sum(1 for r in regs if r.get("state") not in ("no_show", "not_eligible")),
            "donated": sum(1 for r in regs if r.get("state") == "donated"),
            "slot_count": len(nx.where(gc.slot.SLOTS, drive_id=d["id"]))}


def _interest(r: dict) -> dict:
    """A registration in the original "interests" shape."""
    r = {**INTEREST_COLUMNS, **r}
    slot = nx.one(gc.slot.SLOTS, r.get("slot_id")) if r.get("slot_id") else None
    donor = nx.one(gc.people.PEOPLE, r.get("donor_id")) if r.get("donor_id") else None
    return {**r, "status": r.get("state"), "slot_id": r.get("slot_id") or None, "donor_id": r.get("donor_id") or None,
            "slot_start": (slot or {}).get("starts_at") or r.get("slot_start") or None,
            "slot_end": (slot or {}).get("ends_at") or r.get("slot_end") or None,
            "photo_id": (donor or {}).get("photo_id"), "name": r.get("name") or (donor or {}).get("name", ""),
            "phone": r.get("phone") or (donor or {}).get("phone", ""), "email": r.get("email") or (donor or {}).get("email", "")}


class DriveRepo:
    def upcoming(self):
        return sorted((_drive(d) for d in nx.table(gc.event.EVENTS) if (d.get("drive_date") or "") >= today()), key=lambda d: d["drive_date"])

    def all(self):
        return sorted((_drive(d) for d in nx.table(gc.event.EVENTS)), key=lambda d: d.get("drive_date") or "", reverse=True)

    def by_id(self, i):
        d = nx.one(gc.event.EVENTS, i)
        return _drive(d) if d else None

    def update(self, i, title, venue, date, desc, slot=None, cap=None):
        fields = {"title": title, "venue": venue, "drive_date": date, "description": desc}
        if slot is not None:
            fields["time_slot"] = slot
        if cap is not None:
            fields["capacity"] = cap
        nx.command(DRIVE_REQ, DRIVE_SVC, {"action": "UPDATE", "drive_id": i, **fields})

    def set_status(self, i, status, when=None, by=None):
        action = "COMPLETE" if status == "completed" else "REOPEN"
        nx.command(DRIVE_REQ, DRIVE_SVC, {"action": action, "drive_id": i, "actor_id": by or nx.actor()})

    def uses_picture(self, ref):
        return any(ref == d.get("image_url") or ref in (d.get("images") or []) for d in nx.table(gc.event.EVENTS))

    def set_images(self, i, images_json, cover):
        images = json.loads(images_json) if isinstance(images_json, str) and images_json else list(images_json or [])
        if cover and cover in images:
            images = [cover] + [x for x in images if x != cover]
        nx.command(DRIVE_REQ, DRIVE_SVC, {"action": "SET_IMAGES", "drive_id": i, "images": images})

    def set_capacity(self, i, cap):
        nx.command(DRIVE_REQ, DRIVE_SVC, {"action": "UPDATE", "drive_id": i, "capacity": cap})

    def clone(self, source_id, date, title=None, copy_slots=True, checklist=False):
        """event-service copies details, pictures and (optionally) slots; checklist-service adds the checklist."""
        v = nx.command(DRIVE_REQ, DRIVE_SVC, {"action": "CLONE", "source_drive_id": source_id, "drive_date": date, "title": title or "",
                                              "copy_slots": copy_slots, "apply_checklist": checklist, "actor_id": nx.actor()})
        return v.fields.get("drive_id")

    def create(self, title, venue, date, slot, desc, cap, image, **extra):
        v = nx.command(DRIVE_REQ, DRIVE_SVC, {"action": "CREATE", "title": title, "venue": venue, "drive_date": date,
                                              "time_slot": slot or "", "description": desc or "", "capacity": cap,
                                              "images": [image] if image else [], "actor_id": nx.actor(), **extra})
        return v.fields.get("drive_id")


class SlotRepo:
    @staticmethod
    def _slot(s: dict) -> dict:
        booked = sum(1 for r in _registrations(slot_id=s["id"]) if r.get("state") not in ("no_show", "not_eligible"))
        return {**s, "capacity": int(s.get("capacity") or 0), "booked": booked}

    def for_drive(self, drive_id):
        return sorted((self._slot(s) for s in nx.where(gc.slot.SLOTS, drive_id=drive_id)), key=lambda s: s.get("starts_at") or "")

    def by_id(self, i):
        s = nx.one(gc.slot.SLOTS, i)
        return self._slot(s) if s else None

    def has_bookings(self, drive_id):
        return any(r.get("slot_id") for r in _registrations(drive_id=drive_id))

    def set_capacity(self, slot_id, capacity):
        nx.command(SLOT_REQ, SLOT_SVC, {"action": "SET_CAPACITY", "slot_id": slot_id, "value": int(capacity)})

    def set_all_capacity(self, drive_id, capacity):
        nx.command(SLOT_REQ, SLOT_SVC, {"action": "SET_ALL", "drive_id": drive_id, "value": int(capacity)})

    def total_capacity(self, drive_id):
        return sum(int(s.get("capacity") or 0) for s in nx.where(gc.slot.SLOTS, drive_id=drive_id))

    def replace(self, drive_id, slots):
        nx.command(SLOT_REQ, SLOT_SVC, {"action": "GENERATE", "drive_id": drive_id,
                                        "slots": [{"starts_at": a, "ends_at": b, "capacity": int(c)} for a, b, c in slots]})


class InterestRepo:
    RANK = {"interested": 0, "confirmed": 1, "donated": 2, "no_show": 2, "not_eligible": 2}

    def for_drive(self, drive_id):
        rows = [_interest(r) for r in _registrations(drive_id=drive_id)]
        return sorted(rows, key=lambda r: (r["slot_start"] is None, r["slot_start"] or "", (r["name"] or "").lower()))

    def by_id(self, i):
        r = nx.one(gc.booking.BOOKINGS, i)
        if not r or r.get("state") not in LIVE:
            return None
        d = nx.one(gc.event.EVENTS, r.get("drive_id")) or {}
        return {**_interest(r), "drive_date": d.get("drive_date"), "drive_status": d.get("state") or "open"}

    def add(self, drive_id, donor_id, name, phone, email, status="interested", slot_id=None, source="online"):
        """Record someone for a drive (booking-service keeps one row per person per drive, never moving backwards)."""
        if not donor_id:
            from .donors import DonorRepo
            found = DonorRepo().find_exact(email) or DonorRepo().find_exact(phone)
            donor_id = found["id"] if found else None
        base = {"drive_id": drive_id, "donor_id": donor_id or "", "name": name or "", "phone": phone or "", "email": email or "",
                "source": source}
        if status == "donated" and donor_id:
            v = nx.command(REG_REQ, REG_SVC, {"action": "CHECK_IN", **base})
        elif status == "confirmed" and donor_id:
            v = nx.command(REG_REQ, REG_SVC, {"action": "BOOK", **base, "slot_id": slot_id or ""})
        else:
            v = nx.command(REG_REQ, REG_SVC, {"action": "INTEREST", **base})
            if status not in ("interested", None):
                nx.command(REG_REQ, REG_SVC, {"action": "MARK", "registration_id": v.fields.get("registration_id"), "state": status})
        return v.fields.get("registration_id")

    def find(self, drive_id, donor_id):
        for r in _registrations(drive_id=drive_id, donor_id=donor_id):
            return _interest(r)
        return None

    def status_for(self, drive_id, donor_id):
        row = self.find(drive_id, donor_id)
        return row["status"] if row else None

    def sync_contacts(self):
        pass                                    # booking-service reads contact details from the donor profile

    def close_open(self, drive_id):
        open_ = [r for r in _registrations(drive_id=drive_id) if r.get("state") in ("interested", "confirmed")]
        for r in open_:
            self.set_status(r["id"], "no_show")
        return len(open_)

    def set_slot(self, i, slot_id, notify=False):
        """booking-service moves the booking (admins may overbook) and tells the person when notify is on."""
        nx.command(REG_REQ, REG_SVC, {"action": "MOVE", "registration_id": i, "slot_id": slot_id or "", "override_capacity": True,
                                      "notify": bool(notify), "actor_id": nx.actor()})

    def set_status(self, i, status):
        nx.command(REG_REQ, REG_SVC, {"action": "MARK", "registration_id": i, "state": status, "actor_id": nx.actor()})

    def cancel(self, drive_id, donor_id):
        nx.command(REG_REQ, REG_SVC, {"action": "CANCEL", "drive_id": drive_id, "donor_id": donor_id}, ok_only=False)

    def upsert(self, drive_id, user, status, slot_id=None):
        return self.add(drive_id, user.id, user.name, user.phone, user.email, status, slot_id)

    def book(self, drive_id, user, slot_id):
        """BOOK through booking-service (it checks slot capacity); returns the slot row or None."""
        nx.command(REG_REQ, REG_SVC, {"action": "BOOK", "drive_id": drive_id, "donor_id": user.id, "slot_id": slot_id or "",
                                      "name": user.name, "phone": user.phone, "email": user.email})
        return SlotRepo().by_id(slot_id) if slot_id else None

    def mine(self, donor_id):
        out = []
        for r in _registrations(donor_id=donor_id):
            d = nx.one(gc.event.EVENTS, r.get("drive_id"))
            if d and (d.get("drive_date") or "") >= today():
                i = _interest(r)
                out.append({**_drive(d), "status": i["status"], "slot_start": i["slot_start"], "slot_end": i["slot_end"]})
        return sorted(out, key=lambda d: d["drive_date"])

    def due_reminders(self, day):
        return []                               # booking-service sends drive reminders itself (scheduler tick)

    def mark_reminded(self, i, when):
        pass
