# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

"""Small request helpers shared by every blueprint (one place for redirects and form parsing)."""
from urllib.parse import urlparse
from flask import redirect, request, flash

def _local(url):
    """Only paths on this site (no //evil.com, no other hosts)."""
    if not url: return None
    u = urlparse(url)
    if u.netloc and u.netloc != request.host: return None
    path = u.path or "/"
    if not path.startswith("/") or path.startswith("//"): return None
    return path + (f"?{u.query}" if u.query else "") + (f"#{u.fragment}" if u.fragment else "")

def go_next(default):
    """Redirect to ?next= / form 'next' when it is a page of this site, otherwise to default."""
    return redirect(_local(request.values.get("next", "")) or default)

def go_back(default):
    """Redirect to the page the person came from (same site only), otherwise to default."""
    return redirect(_local(request.referrer) or default)

def id_list(value):
    """'3, 7,x,9' -> [3, 7, 9]"""
    return [x.strip() for x in (value or "").split(",") if x.strip()]

def flash_form_errors(errors, prefix="Please fix: "):
    from validation import summary
    flash(prefix + summary(errors), "error")
