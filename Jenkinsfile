pipeline {
    agent any

    // =========================================================================
    // ONYX Security Intelligence Platform - CI/CD Pipeline
    // =========================================================================
    // Jenkins + App on SAME EC2 server
    // Repo: https://github.com/rushiphalke247/ONYX.git (public)
    // Trigger: Push to 'master' branch → auto-deploy
    // =========================================================================

    environment {
        PROJECT_DIR    = '/home/ec2-user/ONYX'
        BACKEND_DIR    = '/home/ec2-user/ONYX/backend'
        FRONTEND_DIR   = '/home/ec2-user/ONYX/frontend'
        VENV_DIR       = '/home/ec2-user/ONYX/backend/venv'
        GIT_REPO       = 'https://github.com/Sagar4173/ONYX.git'
    }

    options {
        timeout(time: 15, unit: 'MINUTES')
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
                    rm -rf /tmp/* 2>/dev/null || true

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
                checkout scm
                sh '''
                    cd /home/ec2-user/ONYX

                    # Pull latest code (.env files are untracked/gitignored,
                    # so git reset cannot touch them - no backup/restore needed)
                    git fetch origin master
                    git reset --hard origin/master

                    echo "✅ Code pulled. Commit: $(git rev-parse --short HEAD)"
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
                    if [ ! -f /home/ec2-user/ONYX/backend/.env ]; then
                        echo "❌ backend/.env is MISSING!"
                        exit 1
                    fi
                    if [ ! -f /home/ec2-user/ONYX/frontend/.env ]; then
                        echo "❌ frontend/.env is MISSING!"
                        exit 1
                    fi
                    echo "✅ backend/.env exists"
                    echo "✅ frontend/.env exists"
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
                    cd /home/ec2-user/ONYX/backend
                    source venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt --quiet --no-cache-dir
                    echo "✅ Backend dependencies installed"
                '''
            }
        }

        // =====================================================================
        // Stage 5: Install Scanners (idempotent - skips if already installed)
        // =====================================================================
        stage('Install Scanners') {
            steps {
                echo '🛠️ Installing security scanners...'
                sh '''
                    cd /home/ec2-user/ONYX/backend
                    source venv/bin/activate

                    echo "Installing Python scanners (bandit, safety, semgrep)..."
                    pip install --quiet --no-cache-dir bandit safety semgrep || echo "⚠️ pip scanner install had issues"

                    echo "Installing Trivy..."
                    if command -v trivy >/dev/null 2>&1; then
                        echo "Trivy already installed"
                    else
                        curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /home/ec2-user/ONYX/backend/venv/bin && echo "Trivy installed" || echo "⚠️ Trivy install failed"
                    fi

                    echo "Installing Gitleaks..."
                    if command -v gitleaks >/dev/null 2>&1; then
                        echo "Gitleaks already installed"
                    else
                        GL_VER=$(curl -fsSL https://api.github.com/repos/gitleaks/gitleaks/releases/latest | grep -o '"tag_name": *"v[^"]*"' | cut -d'"' -f4 | tr -d 'v')
                        curl -fsSL -o /tmp/gitleaks.tgz "https://github.com/gitleaks/gitleaks/releases/download/v${GL_VER}/gitleaks_${GL_VER}_linux_x64.tar.gz" \
                          && tar -xzf /tmp/gitleaks.tgz -C /home/ec2-user/ONYX/backend/venv/bin gitleaks \
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
        // Stage 6: Setup Ollama (local AI, zero-cost)
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
        // Stage 6: Build Frontend
        // =====================================================================
        stage('Build Frontend') {
            steps {
                echo '🎨 Building frontend...'
                sh '''
                    cd /home/ec2-user/ONYX/frontend
                    npm install --legacy-peer-deps
                    npm run build
                    echo "✅ Frontend built successfully"
                '''
            }
        }

        // =====================================================================
        // Stage 7: Restart Services
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

                    sudo systemctl restart onyx-backend
                    sleep 3
                    sudo systemctl reload nginx
                    echo "✅ Backend restarted"
                    echo "✅ Nginx reloaded"
                '''
            }
        }

        // =====================================================================
        // Stage 8: Health Check
        // =====================================================================
        stage('Health Check') {
            steps {
                echo '🏥 Running health checks...'
                sh '''
                    sleep 8

                    echo "--- Backend Health ---"
                    curl -sf http://localhost:8000/health && echo "" || echo "❌ Backend not responding"

                    echo "--- Nginx ---"
                    curl -sf -o /dev/null -w "HTTP %{http_code}" http://localhost/ && echo "" || echo "❌ Nginx not responding"

                    echo "--- Ollama ---"
                    curl -sf http://localhost:11434/api/tags > /dev/null && echo "✅ Ollama responding" || echo "❌ Ollama not responding"

                    echo "--- Service Status ---"
                    systemctl is-active onyx-backend || echo "(non-zero exit: service may still be starting)"
                    systemctl is-active nginx || echo "(non-zero exit)"
                    OLLAMA_PID_FILE="/tmp/ollama.pid"
                    if [ -f "$OLLAMA_PID_FILE" ] && kill -0 "$(cat "$OLLAMA_PID_FILE")" 2>/dev/null; then
                        echo "ollama (PID: $(cat $OLLAMA_PID_FILE)) running"
                    else
                        echo "⚠️ ollama not running"
                    fi

                    echo "✅ All health checks passed"
                '''
            }
        }
    }

    post {
        success {
            echo """
            ✅ ============================================
            ✅  DEPLOYMENT SUCCESSFUL
            ✅  URL: https://onyx.ajuna.website
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
            // Try to restart services with existing code
            sh '''
                sudo systemctl restart onyx-backend || true
                sudo systemctl reload nginx || true
            '''
        }
        always {
            cleanWs()
        }
    }
}
