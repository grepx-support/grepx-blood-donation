"""Booking a donor onto a drive: booking-service enforces slot capacity; this maps its answer to the
exceptions the original routes expect."""
from repos._nexus import RepoError


class SlotFull(Exception): pass
class SlotRequired(Exception): pass


class BookingService:
    def __init__(self, interests, slots): self.interests, self.slots = interests, slots

    def book(self, drive_id, user, slot_id=None):
        if not slot_id and self.slots.for_drive(drive_id):
            raise SlotRequired()
        try:
            return self.interests.book(drive_id, user, slot_id)
        except RepoError as exc:
            if exc.reason in ("SLOT_REQUIRED",):
                raise SlotRequired() from exc
            if exc.reason in ("SLOT_FULL", "UNKNOWN_SLOT"):
                raise SlotFull() from exc
            raise
