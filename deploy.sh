#!/bin/bash

# SecureDevOps AI Platform - Complete Deployment Script
# This script deploys the full platform including frontend, backend, and database

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PLATFORM_NAME="SecureDevOps AI Platform"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$PROJECT_DIR/.env"
BACKUP_DIR="$PROJECT_DIR/backups"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

header() {
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════${NC}"
}

# Check requirements
check_requirements() {
    log "Checking system requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
    fi
    
    local docker_version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    info "Docker version: $docker_version"
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        local compose_version=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
        info "Docker Compose version: $compose_version"
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        local compose_version=$(docker compose version --short)
        info "Docker Compose (plugin) version: $compose_version"
        COMPOSE_CMD="docker compose"
    else
        error "Docker Compose is not installed. Please install Docker Compose first."
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running. Please start Docker first."
    fi
    
    # Check disk space (minimum 5GB)
    local available_space=$(df "$PROJECT_DIR" | awk 'NR==2 {print $4}')
    local required_space=5242880  # 5GB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        warn "Low disk space. Recommended: 5GB+, Available: $(($available_space/1024/1024))GB"
    else
        info "Disk space: $(($available_space/1024/1024))GB available"
    fi
    
    # Check memory (minimum 4GB)
    local total_memory=$(free -m | awk 'NR==2{print $2}')
    if [ "$total_memory" -lt 4096 ]; then
        warn "Low memory. Recommended: 4GB+, Available: ${total_memory}MB"
    else
        info "Memory: ${total_memory}MB available"
    fi
    
    success "System requirements check passed"
}

# Create environment file
create_env_file() {
    log "Setting up environment configuration..."
    
    if [[ ! -f "$ENV_FILE" ]]; then
        log "Creating .env file from .env.example..."
        cp ".env.example" "$ENV_FILE"
        
        # Generate secure random values
        local secret_key=$(openssl rand -hex 32 2>/dev/null || head -c 32 /dev/urandom | xxd -p -c 32)
        local mongo_password=$(openssl rand -base64 32 2>/dev/null || head -c 24 /dev/urandom | base64)
        local redis_password=$(openssl rand -base64 32 2>/dev/null || head -c 24 /dev/urandom | base64)
        
        # Update environment file with generated values
        sed -i.bak "s/SECRET_KEY=.*/SECRET_KEY=$secret_key/" "$ENV_FILE"
        sed -i.bak "s/MONGO_PASSWORD=.*/MONGO_PASSWORD=$mongo_password/" "$ENV_FILE"
        sed -i.bak "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=$redis_password/" "$ENV_FILE"
        
        # Clean up backup file
        rm -f "$ENV_FILE.bak"
        
        warn "Created .env file with generated secrets."
        warn "Please update OPENAI_API_KEY and other settings before proceeding."
        warn "Edit $ENV_FILE to configure your environment."
        
        echo
        info "Required configuration:"
        echo "  OPENAI_API_KEY - Get from https://platform.openai.com/api-keys"
        echo "  ALLOWED_ORIGINS - Add your frontend domain"
        echo "  SLACK_WEBHOOK_URL - Optional: Slack notifications"
        echo "  TEAMS_WEBHOOK_URL - Optional: Teams notifications"
        echo
        
        read -p "Press Enter after updating the .env file to continue, or Ctrl+C to exit..."
    else
        info "Environment file already exists: $ENV_FILE"
    fi
}

# Validate environment
validate_env() {
    log "Validating environment configuration..."
    
    if [[ ! -f "$ENV_FILE" ]]; then
        error "Environment file not found: $ENV_FILE"
    fi
    
    source "$ENV_FILE"
    
    # Check critical settings
    local validation_errors=0
    
    if [[ -z "$SECRET_KEY" || "$SECRET_KEY" == "your-super-secret-key-change-in-production-make-it-long-and-random" ]]; then
        error "SECRET_KEY is not configured or using default value"
        validation_errors=$((validation_errors + 1))
    fi
    
    if [[ -z "$MONGO_PASSWORD" || "$MONGO_PASSWORD" == "securepass123" ]]; then
        warn "MONGO_PASSWORD is using default value - consider changing for production"
    fi
    
    if [[ -z "$OPENAI_API_KEY" || "$OPENAI_API_KEY" == "sk-your-openai-api-key-here" ]]; then
        warn "OPENAI_API_KEY not configured. AI analysis features will be disabled."
        read -p "Continue without AI features? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "Please configure OPENAI_API_KEY in .env file"
        fi
    fi
    
    if [[ $validation_errors -gt 0 ]]; then
        error "Environment validation failed. Please fix the configuration issues."
    fi
    
    success "Environment validation completed"
}

