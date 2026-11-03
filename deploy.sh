#!/usr/bin/env bash
# Get, build and run everything - one command for a new server and for every update after.
#   ./deploy.sh            clone/pull all four repos, build Nexus, set up, migrate, (re)start, seed
#   ./deploy.sh --no-pull  same, without git pull (deploy exactly what is checked out)
# Safe to run again: every step only does what is missing or changed.
# Env: SKIP_INFRA=1 (databases / toolchain already set up), NO_RESTART=1 (set up only, don't touch running services),
#      SITE_URL=https://… (written to .env), ADMIN_EMAIL + ADMIN_PASSWORD + ADMIN_PHONE [+ ADMIN_NAME] (create the admin).
# Secrets in .env (JWT_SECRET, SECRET_BOX_KEY, NEXUS_SERVICE_SECRET) are generated when still placeholders.
#
# Steps
#   1 repos    ./workspace.sh clone: ../grepx-platform ../grepx-services ../grepx-nexus-cpp next to this repo; git pull each
#   2 nexus    cmake build of nexus_server in ../grepx-nexus-cpp/build (needs cmake + a C++20 compiler; installed on Linux)
#   3 link     ./workspace.sh: platform/, scripts/, common-services/ … linked in, the new nexus_server copied in
#   4 infra    scripts/infra.sh (toolchain + database engines)        5 setup   scripts/setup.sh (venvs, contracts, tables)
#   6 data     stop, backup, every migration in platform/tools/migrations (each is a no-op once applied), Nexus accounts
#   7 run      scripts/run.sh start, seed, status, workspace check
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
PULL=1; [ "${1:-}" = "--no-pull" ] && PULL=0
NEXUS="${GREPX_NEXUS:-../grepx-nexus-cpp}"
say() { printf '%s %-5s [deploy] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" "$2"; }
die() { say ERROR "$1"; exit 1; }
step() { say INFO "── $1"; }
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO=sudo

# Repos committed from Windows lose the executable bit: set it on every script before using any of them
# (core.fileMode=false so git does not count that as a local change and later pulls stay clean).
for repo in . "${GREPX_PLATFORM:-../grepx-platform}" "${GREPX_SERVICES:-../grepx-services}"; do
  [ -d "$repo/.git" ] && git -C "$repo" config core.fileMode false
  [ -d "$repo" ] && find "$repo" -name "*.sh" -not -path "*/.venv/*" -not -path "*/node_modules/*" -exec chmod +x {} + 2>/dev/null || true
done

step "1/7 repos"
bash workspace.sh clone >/dev/null || die "could not get the sibling repos (check git access to ${GREPX_GIT:-git@github.com:grepx-support})"
if [ "$PULL" = 1 ]; then
  for repo in . "${GREPX_PLATFORM:-../grepx-platform}" "${GREPX_SERVICES:-../grepx-services}" "$NEXUS"; do
    if git -C "$repo" rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; then
      git -C "$repo" pull --ff-only -q && say OK "$(basename "$(cd "$repo" && pwd)") @ $(git -C "$repo" rev-parse --short HEAD)" \
        || die "git pull failed in $repo (local changes?) - commit or stash them, or run ./deploy.sh --no-pull"
    else
      say WARN "$(basename "$(cd "$repo" && pwd)"): no upstream branch - not pulled"
    fi
  done
fi

step "2/7 build nexus_server"
BIN="${GREPX_PLATFORM:-../grepx-platform}/platform/nexus-server/bin/nexus_server"
build_nexus() {
  if ! command -v cmake >/dev/null 2>&1 || ! command -v g++ >/dev/null 2>&1; then
    command -v apt-get >/dev/null 2>&1 || { say WARN "no cmake / C++ compiler"; return 1; }
    say INFO "installing cmake + g++"; $SUDO apt-get update -qq && $SUDO apt-get install -y -qq cmake g++ ninja-build >/dev/null
  fi
  local gen=""; command -v ninja >/dev/null 2>&1 && gen="-G Ninja"
  [ -f "$NEXUS/build/CMakeCache.txt" ] || cmake -S "$NEXUS" -B "$NEXUS/build" $gen -DCMAKE_BUILD_TYPE=Release >/dev/null || return 1
  # Parallel jobs: one per ~1.5 GB of available memory (sqlite3.c alone needs ~1 GB to compile), at most one per CPU.
  local mem_kb jobs cpus
  mem_kb="$(awk '/MemAvailable/ {print $2}' /proc/meminfo 2>/dev/null || echo 0)"
  jobs="${NEXUS_JOBS:-$(( mem_kb / 1500000 ))}"; cpus="$(nproc 2>/dev/null || echo 1)"
  [ "$jobs" -lt 1 ] && jobs=1; [ "$jobs" -gt "$cpus" ] && jobs="$cpus"
  say INFO "building with $jobs parallel job(s) - the first build takes a few minutes"
  cmake --build "$NEXUS/build" --target nexus_server -j "$jobs" >/dev/null
}
if [ "${NEXUS_SKIP_BUILD:-0}" = 1 ]; then
  say INFO "build skipped (NEXUS_SKIP_BUILD=1) - using $BIN"
elif build_nexus; then
  say OK "nexus_server built"
elif [ -x "$BIN" ]; then
  say WARN "nexus_server could not be built here - using the binary already in $BIN"
else
  die "nexus_server could not be built and $BIN is missing - build it elsewhere and copy it there (see README)"
fi

step "3/7 link the workspace"
for repo in "${GREPX_PLATFORM:-../grepx-platform}" "${GREPX_SERVICES:-../grepx-services}"; do git -C "$repo" config core.fileMode false 2>/dev/null || true; done
find "${GREPX_PLATFORM:-../grepx-platform}" "${GREPX_SERVICES:-../grepx-services}" -name "*.sh" -not -path "*/.venv/*" -exec chmod +x {} + 2>/dev/null || true
bash workspace.sh | grep -v "^.*OK .*->" || true

if [ "${SKIP_INFRA:-0}" != 1 ]; then step "4/7 infrastructure"; scripts/infra.sh; else say INFO "── 4/7 infrastructure skipped (SKIP_INFRA=1)"; fi

step "5/7 set up services"
scripts/setup.sh
secret() { python3 -c 'import secrets; print(secrets.token_hex(32))'; }
fill() {   # fill KEY: generate a value only while .env still has the placeholder (or nothing) - never replaces a real one
  if grep -qE "^$1=(change-me.*)?$" .env; then sed -i "s#^$1=.*#$1=$(secret)#" .env; say OK "$1 generated in .env"; fi
}
fill JWT_SECRET; fill SECRET_BOX_KEY; fill NEXUS_SERVICE_SECRET
[ -n "${SITE_URL:-}" ] && sed -i "s#^SITE_URL=.*#SITE_URL=$SITE_URL#" .env

if [ "${NO_RESTART:-0}" = 1 ]; then say OK "set up only (NO_RESTART=1) - start with: scripts/run.sh restart"; exit 0; fi

step "6/7 data"
scripts/run.sh stop >/dev/null 2>&1 || true
if [ -f platform/nexus-server/bin/nexus_data.db ]; then
  scripts/run.sh backup >/dev/null 2>&1 && say OK "backup taken" || say WARN "backup failed - continuing"
  for m in platform/tools/migrations/*.yaml; do scripts/run.sh migrate "$(basename "$m" .yaml)"; done
fi
bash platform/nexus-server/setup.sh >/dev/null          # schema, Nexus user, per-service accounts (NEXUS_SERVICE_SECRET)

step "7/7 start"
scripts/run.sh start >/dev/null
for _ in $(seq 1 30); do scripts/run.sh status 2>&1 | grep -qE "STARTING|DOWN" || break; sleep 2; done
scripts/run.sh seed
scripts/run.sh status | tail -1
scripts/run.sh workspace || true
if [ -n "${ADMIN_EMAIL:-}" ] && [ -n "${ADMIN_PASSWORD:-}" ] && [ -n "${ADMIN_PHONE:-}" ]; then
  scripts/run.sh admin "$ADMIN_EMAIL" "$ADMIN_PASSWORD" "${ADMIN_NAME:-Admin}" "$ADMIN_PHONE"
fi
say OK "deployed - $(grep -E '^SITE_URL=' .env | cut -d= -f2-)"
