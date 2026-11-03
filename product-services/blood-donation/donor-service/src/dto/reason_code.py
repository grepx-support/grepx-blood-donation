# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Why a donor-service request is rejected."""
from enum import Enum


class ReasonCode(str, Enum):
    MISSING_NAME = "MISSING_NAME"
    UNKNOWN_SEGMENT = "UNKNOWN_SEGMENT"
    INVALID_ROW = "INVALID_ROW"
    UNKNOWN_ROW = "UNKNOWN_ROW"
