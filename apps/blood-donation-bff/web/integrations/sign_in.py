# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Sign in with Google: the web only runs the OAuth redirect (Authlib) and hands Google's ID token to auth-service,
which verifies it and decides who the person is. Credentials come from the Integrations page (or .env)."""
from flask import url_for

from ui.site import site_url
from .settings import setting

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "openid email profile"


def google_enabled() -> bool:
    return bool(setting("GOOGLE_CLIENT_ID") and setting("GOOGLE_CLIENT_SECRET"))


def redirect_uri() -> str:
    """The exact address to register in Google Cloud (Authorized redirect URIs)."""
    return site_url() + url_for("google_login.callback")


def google_client():
    from authlib.integrations.requests_client import OAuth2Session  # only needed once Google sign-in is used
    return OAuth2Session(setting("GOOGLE_CLIENT_ID"), setting("GOOGLE_CLIENT_SECRET"), scope=SCOPE, redirect_uri=redirect_uri())
