#!/bin/bash
# Security Tools Installation Script for SecureDevOps AI Platform
# This script installs and configures all required security scanning tools

set -e

echo "🛡️ SecureDevOps AI Platform - Security Tools Setup"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_permissions() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "Running as root. Some tools may not work correctly."
    fi
}

# Install Python security tools
install_python_tools() {
    print_status "Installing Python security scanning tools..."
    
    # Upgrade pip first
    python -m pip install --upgrade pip
    
    # Install core security tools
    pip install bandit==1.7.5
    pip install safety==2.3.5
    pip install semgrep==1.45.0
    pip install detect-secrets==1.4.0
    
    print_success "Python security tools installed"
}

# Install Trivy
install_trivy() {
    print_status "Installing Trivy container scanner..."
    
    if command -v trivy &> /dev/null; then
        print_warning "Trivy already installed, skipping..."
        return
    fi
    
    # Detect OS and architecture
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    
    case $ARCH in
        x86_64) ARCH="64bit" ;;
        aarch64|arm64) ARCH="ARM64" ;;
        *) print_error "Unsupported architecture: $ARCH"; exit 1 ;;
    esac
    
    TRIVY_VERSION="0.48.3"
    DOWNLOAD_URL="https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_${OS^}_${ARCH}.tar.gz"
    
    # Download and install Trivy
    curl -sfL "$DOWNLOAD_URL" | tar -xzf - -C /tmp
    sudo mv /tmp/trivy /usr/local/bin/
    
    # Verify installation
    if trivy --version; then
        print_success "Trivy installed successfully"
    else
        print_error "Trivy installation failed"
        exit 1
    fi
}

# Install GitLeaks
install_gitleaks() {
    print_status "Installing GitLeaks secret scanner..."
    
    if command -v gitleaks &> /dev/null; then
        print_warning "GitLeaks already installed, skipping..."
        return
    fi
    
    # Detect OS and architecture
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    
    case $ARCH in
        x86_64) ARCH="x64" ;;
        aarch64|arm64) ARCH="arm64" ;;
        *) print_error "Unsupported architecture: $ARCH"; exit 1 ;;
    esac
    
    GITLEAKS_VERSION="8.18.0"
    DOWNLOAD_URL="https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_${OS}_${ARCH}.tar.gz"
    
    # Download and install GitLeaks
    curl -sfL "$DOWNLOAD_URL" | tar -xzf - -C /tmp
    sudo mv /tmp/gitleaks /usr/local/bin/
    
    # Verify installation
    if gitleaks version; then
        print_success "GitLeaks installed successfully"
    else
        print_error "GitLeaks installation failed"
        exit 1
    fi
}

# Install Lynis
install_lynis() {
    print_status "Installing Lynis security auditing tool..."
    
    if command -v lynis &> /dev/null; then
        print_warning "Lynis already installed, skipping..."
        return
    fi
    
    # Install via package manager or download
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        sudo apt-get update
        sudo apt-get install -y lynis
    elif command -v yum &> /dev/null; then
        # RHEL/CentOS
        sudo yum install -y epel-release
        sudo yum install -y lynis
    elif command -v brew &> /dev/null; then
        # macOS
        brew install lynis
    else
        # Manual installation
        LYNIS_VERSION="3.0.9"
        DOWNLOAD_URL="https://github.com/CISOfy/lynis/archive/refs/tags/${LYNIS_VERSION}.tar.gz"
        
        curl -sfL "$DOWNLOAD_URL" | tar -xzf - -C /tmp
        sudo mv "/tmp/lynis-${LYNIS_VERSION}" /opt/lynis
        sudo ln -sf /opt/lynis/lynis /usr/local/bin/lynis
    fi
    
    # Verify installation
    if lynis --version; then
        print_success "Lynis installed successfully"
    else
        print_error "Lynis installation failed"
        exit 1
    fi
}

