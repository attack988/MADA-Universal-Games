#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install -y python3-pyqt6 wine unar fonts-noto-core

DIR="$HOME/.local/share/mada-universal-games"
mkdir -p "$DIR" "$HOME/.local/share/applications"

cp "$(dirname "$0")/mada_games.py" "$DIR/mada_games.py"
cp "$(dirname "$0")/mada_requirements.py" "$DIR/mada_requirements.py"

cat > "$DIR/run.sh" <<'RUN'
#!/usr/bin/env bash
exec /usr/bin/python3 "$HOME/.local/share/mada-universal-games/mada_games.py"
RUN

chmod +x "$DIR/run.sh"

cat > "$HOME/.local/share/applications/mada-universal-games.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=MADA Universal Games
Exec=$DIR/run.sh
Icon=applications-games
Terminal=false
Categories=Game;
DESKTOP

echo "MADA installed successfully."
