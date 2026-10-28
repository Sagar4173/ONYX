#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${ONYX_PROJECT_DIR:-/home/ec2-user/ONYX}"
BACKEND_DIR="${ONYX_BACKEND_DIR:-$PROJECT_DIR/backend}"
FRONTEND_DIR="${ONYX_FRONTEND_DIR:-$PROJECT_DIR/frontend}"
VENV_DIR="${ONYX_VENV_DIR:-$BACKEND_DIR/venv}"
STATE_DIR="${ONYX_STATE_DIR:-$HOME}"
PREVIOUS_COMMIT_FILE="$STATE_DIR/.onyx_previous_commit"
DEPLOY_MARKER="$STATE_DIR/.onyx_deploy_in_progress"
HEALTH_URL="${ONYX_HEALTH_URL:-http://localhost:8000/health}"

if [ ! -f "$DEPLOY_MARKER" ]; then
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

echo "Rolling back $CURRENT_COMMIT -> $PREVIOUS_COMMIT"
git -C "$PROJECT_DIR" reset --hard "$PREVIOUS_COMMIT"

if [ -x "$VENV_DIR/bin/python" ]; then
    "$VENV_DIR/bin/python" -m pip install -r "$BACKEND_DIR/requirements.txt" \
        --quiet --no-cache-dir
fi

(
    cd "$FRONTEND_DIR"
    npm install --legacy-peer-deps
    npm run build
)

sudo systemctl restart onyx-backend
sudo systemctl reload nginx

for attempt in $(seq 1 20); do
    if curl -fsS "$HEALTH_URL" > /dev/null; then
        echo "Rollback health check passed after $attempt attempt(s)."
        rm -f "$DEPLOY_MARKER"
        exit 0
    fi
    sleep 2
done

echo "Rollback health check failed."
exit 1