# Setup cache directories
setup_cache_directories() {
    print_status "Setting up cache directories..."
    
    # Create cache directories
    sudo mkdir -p /opt/securedevops/cache/trivy
    sudo mkdir -p /opt/securedevops/logs
    sudo mkdir -p /opt/securedevops/config
    
    # Set appropriate permissions
    sudo chown -R $(whoami):$(whoami) /opt/securedevops
    
    print_success "Cache directories created"
}

# Configure Trivy database
configure_trivy() {
    print_status "Configuring Trivy database..."
    
    # Set cache directory
    export TRIVY_CACHE_DIR="/opt/securedevops/cache/trivy"
    
    # Download initial database
    trivy image --download-db-only --cache-dir "$TRIVY_CACHE_DIR"
    
    print_success "Trivy database configured"
}

# Setup custom configurations
setup_custom_configs() {
    print_status "Setting up custom security configurations..."
    
    # Copy custom configs to system location
    sudo cp -r backend/configs/* /opt/securedevops/config/
    
    # Set environment variables
    cat >> ~/.bashrc << 'EOF'
# SecureDevOps Platform Environment Variables
export TRIVY_CACHE_DIR="/opt/securedevops/cache/trivy"
export CUSTOM_GITLEAKS_CONFIG="/opt/securedevops/config/gitleaks-custom.toml"
export CUSTOM_SEMGREP_RULES="/opt/securedevops/config/custom-semgrep-rules.yaml"
EOF
    
    print_success "Custom configurations set up"
}

# Verify all installations
verify_installations() {
    print_status "Verifying all security tool installations..."
    
    tools=(
        "bandit --version"
        "safety --version" 
        "semgrep --version"
        "trivy --version"
        "gitleaks version"
        "lynis --version"
    )
    
    all_ok=true
    
    for tool_cmd in "${tools[@]}"; do
        tool_name=$(echo "$tool_cmd" | cut -d' ' -f1)
        if eval "$tool_cmd" &> /dev/null; then
            print_success "$tool_name: ✓"
        else
            print_error "$tool_name: ✗"
            all_ok=false
        fi
    done
    
    if $all_ok; then
        print_success "All security tools installed and verified!"
        return 0
    else
        print_error "Some tools failed verification. Please check the installation."
        return 1
    fi
}

# Create a health check script
create_health_check() {
    print_status "Creating health check script..."
    
    cat > /opt/securedevops/health_check.sh << 'EOF'
#!/bin/bash
# Security Tools Health Check Script

echo "🔍 SecureDevOps Security Tools Health Check"
echo "==========================================="

tools=("bandit" "safety" "semgrep" "trivy" "gitleaks" "lynis")
failed_tools=()

for tool in "${tools[@]}"; do
    if command -v "$tool" &> /dev/null; then
        echo "✓ $tool: Available"
    else
        echo "✗ $tool: Not available"
        failed_tools+=("$tool")
    fi
done

if [ ${#failed_tools[@]} -eq 0 ]; then
    echo ""
    echo "✅ All security tools are available and healthy!"
    exit 0
else
    echo ""
    echo "❌ Failed tools: ${failed_tools[*]}"
    echo "Please reinstall the missing tools."
    exit 1
fi
EOF

    chmod +x /opt/securedevops/health_check.sh
    print_success "Health check script created at /opt/securedevops/health_check.sh"
}

# Main installation function
main() {
    print_status "Starting SecureDevOps security tools installation..."
    
    check_permissions
    install_python_tools
    install_trivy
    install_gitleaks
    install_lynis
    setup_cache_directories
    configure_trivy
    setup_custom_configs
    create_health_check
    
    echo ""
    print_status "Installation Summary:"
    
    if verify_installations; then
        echo ""
        print_success "🎉 All security tools have been installed successfully!"
        print_status "You can now run: /opt/securedevops/health_check.sh to verify the installation"
        print_status "Don't forget to source your ~/.bashrc or restart your terminal to load environment variables"
    else
        echo ""
        print_error "❌ Installation completed with some errors. Please check the logs above."
        exit 1
    fi
}

# Run main function
main "$@"
