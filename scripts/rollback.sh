#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${ONYX_PROJECT_DIR:-/home/ec2-user/ONYX}"
BACKEND_DIR="${ONYX_BACKEND_DIR:-$PROJECT_DIR/backend}"
FRONTEND_DIR="${ONYX_FRONTEND_DIR:-$PROJECT_DIR/frontend}"
VENV_DIR="${ONYX_VENV_DIR:-$BACKEND_DIR/venv}"
WEB_ROOT="${ONYX_WEB_ROOT:-/var/www/onyx}"
STATE_DIR="${ONYX_STATE_DIR:-$HOME}"
PREVIOUS_COMMIT_FILE="$STATE_DIR/.onyx_previous_commit"
DEPLOYED_COMMIT_FILE="$STATE_DIR/.onyx_deployed_commit"
DEPLOY_MARKER="$STATE_DIR/.onyx_deploy_in_progress"
FORCE_ROLLBACK="${ONYX_FORCE_ROLLBACK:-0}"
HEALTH_URL="${ONYX_HEALTH_URL:-http://127.0.0.1:8000/health}"

health_ok() {
    curl -fsS "$HEALTH_URL" 2>/dev/null \
        | grep -Eq '"status"[[:space:]]*:[[:space:]]*"healthy"'
}

if [ ! -f "$DEPLOY_MARKER" ] && [ "$FORCE_ROLLBACK" != "1" ]; then
    echo "No deployment in progress; rollback is not required."
    exit 0
fi

if [ ! -f "$PREVIOUS_COMMIT_FILE" ]; then
    echo "No previous commit recorded; cannot roll back."
    exit 1
fi

PREVIOUS_COMMIT="$(cat "$PREVIOUS_COMMIT_FILE")"
CURRENT_COMMIT="$(git -C "$PROJECT_DIR" rev-parse HEAD)"

if [ "$PREVIOUS_COMMIT" = "$CURRENT_COMMIT" ]; then
    echo "Previous and current commits match; rollback is not required."
    rm -f "$DEPLOY_MARKER"
    exit 0
fi

if ! git -C "$PROJECT_DIR" rev-parse --verify "$PREVIOUS_COMMIT^0" >/dev/null 2>&1; then
    echo "Previous commit is not valid in $PROJECT_DIR; cannot roll back."
    exit 1
fi

for required_command in npm sudo rsync systemctl curl; do
    if ! command -v "$required_command" >/dev/null 2>&1; then
        echo "Required command is missing: $required_command; cannot roll back."
        exit 1
    fi
done

if [ ! -x "$VENV_DIR/bin/python" ]; then
    echo "Backend virtual environment is missing; cannot roll back safely."
    exit 1
fi

if ! "$VENV_DIR/bin/python" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 13) else 1)'; then
    echo "Backend virtual environment is older than Python 3.13; cannot roll back safely."
    exit 1
fi

echo "Rolling back $CURRENT_COMMIT -> $PREVIOUS_COMMIT"
git -C "$PROJECT_DIR" reset --hard "$PREVIOUS_COMMIT"

"$VENV_DIR/bin/python" -m pip install -r "$BACKEND_DIR/requirements.txt" \
    --quiet --no-cache-dir

(
    cd "$FRONTEND_DIR"
    npm ci --no-audit --no-fund
    npm run build
)

sudo install -d -m 0755 "$WEB_ROOT"
sudo rsync -a --delete --chown=root:root "$FRONTEND_DIR/dist/" "$WEB_ROOT/"
sudo chmod -R u=rwX,go=rX "$WEB_ROOT"

if [ ! -s "$WEB_ROOT/index.html" ]; then
    echo "Frontend publication is missing $WEB_ROOT/index.html."
    exit 1
fi

sudo nginx -t
sudo systemctl restart onyx-backend
sudo systemctl reload nginx

if ! systemctl is-active --quiet onyx-backend; then
    echo "onyx-backend is not active after rollback."
    exit 1
fi
if ! systemctl is-active --quiet nginx; then
    echo "nginx is not active after rollback."
    exit 1
fi

for attempt in $(seq 1 20); do
    if health_ok; then
        echo "Rollback health check passed after $attempt attempt(s)."
        echo "$PREVIOUS_COMMIT" > "$DEPLOYED_COMMIT_FILE"
        rm -f "$DEPLOY_MARKER"
        exit 0
    fi
    sleep 2
done

echo "Rollback health check failed."
exit 1
