# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

from integrations import setting
from .catalog import BY_KEY

class AutoPolicy:
    """Is this automatic message on, and over which channels? (admins decide on Messages → Automatic messages)"""
    @staticmethod
    def enabled(key):
        a = BY_KEY.get(key)
        v = setting(f"auto.{key}.enabled")
        return (a.enabled if a else True) if v == "" else v == "1"

    @staticmethod
    def channels(key, fallback=("email", "whatsapp")):
        if not AutoPolicy.enabled(key): return ()
        v = setting(f"auto.{key}.channels")
        a = BY_KEY.get(key)
        return tuple(c for c in v.split(",") if c) if v else (a.channels if a else tuple(fallback))
