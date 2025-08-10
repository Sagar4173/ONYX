# SecureDevOps AI Platform - Windows PowerShell Deployment Script
# Run this script in PowerShell as Administrator

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("deploy", "stop", "restart", "logs", "backup", "status", "monitor", "update", "clean")]
    [string]$Action = "deploy",
    
    [Parameter(Mandatory=$false)]
    [string]$Service = ""
)

# Colors for output
$Red = [ConsoleColor]::Red
$Green = [ConsoleColor]::Green
$Yellow = [ConsoleColor]::Yellow
$Blue = [ConsoleColor]::Blue
$Cyan = [ConsoleColor]::Cyan
$Magenta = [ConsoleColor]::Magenta

function Write-ColorOutput($Message, $Color = [ConsoleColor]::White) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

function Write-Success($Message) {
    Write-ColorOutput "[SUCCESS] $Message" $Green
}

function Write-Warning($Message) {
    Write-ColorOutput "[WARNING] $Message" $Yellow
}

function Write-Error($Message) {
    Write-ColorOutput "[ERROR] $Message" $Red
    exit 1
}

function Write-Info($Message) {
    Write-ColorOutput "[INFO] $Message" $Cyan
}

function Write-Header($Message) {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor $Magenta
    Write-Host $Message -ForegroundColor $Magenta
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor $Magenta
    Write-Host ""
}

# Configuration
$PlatformName = "SecureDevOps AI Platform"
$ProjectDir = $PSScriptRoot
$EnvFile = Join-Path $ProjectDir ".env"
$BackupDir = Join-Path $ProjectDir "backups"
$ComposeFile = Join-Path $ProjectDir "docker-compose.yml"

# Check if running as Administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check system requirements
function Test-Requirements {
    Write-ColorOutput "Checking system requirements..." $Blue
    
    # Check if running as Administrator
    if (-not (Test-Administrator)) {
        Write-Warning "Not running as Administrator. Some operations may require elevated privileges."
    }
    
    # Check Docker
    try {
        $dockerVersion = docker --version
        Write-Info "Docker version: $dockerVersion"
    }
    catch {
        Write-Error "Docker is not installed. Please install Docker Desktop first."
    }
    
    # Check Docker Compose
    try {
        $composeVersion = docker-compose --version
        Write-Info "Docker Compose version: $composeVersion"
        $script:ComposeCmd = "docker-compose"
    }
    catch {
        try {
            $composeVersion = docker compose version
            Write-Info "Docker Compose (plugin) version: $composeVersion"
            $script:ComposeCmd = "docker compose"
        }
        catch {
            Write-Error "Docker Compose is not installed."
        }
    }
    
    # Check if Docker is running
    try {
        docker info | Out-Null
    }
    catch {
        Write-Error "Docker daemon is not running. Please start Docker Desktop."
    }
    
    # Check disk space (minimum 5GB)
    $drive = Get-PSDrive -Name (Split-Path $ProjectDir -Qualifier).TrimEnd(':')
    $freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
    
    if ($freeSpaceGB -lt 5) {
        Write-Warning "Low disk space. Recommended: 5GB+, Available: ${freeSpaceGB}GB"
    }
    else {
        Write-Info "Disk space: ${freeSpaceGB}GB available"
    }
    
    # Check memory (minimum 4GB)
    $totalMemoryGB = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
    if ($totalMemoryGB -lt 4) {
        Write-Warning "Low memory. Recommended: 4GB+, Available: ${totalMemoryGB}GB"
    }
    else {
        Write-Info "Memory: ${totalMemoryGB}GB available"
    }
    
    Write-Success "System requirements check passed"
}

# Create environment file
function New-EnvironmentFile {
    Write-ColorOutput "Setting up environment configuration..." $Blue
    
    if (-not (Test-Path $EnvFile)) {
        Write-ColorOutput "Creating .env file from .env.example..." $Blue
        
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" $EnvFile
            
            # Generate secure random values
            $secretKey = -join ((1..64) | ForEach-Object { '{0:X}' -f (Get-Random -Max 16) })
            $mongoPassword = [System.Web.Security.Membership]::GeneratePassword(32, 8)
            $redisPassword = [System.Web.Security.Membership]::GeneratePassword(32, 8)
            
            # Update environment file with generated values
            (Get-Content $EnvFile) -replace 'SECRET_KEY=.*', "SECRET_KEY=$secretKey" |
                Set-Content $EnvFile
            (Get-Content $EnvFile) -replace 'MONGO_PASSWORD=.*', "MONGO_PASSWORD=$mongoPassword" |
                Set-Content $EnvFile
            (Get-Content $EnvFile) -replace 'REDIS_PASSWORD=.*', "REDIS_PASSWORD=$redisPassword" |
                Set-Content $EnvFile
            
            Write-Warning "Created .env file with generated secrets."
            Write-Warning "Please update OPENAI_API_KEY and other settings before proceeding."
            Write-Warning "Edit $EnvFile to configure your environment."
            
            Write-Host ""
            Write-Info "Required configuration:"
            Write-Host "  OPENAI_API_KEY - Get from https://platform.openai.com/api-keys"
            Write-Host "  ALLOWED_ORIGINS - Add your frontend domain"
            Write-Host "  SLACK_WEBHOOK_URL - Optional: Slack notifications"
            Write-Host "  TEAMS_WEBHOOK_URL - Optional: Teams notifications"
            Write-Host ""
            
            Read-Host "Press Enter after updating the .env file to continue, or Ctrl+C to exit"
        }
        else {
            Write-Error ".env.example file not found. Cannot create environment configuration."
        }
    }
    else {
        Write-Info "Environment file already exists: $EnvFile"
    }
}

