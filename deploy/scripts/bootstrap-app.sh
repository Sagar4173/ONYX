#!/usr/bin/env bash
#
# First-time application bootstrap for the ONYX EC2 host.
# Run as ec2-user after creating backend/.env and frontend/.env.
#
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${ONYX_PROJECT_DIR:-$(cd -- "$SCRIPT_DIR/../.." && pwd)}"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/venv"
WEB_ROOT="${ONYX_WEB_ROOT:-/var/www/onyx}"

if [ "$(id -u)" -eq 0 ]; then
    echo "ERROR: run this script as the deployment user (for example ec2-user), not root." >&2
    exit 1
fi

if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo "ERROR: $BACKEND_DIR/.env is missing." >&2
    echo "Copy deploy/env/backend.production.env.example and fill in the real values." >&2
    exit 1
fi

if [ ! -f "$FRONTEND_DIR/.env" ]; then
    echo "ERROR: $FRONTEND_DIR/.env is missing." >&2
    echo "Copy deploy/env/frontend.production.env.example to $FRONTEND_DIR/.env." >&2
    exit 1
fi

if awk '!/^[[:space:]]*#/ && /REPLACE_WITH_/ { found = 1 } END { exit !found }' "$BACKEND_DIR/.env"; then
    echo "ERROR: $BACKEND_DIR/.env still contains REPLACE_WITH_ placeholders." >&2
    exit 1
fi

if [ -z "${PYTHON_BIN:-}" ]; then
    if command -v python3.13 >/dev/null 2>&1; then
        PYTHON_BIN="python3.13"
    elif command -v python3 >/dev/null 2>&1; then
        PYTHON_BIN="python3"
    else
        echo "ERROR: Python 3.13+ is required." >&2
        exit 1
    fi
fi

if ! "$PYTHON_BIN" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 13) else 1)'; then
    echo "ERROR: Python 3.13+ is required; found $($PYTHON_BIN --version 2>&1)." >&2
    exit 1
fi

if ! command -v node >/dev/null 2>&1 || ! node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 22 ? 0 : 1)'; then
    echo "ERROR: Node.js 22+ is required; found $(node --version 2>&1 || echo missing)." >&2
    exit 1
fi

if [ -x "$VENV_DIR/bin/python" ]; then
    if ! "$VENV_DIR/bin/python" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 13) else 1)'; then
        echo "ERROR: existing virtual environment uses $("$VENV_DIR/bin/python" --version 2>&1); Python 3.13+ is required." >&2
        echo "Remove $VENV_DIR and rerun this script." >&2
        exit 1
    fi
else
    echo "Creating backend virtual environment with $($PYTHON_BIN --version 2>&1)..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

echo "Installing backend dependencies..."
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -r "$BACKEND_DIR/requirements.txt"

echo "Installing frontend dependencies and building..."
(
    cd "$FRONTEND_DIR"
    npm ci --no-audit --no-fund
    npm run build
)

echo "Publishing frontend build to $WEB_ROOT..."
sudo install -d -m 0755 "$WEB_ROOT"
sudo rsync -a --delete --chown=root:root "$FRONTEND_DIR/dist/" "$WEB_ROOT/"
sudo chmod -R u=rwX,go=rX "$WEB_ROOT"

printf '\nBootstrap complete.\n'
printf 'Next: sudo %s/deploy/scripts/install-host-config.sh\n' "$PROJECT_DIR"
