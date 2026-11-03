# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Admin-side slot management: move one person to another time, and change how many donors each slot takes."""
from dataclasses import dataclass

class SlotError(ValueError): pass

@dataclass
class Reassigned:
    person: dict
    slot: dict | None
    over_capacity: bool

class SlotAllocator:
    """Moves a booking to another slot of the same drive. Admins may go over a slot's capacity (they get told)."""
    def __init__(self, interests, slots, bus=None): self.interests, self.slots, self.bus = interests, slots, bus

    def reassign(self, interest_id, slot_id, notify=True):
        person = self.interests.by_id(interest_id) or self._fail("That booking no longer exists.")
        slot = self._slot_of(person, slot_id)
        if (person["slot_id"] or None) == (slot["id"] if slot else None): return Reassigned(person, slot, False)
        over = bool(slot) and slot["booked"] >= slot["capacity"]
        self.interests.set_slot(interest_id, slot["id"] if slot else None, notify=notify)
        return Reassigned(person, slot, over)

    def _slot_of(self, person, slot_id):
        if not slot_id: return None
        slot = self.slots.by_id(slot_id)
        if not slot or slot["drive_id"] != person["drive_id"]: self._fail("Pick a time slot of this drive.")
        return slot

    @staticmethod
    def _fail(msg): raise SlotError(msg)


class SlotCapacity:
    """Donors per slot. Never below the people already booked; the drive's total capacity follows."""
    MAX = 500

    def __init__(self, slots, drives): self.slots, self.drives = slots, drives

    def change(self, slot_id, value=None, delta=0):
        slot = self.slots.by_id(slot_id) or self._fail("That time slot no longer exists.")
        new = self._clamp(slot, int(value) if value not in (None, "") else slot["capacity"] + int(delta))
        self.slots.set_capacity(slot_id, new)
        self._sync(slot["drive_id"])
        return slot, new

    def set_all(self, drive_id, value):
        value = int(value)
        if not 1 <= value <= self.MAX: self._fail(f"Donors per slot must be 1 to {self.MAX}.")
        raised = [s for s in self.slots.for_drive(drive_id) if s["booked"] > value]
        self.slots.set_all_capacity(drive_id, value)
        for s in raised: self.slots.set_capacity(s["id"], s["booked"])  # keep room for people already booked
        self._sync(drive_id)
        return len(raised)

    def _clamp(self, slot, n):
        if n > self.MAX: self._fail(f"At most {self.MAX} donors per slot.")
        if n < max(1, slot["booked"]): self._fail(f"{slot['starts_at']} already has {slot['booked']} booked, so it can't go below that.")
        return n

    def _sync(self, drive_id): self.drives.set_capacity(drive_id, self.slots.total_capacity(drive_id))

    @staticmethod
    def _fail(msg): raise SlotError(msg)
