pipeline {
    agent any

    // =========================================================================
    // ONYX Security Intelligence Platform - CI/CD Pipeline
    // =========================================================================
    // Jenkins + App on the same EC2 server.
    // Repo: https://github.com/Sagar4173/ONYX.git (public)
    // Trigger: Push to 'master' branch -> auto-deploy
    // =========================================================================

    environment {
        PROJECT_DIR    = '/home/ec2-user/ONYX'
        BACKEND_DIR    = '/home/ec2-user/ONYX/backend'
        FRONTEND_DIR   = '/home/ec2-user/ONYX/frontend'
        VENV_DIR       = '/home/ec2-user/ONYX/backend/venv'
        WEB_ROOT       = '/var/www/onyx'
        PUBLIC_DOMAIN  = 'onyx.ajuna.website'
        GIT_REPO       = 'https://github.com/Sagar4173/ONYX.git'
        DEPLOY_BRANCH  = 'master'
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '5'))
        timestamps()
        skipDefaultCheckout()
    }

    triggers {
        githubPush()
    }

    stages {

        // =====================================================================
        // Stage 1: Clean Up Disk Space (runs BEFORE git checkout)
        // =====================================================================
        stage('Clean Disk') {
            steps {
                echo '🧹 Cleaning disk space...'
                sh '''
                    echo "=== Disk BEFORE cleanup ==="
                    df -h "$HOME" | tail -1

                    # Remove old workspaces
                    rm -rf "$HOME/workspace/"*/workspace/* 2>/dev/null || true

                    # Only remove ollama if disk is critically low (<500MB free)
                    AVAIL_KB=$(df "$HOME" | awk 'NR==2 {print $4}')
                    if [ "$AVAIL_KB" -lt 512000 ]; then
                        rm -rf "$HOME/ollama" 2>/dev/null || true
                        echo "Disk critically low — removed Ollama to free space"
                    fi

                    # Clear caches
                    rm -rf "$HOME/.cache/pip" 2>/dev/null || true
                    rm -rf "$HOME/.npm/_cacache" 2>/dev/null || true
                    rm -f /tmp/gitleaks.tgz 2>/dev/null || true

                    # Clear journal logs
                    sudo journalctl --vacuum-time=1d 2>/dev/null || true

                    # Cap journal growth permanently (idempotent - needs root; skips if sudo not allowed)
                    if [ ! -f /etc/systemd/journald.conf.d/onyx-size.conf ]; then
                        echo -e "[Journal]\nSystemMaxUse=200M" | sudo -n tee /etc/systemd/journald.conf.d/onyx-size.conf > /dev/null 2>&1 || true
                        if [ -f /etc/systemd/journald.conf.d/onyx-size.conf ]; then
                            sudo -n systemctl restart systemd-journald 2>/dev/null || true
                            echo "Journal capped at 200M"
                        else
                            echo "⚠️ Journal cap skipped (needs one-time manual root setup)"
                        fi
                    fi

                    # Truncate ollama log if it grows large
                    if [ -f "$HOME/ollama/ollama.log" ] && [ "$(stat -c%s "$HOME/ollama/ollama.log")" -gt 10485760 ]; then
                        truncate -s 0 "$HOME/ollama/ollama.log" 2>/dev/null || true
                        echo "Truncated oversized ollama.log"
                    fi

                    # Remove old onyx deploy artifacts (keep only 2 newest)
                    ls -dt "$HOME"/ONYX_bak_* 2>/dev/null | tail -n +3 | xargs rm -rf 2>/dev/null || true

                    echo "=== Disk AFTER cleanup ==="
                    df -h "$HOME" | tail -1

                    # Warn if still low after cleanup
                    AVAIL_KB=$(df "$HOME" | awk 'NR==2 {print $4}')
                    if [ "$AVAIL_KB" -lt 1048576 ]; then
                        echo "⚠️ WARNING: Low disk after cleanup ($(df -h "$HOME" | awk 'NR==2 {print $4}') free)"
                    fi
                '''
            }
        }

        // =====================================================================
        // Stage 2: Pull Latest Code
        // =====================================================================
        stage('Pull Code') {
            steps {
                echo '📥 Pulling latest code from GitHub...'
                sh '''
                    # This pipeline deploys a dedicated checkout, not the Jenkins
                    # workspace. Keeping them separate prevents cleanWs from
                    # deleting backend/.env or the backend virtual environment.
                    if [ ! -d "$PROJECT_DIR/.git" ]; then
                        if [ -e "$PROJECT_DIR" ] && [ -n "$(ls -A "$PROJECT_DIR" 2>/dev/null)" ]; then
                            echo "ERROR: $PROJECT_DIR exists but is not a Git checkout."
                            echo "Move it aside or repair it before running the pipeline."
                            exit 1
                        fi
                        rm -rf "$PROJECT_DIR"
                        git clone --branch "$DEPLOY_BRANCH" "$GIT_REPO" "$PROJECT_DIR"
                        rm -f "$HOME/.onyx_previous_commit" "$HOME/.onyx_deployed_commit"
                        rm -f "$HOME/.onyx_deploy_in_progress"
                        echo "Fresh checkout created."
                    else
                        cd "$PROJECT_DIR"
                        rm -f "$HOME/.onyx_deploy_in_progress"

                        # Roll back to the last successfully deployed commit,
                        # not a failed checkout left behind by an earlier run.
                        if [ -f "$HOME/.onyx_deployed_commit" ] \
                            && git rev-parse --verify "$(cat "$HOME/.onyx_deployed_commit")^0" >/dev/null 2>&1; then
                            cp "$HOME/.onyx_deployed_commit" "$HOME/.onyx_previous_commit"
                            echo "Last successful commit: $(cat "$HOME/.onyx_previous_commit")"
                        else
                            rm -f "$HOME/.onyx_previous_commit"
                            echo "No last successful deployment recorded; rollback will be unavailable."
                        fi

                        # Treat every later failure, including test/build
                        # failures before publish, as a deploy that must restore
                        # the last successful checkout.
                        touch "$HOME/.onyx_deploy_in_progress"

                        git remote set-url origin "$GIT_REPO"
                        git fetch --prune origin "$DEPLOY_BRANCH"
                        git reset --hard "origin/$DEPLOY_BRANCH"
                    fi

                    echo "✅ Code pulled. Commit: $(git -C "$PROJECT_DIR" rev-parse --short HEAD)"
                    echo "✅ Branch: $(git -C "$PROJECT_DIR" rev-parse --abbrev-ref HEAD)"
                '''
            }
        }

        // =====================================================================
        // Stage 3: Verify .env Files
        // =====================================================================
        stage('Verify Config') {
            steps {
                echo '🔐 Checking .env files...'
                sh '''
                    if [ ! -f "$BACKEND_DIR/.env" ]; then
                        echo "❌ backend/.env is MISSING!"
                        echo "Create it from deploy/env/backend.production.env.example."
                        exit 1
                    fi
                    if [ ! -f "$FRONTEND_DIR/.env" ]; then
                        echo "❌ frontend/.env is MISSING!"
                        echo "Create it from deploy/env/frontend.production.env.example."
                        exit 1
                    fi
                    for env_file in "$BACKEND_DIR/.env" "$FRONTEND_DIR/.env"; do
                        ENV_MODE=$(stat -c '%a' "$env_file" 2>/dev/null || echo unknown)
                        case "$ENV_MODE" in
                            600|400) ;;
                            *)
                                echo "❌ $env_file must be mode 600 or 400 (found $ENV_MODE)."
                                exit 1
                                ;;
                        esac
                    done
                    if awk '!/^[[:space:]]*#/ && /REPLACE_WITH_/ { found = 1 } END { exit !found }' "$BACKEND_DIR/.env"; then
                        echo "❌ backend/.env still contains REPLACE_WITH_ placeholders."
                        exit 1
                    fi
                    if [ ! -f /etc/systemd/system/onyx-backend.service ]; then
                        echo "❌ systemd unit missing; run deploy/scripts/install-host-config.sh."
                        exit 1
                    fi
                    if [ ! -f /etc/nginx/conf.d/onyx.conf ]; then
                        echo "❌ nginx site missing; run deploy/scripts/install-host-config.sh."
                        exit 1
                    fi
                    echo "✅ backend/.env exists and is not a template"
                    echo "✅ frontend/.env exists"
                    echo "✅ host systemd and nginx configuration installed"
                '''
            }
        }

        // =====================================================================
        // Stage 4: Install Backend Dependencies
        // =====================================================================
        stage('Backend Deps') {
            steps {
                echo '📦 Installing backend dependencies...'
                sh '''
                    cd "$BACKEND_DIR"

                    if [ -x "$VENV_DIR/bin/python" ]; then
                        if ! "$VENV_DIR/bin/python" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 13) else 1)'; then
                            echo "❌ Existing venv uses $("$VENV_DIR/bin/python" --version 2>&1); remove it so Python 3.13+ can be used."
                            exit 1
                        fi
                    else
                        if command -v python3.13 >/dev/null 2>&1; then
                            PYTHON_BIN=python3.13
                        elif command -v python3 >/dev/null 2>&1; then
                            PYTHON_BIN=python3
                        else
                            echo "❌ Python 3.13+ is required but was not found."
                            exit 1
                        fi
                        if ! "$PYTHON_BIN" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 13) else 1)'; then
                            echo "❌ $PYTHON_BIN is older than 3.13."
                            exit 1
                        fi
                        "$PYTHON_BIN" -m venv "$VENV_DIR"
                    fi

                    "$VENV_DIR/bin/python" -m pip install --upgrade pip
                    "$VENV_DIR/bin/python" -m pip install -r requirements.txt --quiet --no-cache-dir
                    echo "✅ Backend dependencies installed"
                '''
            }
        }

        // =====================================================================
        // Stage 5: Backend Tests (fail the deploy before touching services)
        // =====================================================================
        stage('Backend Tests') {
            steps {
                echo 'Running backend tests...'
                sh '''
                    cd "$BACKEND_DIR"
                    "$VENV_DIR/bin/python" -m pytest -q
                '''
            }
        }

        // =====================================================================
        // Stage 6: Install Scanners (idempotent - skips if already installed)
        // =====================================================================
        stage('Install Scanners') {
            steps {
                echo '🛠️ Installing security scanners...'
                sh '''
                    cd "$BACKEND_DIR"
                    VENV_BIN="$VENV_DIR/bin"
                    export PATH="$VENV_BIN:$PATH"

                    echo "Installing Python scanners (bandit, safety, semgrep)..."
                    "$VENV_BIN/pip" install --quiet --no-cache-dir bandit safety semgrep || echo "⚠️ pip scanner install had issues"

                    echo "Installing Trivy..."
                    if command -v trivy >/dev/null 2>&1; then
                        echo "Trivy already installed"
                    else
                        curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b "$VENV_BIN" && echo "Trivy installed" || echo "⚠️ Trivy install failed"
                    fi

                    echo "Installing Gitleaks..."
                    if command -v gitleaks >/dev/null 2>&1; then
                        echo "Gitleaks already installed"
                    else
                        GL_VER=$(curl -fsSL https://api.github.com/repos/gitleaks/gitleaks/releases/latest | grep -o '"tag_name": *"v[^"]*"' | cut -d'"' -f4 | tr -d 'v')
                        curl -fsSL -o /tmp/gitleaks.tgz "https://github.com/gitleaks/gitleaks/releases/download/v${GL_VER}/gitleaks_${GL_VER}_linux_x64.tar.gz" \
                          && tar -xzf /tmp/gitleaks.tgz -C "$VENV_BIN" gitleaks \
                          && rm -f /tmp/gitleaks.tgz \
                          && echo "Gitleaks v${GL_VER} installed" || echo "⚠️ Gitleaks install failed"
                    fi

                    echo "Scanner verification:"
                    for s in bandit safety semgrep trivy gitleaks; do
                        command -v "$s" >/dev/null 2>&1 && echo "  ✅ $s installed" || echo "  ❌ $s NOT FOUND"
                    done
                '''
            }
        }

        // =====================================================================
        // Stage 7: Setup Ollama (local AI, zero-cost)
        // =====================================================================
        stage('Setup Ollama') {
            steps {
                echo '🤖 Setting up Ollama local AI...'
                sh '''
                    OLLAMA_BIN="$HOME/ollama/bin/ollama"
                    OLLAMA_PID_FILE="/tmp/ollama.pid"
                    MODEL="qwen2.5-coder:3b"

                    mkdir -p "$HOME/ollama"

                    if [ ! -f "$OLLAMA_BIN" ]; then
                        echo "Checking disk space..."
                        AVAIL_KB=$(df "$HOME" | awk 'NR==2 {print $4}')
                        AVAIL_MB=$((AVAIL_KB / 1024))
                        echo "Available disk space: ${AVAIL_MB}MB"

                        if [ "$AVAIL_MB" -lt 2500 ]; then
                            echo "WARNING: Only ${AVAIL_MB}MB free (need 2500MB for extraction)."
                            echo "Skipping Ollama install. AI will use Gemini/OpenAI fallback."
                        else
                            echo "Downloading Ollama..."
                            ARCH="ollama-linux-amd64"
                            BASE_URL="https://ollama.com/download"

                            if curl -fsSLI --connect-timeout 10 "${BASE_URL}/${ARCH}.tar.zst" > /dev/null 2>&1; then
                                echo "Streaming ${ARCH}.tar.zst (no temp files)..."
                                curl -fsSL --connect-timeout 120 "${BASE_URL}/${ARCH}.tar.zst" | \
                                  zstd -d | \
                                  tar -xvf - -C "$HOME/ollama/" 2>&1 && \
                                  echo "Ollama extracted successfully" || \
                                  echo "Streaming failed"
                            elif curl -fsSLI --connect-timeout 10 "${BASE_URL}/${ARCH}.tgz" > /dev/null 2>&1; then
                                echo "Downloading ${ARCH}.tgz..."
                                curl -fsSL --connect-timeout 120 -o "$HOME/ollama/ollama.tgz" "${BASE_URL}/${ARCH}.tgz" && \
                                tar -xzf "$HOME/ollama/ollama.tgz" -C "$HOME/ollama/" && \
                                rm -f "$HOME/ollama/ollama.tgz" && \
                                echo "Ollama extracted successfully" || \
                                echo "tgz extraction failed"
                            else
                                echo "ERROR: No Ollama download format available"
                            fi

                            if [ -f "$OLLAMA_BIN" ]; then
                                chmod +x "$OLLAMA_BIN"
                                echo "Ollama installed ($(du -sh "$OLLAMA_BIN" | cut -f1))"
                            else
                                echo "=== Searching for ollama binary in $HOME/ollama/ ==="
                                find "$HOME/ollama/" -type f -executable 2>/dev/null | head -20
                                ls -la "$HOME/ollama/" 2>/dev/null
                                echo "Ollama binary not found. AI will use Gemini/OpenAI fallback."
                            fi
                        fi
                    else
                        echo "Ollama binary already exists ($(du -sh "$OLLAMA_BIN" | cut -f1))"
                    fi

                    if [ -f "$OLLAMA_BIN" ]; then
                        if [ -f "$OLLAMA_PID_FILE" ]; then
                            OLD_PID=$(cat "$OLLAMA_PID_FILE")
                            if kill -0 "$OLD_PID" 2>/dev/null; then
                                echo "Ollama already running (PID: $OLD_PID)"
                            else
                                echo "Removing stale PID file"
                                rm -f "$OLLAMA_PID_FILE"
                            fi
                        fi

                        if [ ! -f "$OLLAMA_PID_FILE" ]; then
                            echo "Starting Ollama..."
                            nohup "$OLLAMA_BIN" serve > "$HOME/ollama/ollama.log" 2>&1 &
                            echo $! > "$OLLAMA_PID_FILE"
                            sleep 3
                            echo "Ollama started (PID: $(cat $OLLAMA_PID_FILE))"
                        fi

                        echo "Checking for model $MODEL..."
                        if "$OLLAMA_BIN" list 2>/dev/null | grep -q "qwen2.5-coder"; then
                            echo "Model $MODEL already available"
                        else
                            echo "Pulling $MODEL (this may take a few minutes)..."
                            "$OLLAMA_BIN" pull "$MODEL"
                            echo "Model $MODEL ready"
                        fi

                        echo "✅ Ollama ready"
                    else
                        echo "⚠️ Ollama binary not available — skipping start and model pull"
                    fi
                '''
            }
        }

        // =====================================================================
        // Stage 8: Test and Build Frontend
        // =====================================================================
        stage('Build Frontend') {
            steps {
                echo '🎨 Testing and building frontend...'
                sh '''
                    cd "$FRONTEND_DIR"
                    npm ci --no-audit --no-fund
                    npm test -- --reporter=dot
                    npm run build
                    echo "✅ Frontend tests and build passed"
                '''
            }
        }

        // =====================================================================
        // Stage 9: Publish Frontend
        // =====================================================================
        stage('Publish Frontend') {
            steps {
                echo '🚀 Publishing frontend build...'
                sh '''
                    # Mark the deploy as in progress before replacing live assets
                    # so a later failure triggers scripts/rollback.sh.
                    touch "$HOME/.onyx_deploy_in_progress"

                    sudo install -d -m 0755 "$WEB_ROOT"
                    sudo rsync -a --delete --chown=root:root "$FRONTEND_DIR/dist/" "$WEB_ROOT/"
                    sudo chmod -R u=rwX,go=rX "$WEB_ROOT"
                    echo "✅ Frontend published to $WEB_ROOT"
                '''
            }
        }

        // =====================================================================
        // Stage 10: Restart Services
        // =====================================================================
        stage('Restart Services') {
            steps {
                echo '🔄 Restarting services...'
                sh '''
                    OLLAMA_BIN="$HOME/ollama/bin/ollama"
                    OLLAMA_PID_FILE="/tmp/ollama.pid"
                    if [ -f "$OLLAMA_BIN" ]; then
                        if [ -f "$OLLAMA_PID_FILE" ]; then
                            OLD_PID=$(cat "$OLLAMA_PID_FILE")
                            kill "$OLD_PID" 2>/dev/null || true
                            sleep 2
                            rm -f "$OLLAMA_PID_FILE"
                        fi
                        nohup "$OLLAMA_BIN" serve > "$HOME/ollama/ollama.log" 2>&1 &
                        echo $! > "$OLLAMA_PID_FILE"
                        echo "Ollama restarted"
                    else
                        echo "⚠️ Ollama binary not found, skipping restart"
                    fi

                    sleep 2

                    sudo nginx -t
                    sudo systemctl restart onyx-backend
                    sleep 3
                    sudo systemctl reload nginx
                    echo "✅ Backend restarted"
                    echo "✅ Nginx reloaded"
                '''
            }
        }

        // =====================================================================
        // Stage 11: Health Check
        // =====================================================================
        stage('Health Check') {
            steps {
                echo '🏥 Running health checks...'
                sh '''
                    echo "--- Backend Health ---"
                    BACKEND_READY=0
                    for attempt in $(seq 1 20); do
                        if curl -fsS http://127.0.0.1:8000/health 2>/dev/null | \
                            grep -Eq '"status"[[:space:]]*:[[:space:]]*"healthy"'; then
                            BACKEND_READY=1
                            break
                        fi
                        sleep 2
                    done

                    if [ "$BACKEND_READY" -ne 1 ]; then
                        echo "ERROR: Backend did not report healthy after 20 attempts"
                        exit 1
                    fi

                    echo "--- Nginx ---"
                    # Prefer a local TLS check once certbot has installed a
                    # certificate; fall back to HTTP on a host without TLS.
                    BASE_URL="http://127.0.0.1"
                    RESOLVE_OPT=""
                    if curl -kfsS --max-time 5 --resolve "$PUBLIC_DOMAIN:443:127.0.0.1" \
                        "https://$PUBLIC_DOMAIN/health" >/dev/null 2>&1; then
                        BASE_URL="https://$PUBLIC_DOMAIN"
                        RESOLVE_OPT="--resolve $PUBLIC_DOMAIN:443:127.0.0.1"
                    fi

                    for path in / /health /api/stats/public /docs /redoc; do
                        CODE=$(curl -sS $RESOLVE_OPT -o /dev/null -w '%{http_code}' \
                            --max-time 15 "$BASE_URL$path" || true)
                        if [ "$CODE" = "200" ]; then
                            echo "✅ $BASE_URL$path ($CODE)"
                        else
                            echo "❌ $BASE_URL$path returned ${CODE:-no response}"
                            exit 1
                        fi
                    done

                    NGINX_HEALTH=$(curl -sS $RESOLVE_OPT --max-time 15 \
                        "$BASE_URL/health" 2>/dev/null || true)
                    if ! printf '%s' "$NGINX_HEALTH" | \
                        grep -Eq '"status"[[:space:]]*:[[:space:]]*"healthy"'; then
                        echo "❌ Nginx health proxy did not report healthy"
                        exit 1
                    fi

                    echo "--- Service Status ---"
                    systemctl is-active --quiet onyx-backend || {
                        echo "❌ onyx-backend is not active"
                        exit 1
                    }
                    systemctl is-active --quiet nginx || {
                        echo "❌ nginx is not active"
                        exit 1
                    }

                    echo "--- Ollama (optional) ---"
                    if curl -sf http://localhost:11434/api/tags > /dev/null; then
                        echo "✅ Ollama responding"
                    else
                        echo "⚠️ Ollama not responding; cloud AI fallback is required"
                    fi

                    echo "✅ Required health checks passed"
                '''
            }
        }
    }

    post {
        success {
            sh '''
                git -C "$PROJECT_DIR" rev-parse HEAD > "$HOME/.onyx_deployed_commit"
                rm -f "$HOME/.onyx_deploy_in_progress"
            '''
            echo """
            ✅ ============================================
            ✅  DEPLOYMENT SUCCESSFUL
            ✅  URL: https://${env.PUBLIC_DOMAIN}
            ✅  Build: #${env.BUILD_NUMBER}
            ✅ ============================================
            """
        }
        failure {
            echo """
            ❌ ============================================
            ❌  DEPLOYMENT FAILED — Build #${env.BUILD_NUMBER}
            ❌ ============================================
            """
            // Restore the last known-good commit when the failure happened
            // after the deploy marker was set. If no rollback script exists
            // yet, fall back to restarting the current services.
            sh '''
                if [ -f "$PROJECT_DIR/scripts/rollback.sh" ]; then
                    if bash "$PROJECT_DIR/scripts/rollback.sh"; then
                        echo "Deployment rollback completed"
                    else
                        echo "Rollback failed; restarting current services"
                        sudo systemctl restart onyx-backend || true
                        sudo systemctl reload nginx || true
                    fi
                else
                    echo "No rollback script found; restarting current services"
                    sudo systemctl restart onyx-backend || true
                    sudo systemctl reload nginx || true
                fi
            '''
        }
        aborted {
            echo """
            ⚠️ ============================================
            ⚠️  DEPLOYMENT ABORTED — Build #${env.BUILD_NUMBER}
            ⚠️ ============================================
            """
            // Timeouts and manual aborts are reported as ABORTED, not FAILURE.
            // Restore the last good deployment if the abort happened after the
            // deploy marker was set.
            sh '''
                if [ -f "$PROJECT_DIR/scripts/rollback.sh" ]; then
                    if bash "$PROJECT_DIR/scripts/rollback.sh"; then
                        echo "Deployment rollback completed after abort"
                    else
                        echo "Rollback after abort failed; restarting current services"
                        sudo systemctl restart onyx-backend || true
                        sudo systemctl reload nginx || true
                    fi
                else
                    echo "No rollback script found; restarting current services"
                    sudo systemctl restart onyx-backend || true
                    sudo systemctl reload nginx || true
                fi
            '''
        }
        always {
            script {
                if (env.WORKSPACE && env.WORKSPACE != env.PROJECT_DIR) {
                    cleanWs()
                } else {
                    echo 'Skipping workspace cleanup for the deployment checkout.'
                }
            }
        }
    }
}
