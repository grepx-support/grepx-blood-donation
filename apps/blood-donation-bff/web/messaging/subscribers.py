# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

from repos import DonorRepo, NotificationLogRepo
from .events import bus
from .messenger import Messenger
from .recipient import Recipient

ALL = ("email", "sms", "whatsapp")

def _messenger(): return Messenger(NotificationLogRepo())
def _person(i):
    row = DonorRepo().by_id(i) if i else None
    return Recipient.from_row(row) if row else None

def on_task_assigned(task, by):
    who = _person(task["assignee_id"])
    if who and who.id != by.id: _messenger().send("task_assigned", [who], ALL, task=task, by=by)

def on_donor_registered(donor):
    _messenger().send_auto("welcome", [Recipient.from_row(donor)])

def on_donation_recorded(donor_id, drive=None):
    who = _person(donor_id)
    if who: _messenger().send_auto("donation_thanks", [who], drive=drive)

def on_referral_joined(referrer, friend):
    _messenger().send_auto("referral_joined", [Recipient.from_row(referrer)], friend=friend)

def on_booking_moved(person, slot):
    """An organiser gave someone a new time: tell them, with a link to change it again."""
    from repos import DriveRepo
    who = _person(person["donor_id"]) or Recipient(None, person["name"], person["email"] or "", person["phone"] or "", "donor")
    _messenger().send_auto("slot_changed", [who], drive=DriveRepo().by_id(person["drive_id"]), slot=slot)

def on_certificate_issued(certificate, voucher=None):
    """Thank the donor with their certificate link (and partner voucher, if there is one)."""
    from repos import DriveRepo
    who = _person(certificate["donor_id"])
    if who: _messenger().send_auto("certificate", [who], cert=certificate, voucher=voucher,
                              drive=DriveRepo().by_id(certificate["drive_id"]))

def on_drive_created(drive, announce=True):
    """New drive: tell every donor (admins can untick this on the form or switch it off for good)."""
    if not announce: return
    from .audiences import AUDIENCES
    _messenger().send_auto("drive_announcement", AUDIENCES["donor"].recipients(), drive_id=drive["id"], drive=drive)

def wire():
    bus.subscribe("task.assigned", on_task_assigned)
    bus.subscribe("donor.registered", on_donor_registered)
    bus.subscribe("donation.recorded", on_donation_recorded)
    bus.subscribe("referral.joined", on_referral_joined)
    bus.subscribe("booking.moved", on_booking_moved)
    bus.subscribe("certificate.issued", on_certificate_issued)
    bus.subscribe("drive.created", on_drive_created)
