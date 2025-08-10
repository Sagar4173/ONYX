#!/bin/bash
# Production deployment script for SecureDevOps AI Platform

set -e

echo "🔒 SecureDevOps AI Platform Deployment Script"
echo "=============================================="

# Configuration
IMAGE_NAME="securedevops-platform"
CONTAINER_NAME="securedevops-backend"
NETWORK_NAME="securedevops-net"
MONGODB_CONTAINER="securedevops-mongodb"
VERSION=${VERSION:-"latest"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        error "Docker is not running or not accessible"
        exit 1
    fi
    success "Docker is running"
}

# Function to create Docker network
create_network() {
    if ! docker network ls | grep -q "$NETWORK_NAME"; then
        info "Creating Docker network: $NETWORK_NAME"
        docker network create $NETWORK_NAME
        success "Network created"
    else
        info "Network $NETWORK_NAME already exists"
    fi
}

# Function to start MongoDB
start_mongodb() {
    if ! docker ps | grep -q "$MONGODB_CONTAINER"; then
        info "Starting MongoDB container"
        docker run -d \
            --name $MONGODB_CONTAINER \
            --network $NETWORK_NAME \
            -p 27017:27017 \
            -v mongodb_data:/data/db \
            -e MONGO_INITDB_ROOT_USERNAME=admin \
            -e MONGO_INITDB_ROOT_PASSWORD=password \
            --restart unless-stopped \
            mongo:7.0
        
        # Wait for MongoDB to start
        info "Waiting for MongoDB to start..."
        sleep 10
        success "MongoDB started"
    else
        info "MongoDB container already running"
    fi
}

# Function to build the application image
build_image() {
    info "Building Docker image: $IMAGE_NAME:$VERSION"
    docker build \
        --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
        --build-arg VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown") \
        --build-arg VERSION=$VERSION \
        -t $IMAGE_NAME:$VERSION \
        -t $IMAGE_NAME:latest \
        .
    success "Image built successfully"
}

# Function to stop existing container
stop_container() {
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        info "Stopping existing container: $CONTAINER_NAME"
        docker stop $CONTAINER_NAME
        docker rm $CONTAINER_NAME
        success "Container stopped and removed"
    fi
}

# Function to start the application container
start_container() {
    info "Starting application container: $CONTAINER_NAME"
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        warning ".env file not found. Please create one based on .env.example"
        return 1
    fi
    
    docker run -d \
        --name $CONTAINER_NAME \
        --network $NETWORK_NAME \
        -p 8000:8000 \
        --env-file .env \
        -e MONGODB_URI=mongodb://admin:password@$MONGODB_CONTAINER:27017/securedevops?authSource=admin \
        -v app_logs:/app/logs \
        -v app_temp:/app/temp \
        --restart unless-stopped \
        --health-cmd="curl -f http://localhost:8000/health || exit 1" \
        --health-interval=30s \
        --health-timeout=10s \
        --health-retries=3 \
        $IMAGE_NAME:$VERSION
    
    success "Container started"
}

# Function to show container logs
show_logs() {
    info "Container logs (last 50 lines):"
    docker logs --tail 50 $CONTAINER_NAME
}

# Function to check container health
check_health() {
    info "Checking container health..."
    
    # Wait for container to start
    sleep 5
    
    if docker ps | grep -q "$CONTAINER_NAME.*healthy"; then
        success "Container is healthy"
        return 0
    else
        warning "Container health check pending..."
        for i in {1..12}; do
            sleep 5
            if docker ps | grep -q "$CONTAINER_NAME.*healthy"; then
                success "Container is healthy"
                return 0
            fi
            echo -n "."
        done
        echo
        error "Container failed health check"
        return 1
    fi
}

# Function to run post-deployment tests
run_tests() {
    info "Running post-deployment tests..."
    
    # Test API endpoint
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        success "Health endpoint is responding"
    else
        error "Health endpoint is not responding"
        return 1
    fi
    
    # Test API root
    if curl -f http://localhost:8000/ >/dev/null 2>&1; then
        success "API root endpoint is responding"
    else
        error "API root endpoint is not responding"
        return 1
    fi
    
    success "All tests passed"
}

# Function to display deployment info
show_info() {
    echo
    echo "🎉 Deployment Complete!"
    echo "======================="
    echo "Application URL: http://localhost:8000"
    echo "API Documentation: http://localhost:8000/docs"
    echo "Health Check: http://localhost:8000/health"
    echo
    echo "Useful Commands:"
    echo "  View logs: docker logs -f $CONTAINER_NAME"
    echo "  Stop app: docker stop $CONTAINER_NAME"
    echo "  Restart app: docker restart $CONTAINER_NAME"
    echo "  Update app: ./deploy.sh"
    echo
}

# Function to clean up old images
cleanup() {
    info "Cleaning up old Docker images..."
    docker image prune -f
    success "Cleanup complete"
}

# Main deployment function
deploy() {
    info "Starting deployment process..."
    
    check_docker
    create_network
    start_mongodb
    build_image
    stop_container
    start_container
    
    if check_health; then
        run_tests
        show_info
        cleanup
    else
        error "Deployment failed - container is not healthy"
        show_logs
        exit 1
    fi
}

# Parse command line arguments
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "build")
        check_docker
        build_image
        ;;
    "start")
        check_docker
        create_network
        start_mongodb
        start_container
        check_health
        ;;
    "stop")
        stop_container
        ;;
    "restart")
        stop_container
        start_container
        check_health
        ;;
    "logs")
        show_logs
        ;;
    "health")
        check_health
        ;;
    "test")
        run_tests
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  deploy   - Full deployment (default)"
        echo "  build    - Build Docker image only"
        echo "  start    - Start containers"
        echo "  stop     - Stop application container"
        echo "  restart  - Restart application container"
        echo "  logs     - Show container logs"
        echo "  health   - Check container health"
        echo "  test     - Run post-deployment tests"
        echo "  cleanup  - Clean up old Docker images"
        echo "  help     - Show this help message"
        ;;
    *)
        error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
