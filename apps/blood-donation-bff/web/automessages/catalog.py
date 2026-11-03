# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from dataclasses import dataclass

@dataclass(frozen=True)
class AutoMessage:
    key: str                 # the message event (templates/messages/<key>/)
    label: str
    when: str
    channels: tuple          # default channels
    enabled: bool = True     # default on/off
    placeholders: tuple = ("first_name", "name", "org", "link")
    subject: str = ""        # default custom text, shown when an admin starts editing
    text: str = ""

COMMON = ("first_name", "name", "org", "link")
DRIVE = COMMON + ("drive_title", "drive_date", "drive_time", "venue")

AUTO = [
    AutoMessage("welcome", "Welcome a new donor", "Right after someone registers on the website (or is quick-registered).", ("email", "whatsapp"),
                subject="Welcome to {org}, {first_name} 🩸",
                text="Hi {first_name},\n\nWelcome to {org}! Your donor account is ready. Register for drives in one tap, track your impact and get a reminder when you can donate again.\n\nYour dashboard: {link}"),
    AutoMessage("drive_announcement", "New drive announced", "When an admin creates a drive (they can untick it on the form), to all donors.", ("email", "whatsapp"),
                placeholders=DRIVE, subject="🩸 New blood drive: {drive_title}",
                text="Hi {first_name},\n\nA new blood drive is coming up:\n{drive_title}\n📅 {drive_date}  🕒 {drive_time}\n📍 {venue}\n\nBook your time (no queues): {link}"),
    AutoMessage("drive_reminder", "Day-before reminder", "The day before a drive, to everyone booked.", ("email", "whatsapp"), placeholders=DRIVE,
                subject="⏰ Tomorrow: {drive_title}",
                text="Hi {first_name}, see you tomorrow at {drive_title} ({drive_time}, {venue}). Eat well and drink plenty of water. Can't come? Change or cancel: {link}"),
    AutoMessage("slot_changed", "Time slot changed", "When an organiser moves someone to another time.", ("email", "whatsapp"), placeholders=DRIVE + ("slot_time",),
                subject="🕒 New time for {drive_title}: {slot_time}",
                text="Hi {first_name}, your time for {drive_title} on {drive_date} is now {slot_time} ({venue}). Change or cancel: {link}"),
    AutoMessage("donation_thanks", "Thank you after donating", "When someone is marked Donated.", ("email", "whatsapp"),
                subject="💚 Thank you, {first_name}", text="Thank you {first_name}! Your donation can save up to 3 lives. See your impact: {link}"),
    AutoMessage("certificate", "Certificate after a drive", "When a drive is completed, to each donor (with their voucher, if any).", ("email", "whatsapp"),
                placeholders=DRIVE + ("voucher",), subject="🏅 Your certificate from {drive_title}",
                text="Thank you {first_name}! Your donation at {drive_title} can save up to 3 lives. Here is your certificate: {link}\n{voucher}"),
    AutoMessage("eligible_again", "Can donate again", "When a donor becomes eligible again (about 12 weeks after donating).", ("email", "whatsapp"),
                subject="🩸 You can donate again, {first_name}", text="Hi {first_name}, you're eligible to donate again! Find a drive: {link}"),
    AutoMessage("referral_joined", "Friend joined with an invite", "When someone signs up with a donor's invite link.", ("email", "whatsapp"),
                placeholders=COMMON + ("friend",), subject="🎉 {friend} joined with your invite",
                text="🎉 {friend} joined {org} with your invite! +1 point (and +2 when they donate). Leaderboard: {link}"),
]
BY_KEY = {a.key: a for a in AUTO}
