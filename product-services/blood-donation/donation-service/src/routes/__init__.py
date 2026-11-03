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