# Pull latest images
pull_images() {
    log "Pulling latest base images..."
    
    docker pull mongo:7.0
    docker pull redis:7-alpine
    docker pull node:18-alpine
    docker pull nginx:alpine
    docker pull python:3.11-slim
    
    success "Base images updated"
}

# Build images
build_images() {
    log "Building Docker images..."
    
    # Build backend
    log "Building backend image..."
    docker build -t securedevops-backend:latest \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        --build-arg VERSION="1.0.0" \
        ./backend/
    
    # Build frontend
    log "Building frontend image..."
    docker build -t securedevops-frontend:latest \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        --build-arg VERSION="1.0.0" \
        ./frontend/
    
    success "Docker images built successfully"
}

# Setup directories
setup_directories() {
    log "Setting up directories..."
    
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$PROJECT_DIR/logs"
    mkdir -p "$PROJECT_DIR/data/mongodb"
    mkdir -p "$PROJECT_DIR/data/redis"
    mkdir -p "$PROJECT_DIR/ssl"
    
    # Set proper permissions
    chmod 755 "$BACKUP_DIR"
    chmod 755 "$PROJECT_DIR/logs"
    
    success "Directories created"
}

# Stop existing services
stop_services() {
    log "Stopping existing services..."
    
    if [ -f "$COMPOSE_FILE" ]; then
        $COMPOSE_CMD -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
        
        # Clean up any remaining containers
        docker ps -a --filter "name=securedevops" --format "{{.Names}}" | xargs -r docker rm -f 2>/dev/null || true
    fi
    
    success "Existing services stopped"
}

# Deploy services
deploy_services() {
    log "Deploying services..."
    
    # Deploy with Docker Compose
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d --remove-orphans
    
    success "Services deployed"
}

# Wait for services
wait_for_services() {
    log "Waiting for services to be ready..."
    
    local max_attempts=60
    local attempt=0
    
    # Wait for MongoDB
    log "Waiting for MongoDB..."
    while [[ $attempt -lt $max_attempts ]]; do
        if $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T mongodb mongosh --quiet --eval "db.adminCommand('ping')" &>/dev/null; then
            success "MongoDB is ready"
            break
        fi
        
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    if [[ $attempt -eq $max_attempts ]]; then
        error "MongoDB failed to start within timeout"
    fi
    
    # Wait for Backend
    log "Waiting for Backend API..."
    attempt=0
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -f http://localhost:8000/health &>/dev/null; then
            success "Backend service is ready"
            break
        fi
        
        attempt=$((attempt + 1))
        echo -n "."
        sleep 3
    done
    
    if [[ $attempt -eq $max_attempts ]]; then
        error "Backend service failed to start within timeout"
    fi
    
    # Wait for Frontend
    log "Waiting for Frontend..."
    attempt=0
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -f http://localhost/health &>/dev/null; then
            success "Frontend service is ready"
            break
        fi
        
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    if [[ $attempt -eq $max_attempts ]]; then
        error "Frontend service failed to start within timeout"
    fi
    
    # Wait for Redis
    log "Waiting for Redis..."
    attempt=0
    while [[ $attempt -lt $max_attempts ]]; do
        if $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T redis redis-cli ping &>/dev/null; then
            success "Redis is ready"
            break
        fi
        
        attempt=$((attempt + 1))
        echo -n "."
        sleep 1
    done
    
    if [[ $attempt -eq $max_attempts ]]; then
        warn "Redis may not be fully ready, but continuing..."
    fi
}

