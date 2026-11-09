#!/usr/bin/env bash
# One Flutter app (Android + iOS) for every GrepX product - built on a developer machine, not on the server.
#   ./setup.sh                      once: generate the android/ and ios/ shells around lib/ and fetch packages
#   flutter run --dart-define=PRODUCT=blood-donation --dart-define=API_BASE=https://your.domain.com
#   flutter build appbundle --dart-define=PRODUCT=blood-donation --dart-define=API_BASE=https://your.domain.com
# Emulator against a local server: API_BASE=http://10.0.2.2:8851 (Android) or http://localhost:8851 (iOS simulator).
set -euo pipefail
cd "$(dirname "$0")"

say() { printf '%s %-5s [%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" "mobile" "$2"; }
die() { say ERROR "$1"; exit 1; }

command -v flutter >/dev/null 2>&1 || die "Flutter is not installed - see https://docs.flutter.dev/get-started/install"
if [ ! -d android ]; then
  say INFO "generating the android/ and ios/ shells (first time)"
  flutter create --org sg.grepx --project-name grepx_mobile --platforms=android,ios . >/dev/null || die "flutter create failed"
fi
say INFO "fetching packages"
flutter pub get >/dev/null || die "flutter pub get failed"
say OK "mobile ready - for QR scanning add NSCameraUsageDescription to ios/Runner/Info.plist"
