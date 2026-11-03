"""Blood-donation routes; the common ones (auth, tasks, messages, access, media, gateway) come from grepx_bff."""
from . import donors, drives, eligibility, me, public, reports, signup

ROUTERS = [public.router, signup.router, me.router, eligibility.router, drives.router, donors.router, reports.router]