# Initialize database
init_database() {
    log "Verifying database initialization..."
    
    # The init script runs automatically, just verify it worked
    local collections_count=$($COMPOSE_CMD -f "$COMPOSE_FILE" exec -T mongodb mongosh securedevops --quiet --eval "db.getCollectionNames().length" 2>/dev/null || echo "0")
    
    if [[ "$collections_count" -gt 5 ]]; then
        success "Database initialization completed ($collections_count collections)"
    else
        warn "Database may not be fully initialized. Collections found: $collections_count"
    fi
}

# Create backup script
create_backup_script() {
    log "Creating backup script..."
    
    cat > "$PROJECT_DIR/backup.sh" << 'EOF'
#!/bin/bash

# Automated backup script for SecureDevOps Platform

set -e

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Determine compose command
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "Error: Docker Compose not found"
    exit 1
fi

mkdir -p "$BACKUP_DIR"

echo "Creating backup: $DATE"

# Source environment
if [ -f ".env" ]; then
    source .env
fi

# Backup MongoDB
echo "Backing up MongoDB..."
$COMPOSE_CMD exec -T mongodb mongodump \
    --username admin \
    --password "${MONGO_PASSWORD:-securepass123}" \
    --authenticationDatabase admin \
    --archive | gzip > "$BACKUP_DIR/mongodb_$DATE.gz"

# Backup Redis
echo "Backing up Redis..."
$COMPOSE_CMD exec -T redis redis-cli --rdb /data/dump.rdb BGSAVE >/dev/null
sleep 5  # Wait for background save to complete
docker cp $($COMPOSE_CMD ps -q redis):/data/dump.rdb "$BACKUP_DIR/redis_$DATE.rdb" 2>/dev/null || echo "Redis backup may have failed"

# Backup configuration
echo "Backing up configuration..."
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" .env docker-compose.yml 2>/dev/null || true

# Backup logs
echo "Backing up logs..."
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" logs/ 2>/dev/null || true

# Backup named volumes
echo "Backing up Docker volumes..."
docker run --rm -v securedevops_mongodb_data:/data -v "$PROJECT_DIR/backups:/backup" alpine \
    tar -czf "/backup/volumes_$DATE.tar.gz" -C /data . 2>/dev/null || echo "Volume backup may have failed"

# Cleanup old backups (keep last 30 days)
find "$BACKUP_DIR" -name "*.gz" -o -name "*.rdb" -o -name "*.tar.gz" | grep -E "_[0-9]{8}_[0-9]{6}" | sort | head -n -30 | xargs rm -f 2>/dev/null || true

echo "Backup completed successfully: $DATE"
ls -lh "$BACKUP_DIR/"*"$DATE"*
EOF

    chmod +x "$PROJECT_DIR/backup.sh"
    success "Backup script created at $PROJECT_DIR/backup.sh"
}

# Create monitoring script
create_monitoring_script() {
    log "Creating monitoring script..."
    
    cat > "$PROJECT_DIR/monitor.sh" << 'EOF'
#!/bin/bash

# Monitoring script for SecureDevOps Platform

# Determine compose command
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "Error: Docker Compose not found"
    exit 1
fi

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_service() {
    local service=$1
    local url=$2
    
    if curl -f "$url" &>/dev/null; then
        echo -e "${GREEN}✓${NC} $service is healthy"
        return 0
    else
        echo -e "${RED}✗${NC} $service is unhealthy"
        return 1
    fi
}

echo "SecureDevOps Platform Health Check"
echo "=================================="

# Check services
check_service "Frontend" "http://localhost/health"
check_service "Backend" "http://localhost:8000/health"

# Check containers
echo
echo "Container Status:"
$COMPOSE_CMD ps

# Check resources
echo
echo "Resource Usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Check logs for errors
echo
echo "Recent Errors (last 10 minutes):"
$COMPOSE_CMD logs --since=10m 2>&1 | grep -i error | tail -5 || echo "No errors found"
EOF

    chmod +x "$PROJECT_DIR/monitor.sh"
    success "Monitoring script created at $PROJECT_DIR/monitor.sh"
}

