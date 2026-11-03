# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Functions an admin can switch on per user. Add a key here to add a new function."""
from pathlib import Path

from grepx_common import Roles
from grepx_config import load_config

_ROLES = Roles.of(load_config(Path(__file__).resolve().parents[1] / "config"))  # the ladder lives in config `roles:`
PERMS = {"manage_drives": "Create & manage drives", "checkin": "Drive check-in", "notify": "Send announcements",
         "manage_donors": "Manage donors", "bulk_import": "Bulk Excel import", "view_log": "View message log",
         "manage_tasks": "Assign tasks to others",
         "reports": "Drive reports & retros"}
STAFF_ROLES = _ROLES.staff

# Starter volunteer roles (admins can rename, change or add their own on Volunteers & admins).
DEFAULT_VOLUNTEER_ROLES = [
    ("Check-in desk", "Welcomes donors, checks them in, registers walk-ins.", ["checkin"]),
    ("Drive coordinator", "Runs drives end to end: drives, check-in, tasks, reports.", ["manage_drives", "checkin", "manage_tasks", "reports"]),
    ("Donor relations", "Looks after donors: details, invitations, messages.", ["manage_donors", "notify", "view_log"]),
    ("Data entry", "Adds and updates donors, including Excel imports.", ["manage_donors", "bulk_import"]),
]
ROLES = _ROLES.all
