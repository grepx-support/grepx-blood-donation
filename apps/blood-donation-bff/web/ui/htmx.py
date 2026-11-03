# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

import json
from flask import request, make_response

def is_htmx(): return request.headers.get("HX-Request") == "true"

def with_toast(response, message, kind="success"):
    """Attach a toast to an htmx response; the browser shows it via the 'toast' event."""
    response = make_response(response)
    response.headers["HX-Trigger"] = json.dumps({"toast": {"type": kind, "message": message}})
    return response
