# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

from flask import current_app, g, has_app_context
from repos.settings_repo import SettingsRepo
from grepx_auth import open_value, seal_value

def settings():
    """Merged view for this request: .env/config values, overridden by what admins saved in the app."""
    if has_app_context() and "_settings" in g: return g._settings
    merged = dict(current_app.config)
    for k, v in SettingsRepo().all().items():
        if v not in (None, ""): merged[k] = open_value(v)
    if has_app_context(): g._settings = merged
    return merged

def setting(key, default=""):
    v = settings().get(key)
    return default if v in (None, "") else v

def save_settings(values, secret_keys=()):
    """values: {KEY: text}. Empty secret = keep the saved one; '__clear__' removes a value (falls back to .env)."""
    repo = SettingsRepo()
    for k, v in values.items():
        v = (v or "").strip()
        if v == "__clear__": repo.delete(k); continue
        if k in secret_keys:
            if not v: continue
            v = seal_value(v)
        repo.set(k, v)
    g.pop("_settings", None)
