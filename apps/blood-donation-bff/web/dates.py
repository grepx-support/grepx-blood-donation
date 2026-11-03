# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

"""Dates computed in Python and passed as parameters, so SQL stays portable across databases."""
from datetime import datetime, timedelta

from grepx_config.deployment import timezone

TZ = timezone()  # the deployment's own day (TIMEZONE), even when the server clock runs on UTC

def local_date(): return datetime.now(TZ).date()
def today(): return local_date().isoformat()
def days_ago(n): return (local_date() - timedelta(days=int(n))).isoformat()
def years_ago(n):
    t = local_date()
    try: return t.replace(year=t.year - int(n)).isoformat()
    except ValueError: return t.replace(year=t.year - int(n), day=28).isoformat()
