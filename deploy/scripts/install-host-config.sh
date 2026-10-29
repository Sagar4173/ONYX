#!/usr/bin/env bash
#
# Install the systemd unit and host nginx site for ONYX.
# Run with sudo after backend/.env exists and bootstrap-app.sh has completed.
#
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
PROJECT_DIR="${ONYX_PROJECT_DIR:-/home/ec2-user/ONYX}"
SERVICE_USER="${ONYX_USER:-ec2-user}"
DOMAIN="${ONYX_DOMAIN:-onyx.ajuna.website}"
SYSTEMD_UNIT="${ONYX_SYSTEMD_UNIT:-/etc/systemd/system/onyx-backend.service}"
NGINX_CONF="${ONYX_NGINX_CONF:-/etc/nginx/conf.d/onyx.conf}"
SYSTEMD_TEMPLATE="$DEPLOY_DIR/systemd/onyx-backend.service.template"
NGINX_TEMPLATE="$DEPLOY_DIR/nginx/onyx.conf.template"

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: run with sudo so the systemd unit and nginx site can be installed." >&2
    exit 1
fi

if [ "$SERVICE_USER" = "root" ]; then
    echo "ERROR: refusing to run the backend as root; set ONYX_USER to an unprivileged user." >&2
    exit 1
fi

if ! id "$SERVICE_USER" >/dev/null 2>&1; then
    echo "ERROR: service user does not exist: $SERVICE_USER" >&2
    exit 1
fi

if [ ! -f "$PROJECT_DIR/backend/.env" ]; then
    echo "ERROR: backend/.env is missing." >&2
    exit 1
fi

if awk '!/^[[:space:]]*#/ && /REPLACE_WITH_/ { found = 1 } END { exit !found }' "$PROJECT_DIR/backend/.env"; then
    echo "ERROR: backend/.env still contains REPLACE_WITH_ placeholders." >&2
    exit 1
fi

if [ ! -x "$PROJECT_DIR/backend/venv/bin/uvicorn" ]; then
    echo "ERROR: backend virtual environment is incomplete; run bootstrap-app.sh first." >&2
    exit 1
fi

if ! "$PROJECT_DIR/backend/venv/bin/python" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 13) else 1)'; then
    echo "ERROR: backend virtual environment uses $("$PROJECT_DIR/backend/venv/bin/python" --version 2>&1); remove it and rerun bootstrap-app.sh." >&2
    exit 1
fi

PRESERVE_NGINX=0
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ] \
    && [ "${ONYX_FORCE_NGINX:-0}" != "1" ]; then
    if [ ! -f "$NGINX_CONF" ]; then
        echo "ERROR: a certificate exists but $NGINX_CONF is missing." >&2
        echo "Set ONYX_FORCE_NGINX=1, rerun this script, and then rerun" >&2
        echo "enable-tls.sh to restore HTTPS." >&2
        exit 1
    fi
    if grep -Eq '^[[:space:]]*listen[[:space:]]+[^;]*443[[:space:]]+ssl' "$NGINX_CONF" \
        && grep -Eq '^[[:space:]]*ssl_certificate[[:space:]]' "$NGINX_CONF"; then
        PRESERVE_NGINX=1
    else
        echo "ERROR: a certificate exists but $NGINX_CONF does not contain an" >&2
        echo "SSL listener. Set ONYX_FORCE_NGINX=1, rerun this script, and then" >&2
        echo "rerun enable-tls.sh to restore HTTPS." >&2
        exit 1
    fi
fi

backup_file() {
    if [ -f "$1" ]; then
        cp -a "$1" "$1.bak.$(date +%Y%m%d%H%M%S)"
    fi
}

render_template() {
    sed \
        -e "s|__ONYX_PROJECT_DIR__|$PROJECT_DIR|g" \
        -e "s|__ONYX_USER__|$SERVICE_USER|g" \
        -e "s|__ONYX_DOMAIN__|$DOMAIN|g" \
        "$1"
}

health_ok() {
    curl -fsS http://127.0.0.1:8000/health 2>/dev/null \
        | grep -Eq '"status"[[:space:]]*:[[:space:]]*"healthy"'
}

echo "Installing systemd unit..."
backup_file "$SYSTEMD_UNIT"
render_template "$SYSTEMD_TEMPLATE" > "$SYSTEMD_UNIT"
chmod 0644 "$SYSTEMD_UNIT"

echo "Installing nginx site..."
install -d -m 0755 /var/www/onyx /var/www/certbot
NGINX_BACKUP=""
if [ "$PRESERVE_NGINX" -eq 1 ]; then
    echo "TLS certificate exists; preserving certbot-managed $NGINX_CONF."
    echo "Set ONYX_FORCE_NGINX=1 only if you will rerun enable-tls.sh afterwards."
else
    if [ -f "$NGINX_CONF" ]; then
        NGINX_BACKUP="$NGINX_CONF.bak.$(date +%Y%m%d%H%M%S)"
        cp -a "$NGINX_CONF" "$NGINX_BACKUP"
    fi
    render_template "$NGINX_TEMPLATE" > "$NGINX_CONF"
    chmod 0644 "$NGINX_CONF"
fi

if ! nginx -t; then
    if [ -n "$NGINX_BACKUP" ] && [ -f "$NGINX_BACKUP" ]; then
        cp -a "$NGINX_BACKUP" "$NGINX_CONF"
        echo "ERROR: nginx configuration test failed; restored $NGINX_CONF from $NGINX_BACKUP." >&2
    elif [ "$PRESERVE_NGINX" -eq 0 ]; then
        rm -f "$NGINX_CONF"
        echo "ERROR: nginx configuration test failed; removed the invalid new site." >&2
    else
        echo "ERROR: nginx configuration test failed; the existing site was not changed." >&2
    fi
    exit 1
fi

systemctl daemon-reload
systemctl enable onyx-backend
systemctl restart onyx-backend

if systemctl is-active --quiet nginx; then
    systemctl reload nginx
else
    systemctl enable --now nginx
fi

echo "Waiting for the backend health endpoint..."
HEALTHY=0
for attempt in $(seq 1 20); do
    if health_ok; then
        echo "Backend health check passed after $attempt attempt(s)."
        HEALTHY=1
        break
    fi
    sleep 2
done

if [ "$HEALTHY" -ne 1 ]; then
    echo "ERROR: backend did not report healthy. Inspect:" >&2
    echo "  journalctl -u onyx-backend -n 100 --no-pager" >&2
    exit 1
fi

printf '\nHost configuration installed for %s.\n' "$DOMAIN"
printf 'Run %s/deploy/scripts/smoke-test.sh to verify the full stack.\n' "$PROJECT_DIR"
