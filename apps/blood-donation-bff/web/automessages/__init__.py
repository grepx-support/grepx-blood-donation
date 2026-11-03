# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

"""Automatic messages (welcome, new drive, certificates …): admins switch each on/off, pick channels and can
replace the built-in wording with their own text using {placeholders}. Stored in app_settings."""
from .catalog import AUTO, BY_KEY
from .policy import AutoPolicy
from .custom import CustomText

__all__ = ["AUTO", "BY_KEY", "AutoPolicy", "CustomText"]
