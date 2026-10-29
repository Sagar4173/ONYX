#!/usr/bin/env bash
#
# Request and install a Let's Encrypt certificate for the ONYX host.
# Run after DNS points at the Elastic IP and the HTTP site is healthy.
#
set -euo pipefail

DOMAIN="${1:-${ONYX_DOMAIN:-}}"
EMAIL="${ONYX_EMAIL:-}"

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: run with sudo so certbot can update nginx." >&2
    exit 1
fi

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "Usage: sudo ONYX_EMAIL=admin@example.com $0 [domain]" >&2
    echo "Example: sudo ONYX_EMAIL=admin@example.com $0 onyx.ajuna.website" >&2
    exit 1
fi

if ! command -v certbot >/dev/null 2>&1; then
    echo "ERROR: certbot is not installed; run install-packages.sh first." >&2
    exit 1
fi

health_ok() {
    curl -fsS --max-time 10 "$1" 2>/dev/null \
        | grep -Eq '"status"[[:space:]]*:[[:space:]]*"healthy"'
}

if ! health_ok "http://$DOMAIN/health" && ! health_ok "https://$DOMAIN/health"; then
    echo "ERROR: the public health endpoint is not reachable and healthy." >&2
    echo "Confirm DNS, the security group, nginx, and the backend before requesting a certificate." >&2
    exit 1
fi

echo "Requesting certificate for $DOMAIN..."
certbot --nginx \
    -d "$DOMAIN" \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    --no-eff-email \
    --keep-until-expiring \
    --redirect

systemctl enable --now certbot-renew.timer
systemctl reload nginx

echo "Checking HTTPS..."
if ! health_ok "https://$DOMAIN/health"; then
    echo "ERROR: certificate was requested but https://$DOMAIN/health is not healthy." >&2
    exit 1
fi

printf '\nTLS enabled for https://%s\n' "$DOMAIN"
printf 'Renewal timer: %s\n' "$(systemctl is-active certbot-renew.timer)"
