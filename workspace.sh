#!/usr/bin/env bash
# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

# Assemble this product's workspace from its sibling repositories (Linux / macOS / WSL - uses symlinks).
#   ./workspace.sh          link the repos below into this folder (run once after cloning, again after moving them)
#   ./workspace.sh clone    git clone any missing sibling repo first, then link
#   ./workspace.sh status   where each link points
# Then, as always:  scripts/infra.sh -> scripts/setup.sh -> scripts/run.sh start
#
# Layout (siblings of this repo; override with GREPX_PLATFORM / GREPX_SERVICES / GREPX_NEXUS):
#   ../grepx-platform    platform/ scripts/ observability/ infra/   (libraries, tools, scripts, monitoring)
#   ../grepx-services    common-services/                           (the generic services)
#   ../grepx-nexus-cpp   the C++ Nexus hub; its built nexus_server is copied into platform/nexus-server/bin/
#                        (copied, not linked: the server keeps nexus_data.db next to its own binary)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
ORG="${GREPX_GIT:-git@github.com:grepx-support}"
PLATFORM="${GREPX_PLATFORM:-../grepx-platform}"
SERVICES="${GREPX_SERVICES:-../grepx-services}"
NEXUS="${GREPX_NEXUS:-../grepx-nexus-cpp}"
LINKS="platform:$PLATFORM/platform scripts:$PLATFORM/scripts observability:$PLATFORM/observability infra:$PLATFORM/infra docs/platform:$PLATFORM/docs common-services:$SERVICES/common-services"

say() { printf '%s %-5s [workspace] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" "$2"; }

clone() {   # clone <folder> <repo name>
  [ -d "$1" ] && return 0
  say INFO "cloning $2 into $1"
  git clone "$ORG/$2.git" "$1"
}

link() {   # link <name> <target>   (target relative to this repo, or absolute)
  local name="$1" target="$2" value="$2" up
  [ -e "$target" ] || { say ERROR "$target not found - clone it next to this repo (./workspace.sh clone) or set its GREPX_* path"; return 1; }
  if [ -e "$name" ] && [ ! -L "$name" ]; then say ERROR "$name exists and is not a link - move it away first"; return 1; fi
  up="$(dirname "$name")"
  case "$target" in /*) ;; *) [ "$up" = . ] || value="$(echo "$up" | sed 's#[^/][^/]*#..#g')/$target" ;; esac
  mkdir -p "$(dirname "$name")"
  ln -sfn "$value" "$name"
  say OK "$name -> $target"
}

nexus_binary() {   # copy the newest build of nexus_server when it is newer than the one in bin/
  local bin="$PLATFORM/platform/nexus-server/bin/nexus_server" built
  [ -d "$NEXUS" ] || { [ -e "$bin" ] || say WARN "no $NEXUS - copy a built nexus_server into platform/nexus-server/bin/ yourself"; return 0; }
  built="$(find "$NEXUS" -type f -name nexus_server -perm -u+x -not -path '*/platform/*' 2>/dev/null | xargs -r ls -t 2>/dev/null | head -1 || true)"
  if [ -z "$built" ]; then
    [ -e "$bin" ] || say WARN "no built nexus_server in $NEXUS yet - build it (cmake), then run ./workspace.sh again"
  elif [ ! -e "$bin" ] || [ -L "$bin" ] || [ "$built" -nt "$bin" ]; then
    rm -f "$bin"; cp "$built" "$bin"; chmod 755 "$bin"; say OK "nexus_server copied from $built"
  fi
}

case "${1:-link}" in
  clone)
    clone "$PLATFORM" grepx-platform; clone "$SERVICES" grepx-services; clone "$NEXUS" grepx-nexus-cpp ;&
  link)
    for pair in $LINKS; do link "${pair%%:*}" "${pair#*:}"; done
    nexus_binary
    say OK "workspace ready - next: scripts/setup.sh (first time: scripts/infra.sh)" ;;
  status)
    for pair in $LINKS; do name="${pair%%:*}"; printf '  %-16s %s\n' "$name" "$(readlink "$name" 2>/dev/null || echo 'not linked')"; done ;;
  *) sed -n '2,12p' "$0"; exit 1 ;;
esac
