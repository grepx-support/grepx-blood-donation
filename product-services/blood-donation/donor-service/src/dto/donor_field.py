"""Fields of donor-service requests and rows."""
from enum import Enum


class DonorField(str, Enum):
    SEGMENT_ID = "segment_id"
    NAME = "name"
    QUERY = "query"
    ROW_ID = "row_id"
    BATCH = "batch"
    ROW_NO = "row_no"
    DATA = "data"
    ERRORS = "errors"
    ROW_STATUS = "row_status"
    ACTOR_ID = "actor_id"
    TENANT_ID = "tenant_id"
