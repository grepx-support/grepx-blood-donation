"""Action routing for donor-service: one module per action. The donor's person record (contact + blood fields) is
people-service's (`people` table, blood fields through plugins/blood_profile.py); this service keeps the staff tools."""
from grepx_service import ActionDispatcher

from dto import DonorAction
from . import import_rows, segments

TABLE = "donor_requests"
ROUTES = {
    DonorAction.SAVE_SEGMENT: segments.save,
    DonorAction.DELETE_SEGMENT: segments.delete,
    DonorAction.STAGE_IMPORT_ROW: import_rows.stage,
    DonorAction.UPDATE_IMPORT_ROW: import_rows.update,
}
handle = ActionDispatcher(ROUTES, DonorAction, TABLE)
