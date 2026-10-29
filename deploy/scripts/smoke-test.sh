#!/usr/bin/env bash
#
# Verify the deployed ONYX stack through nginx and directly on the backend.
# Run as ec2-user after install-host-config.sh.
#
set -uo pipefail

PROJECT_DIR="${ONYX_PROJECT_DIR:-/home/ec2-user/ONYX}"
TLS_DOMAIN="${ONYX_TLS_DOMAIN:-}"
if [ -n "${ONYX_BASE_URL:-}" ]; then
    BASE_URL="$ONYX_BASE_URL"
elif [ -n "$TLS_DOMAIN" ]; then
    BASE_URL="https://$TLS_DOMAIN"
else
    BASE_URL="http://127.0.0.1"
fi
TIMEOUT="${ONYX_CURL_TIMEOUT:-10}"

FAILURES=0
WARNINGS=0

pass() { printf 'PASS  %s\n' "$*"; }
warn() { printf 'WARN  %s\n' "$*"; WARNINGS=$((WARNINGS + 1)); }
fail() { printf 'FAIL  %s\n' "$*"; FAILURES=$((FAILURES + 1)); }

check_status() {
    local name="$1"
    local url="$2"
    local code
    code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time "$TIMEOUT" "$url" 2>/dev/null || true)"
    if [ "$code" = "200" ]; then
        pass "$name ($code)"
    else
        fail "$name returned ${code:-no response}"
    fi
}

printf 'ONYX smoke test\n'
printf 'Base URL: %s\n' "$BASE_URL"
printf 'Commit:   %s\n\n' "$(git -C "$PROJECT_DIR" rev-parse --short HEAD 2>/dev/null || echo unknown)"

for service_name in onyx-backend nginx; do
    if systemctl is-active --quiet "$service_name"; then
        pass "service active: $service_name"
    else
        fail "service inactive: $service_name"
    fi
done

health_body="$(curl -fsS --max-time "$TIMEOUT" http://127.0.0.1:8000/health 2>/dev/null || true)"
if printf '%s' "$health_body" | grep -Eq '"status"[[:space:]]*:[[:space:]]*"healthy"'; then
    pass "backend health endpoint reports healthy"
elif [ -n "$health_body" ]; then
    fail "backend health endpoint did not report healthy"
else
    fail "backend health endpoint did not respond"
fi

check_status "nginx root" "$BASE_URL/"
check_status "nginx health proxy" "$BASE_URL/health"
check_status "public stats API" "$BASE_URL/api/stats/public"
check_status "API documentation" "$BASE_URL/docs"
check_status "API ReDoc" "$BASE_URL/redoc"
check_status "OpenAPI schema" "$BASE_URL/openapi.json"

headers="$(curl -fsS -D - -o /dev/null --max-time "$TIMEOUT" "$BASE_URL/" 2>/dev/null || true)"
if printf '%s' "$headers" | grep -qi '^X-Content-Type-Options:[[:space:]]*nosniff'; then
    pass "security header: X-Content-Type-Options"
else
    fail "missing security header: X-Content-Type-Options"
fi

if printf '%s' "$headers" | grep -qi '^X-Frame-Options:[[:space:]]*DENY'; then
    pass "security header: X-Frame-Options"
else
    fail "missing security header: X-Frame-Options"
fi

spa_code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time "$TIMEOUT" "$BASE_URL/dashboard" 2>/dev/null || true)"
if [ "$spa_code" = "200" ]; then
    pass "SPA fallback (/dashboard)"
else
    fail "SPA fallback (/dashboard) returned ${spa_code:-no response}"
fi

if [ -n "$TLS_DOMAIN" ]; then
    check_status "HTTPS root" "https://$TLS_DOMAIN/"
    check_status "HTTPS health" "https://$TLS_DOMAIN/health"
    redirect_code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time "$TIMEOUT" "http://$TLS_DOMAIN/" 2>/dev/null || true)"
    if [ "$redirect_code" = "301" ] || [ "$redirect_code" = "308" ]; then
        pass "HTTP redirects to HTTPS ($redirect_code)"
    else
        warn "HTTP did not redirect to HTTPS (returned ${redirect_code:-no response})"
    fi
else
    warn "HTTPS checks skipped; set ONYX_TLS_DOMAIN after enabling TLS"
fi

printf '\nSummary: %d failure(s), %d warning(s)\n' "$FAILURES" "$WARNINGS"
if [ "$FAILURES" -gt 0 ]; then
    exit 1
fi
