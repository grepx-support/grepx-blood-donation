"""Actions donation-service accepts."""
from enum import Enum


class DonationAction(str, Enum):
    RECORD = "RECORD"
    VOID = "VOID"
