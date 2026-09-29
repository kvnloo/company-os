#!/usr/bin/env bash
set -euo pipefail
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"

check_link() {
  local path=$1
  if [[ -L $path || -d $path ]]; then
    printf 'OK   %s\n' "$path"
  else
    printf 'MISS %s\n' "$path"
  fi
}

check_link "$HERMES_HOME/desktop-plugins/company-os"
check_link "$HERMES_HOME/plugins/company-os"

AGENTSVIEW_ROOT="${AGENTSVIEW_DATA_DIR:-$HOME/.agentsview}"
printf 'INFO AgentsView data dir: %s\n' "$AGENTSVIEW_ROOT"
if [[ -L "$AGENTSVIEW_ROOT" ]]; then
  printf 'WARN effective AgentsView data dir is symlink -> %s\n' "$(readlink "$AGENTSVIEW_ROOT")"
elif [[ -d "$AGENTSVIEW_ROOT" ]]; then
  printf 'OK   effective AgentsView data dir is a real directory\n'
else
  printf 'MISS effective AgentsView data dir\n'
fi
if [[ -z ${AGENTSVIEW_DATA_DIR:-} && -L "$HOME/.agentsview" ]]; then
  printf 'HINT export AGENTSVIEW_DATA_DIR="%s" to bypass the symlink safely\n' "$(readlink -f "$HOME/.agentsview")"
fi

df -h "$HOME" /mnt 2>/dev/null || true

if command -v curl >/dev/null 2>&1; then
  if curl -fsS --max-time 3 http://127.0.0.1:9119/api/plugins/company-os/health; then
    printf '\nOK   Company OS projection API\n'
  else
    printf '\nWARN projection API unavailable; restart hermes dashboard if plugin_api.py was newly installed\n'
  fi
fi
