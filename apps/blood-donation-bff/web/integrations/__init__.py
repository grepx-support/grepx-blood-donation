# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Accounts the app connects to (social media, email, SMS/WhatsApp), managed by admins in the app.

Values saved on the Integrations page live in the app_settings table (secrets encrypted with SECRET_KEY);
anything not saved there still comes from .env, so existing servers keep working."""
from .settings import setting, settings, save_settings

__all__ = ["setting", "settings", "save_settings"]
