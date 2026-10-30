#!/usr/bin/env bash
# MADA Suite: Educational Study V14 + MADA Anywhere V2 (Ubuntu / Linux desktop).
# This script NEVER launches or installs MADA Universal Games.
set -Eeuo pipefail
APP_HOME="${MADA_HOME:-$HOME/MADA-Apps}"
STUDY="$APP_HOME/MADA_Study"
ANYWHERE="$APP_HOME/MADA-Anywhere"
RUNTIME="$APP_HOME/.runtime"
SELF_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
STUDY_PORT=4177
ANYWHERE_PORT=8787
mkdir -p "$RUNTIME"

say(){ printf '\n[MADA] %s\n' "$*"; }
err(){ printf '\n[MADA - ERROR] %s\n' "$*" >&2; }
has(){ command -v "$1" >/dev/null 2>&1; }
die(){ err "$*"; exit 1; }

# We only consider a port ready if it belongs to the expected application.
probe(){
  local app="$1" port="$2"
  python3 - "$app" "$port" <<'PY'
import sys,urllib.request
app,port=sys.argv[1:]
try:
  url=f'http://127.0.0.1:{port}/api/health' if app=='anywhere' else f'http://127.0.0.1:{port}/'
  with urllib.request.urlopen(url,timeout=.65) as res: data=res.read(40000).decode('utf8','ignore')
  good=('MADA Anywhere' in data or '"ok"' in data or '"version"' in data) if app=='anywhere' else ('مَدَى' in data or 'mada-' in data.lower() or 'MADA' in data)
  sys.exit(0 if good else 1)
except Exception: sys.exit(1)
PY
}
port_taken(){
  python3 - "$1" <<'PY'
import socket,sys
s=socket.socket();s.settimeout(.35)
try: s.connect(('127.0.0.1',int(sys.argv[1])));sys.exit(0)
except OSError: sys.exit(1)
finally: s.close()
PY
}
wait_for(){
  local app="$1" port="$2" pidfile="$3" n
  for ((n=0;n<35;n++)); do
    if probe "$app" "$port"; then return 0; fi
    if [[ -f "$pidfile" ]] && ! kill -0 "$(cat "$pidfile")" 2>/dev/null; then return 1; fi
    sleep .3
  done
  return 1
}
open_browser(){
  local url="$1"
  if [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]]; then
    if has xdg-open; then xdg-open "$url" >/dev/null 2>&1 || true
    elif has gio; then gio open "$url" >/dev/null 2>&1 || true
    fi
  fi
}

find_study(){
  local dir zip tmp
  [[ -f "$STUDY/server.cjs" && -f "$STUDY/package.json" ]] && return 0
  for dir in \
    "$SELF_DIR/MADA_V14" \
    "$HOME/Downloads/MADA_V14" \
    "$HOME/Downloads/MADA_Smart_Study_v14/MADA_V14" \
    "$HOME/MADA_V14"; do
    if [[ -f "$dir/server.cjs" && -f "$dir/package.json" ]]; then
      if [[ "$dir" != "$STUDY" ]]; then
        [[ ! -e "$STUDY" ]] || die "The study destination already exists and is incomplete: $STUDY"
        mkdir -p "$STUDY"; cp -a "$dir/." "$STUDY/"
      fi
      return 0
    fi
  done
  for zip in "$SELF_DIR/MADA_Smart_Study_v14.zip" "$HOME/Downloads/MADA_Smart_Study_v14.zip"; do
    if [[ -s "$zip" ]]; then
      has unzip || die 'unzip is required.'
      [[ ! -e "$STUDY" ]] || die "Incomplete Study directory exists; not overwriting: $STUDY"
      tmp="$(mktemp -d)"
      if ! unzip -q "$zip" -d "$tmp"; then rm -rf "$tmp"; die "Cannot unzip $zip"; fi
      [[ -f "$tmp/MADA_V14/server.cjs" ]] || { rm -rf "$tmp"; die "Unexpected Study ZIP structure."; }
      mv "$tmp/MADA_V14" "$STUDY"
      rmdir "$tmp"
      return 0
    fi
  done
  return 1
}

