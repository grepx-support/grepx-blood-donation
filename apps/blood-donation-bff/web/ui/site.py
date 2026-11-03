# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""The public address used in links (share buttons, invite links, emails, WhatsApp, calendar feeds)."""
from urllib.parse import urlparse
from flask import current_app, has_request_context, request

LOCAL = {"", "127.0.0.1", "localhost", "0.0.0.0"}

def configured():
    """SITE_URL from .env, unless it is empty or still the local default."""
    url = (current_app.config.get("SITE_URL") or "").strip().rstrip("/")
    return url if urlparse(url).hostname not in LOCAL else ""

def site_url():
    """SITE_URL when set properly; otherwise the address people actually opened the site with."""
    if configured(): return configured()
    if has_request_context(): return request.host_url.rstrip("/")
    return (current_app.config.get("SITE_URL") or "http://127.0.0.1:5000").rstrip("/")
