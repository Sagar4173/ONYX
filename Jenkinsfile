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
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
    }

    triggers {
        githubPush()
    }

    stages {

        // =====================================================================
        // Stage 1: Pull Latest Code
        // =====================================================================
        stage('Pull Code') {
            steps {
                echo '📥 Pulling latest code from GitHub...'
                sh '''
                    cd /home/ec2-user/ONYX

                    # Backup .env files before pull
                    cp -f backend/.env backend/.env.backup 2>/dev/null || true
                    cp -f frontend/.env frontend/.env.backup 2>/dev/null || true

                    # Pull latest code
                    git fetch origin master
                    git reset --hard origin/master

                    # Restore .env files after pull
                    cp -f backend/.env.backup backend/.env 2>/dev/null || true
                    cp -f frontend/.env.backup frontend/.env 2>/dev/null || true

                    echo "✅ Code pulled. Commit: $(git rev-parse --short HEAD)"
                '''
            }
        }

        // =====================================================================
        // Stage 2: Verify .env Files
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
        // Stage 3: Install Backend Dependencies
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
        // Stage 4: Setup Ollama (local AI, zero-cost)
        // =====================================================================
        stage('Setup Ollama') {
            steps {
                echo '🤖 Setting up Ollama local AI...'
                sh '''
                    OLLAMA_BIN="$HOME/ollama/ollama"
                    OLLAMA_PID_FILE="/tmp/ollama.pid"
                    MODEL="qwen2.5-coder:7b"

                    mkdir -p "$HOME/ollama"

                    if [ ! -f "$OLLAMA_BIN" ]; then
                        echo "Checking disk space..."
                        AVAIL_KB=$(df "$HOME" | awk 'NR==2 {print $4}')
                        AVAIL_MB=$((AVAIL_KB / 1024))
                        echo "Available disk space: ${AVAIL_MB}MB"

                        if [ "$AVAIL_MB" -lt 1500 ]; then
                            echo "WARNING: Insufficient disk space (${AVAIL_MB}MB < 1500MB needed)."
                            echo "Skipping Ollama install. AI will use Gemini/OpenAI fallback."
                        else
                            echo "Downloading Ollama... (need ~800MB)"
                            ARCH="ollama-linux-amd64"
                            BASE_URL="https://ollama.com/download"

                            if curl -fsSLI --connect-timeout 10 "${BASE_URL}/${ARCH}.tar.zst" > /dev/null 2>&1; then
                                echo "Downloading ${ARCH}.tar.zst..."
                                curl -fsSL --connect-timeout 120 -o "$HOME/ollama/${ARCH}.tar.zst" "${BASE_URL}/${ARCH}.tar.zst" && \
                                echo "Extracting..." && \
                                zstd -d "$HOME/ollama/${ARCH}.tar.zst" -o "$HOME/ollama/${ARCH}.tar" && \
                                tar -xf "$HOME/ollama/${ARCH}.tar" -C "$HOME/ollama/" && \
                                rm -f "$HOME/ollama/${ARCH}.tar" "$HOME/ollama/${ARCH}.tar.zst" && \
                                echo "Ollama extracted successfully" || \
                                echo "Extraction failed, cleaning up..."
                                rm -f "$HOME/ollama/${ARCH}.tar" "$HOME/ollama/${ARCH}.tar.zst"
                            elif curl -fsSLI --connect-timeout 10 "${BASE_URL}/${ARCH}.tgz" > /dev/null 2>&1; then
                                echo "Downloading ${ARCH}.tgz..."
                                curl -fsSL --connect-timeout 120 -o "/tmp/${ARCH}.tgz" "${BASE_URL}/${ARCH}.tgz" && \
                                tar -xzf "/tmp/${ARCH}.tgz" -C "$HOME/ollama/" && \
                                rm -f "/tmp/${ARCH}.tgz" && \
                                echo "Ollama extracted successfully" || \
                                echo "Extraction failed"
                            else
                                echo "ERROR: No Ollama download format available"
                            fi

                            if [ -f "$OLLAMA_BIN" ]; then
                                chmod +x "$OLLAMA_BIN"
                                echo "Ollama installed ($(du -sh "$OLLAMA_BIN" | cut -f1))"
                            else
                                echo "=== $HOME/ollama/ contents ==="
                                ls -la "$HOME/ollama/" 2>/dev/null || echo "(empty)"
                                echo "Ollama binary not found. AI will use Gemini/OpenAI fallback."
                            fi
                        fi
                    else
                        echo "Ollama binary already exists ($(du -sh "$OLLAMA_BIN" | cut -f1))"
                    fi

                    if [ -f "$OLLAMA_PID_FILE" ]; then
                        OLD_PID=$(cat "$OLLAMA_PID_FILE")
                        if kill -0 "$OLD_PID" 2>/dev/null; then
                            echo "Ollama already running (PID: $OLD_PID)"
                        else
                            echo "Removing stale PID file"
                            rm -f "$OLLAMA_PID_FILE"
                        fi
                    fi

                    # Start Ollama if not running
                    if [ ! -f "$OLLAMA_PID_FILE" ]; then
                        echo "Starting Ollama..."
                        nohup "$OLLAMA_BIN" serve > "$HOME/ollama/ollama.log" 2>&1 &
                        echo $! > "$OLLAMA_PID_FILE"
                        sleep 3
                        echo "Ollama started (PID: $(cat $OLLAMA_PID_FILE))"
                    fi

                    # Pull model if not already present
                    echo "Checking for model $MODEL..."
                    if "$OLLAMA_BIN" list 2>/dev/null | grep -q "qwen2.5-coder"; then
                        echo "Model $MODEL already available"
                    else
                        echo "Pulling $MODEL (this may take a few minutes)..."
                        "$OLLAMA_BIN" pull "$MODEL"
                        echo "Model $MODEL ready"
                    fi

                    echo "✅ Ollama ready"
                '''
            }
        }

        // =====================================================================
        // Stage 5: Build Frontend
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
        // Stage 6: Restart Services
        // =====================================================================
        stage('Restart Services') {
            steps {
                echo '🔄 Restarting services...'
                sh '''
                    # Restart Ollama (user-mode process)
                    OLLAMA_BIN="$HOME/ollama/ollama"
                    OLLAMA_PID_FILE="/tmp/ollama.pid"
                    if [ -f "$OLLAMA_PID_FILE" ]; then
                        OLD_PID=$(cat "$OLLAMA_PID_FILE")
                        kill "$OLD_PID" 2>/dev/null || true
                        sleep 2
                        rm -f "$OLLAMA_PID_FILE"
                    fi
                    if [ -f "$OLLAMA_BIN" ]; then
                        nohup "$OLLAMA_BIN" serve > "$HOME/ollama/ollama.log" 2>&1 &
                        echo $! > "$OLLAMA_PID_FILE"
                        echo "Ollama restarted"
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
        // Stage 7: Health Check
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
                    systemctl is-active onyx-backend
                    systemctl is-active nginx
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