find_anywhere(){
  local dir zip tmp
  [[ -f "$ANYWHERE/server.py" && -f "$ANYWHERE/requirements.txt" ]] && return 0
  for dir in "$SELF_DIR/MADA_Anywhere" "$HOME/Downloads/MADA_Anywhere"; do
    if [[ -f "$dir/server.py" && -f "$dir/requirements.txt" ]]; then
      [[ ! -e "$ANYWHERE" ]] || die "Incomplete Anywhere folder exists; not overwriting: $ANYWHERE"
      mkdir -p "$ANYWHERE"; cp -a "$dir/." "$ANYWHERE/"
      return 0
    fi
  done
  for zip in "$SELF_DIR/MADA_Anywhere_v2.zip" "$HOME/Downloads/MADA_Anywhere_v2.zip"; do
    if [[ -s "$zip" ]]; then
      [[ ! -e "$ANYWHERE" ]] || die "Incomplete Anywhere folder exists; not overwriting: $ANYWHERE"
      tmp="$(mktemp -d)"
      if ! unzip -q "$zip" -d "$tmp"; then rm -rf "$tmp"; die "Cannot unzip $zip"; fi
      [[ -f "$tmp/MADA_Anywhere/server.py" ]] || { rm -rf "$tmp"; die "Unexpected Anywhere ZIP structure."; }
      mv "$tmp/MADA_Anywhere" "$ANYWHERE"
      rmdir "$tmp"
      return 0
    fi
  done
  # Public ZIP from the user's existing GitHub repository (no login needed).
  if has curl && has unzip; then
    say 'Downloading MADA Anywhere from your public GitHub repository...'
    tmp="$(mktemp -d)"
    if curl --fail --location --silent --show-error \
      'https://raw.githubusercontent.com/attack988/MADA-Universal-Games/main/apps/MADA-Anywhere/MADA_Anywhere_v2.zip' \
      -o "$tmp/MADA_Anywhere_v2.zip" && unzip -q "$tmp/MADA_Anywhere_v2.zip" -d "$tmp"; then
      [[ -f "$tmp/MADA_Anywhere/server.py" ]] || { rm -rf "$tmp"; die 'Unexpected Anywhere download.'; }
      [[ ! -e "$ANYWHERE" ]] || die "Incomplete Anywhere folder exists: $ANYWHERE"
      mv "$tmp/MADA_Anywhere" "$ANYWHERE"
      rm -rf "$tmp"
      return 0
    fi
    rm -rf "$tmp"
  fi
  return 1
}
install_apps(){
  has apt-get || die 'Automatic installation currently targets Ubuntu / Debian-based Linux.'
  say 'Installing system requirements. sudo may ask for your Ubuntu password.'
  if [[ "${MADA_SKIP_APT:-0}" != 1 ]]; then
    sudo apt-get update
    sudo apt-get install -y curl unzip nodejs npm python3 python3-venv python3-pip ffmpeg xdg-utils ca-certificates
  fi
  has npm && has node && has python3 && has unzip || die 'Missing npm/node/python3/unzip; install these and retry.'
  local major
  major="$(node -p 'parseInt(process.versions.node.split(".")[0],10)' 2>/dev/null || echo 0)"
  (( major >= 20 )) || die "MADA Study requires Node.js 20 or later. Installed: $(node --version)."
  mkdir -p "$APP_HOME"
  find_study || die 'MADA educational V14 is missing. Download MADA_Smart_Study_v14.zip to ~/Downloads, or use the MADA combined package provided in chat, then run setup again.'
  find_anywhere || die 'MADA Anywhere download failed. Check your internet connection, or use the combined package.'
  say 'Setting up MADA educational V14...'
  (cd "$STUDY" && npm install --omit=dev --no-audit --no-fund)
  say 'Setting up MADA Anywhere v2...'
  if [[ ! -x "$ANYWHERE/.venv/bin/python" ]]; then python3 -m venv "$ANYWHERE/.venv"; fi
  "$ANYWHERE/.venv/bin/python" -m pip install -r "$ANYWHERE/requirements.txt"
  mkdir -p "$HOME/.local/bin" "$HOME/.local/share/mada-suite" "$HOME/.local/share/applications"
  cp "$SELF_DIR/$(basename "${BASH_SOURCE[0]}")" "$HOME/.local/share/mada-suite/mada.sh"
  chmod +x "$HOME/.local/share/mada-suite/mada.sh"
  ln -sfn "$HOME/.local/share/mada-suite/mada.sh" "$HOME/.local/bin/mada"
  cat > "$HOME/.local/share/applications/mada-suite.desktop" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=MADA Study + Anywhere
Name[ar]=مَدَى التعليمي + مَدَى أنوير
Comment=Open MADA Study and MADA Anywhere together
Exec=$HOME/.local/bin/mada start
Icon=applications-education
Terminal=false
Categories=Education;Utility;
EOF
  say 'Setup finished! To open BOTH programs:'
  printf '  %s\n' "$HOME/.local/bin/mada start"
  say 'The old MADA Games application was NOT started, installed or deleted.'
}

