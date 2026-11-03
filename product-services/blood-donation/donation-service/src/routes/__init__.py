# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Action routing for donation-service: one module per action."""
from grepx_service import ActionDispatcher

from dto import DonationAction
from . import record
from . import void

TABLE = "donation_requests"
ROUTES = {
    DonationAction.RECORD: record.handle,
    DonationAction.VOID: void.handle,
}
handle = ActionDispatcher(ROUTES, DonationAction, TABLE)
