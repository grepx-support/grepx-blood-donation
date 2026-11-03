# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Puts the platform libraries on sys.path so every test suite runs from the repo root (pytest)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for path in sorted((ROOT / "platform" / "libs").glob("*/")):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import os

os.environ.setdefault("GREPX_DATABASE_URL", "memory://")  # tests keep every service database in memory
