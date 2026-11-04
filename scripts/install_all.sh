#!/usr/bin/env bash
# Install all six Jev toolkit repositories into one virtual environment, in dependency order.
# No prompts. Usage:
#   scripts/install_all.sh [--dir DIR] [--source URL_OR_FOLDER] [--jev-home DIR] [--offline]
# The TypeSafe key is read from the environment variable TYPESAFE_API_KEY if set, else .env gets an empty
# key to fill in later. The key is never printed. --source: before the repositories are public, point it at a
# folder holding local clones. --offline: run the final check with the fake judge (no key, no network).
set -euo pipefail

DIR="$PWD/jev-toolkit-all"
SOURCE="https://github.com/Wrenik"
JEV_HOME_DIR="${JEV_HOME:-$HOME/.jev-toolkit}"
OFFLINE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --dir) DIR="$2"; shift 2 ;;
    --source) SOURCE="$2"; shift 2 ;;
    --jev-home) JEV_HOME_DIR="$2"; shift 2 ;;
    --offline) OFFLINE=1; shift ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

# Dependency order: usage is the base; Scanner is optional for FactCheck; Sources needs FactCheck.
REPOS="Jev-toolkit-usage Jev-toolkit-Scanner Jev-toolkit-Compiler Jev-toolkit-FactCheck Jev-toolkit-Monitor Jev-toolkit-Sources"
PYTHON="${PYTHON:-python3}"

mkdir -p "$DIR"; DIR="$(cd "$DIR" && pwd)"
for r in $REPOS; do
  if [ -d "$DIR/$r/.git" ]; then
    echo "update $r"; git -C "$DIR/$r" pull --ff-only --quiet
  else
    echo "clone  $r"
    if [ -d "$SOURCE" ]; then url="$(cd "$SOURCE" && pwd)/$r"; else url="${SOURCE%/}/$r.git"; fi
    git clone --quiet "$url" "$DIR/$r"
  fi
done

[ -d "$DIR/.venv" ] || "$PYTHON" -m venv "$DIR/.venv"
PY="$DIR/.venv/bin/python"; [ -x "$PY" ] || PY="$DIR/.venv/Scripts/python"
"$PY" -m pip install --quiet --upgrade pip

# The first install pulls the real dependencies (typesafe-sdk). The others use --no-deps because their
# git-URL dependencies on each other are already satisfied by the editable installs above them.
first=1
for r in $REPOS; do
  if [ $first = 1 ]; then "$PY" -m pip install --quiet -e "$DIR/$r"; first=0
  else "$PY" -m pip install --quiet --no-deps -e "$DIR/$r"; fi
done

# JEV_HOME and its .env, without asking anything.
mkdir -p "$JEV_HOME_DIR"
if [ ! -f "$JEV_HOME_DIR/.env" ]; then
  printf 'TYPESAFE_API_KEY=%s\nJEV_MODEL=jev-1.14.0\n' "${TYPESAFE_API_KEY:-}" > "$JEV_HOME_DIR/.env"
  chmod 600 "$JEV_HOME_DIR/.env" 2>/dev/null || true
  if [ -n "${TYPESAFE_API_KEY:-}" ]; then echo "created $JEV_HOME_DIR/.env (key taken from the environment)"
  else echo "created $JEV_HOME_DIR/.env (key empty: fill it in later)"; fi
else
  echo "kept existing $JEV_HOME_DIR/.env"
fi

export JEV_HOME="$JEV_HOME_DIR"
[ $OFFLINE = 1 ] && export JEV_JUDGE=fake
echo; echo "running: python -m jev_core check"
rc=0; "$PY" -m jev_core check || rc=$?
echo; echo "Venv: $DIR/.venv   (activate: source $DIR/.venv/bin/activate, or .venv/Scripts/activate on Windows)"
echo "If JEV_HOME is not the default, add to your shell profile:  export JEV_HOME=\"$JEV_HOME_DIR\""
[ $rc -ne 0 ] && echo "check exited with $rc (no key yet? rerun with --offline to test without one)"
exit $rc
