#!/usr/bin/env bash
#
# Read-only readiness check for the ONYX Amazon Linux 2023 host.
# Run as the deployment user (ec2-user), not as root.
#
set -uo pipefail

PROJECT_DIR="${ONYX_PROJECT_DIR:-/home/ec2-user/ONYX}"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
DOMAIN="${ONYX_DOMAIN:-onyx.ajuna.website}"

ERRORS=0
WARNINGS=0

pass() { printf 'PASS  %s\n' "$*"; }
warn() { printf 'WARN  %s\n' "$*"; WARNINGS=$((WARNINGS + 1)); }
fail() { printf 'FAIL  %s\n' "$*"; ERRORS=$((ERRORS + 1)); }

env_value() {
    local file="$1"
    local key="$2"
    grep -m1 "^${key}=" "$file" 2>/dev/null | cut -d= -f2- || true
}

check_env_mode() {
    local label="$1"
    local file="$2"
    local mode
    mode="$(stat -c '%a' "$file" 2>/dev/null || echo unknown)"
    case "$mode" in
        600|400)
            pass "$label permissions: $mode"
            ;;
        *)
            fail "$label must be mode 600 or 400 (found $mode); run chmod 600 $file"
            ;;
    esac
}

check_command() {
    local name="$1"
    if command -v "$name" >/dev/null 2>&1; then
        pass "command available: $name"
    else
        fail "missing command: $name"
    fi
}

printf 'ONYX deployment preflight\n'
printf 'Project: %s\n' "$PROJECT_DIR"
printf 'Domain:  %s\n\n' "$DOMAIN"

if [ -r /etc/system-release ] && grep -qi 'Amazon Linux release 2023' /etc/system-release; then
    pass "operating system: $(cat /etc/system-release)"
else
    warn "expected Amazon Linux 2023; found: $(cat /etc/system-release 2>/dev/null || uname -a)"
fi

for command_name in git curl openssl rsync nginx systemctl certbot; do
    check_command "$command_name"
done

PYTHON_BIN=""
if command -v python3.13 >/dev/null 2>&1; then
    PYTHON_BIN="python3.13"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
fi

if [ -z "$PYTHON_BIN" ]; then
    fail "Python 3.13+ is not installed"
elif "$PYTHON_BIN" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 13) else 1)' 2>/dev/null; then
    pass "Python 3.13+: $($PYTHON_BIN --version 2>&1)"
else
    fail "Python 3.13+ required; found $($PYTHON_BIN --version 2>&1)"
fi

if ! command -v node >/dev/null 2>&1; then
    fail "Node.js is not installed"
elif node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 22 ? 0 : 1)'; then
    pass "Node.js 22+: $(node --version)"
else
    fail "Node.js 22+ required; found $(node --version)"
fi

if command -v npm >/dev/null 2>&1; then
    pass "npm available: $(npm --version)"
else
    fail "npm is not installed"
fi

if [ -d "$PROJECT_DIR/.git" ]; then
    pass "git checkout present: $PROJECT_DIR"
else
    fail "git checkout missing: $PROJECT_DIR"
fi

