#!/usr/bin/env bash
# Install Company OS HUD into Hermes Desktop.
#
#   ./scripts/install.sh
#   curl -fsSL https://raw.githubusercontent.com/kvnloo/company-os/main/scripts/install.sh | bash
set -euo pipefail

REPO_URL="${COMPANY_OS_REPO:-https://github.com/kvnloo/company-os.git}"
INSTALL_HOME="${COMPANY_OS_HOME:-$HOME/.local/share/company-os}"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
PLUGIN_ID="company-os"

log() { printf 'company-os: %s\n' "$*"; }
die() { printf 'company-os: ERROR: %s\n' "$*" >&2; exit 1; }

if [[ -n ${BASH_SOURCE[0]+x} && -f ${BASH_SOURCE[0]} ]]; then
  _self=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
  if [[ -f $_self/../plugin/plugin.js ]]; then
    ROOT=$(cd -- "$_self/.." && pwd)
  fi
fi

if [[ -z ${ROOT:-} ]]; then
  if [[ -d $INSTALL_HOME/.git ]]; then
    log "updating $INSTALL_HOME"
    git -C "$INSTALL_HOME" pull --ff-only || log "pull failed; using existing tree"
  else
    log "cloning into $INSTALL_HOME"
    mkdir -p "$(dirname -- "$INSTALL_HOME")"
    git clone --depth 1 "$REPO_URL" "$INSTALL_HOME"
  fi
  ROOT=$INSTALL_HOME
fi

[[ -f $ROOT/plugin/plugin.js ]] || die "plugin.js missing under $ROOT/plugin"

mkdir -p "$HERMES_HOME/desktop-plugins"
ln -sfn "$ROOT/plugin" "$HERMES_HOME/desktop-plugins/$PLUGIN_ID"
log "linked $HERMES_HOME/desktop-plugins/$PLUGIN_ID → $ROOT/plugin"
log "In Hermes Desktop: ⌘K → Reload desktop plugins → open Company OS"
