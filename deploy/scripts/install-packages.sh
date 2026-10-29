#!/usr/bin/env bash
#
# Install the application runtime packages on Amazon Linux 2023.
# MongoDB is intentionally not installed here; use Atlas or install MongoDB 7
# separately and set MONGODB_URI in backend/.env.
#
set -euo pipefail

run_as_root() {
    if [ "$(id -u)" -eq 0 ]; then
        "$@"
    else
        sudo "$@"
    fi
}

if [ ! -r /etc/system-release ] || ! grep -qi 'Amazon Linux release 2023' /etc/system-release; then
    echo "ERROR: this script supports Amazon Linux 2023 only." >&2
    exit 1
fi

run_as_root dnf install -y \
    git \
    curl \
    openssl \
    rsync \
    nginx \
    python3.13 \
    python3.13-pip \
    nodejs22 \
    nodejs22-npm \
    certbot \
    python3-certbot-nginx \
    zstd

run_as_root systemctl enable --now certbot-renew.timer

printf '\nInstalled runtime versions:\n'
printf '  Python: %s\n' "$(python3.13 --version 2>&1 || echo missing)"
printf '  Node:   %s\n' "$(node --version 2>&1 || echo missing)"
printf '  npm:    %s\n' "$(npm --version 2>&1 || echo missing)"
printf '  nginx:  %s\n' "$(nginx -v 2>&1 || echo missing)"
printf '  certbot: %s\n' "$(certbot --version 2>&1 || echo missing)"

node_major="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)"
if [ "$node_major" -lt 22 ]; then
    echo "WARNING: node is not version 22. Select the nodejs22 alternative before deploying." >&2
fi

echo
echo "MongoDB is not installed by this script."
echo "Use MongoDB Atlas, or install MongoDB 7, configure authentication, and set"
echo "MONGODB_URI in backend/.env before running bootstrap-app.sh."