if [ -f "$BACKEND_DIR/.env" ]; then
    pass "backend environment file present"
    check_env_mode "backend/.env" "$BACKEND_DIR/.env"

    if awk '!/^[[:space:]]*#/ && /REPLACE_WITH_/ { found = 1 } END { exit !found }' "$BACKEND_DIR/.env"; then
        fail "backend environment file still contains REPLACE_WITH_ placeholders"
    fi

    allow_registration="$(env_value "$BACKEND_DIR/.env" ALLOW_REGISTRATION)"
    case "${allow_registration:-true}" in
        false|False|FALSE)
            pass "self-service registration disabled"
            ;;
        *)
            warn "ALLOW_REGISTRATION is enabled or unset; disable it after creating the initial administrator"
            ;;
    esac

    secret_key="$(env_value "$BACKEND_DIR/.env" SECRET_KEY)"
    if [ "${#secret_key}" -ge 32 ]; then
        pass "SECRET_KEY is at least 32 characters"
    else
        fail "SECRET_KEY is missing or shorter than 32 characters"
    fi

    mongodb_uri="$(env_value "$BACKEND_DIR/.env" MONGODB_URI)"
    case "$mongodb_uri" in
        ""|*REPLACE_WITH*|*USERNAME:PASSWORD*)
            fail "MONGODB_URI is missing or still a placeholder"
            ;;
        *)
            pass "MONGODB_URI is configured"
            ;;
    esac

    frontend_url="$(env_value "$BACKEND_DIR/.env" FRONTEND_URL)"
    case "$frontend_url" in
        "https://$DOMAIN"|"https://$DOMAIN/"*)
            pass "FRONTEND_URL matches $DOMAIN"
            ;;
        "")
            fail "FRONTEND_URL is not set"
            ;;
        *)
            warn "FRONTEND_URL is not https://$DOMAIN (found: $frontend_url)"
            ;;
    esac

    cors_origins="$(env_value "$BACKEND_DIR/.env" CORS_ORIGINS)"
    case "$cors_origins" in
        *"$DOMAIN"*)
            pass "CORS_ORIGINS includes $DOMAIN"
            ;;
        "")
            fail "CORS_ORIGINS is not set"
            ;;
        *)
            warn "CORS_ORIGINS does not include $DOMAIN"
            ;;
    esac

    environment_value="$(env_value "$BACKEND_DIR/.env" ENVIRONMENT)"
    if [ "$environment_value" = "production" ]; then
        pass "ENVIRONMENT=production"
    else
        warn "ENVIRONMENT is not production (found: ${environment_value:-unset})"
    fi

    debug_value="$(env_value "$BACKEND_DIR/.env" DEBUG)"
    if [ "$debug_value" = "false" ]; then
        pass "DEBUG=false"
    else
        warn "DEBUG is not false (found: ${debug_value:-unset})"
    fi

    webhook_secret="$(env_value "$BACKEND_DIR/.env" WEBHOOK_SECRET)"
    if [ "${#webhook_secret}" -ge 32 ]; then
        pass "WEBHOOK_SECRET is configured"
    else
        warn "WEBHOOK_SECRET is missing or short; webhook endpoints will fail closed"
    fi
else
    fail "backend environment file missing: $BACKEND_DIR/.env"
fi

if [ -f "$FRONTEND_DIR/.env" ]; then
    pass "frontend environment file present"
    check_env_mode "frontend/.env" "$FRONTEND_DIR/.env"
    vite_api_url="$(env_value "$FRONTEND_DIR/.env" VITE_API_URL)"
    if [ "$vite_api_url" = "/api" ]; then
        pass "VITE_API_URL=/api"
    else
        warn "VITE_API_URL is not /api (found: ${vite_api_url:-unset})"
    fi
else
    fail "frontend environment file missing: $FRONTEND_DIR/.env"
fi

if [ -x "$BACKEND_DIR/venv/bin/python" ]; then
    pass "backend virtual environment present"
    if "$BACKEND_DIR/venv/bin/python" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 13) else 1)'; then
        pass "virtual environment Python 3.13+"
    else
        fail "virtual environment is older than Python 3.13"
    fi
else
    fail "backend virtual environment missing; run deploy/scripts/bootstrap-app.sh"
fi

if [ -f "$FRONTEND_DIR/dist/index.html" ]; then
    pass "frontend production build present"
else
    warn "frontend production build missing; run deploy/scripts/bootstrap-app.sh"
fi

if [ -f /var/www/onyx/index.html ]; then
    pass "nginx document root populated: /var/www/onyx"
else
    warn "nginx document root is empty; run deploy/scripts/bootstrap-app.sh"
fi

if [ -f /etc/systemd/system/onyx-backend.service ]; then
    pass "systemd unit installed"
else
    warn "systemd unit missing; run deploy/scripts/install-host-config.sh"
fi

if [ -f /etc/nginx/conf.d/onyx.conf ]; then
    pass "nginx site installed"
else
    warn "nginx site missing; run deploy/scripts/install-host-config.sh"
fi

if sudo -n true >/dev/null 2>&1; then
    pass "passwordless sudo available"
else
    warn "passwordless sudo not available; Jenkins needs it for service restart and rsync"
fi

available_kb="$(df -Pk "$PROJECT_DIR" 2>/dev/null | awk 'NR==2 {print $4}')"
if [ -n "$available_kb" ] && [ "$available_kb" -ge 2097152 ]; then
    pass "at least 2 GiB free disk space"
else
    warn "less than 2 GiB free disk space"
fi

memory_kb="$(awk '/MemTotal/ {print $2}' /proc/meminfo 2>/dev/null || true)"
if [ -n "$memory_kb" ] && [ "$memory_kb" -ge 7340032 ]; then
    pass "at least 7 GiB RAM"
else
    warn "less than 7 GiB RAM; local Ollama may not fit"
fi

printf '\nSummary: %d failure(s), %d warning(s)\n' "$ERRORS" "$WARNINGS"
if [ "$ERRORS" -gt 0 ]; then
    exit 1
fi
