# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from flask import Blueprint, request, session, jsonify
from repos import eligibility

bp = Blueprint("chat", __name__)

@bp.post("/api/chat")
def chat():
    message = (request.get_json(silent=True) or {}).get("message", "__start__")
    reply, session["chat"] = eligibility.chat(dict(session.get("chat", {})), message)
    return jsonify(reply)