# Validate environment
function Test-Environment {
    Write-ColorOutput "Validating environment configuration..." $Blue
    
    if (-not (Test-Path $EnvFile)) {
        Write-Error "Environment file not found: $EnvFile"
    }
    
    # Read environment file
    $envVars = @{}
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $envVars[$matches[1]] = $matches[2]
        }
    }
    
    # Check critical settings
    $validationErrors = 0
    
    if (-not $envVars['SECRET_KEY'] -or $envVars['SECRET_KEY'] -eq 'your-super-secret-key-change-in-production-make-it-long-and-random') {
        Write-Error "SECRET_KEY is not configured or using default value"
        $validationErrors++
    }
    
    if (-not $envVars['MONGO_PASSWORD'] -or $envVars['MONGO_PASSWORD'] -eq 'securepass123') {
        Write-Warning "MONGO_PASSWORD is using default value - consider changing for production"
    }
    
    if (-not $envVars['OPENAI_API_KEY'] -or $envVars['OPENAI_API_KEY'] -eq 'sk-your-openai-api-key-here') {
        Write-Warning "OPENAI_API_KEY not configured. AI analysis features will be disabled."
        $continue = Read-Host "Continue without AI features? (y/N)"
        if ($continue -ne 'y' -and $continue -ne 'Y') {
            Write-Error "Please configure OPENAI_API_KEY in .env file"
        }
    }
    
    if ($validationErrors -gt 0) {
        Write-Error "Environment validation failed. Please fix the configuration issues."
    }
    
    Write-Success "Environment validation completed"
}

# Setup directories
function New-Directories {
    Write-ColorOutput "Setting up directories..." $Blue
    
    $directories = @($BackupDir, (Join-Path $ProjectDir "logs"), (Join-Path $ProjectDir "ssl"))
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    Write-Success "Directories created"
}

# Pull latest images
function Get-LatestImages {
    Write-ColorOutput "Pulling latest base images..." $Blue
    
    $images = @("mongo:7.0", "redis:7-alpine", "node:18-alpine", "nginx:alpine", "python:3.11-slim")
    
    foreach ($image in $images) {
        docker pull $image
    }
    
    Write-Success "Base images updated"
}

# Build images
function Build-Images {
    Write-ColorOutput "Building Docker images..." $Blue
    
    # Build backend
    Write-ColorOutput "Building backend image..." $Blue
    docker build -t securedevops-backend:latest `
        --build-arg BUILD_DATE=(Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ") `
        --build-arg VCS_REF="unknown" `
        --build-arg VERSION="1.0.0" `
        ./backend/
    
    # Build frontend
    Write-ColorOutput "Building frontend image..." $Blue
    docker build -t securedevops-frontend:latest `
        --build-arg BUILD_DATE=(Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ") `
        --build-arg VCS_REF="unknown" `
        --build-arg VERSION="1.0.0" `
        ./frontend/
    
    Write-Success "Docker images built successfully"
}

# Stop existing services
function Stop-Services {
    Write-ColorOutput "Stopping existing services..." $Blue
    
    if (Test-Path $ComposeFile) {
        & $script:ComposeCmd -f $ComposeFile down --remove-orphans 2>$null
        
        # Clean up any remaining containers
        $containers = docker ps -a --filter "name=securedevops" --format "{{.Names}}"
        if ($containers) {
            $containers | ForEach-Object { docker rm -f $_ 2>$null }
        }
    }
    
    Write-Success "Existing services stopped"
}

# Deploy services
function Start-Services {
    Write-ColorOutput "Deploying services..." $Blue
    
    & $script:ComposeCmd -f $ComposeFile up -d --remove-orphans
    
    Write-Success "Services deployed"
}

