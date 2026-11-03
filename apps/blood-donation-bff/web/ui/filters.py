# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

"""Jinja filters: tiny presentation helpers."""
from grepx_common import Phone
from grepx_config.deployment import timezone as local_zone
import re
from datetime import datetime, timedelta
from urllib.parse import quote

def _date(s): return datetime.strptime(s, "%Y-%m-%d") if s else None
def nice_date(s): return _date(s).strftime("%a, %d %b %Y") if s else "—"
def day(s): return _date(s).strftime("%d") if s else ""
def month(s): return _date(s).strftime("%b") if s else ""
def initials(name): return "".join(p[0] for p in (name or "?").split()[:2]).upper()
def pct(part, whole): return min(100, round((part or 0) / (whole or 100) * 100))
def maps(venue): return "https://www.google.com/maps/search/?api=1&query=" + quote(venue or "")

def wa_link(phone, country=""):
    """wa.me link for a stored (E.164) or typed number."""
    return "https://wa.me/" + re.sub(r"\D", "", Phone.clean_or_none(phone) or phone or "")

def _gcal(title, dates, details="", location=""):
    q = {"action": "TEMPLATE", "text": title, "dates": dates, "details": details, "location": location, "ctz": local_zone().key}
    return "https://calendar.google.com/calendar/render?" + "&".join(f"{k}={quote(str(v))}" for k, v in q.items())

def gcal_task(t):
    if not t["due_at"]: return ""
    start = datetime.strptime(t["due_at"], "%Y-%m-%dT%H:%M")
    return _gcal(t["title"], f"{start:%Y%m%dT%H%M%S}/{start + timedelta(minutes=30):%Y%m%dT%H%M%S}", t["description"] or "")

def gcal_drive(d, slot_start=None, slot_end=None):
    day = d["drive_date"].replace("-", "")
    dates = f"{day}T{slot_start.replace(':', '')}00/{day}T{slot_end.replace(':', '')}00" if slot_start else f"{day}/{day}"
    return _gcal("🩸 " + d["title"], dates, d["time_slot"] or "", d["venue"])

def card_no(i):
    """Donor card number (BC-12345) for any id: the services use text ids, the card shows 5 stable digits."""
    import zlib
    return f"{int(i):05d}" if str(i).isdigit() else f"{zlib.crc32(str(i).encode()) % 100000:05d}"


def register(app):
    for f in (nice_date, day, month, initials, pct, maps, gcal_task, gcal_drive, card_no):
        app.jinja_env.filters[f.__name__] = f
    app.jinja_env.filters["wa"] = lambda p: wa_link(p, app.config["COUNTRY_CODE"])
    from validation import Phone, attrs
    app.jinja_env.filters["phone"] = Phone.pretty
    from media import media_url
    app.jinja_env.filters["media"] = media_url  # media id -> URL (works whatever MEDIA_STORAGE is)
    app.jinja_env.globals["rules"] = attrs
    from integrations.sign_in import google_enabled
    app.jinja_env.globals["google_sign_in"] = google_enabled  # show "Continue with Google" only once it is set up  # {{ rules('phone') }} -> the same limits the server checks
    from repos.eligibility import criteria
    app.jinja_env.globals["elig"] = criteria  # donor requirements, one source for website + LifeBot
