# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Single import door for donor-service vocabulary."""
from .donor_action import DonorAction
from .donor_field import DonorField
from .reason_code import ReasonCode

SEGMENTS_TABLE = "donor_segments"      # saved donor-grid filters
IMPORT_ROWS_TABLE = "import_rows"      # Excel rows waiting for review before they become people

__all__ = ["DonorAction", "DonorField", "ReasonCode", "SEGMENTS_TABLE", "IMPORT_ROWS_TABLE"]
