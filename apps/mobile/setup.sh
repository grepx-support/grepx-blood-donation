#!/usr/bin/env bash
# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

# LifeFlow's phone app - once, after cloning (and after a Flutter upgrade); the work is in the shared setup.
#   ./setup.sh
#   flutter run --dart-define=API_BASE=https://your.domain.com      (emulator + local server: http://10.0.2.2:8851)
#   flutter build apk --release --dart-define=API_BASE=https://your.domain.com
set -euo pipefail
cd "$(dirname "$0")"
exec bash ../../platform/mobile/setup.sh grepx_blood "LifeFlow"