# Show status
show_status() {
    header "Platform Status"
    
    log "Service Status:"
    $COMPOSE_CMD -f "$COMPOSE_FILE" ps
    echo
    
    log "Service URLs:"
    echo "🌐 Frontend:       http://localhost"
    echo "🔧 Backend API:    http://localhost:8000"
    echo "📊 API Docs:       http://localhost:8000/docs"
    echo "🔄 Health Check:   http://localhost:8000/health"
    echo "💾 MongoDB:        localhost:27017"
    echo "🔄 Redis:          localhost:6379"
    echo
    
    log "Management Commands:"
    echo "📜 View logs:           $COMPOSE_CMD logs -f [service]"
    echo "🔄 Restart services:    $COMPOSE_CMD restart [service]"
    echo "🛑 Stop platform:       $COMPOSE_CMD down"
    echo "💾 Create backup:       ./backup.sh"
    echo "📊 Monitor status:      ./monitor.sh"
    echo "📈 View metrics:        docker stats"
    echo
    
    log "Configuration Files:"
    echo "⚙️  Environment:        .env"
    echo "🐳 Docker Compose:     docker-compose.yml"
    echo "📝 Logs:               logs/"
    echo "💾 Backups:            backups/"
    echo
}

# Main deployment function
main() {
    header "Starting deployment of $PLATFORM_NAME"
    
    check_requirements
    create_env_file
    validate_env
    setup_directories
    stop_services
    pull_images
    build_images
    deploy_services
    wait_for_services
    init_database
    create_backup_script
    create_monitoring_script
    
    echo
    header "🎉 $PLATFORM_NAME deployed successfully!"
    show_status
    
    log "Next steps:"
    echo "1. Access the platform at http://localhost"
    echo "2. Configure webhooks in your Git repositories"
    echo "3. Set up notification channels (Slack/Teams)"
    echo "4. Schedule regular backups with: crontab -e"
    echo "   Add: 0 2 * * * /path/to/securedevops-platform/backup.sh"
    echo
    warn "Production recommendations:"
    echo "- Configure SSL certificates for HTTPS"
    echo "- Set up firewall rules and security groups"
    echo "- Configure proper DNS records"
    echo "- Set up log rotation and monitoring"
    echo "- Review and harden security settings"
    echo "- Configure backup retention policies"
}

# Handle script arguments
case "${1:-deploy}" in
    deploy)
        main
        ;;
    stop)
        log "Stopping services..."
        $COMPOSE_CMD -f "$COMPOSE_FILE" down
        success "Services stopped"
        ;;
    restart)
        log "Restarting services..."
        $COMPOSE_CMD -f "$COMPOSE_FILE" restart
        success "Services restarted"
        ;;
    logs)
        $COMPOSE_CMD -f "$COMPOSE_FILE" logs -f "${2:-}"
        ;;
    backup)
        if [ -f "./backup.sh" ]; then
            ./backup.sh
        else
            error "Backup script not found. Run deploy first."
        fi
        ;;
    status)
        show_status
        ;;
    monitor)
        if [ -f "./monitor.sh" ]; then
            ./monitor.sh
        else
            error "Monitor script not found. Run deploy first."
        fi
        ;;
    update)
        log "Updating platform..."
        pull_images
        build_images
        $COMPOSE_CMD -f "$COMPOSE_FILE" up -d
        success "Platform updated"
        ;;
    clean)
        warn "This will remove all containers, images, and volumes!"
        read -p "Are you sure? (y/N): " -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            $COMPOSE_CMD -f "$COMPOSE_FILE" down -v --rmi all
            docker system prune -f
            success "Platform cleaned"
        fi
        ;;
    *)
        echo "Usage: $0 {deploy|stop|restart|logs|backup|status|monitor|update|clean}"
        echo
        echo "Commands:"
        echo "  deploy   - Deploy the complete platform (default)"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  logs     - Show service logs (optional service name)"
        echo "  backup   - Create a backup"
        echo "  status   - Show platform status"
        echo "  monitor  - Run health checks and show monitoring info"
        echo "  update   - Update and restart the platform"
        echo "  clean    - Remove all containers, images, and volumes"
        exit 1
        ;;
esac
