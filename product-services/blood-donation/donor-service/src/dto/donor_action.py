# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Actions donor-service accepts (creating and editing a donor is people-service CREATE / UPDATE)."""
from enum import Enum


class DonorAction(str, Enum):
    SAVE_SEGMENT = "SAVE_SEGMENT"
    DELETE_SEGMENT = "DELETE_SEGMENT"
    STAGE_IMPORT_ROW = "STAGE_IMPORT_ROW"
    UPDATE_IMPORT_ROW = "UPDATE_IMPORT_ROW"
