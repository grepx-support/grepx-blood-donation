# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Why a donation request is rejected."""
from enum import Enum


class ReasonCode(str, Enum):
    UNKNOWN_DONOR = "UNKNOWN_DONOR"
    INVALID_DATE = "INVALID_DATE"
    INVALID_UNITS = "INVALID_UNITS"
    UNKNOWN_DONATION = "UNKNOWN_DONATION"
