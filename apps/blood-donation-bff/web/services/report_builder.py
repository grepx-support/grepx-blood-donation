# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Drive report numbers are computed by event-report-service when the report is opened or refreshed (SNAPSHOT), with the same
definitions this builder used; build() stays for the original call sites and returns nothing to send."""


class DriveReportBuilder:
    def __init__(self, stats=None): pass

    def build(self, drive_id): return None
