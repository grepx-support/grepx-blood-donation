# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Single import door for donation-service vocabulary."""
import grepx_contracts as gc
from .donation_action import DonationAction
from .donation_field import DonationField
from .reason_code import ReasonCode

DONATIONS_TABLE = "donations"
STATS_TABLE = "donor_stats"
PEOPLE_TABLE = gc.people.PEOPLE        # the donor record (people-service, blood fields via plugins/blood_profile)
EVENTS_TABLE = gc.event.EVENTS

__all__ = ["DonationAction", "DonationField", "ReasonCode", "DONATIONS_TABLE", "STATS_TABLE", "PEOPLE_TABLE", "EVENTS_TABLE"]
