"""Fields of donation requests, donations and donor_stats."""
from enum import Enum


class DonationField(str, Enum):
    DONATION_ID = "donation_id"
    DONOR_ID = "donor_id"
    DRIVE_ID = "drive_id"
    DRIVE_TITLE = "drive_title"
    VENUE = "venue"
    DONATED_ON = "donated_on"
    UNITS = "units"
    REGISTRATION_ID = "registration_id"
    TENANT_ID = "tenant_id"
