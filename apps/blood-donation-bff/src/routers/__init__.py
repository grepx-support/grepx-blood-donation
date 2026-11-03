# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Blood-donation routes; the common ones (auth, tasks, messages, access, media, gateway) come from grepx_bff."""
from . import donors, drives, eligibility, me, public, reports, signup

ROUTERS = [public.router, signup.router, me.router, eligibility.router, drives.router, donors.router, reports.router]