start_study(){
  [[ -f "$STUDY/server.cjs" ]] || { err 'MADA Study V14 not installed. Run: mada setup'; return 1; }
  if probe study "$STUDY_PORT"; then say 'MADA Study already running; opening it.'
  elif port_taken "$STUDY_PORT"; then err 'Port 4177 is occupied by an unknown application. Not killing it. Stop that application and retry.'; return 1
  else
    local nbin="$(command -v node || true)"
    [[ -n "$nbin" ]] || { err 'Node.js missing; run setup first.'; return 1; }
    (cd "$STUDY"; nohup "$nbin" server.cjs > "$RUNTIME/study.log" 2>&1 </dev/null & echo "$!" > "$RUNTIME/study.pid")
    if ! wait_for study "$STUDY_PORT" "$RUNTIME/study.pid"; then err "Study failed: see $RUNTIME/study.log"; return 1; fi
    say 'Started MADA educational V14.'
  fi
  open_browser "http://127.0.0.1:$STUDY_PORT"
  say "Study: http://127.0.0.1:$STUDY_PORT"
}
start_anywhere(){
  [[ -f "$ANYWHERE/server.py" ]] || { err 'MADA Anywhere not installed. Run: mada setup'; return 1; }
  if probe anywhere "$ANYWHERE_PORT"; then say 'MADA Anywhere already running; opening it.'
  elif port_taken "$ANYWHERE_PORT"; then err 'Port 8787 is occupied by an unknown application. Not killing it. Stop that application and retry.'; return 1
  else
    local py="$ANYWHERE/.venv/bin/python"
    [[ -x "$py" ]] || { err 'Anywhere Python environment missing; run setup.'; return 1; }
    (cd "$ANYWHERE"; nohup "$py" server.py > "$RUNTIME/anywhere.log" 2>&1 </dev/null & echo "$!" > "$RUNTIME/anywhere.pid")
    if ! wait_for anywhere "$ANYWHERE_PORT" "$RUNTIME/anywhere.pid"; then err "Anywhere failed: see $RUNTIME/anywhere.log"; return 1; fi
    say 'Started MADA Anywhere.'
  fi
  open_browser "http://127.0.0.1:$ANYWHERE_PORT"
  say "Anywhere: http://127.0.0.1:$ANYWHERE_PORT"
}
start_both(){ local errors=0; start_study || errors=1; start_anywhere || errors=1; return "$errors"; }
stop_one(){
  local name="$1" pidfile="$RUNTIME/$1.pid" pid
  [[ -f "$pidfile" ]] || { say "$name was not started by this launcher."; return 0; }
  pid="$(cat "$pidfile")"
  if [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" && say "Stopped $name (PID $pid)." || true
  fi
  rm -f "$pidfile"
}
case "${1:-help}" in
  setup|install) install_apps ;;
  start|all) start_both ;;
  study|education|educational) start_study ;;
  anywhere) start_anywhere ;;
  stop) stop_one study; stop_one anywhere ;;
  status)
    if probe study "$STUDY_PORT"; then say 'MADA Study: active (4177)'; else say 'MADA Study: stopped'; fi
    if probe anywhere "$ANYWHERE_PORT"; then say 'MADA Anywhere: active (8787)'; else say 'MADA Anywhere: stopped'; fi ;;
  help|-h|--help)
    cat <<'HELP'
MADA educational + MADA Anywhere (NO games)
  mada setup     Install both apps on Ubuntu
  mada start     Open Study and Anywhere together
  mada study     Open educational app only
  mada anywhere  Open downloader only
  mada status    Check status
  mada stop      Stop processes launched by this script
HELP
    ;;
  *) die "Unknown command: $1 (use: mada help)" ;;
esac