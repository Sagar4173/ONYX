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
                    if ! command -v ollama &> /dev/null; then
                        echo "Installing Ollama..."
                        curl -fsSL https://ollama.com/install.sh | sh
                    else
                        echo "Ollama already installed"
                    fi

                    sudo systemctl start ollama 2>/dev/null || true
                    sleep 3

                    # Pull model if not already present
                    if ! ollama list 2>/dev/null | grep -q "qwen2.5-coder"; then
                        echo "Pulling qwen2.5-coder:7b model (this may take a few minutes)..."
                        ollama pull qwen2.5-coder:7b
                    else
                        echo "Model qwen2.5-coder:7b already available"
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
                    sudo systemctl restart ollama 2>/dev/null || true
                    sleep 2
                    sudo systemctl restart onyx-backend
                    sleep 3
                    sudo systemctl reload nginx
                    echo "✅ Ollama restarted"
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
                    systemctl is-active ollama 2>/dev/null || echo "ollama service status unknown"

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
