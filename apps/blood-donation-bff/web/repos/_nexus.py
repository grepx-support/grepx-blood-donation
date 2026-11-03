"""The web tier's only door to the data: Nexus state tables (read) and requests to the owning service (write).

Repositories keep the original method names and row shapes, so routes, services and templates work unchanged;
underneath, every read is a SELECT of a service's state table and every write is a request that the owning
microservice validates and applies (business rules stay in the services).
"""
from __future__ import annotations

from typing import Any, Optional

GW = None                     # grepx_bff.Gateway, set by web.create_web_app()


class RepoError(Exception):
    """A service refused a change; str(e) is a readable reason."""
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(detail or reason.replace("_", " ").capitalize())
        self.reason, self.detail = reason, detail


def _cache() -> Optional[dict]:
    try:
        from flask import g, has_app_context
        if has_app_context():
            if not hasattr(g, "_nexus_rows"):
                g._nexus_rows = {}
            return g._nexus_rows
    except ImportError:
        pass
    return None


def table(name: str) -> list[dict]:
    """Every live row of a state table, with "id" = its key (cached for the current request)."""
    cache = _cache()
    if cache is not None and name in cache:
        return cache[name]
    rows = [{**r, "id": r["_key"]} for r in GW.read.accepted(name)]
    if cache is not None:
        cache[name] = rows
    return rows


def where(name: str, **eq: Any) -> list[dict]:
    return [r for r in table(name) if all(str(r.get(k, "") or "") == str(v if v is not None else "") for k, v in eq.items())]


def one(name: str, key: Any) -> Optional[dict]:
    if key in (None, ""):
        return None
    for r in table(name):
        if r["id"] == str(key):
            return r
    return None


def command(request_table: str, service: str, fields: dict, ok_only: bool = True):
    """Send a request to the owning service and wait for its verdict; clears the read cache."""
    from grepx_bff.errors import ApiError
    cache = _cache()
    if cache is not None:
        cache.clear()
    try:
        verdict = GW.command(request_table, service, {k: v for k, v in fields.items() if v is not None}, ok_only=False)
    except ApiError as exc:
        raise RepoError((exc.detail or {}).get("reason", "SERVICE_UNAVAILABLE") if isinstance(exc.detail, dict) else "SERVICE_UNAVAILABLE") from exc
    if ok_only and not verdict.ok:
        raise RepoError(verdict.reason, str(verdict.fields.get("detail") or ""))
    return verdict


def actor() -> str:
    try:
        from flask_login import current_user
        return str(current_user.id) if current_user and current_user.is_authenticated else ""
    except Exception:
        return ""
