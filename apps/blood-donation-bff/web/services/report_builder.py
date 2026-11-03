"""Drive report numbers are computed by event-report-service when the report is opened or refreshed (SNAPSHOT), with the same
definitions this builder used; build() stays for the original call sites and returns nothing to send."""


class DriveReportBuilder:
    def __init__(self, stats=None): pass

    def build(self, drive_id): return None
