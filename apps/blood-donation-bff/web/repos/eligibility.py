# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Donor eligibility lives in questionnaire-service; the web only asks (form check, LifeBot turn, requirement numbers)."""
from __future__ import annotations
import grepx_contracts as gc

import time

from ._nexus import command

TABLE, SERVICE = gc.questionnaire.REQUESTS, gc.questionnaire.SERVICE
_CACHE: dict = {}
TTL = 600  # seconds; the requirements change only when the service is updated


def check(form: dict) -> tuple[bool, list, list]:
    """(eligible, reasons, notes) for the quick form; RepoError("INVALID_ANSWERS") on bad values."""
    f = command(TABLE, SERVICE, {"action": "CHECK", "answers": {k: v for k, v in form.items() if k != "csrf_token"}}).fields
    return bool(f.get("eligible")), list(f.get("reasons") or []), list(f.get("notes") or [])


def chat(state: dict, message: str) -> tuple[dict, dict]:
    """One LifeBot turn: (reply, new state)."""
    f = command(TABLE, SERVICE, {"action": "CHAT", "state": state, "message": message}).fields
    return dict(f.get("reply") or {}), dict(f.get("state") or {})


class Criteria:
    """The requirement numbers for templates ({{ elig.AGE_MIN }}), fetched from the service and cached."""

    def _data(self) -> dict:
        if not _CACHE or time.time() - _CACHE.get("at", 0) > TTL:
            _CACHE.update(data=command(TABLE, SERVICE, {"action": "CRITERIA"}).fields.get("criteria") or {}, at=time.time())
        return _CACHE["data"]

    def __getattr__(self, name: str):
        try:
            return self._data()[name]
        except KeyError:
            raise AttributeError(name) from None


criteria = Criteria()
