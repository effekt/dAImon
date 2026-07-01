#!/usr/bin/env bash
# Scaffold machine-local config from the tracked *.example files so a fresh clone
# has editable daemon.local.toml / profile.local.toml files to fill in. Idempotent:
# existing files are left untouched.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

CONFIG_DIR="$HOME/.config/daimon"
CONFIG="$CONFIG_DIR/daimon.toml"
if [ ! -f "$CONFIG" ]; then
  mkdir -p "$CONFIG_DIR"
  cp "$ROOT/config/daimon.toml.example" "$CONFIG"
  echo "  new   $CONFIG"
else
  echo "  skip  $CONFIG (exists)"
fi

scaffold() {
  local ex="$1" dest="${1%.example}"
  if [ -f "$dest" ]; then
    echo "  skip  ${dest#"$ROOT"/} (exists)"
  else
    cp "$ex" "$dest"
    echo "  new   ${dest#"$ROOT"/}"
  fi
}

for ex in "$ROOT"/daemons/*/daemon.local.toml.example "$ROOT"/profiles/*/profile.local.toml.example; do
  [ -f "$ex" ] && scaffold "$ex"
done

echo ""
echo "next: set working_dir in each daemons/*/daemon.local.toml, then run 'daimon doctor'."