# Wait for services
function Wait-ForServices {
    Write-ColorOutput "Waiting for services to be ready..." $Blue
    
    $maxAttempts = 60
    
    # Wait for MongoDB
    Write-ColorOutput "Waiting for MongoDB..." $Blue
    for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
        try {
            & $script:ComposeCmd -f $ComposeFile exec -T mongodb mongosh --quiet --eval "db.adminCommand('ping')" 2>$null | Out-Null
            Write-Success "MongoDB is ready"
            break
        }
        catch {
            if ($attempt -eq $maxAttempts) {
                Write-Error "MongoDB failed to start within timeout"
            }
            Write-Host "." -NoNewline
            Start-Sleep -Seconds 2
        }
    }
    
    # Wait for Backend
    Write-ColorOutput "Waiting for Backend API..." $Blue
    for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-Success "Backend service is ready"
                break
            }
        }
        catch {
            if ($attempt -eq $maxAttempts) {
                Write-Error "Backend service failed to start within timeout"
            }
            Write-Host "." -NoNewline
            Start-Sleep -Seconds 3
        }
    }
    
    # Wait for Frontend
    Write-ColorOutput "Waiting for Frontend..." $Blue
    for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost/health" -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-Success "Frontend service is ready"
                break
            }
        }
        catch {
            if ($attempt -eq $maxAttempts) {
                Write-Error "Frontend service failed to start within timeout"
            }
            Write-Host "." -NoNewline
            Start-Sleep -Seconds 2
        }
    }
}

# Show status
function Show-Status {
    Write-Header "Platform Status"
    
    Write-ColorOutput "Service Status:" $Blue
    & $script:ComposeCmd -f $ComposeFile ps
    Write-Host ""
    
    Write-ColorOutput "Service URLs:" $Blue
    Write-Host "🌐 Frontend:       http://localhost"
    Write-Host "🔧 Backend API:    http://localhost:8000"
    Write-Host "📊 API Docs:       http://localhost:8000/docs"
    Write-Host "🔄 Health Check:   http://localhost:8000/health"
    Write-Host "💾 MongoDB:        localhost:27017"
    Write-Host "🔄 Redis:          localhost:6379"
    Write-Host ""
    
    Write-ColorOutput "Management Commands:" $Blue
    Write-Host "📜 View logs:           $($script:ComposeCmd) logs -f [service]"
    Write-Host "🔄 Restart services:    $($script:ComposeCmd) restart [service]"
    Write-Host "🛑 Stop platform:       $($script:ComposeCmd) down"
    Write-Host "📊 View metrics:        docker stats"
    Write-Host ""
}

# Main deployment function
function Start-Deployment {
    Write-Header "Starting deployment of $PlatformName"
    
    Test-Requirements
    New-EnvironmentFile
    Test-Environment
    New-Directories
    Stop-Services
    Get-LatestImages
    Build-Images
    Start-Services
    Wait-ForServices
    
    Write-Host ""
    Write-Header "🎉 $PlatformName deployed successfully!"
    Show-Status
    
    Write-ColorOutput "Next steps:" $Blue
    Write-Host "1. Access the platform at http://localhost"
    Write-Host "2. Configure webhooks in your Git repositories"
    Write-Host "3. Set up notification channels (Slack/Teams)"
    Write-Host "4. Schedule regular backups"
    Write-Host ""
    Write-Warning "Production recommendations:"
    Write-Host "- Configure SSL certificates for HTTPS"
    Write-Host "- Set up firewall rules and security groups"
    Write-Host "- Configure proper DNS records"
    Write-Host "- Set up log rotation and monitoring"
    Write-Host "- Review and harden security settings"
}

# Handle script actions
switch ($Action) {
    "deploy" {
        Start-Deployment
    }
    "stop" {
        Write-ColorOutput "Stopping services..." $Blue
        & $script:ComposeCmd -f $ComposeFile down
        Write-Success "Services stopped"
    }
    "restart" {
        Write-ColorOutput "Restarting services..." $Blue
        & $script:ComposeCmd -f $ComposeFile restart $Service
        Write-Success "Services restarted"
    }
    "logs" {
        & $script:ComposeCmd -f $ComposeFile logs -f $Service
    }
    "status" {
        Show-Status
    }
    "update" {
        Write-ColorOutput "Updating platform..." $Blue
        Get-LatestImages
        Build-Images
        & $script:ComposeCmd -f $ComposeFile up -d
        Write-Success "Platform updated"
    }
    "clean" {
        Write-Warning "This will remove all containers, images, and volumes!"
        $confirm = Read-Host "Are you sure? (y/N)"
        if ($confirm -eq 'y' -or $confirm -eq 'Y') {
            & $script:ComposeCmd -f $ComposeFile down -v --rmi all
            docker system prune -f
            Write-Success "Platform cleaned"
        }
    }
    default {
        Write-Host "Usage: .\deploy.ps1 [-Action] {deploy|stop|restart|logs|status|update|clean} [-Service servicename]"
        Write-Host ""
        Write-Host "Commands:"
        Write-Host "  deploy   - Deploy the complete platform (default)"
        Write-Host "  stop     - Stop all services"
        Write-Host "  restart  - Restart all services"
        Write-Host "  logs     - Show service logs (optional service name)"
        Write-Host "  status   - Show platform status"
        Write-Host "  update   - Update and restart the platform"
        Write-Host "  clean    - Remove all containers, images, and volumes"
        Write-Host ""
        Write-Host "Examples:"
        Write-Host "  .\deploy.ps1"
        Write-Host "  .\deploy.ps1 -Action logs -Service backend"
        Write-Host "  .\deploy.ps1 -Action restart"
    }
}
