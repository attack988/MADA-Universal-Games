#!/usr/bin/env bash
# Update only the MADA Games launcher code; preserve game library and Wine prefixes.
set -Eeuo pipefail
SOURCE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$HOME/.local/share/mada-universal-games"

if [[ ! -f "$APP_DIR/run.sh" ]]; then
  echo "MADA Games is not installed. Run: bash \"$SOURCE_DIR/install.sh\"" >&2
  exit 1
fi

python3 -m py_compile "$SOURCE_DIR/mada_games.py" "$SOURCE_DIR/mada_requirements.py"
install -m 0644 "$SOURCE_DIR/mada_games.py" "$APP_DIR/mada_games.py"
install -m 0644 "$SOURCE_DIR/mada_requirements.py" "$APP_DIR/mada_requirements.py"

echo "MADA Games v2.1 updated successfully."
echo "Your saved games and Wine environments were not touched."
echo "Close any running MADA Games windows, then open the app again."
echo "You can start it with: $APP_DIR/run.sh"
