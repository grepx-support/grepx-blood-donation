"""Why a donor-service request is rejected."""
from enum import Enum


class ReasonCode(str, Enum):
    MISSING_NAME = "MISSING_NAME"
    UNKNOWN_SEGMENT = "UNKNOWN_SEGMENT"
    INVALID_ROW = "INVALID_ROW"
    UNKNOWN_ROW = "UNKNOWN_ROW"
