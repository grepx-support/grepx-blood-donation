"""Why a donation request is rejected."""
from enum import Enum


class ReasonCode(str, Enum):
    UNKNOWN_DONOR = "UNKNOWN_DONOR"
    INVALID_DATE = "INVALID_DATE"
    INVALID_UNITS = "INVALID_UNITS"
    UNKNOWN_DONATION = "UNKNOWN_DONATION"
