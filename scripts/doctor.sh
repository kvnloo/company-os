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

manager_agentsview_root=""
if [[ -z ${AGENTSVIEW_DATA_DIR:-} ]] && command -v systemctl >/dev/null 2>&1; then
  manager_agentsview_root=$(
    systemctl --user show-environment 2>/dev/null \
      | sed -n 's/^AGENTSVIEW_DATA_DIR=//p' \
      | head -n 1
  )
fi
AGENTSVIEW_ROOT="${AGENTSVIEW_DATA_DIR:-${manager_agentsview_root:-$HOME/.agentsview}}"
AGENTSVIEW_SOURCE="default"
[[ -n ${manager_agentsview_root:-} ]] && AGENTSVIEW_SOURCE="systemd-user-manager"
[[ -n ${AGENTSVIEW_DATA_DIR:-} ]] && AGENTSVIEW_SOURCE="ambient-env"
printf 'INFO AgentsView data dir: %s (%s)\n' "$AGENTSVIEW_ROOT" "$AGENTSVIEW_SOURCE"
if [[ -L "$AGENTSVIEW_ROOT" ]]; then
  printf 'WARN effective AgentsView data dir is symlink -> %s\n' "$(readlink "$AGENTSVIEW_ROOT")"
elif [[ -d "$AGENTSVIEW_ROOT" ]]; then
  printf 'OK   effective AgentsView data dir is a real directory\n'
else
  printf 'MISS effective AgentsView data dir\n'
fi
if [[ "$AGENTSVIEW_SOURCE" == "default" && -L "$HOME/.agentsview" ]]; then
  printf 'HINT persist AGENTSVIEW_DATA_DIR="%s" to bypass the symlink safely\n' "$(readlink -f "$HOME/.agentsview")"
fi

df -h "$HOME" /mnt 2>/dev/null || true

Z0INT_HOME="${Z0INT_HOME:-$HOME/.z0int}"
CAPACITY_SNAPSHOT="${COMPANY_OS_Z0_CAPACITY_SNAPSHOT:-$Z0INT_HOME/state/capacity_snapshot.json}"
if [[ -f "$CAPACITY_SNAPSHOT" ]]; then
  if command -v python3 >/dev/null 2>&1 && python3 - "$CAPACITY_SNAPSHOT" <<'PY'
import json, sys
from pathlib import Path
try:
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(1)
raise SystemExit(0 if data.get("schema") == "z0.capacity.snapshot.v1" else 1)
PY
  then
    printf 'OK   z0 capacity snapshot: %s\n' "$CAPACITY_SNAPSHOT"
  else
    printf 'WARN z0 capacity snapshot exists but schema/JSON is invalid: %s\n' "$CAPACITY_SNAPSHOT"
  fi
else
  printf 'INFO z0 capacity snapshot not emitted yet (optional): %s\n' "$CAPACITY_SNAPSHOT"
  printf 'HINT run: z0int capacity snapshot --json\n'
fi

if command -v curl >/dev/null 2>&1; then
  if curl -fsS --max-time 3 http://127.0.0.1:9119/api/plugins/company-os/health; then
    printf '\nOK   Company OS projection API\n'
  else
    printf '\nWARN projection API unavailable; restart hermes dashboard if plugin_api.py was newly installed\n'
  fi
fi

printf '\nSecurity metadata checks (contents are never read):\n'
envd="$HOME/.config/environment.d"
if [[ -d "$envd" ]]; then
  found=0
  while IFS= read -r -d '' f; do
    mode=$(stat -c '%a' "$f" 2>/dev/null || true)
    [[ -z "$mode" ]] && continue
    last2=$((10#$mode % 100))
    group=$((last2 / 10))
    other=$((last2 % 10))
    if (( (group & 2) != 0 || (other & 2) != 0 )); then
      printf 'CRIT %s mode=%s is group/world-writable\n' "$f" "$mode"
      found=1
    fi
  done < <(find "$envd" -maxdepth 1 -type f -name '*.conf' -print0 2>/dev/null)
  if [[ $found -eq 0 ]]; then
    printf 'OK   no group/world-writable environment.d files\n'
  fi
fi

printf '\nNote: first AgentsView start against a large archive may spend ~100s indexing before daemon readiness.\n'
