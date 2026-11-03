"""Plain-language copy for the blood-donation services' reason codes (added to the platform's at start-up)."""

COPY = {
    "INVALID_PHONE": "Enter an 8-digit local number or + country code.", "INVALID_WEIGHT": "Weight must be 30–250 kg.",
    "INVALID_AGE": "Donors must be 16–75 years old.", "INVALID_BLOOD_GROUP": "Pick a blood group from the list.",
    "UNKNOWN_DRIVE": "That drive no longer exists.", "DRIVE_CLOSED": "This drive has finished.",
    "SLOT_REQUIRED": "Pick a time first.", "SLOT_FULL": "That time is full — pick another.", "UNKNOWN_SLOT": "That time no longer exists.",
    "NOT_REGISTERED": "You're not registered for this drive.", "ALREADY_DONATED": "A donation can't be cancelled.",
    "NOT_DRIVE_DAY": "Donated / no-show can only be marked on the drive day.", "TOO_EARLY": "A drive can be completed on or after its date.",
    "HAS_BOOKINGS": "People have already booked; change capacities instead.", "BELOW_BOOKED": "Capacity can't go below the bookings.",
    "TOO_MANY_IMAGES": "Up to 3 pictures per drive.", "NOT_ENOUGH_CODES": "Add one voucher code per donor.",
    "INVALID_PLAN": "Check the slot start, end, length and capacity.",
}
