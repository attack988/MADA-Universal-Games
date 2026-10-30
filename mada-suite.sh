#!/usr/bin/env bash
# MADA Suite — Ubuntu launcher for the currently available MADA apps.
# All files stay under ~/MADA-Apps. No repo files are deleted.
set -Eeuo pipefail
OWNER="attack988"
BASE="${MADA_BASE:-$HOME/MADA-Apps}"
GAMES="$BASE/MADA-Universal-Games"
ANYWHERE="$BASE/MADA-Anywhere"
RUNTIME="$BASE/.runtime"
PORT="8787"
mkdir -p "$RUNTIME"
msg(){ printf '\n[MADA] %s\n' "$*"; }
fail(){ printf '\n[MADA ERROR] %s\n' "$*" >&2; exit 1; }
has(){ command -v "$1" >/dev/null 2>&1; }
running(){ local pfile="$1"; [[ -f "$pfile" ]] && kill -0 "$(cat "$pfile")" 2>/dev/null; }
port_open(){ python3 - "$PORT" <<'PY'
import socket,sys
try:
    with socket.create_connection(("127.0.0.1",int(sys.argv[1])),timeout=.3): sys.exit(0)
except OSError: sys.exit(1)
PY
}
ensure_games(){
  if [[ -d "$GAMES/.git" ]]; then
    git -C "$GAMES" pull --ff-only || msg "Could not update Games; keeping your existing copy."
  elif [[ -e "$GAMES" ]]; then
    fail "$GAMES already exists and is not a Git checkout. Move it yourself to avoid overwriting."
  else
    git clone "https://github.com/$OWNER/MADA-Universal-Games.git" "$GAMES"
  fi
}
ensure_anywhere(){
  if [[ -s "$ANYWHERE/server.py" ]]; then return; fi
  if [[ -e "$ANYWHERE" ]]; then fail "$ANYWHERE exists but is incomplete. Move it manually before continuing."; fi
  if has gh && gh repo view "$OWNER/MADA-Anywhere" >/dev/null 2>&1; then
    git clone "https://github.com/$OWNER/MADA-Anywhere.git" "$ANYWHERE"
  else
    local zip="$GAMES/apps/MADA-Anywhere/MADA_Anywhere_v2.zip"
    [[ -s "$zip" ]] || fail "Missing Anywhere source package: $zip"
    local tmp
    tmp="$(mktemp -d)"
    unzip -q "$zip" -d "$tmp"
    mv "$tmp/MADA_Anywhere" "$ANYWHERE"
    rmdir "$tmp"
  fi
}
install_apps(){
  has apt-get || fail "This automatic setup targets Ubuntu. Other platforms need their own installers."
  msg "Installing Ubuntu dependencies (sudo will ask for your password)..."
  sudo apt-get update
  sudo apt-get install -y git gh unzip python3 python3-venv python3-pip python3-pyqt6 wine unar fonts-noto-core ffmpeg xdg-utils
  ensure_games
  ensure_anywhere
  msg "Installing MADA Universal Games..."
  bash "$GAMES/install.sh"
  msg "Installing MADA Anywhere dependencies..."
  bash "$ANYWHERE/install_ubuntu_mac.sh"
  mkdir -p "$HOME/.local/bin" "$HOME/.local/share/applications"
  ln -sfn "$GAMES/mada-suite.sh" "$HOME/.local/bin/mada"
  cat > "$HOME/.local/share/applications/mada-suite.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=MADA Suite - Launch All
Name[ar]=مدى - تشغيل كل البرامج
Comment=Launch MADA Games and MADA Anywhere
Exec=$HOME/.local/bin/mada start
Icon=applications-multimedia
Terminal=false
Categories=Utility;Game;
EOF
  msg "Installed. Start BOTH apps with: $HOME/.local/bin/mada start"
  msg "After opening a new Terminal you can simply type: mada start"
}
launch_games(){
  local runner="$HOME/.local/share/mada-universal-games/run.sh"
  [[ -x "$runner" ]] || { msg "Games is not installed. Run setup first."; return 1; }
  if running "$RUNTIME/games.pid"; then msg "Games is already running."; return 0; fi
  if [[ -z "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]]; then msg "No graphical desktop detected; cannot open Games."; return 1; fi
  nohup "$runner" >"$RUNTIME/games.log" 2>&1 </dev/null &
  echo "$!" > "$RUNTIME/games.pid"
  msg "Started MADA Games."
}
launch_anywhere(){
  [[ -s "$ANYWHERE/server.py" ]] || { msg "Anywhere is missing; run setup first."; return 1; }
  if port_open; then
    msg "A server is already using http://127.0.0.1:$PORT (check that it is MADA Anywhere)."
  else
    local py="$ANYWHERE/.venv/bin/python"
    [[ -x "$py" ]] || py=python3
    (cd "$ANYWHERE"; nohup "$py" server.py >"$RUNTIME/anywhere.log" 2>&1 </dev/null & echo "$!" >"$RUNTIME/anywhere.pid")
    for _ in {1..20}; do port_open && break; sleep .3; done
    port_open || { msg "Anywhere server failed. Check $RUNTIME/anywhere.log"; return 1; }
    msg "Started MADA Anywhere."
  fi
  if has xdg-open && [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]]; then
    xdg-open "http://127.0.0.1:$PORT" >/dev/null 2>&1 || true
  fi
  msg "Anywhere address: http://127.0.0.1:$PORT"
}
launch_all(){
  local failed=0
  launch_games || failed=1
  launch_anywhere || failed=1
  (( failed == 0 )) || msg "At least one app did not start. Read the messages above."
  return "$failed"
}
stop_app(){
  local name="$1" pidfile="$RUNTIME/$1.pid"
  if running "$pidfile"; then kill "$(cat "$pidfile")"; msg "Stopped $name."; else msg "$name was not started by this launcher."; fi
  rm -f "$pidfile"
}
case "${1:-help}" in
  setup|install) install_apps ;;
  start|all) launch_all ;;
  games) launch_games ;;
  anywhere) launch_anywhere ;;
  stop) stop_app games; stop_app anywhere ;;
  status)
    for app in games anywhere; do if running "$RUNTIME/$app.pid"; then msg "$app: running (PID $(cat "$RUNTIME/$app.pid"))"; else msg "$app: not running via this launcher"; fi; done
    if port_open; then msg "Port $PORT is active."; fi ;;
  github) [[ -s "$GAMES/mada-github-setup.sh" ]] || fail "Run setup first."; bash "$GAMES/mada-github-setup.sh" ;;
  help|-h|--help)
    cat <<'HELP'
MADA Suite — Ubuntu
  mada setup       Install Games and Anywhere once
  mada start       Open Games and Anywhere together
  mada games       Open only MADA Universal Games
  mada anywhere    Open only MADA Anywhere
  mada status      Show current running status
  mada stop        Stop processes started by this launcher
  mada github      Create the SEPARATE public MADA Anywhere repository
HELP
    ;;
  *) fail "Unknown command: $1. Try: mada help" ;;
esac
