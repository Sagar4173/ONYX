# Security Tools Installation Script for Windows
# PowerShell script to install and configure security scanning tools

param(
    [switch]$Force,
    [switch]$SkipVerification
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "🛡️ SecureDevOps AI Platform - Security Tools Setup (Windows)" -ForegroundColor Blue
Write-Host "=============================================================" -ForegroundColor Blue

# Function to write colored output
function Write-Status {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param($Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param($Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Install Python security tools
function Install-PythonTools {
    Write-Status "Installing Python security scanning tools..."
    
    try {
        # Upgrade pip first
        python -m pip install --upgrade pip
        
        # Install core security tools
        python -m pip install bandit==1.7.5
        python -m pip install safety==2.3.5
        python -m pip install semgrep==1.45.0
        python -m pip install detect-secrets==1.4.0
        
        Write-Success "Python security tools installed"
    }
    catch {
        Write-Error "Failed to install Python tools: $_"
        throw
    }
}

# Install Trivy
function Install-Trivy {
    Write-Status "Installing Trivy container scanner..."
    
    if (Get-Command trivy -ErrorAction SilentlyContinue) {
        Write-Warning "Trivy already installed, skipping..."
        return
    }
    
    try {
        $trivyVersion = "0.48.3"
        $downloadUrl = "https://github.com/aquasecurity/trivy/releases/download/v$trivyVersion/trivy_${trivyVersion}_Windows-64bit.zip"
        $tempPath = "$env:TEMP\trivy.zip"
        $installPath = "$env:ProgramFiles\SecureDevOps\bin"
        
        # Create installation directory
        New-Item -ItemType Directory -Path $installPath -Force | Out-Null
        
        # Download Trivy
        Write-Status "Downloading Trivy..."
        Invoke-WebRequest -Uri $downloadUrl -OutFile $tempPath
        
        # Extract and install
        Expand-Archive -Path $tempPath -DestinationPath $installPath -Force
        
        # Add to PATH
        $currentPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::Machine)
        if ($currentPath -notlike "*$installPath*") {
            [Environment]::SetEnvironmentVariable("Path", "$currentPath;$installPath", [EnvironmentVariableTarget]::Machine)
        }
        
        # Cleanup
        Remove-Item $tempPath -Force
        
        Write-Success "Trivy installed successfully"
    }
    catch {
        Write-Error "Trivy installation failed: $_"
        throw
    }
}

# Install GitLeaks
function Install-GitLeaks {
    Write-Status "Installing GitLeaks secret scanner..."
    
    if (Get-Command gitleaks -ErrorAction SilentlyContinue) {
        Write-Warning "GitLeaks already installed, skipping..."
        return
    }
    
    try {
        $gitleaksVersion = "8.18.0"
        $downloadUrl = "https://github.com/gitleaks/gitleaks/releases/download/v$gitleaksVersion/gitleaks_${gitleaksVersion}_windows_x64.zip"
        $tempPath = "$env:TEMP\gitleaks.zip"
        $installPath = "$env:ProgramFiles\SecureDevOps\bin"
        
        # Create installation directory
        New-Item -ItemType Directory -Path $installPath -Force | Out-Null
        
        # Download GitLeaks
        Write-Status "Downloading GitLeaks..."
        Invoke-WebRequest -Uri $downloadUrl -OutFile $tempPath
        
        # Extract and install
        Expand-Archive -Path $tempPath -DestinationPath $installPath -Force
        
        # Add to PATH if not already present
        $currentPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::Machine)
        if ($currentPath -notlike "*$installPath*") {
            [Environment]::SetEnvironmentVariable("Path", "$currentPath;$installPath", [EnvironmentVariableTarget]::Machine)
        }
        
        # Cleanup
        Remove-Item $tempPath -Force
        
        Write-Success "GitLeaks installed successfully"
    }
    catch {
        Write-Error "GitLeaks installation failed: $_"
        throw
    }
}

# Install Lynis (Note: Lynis has limited Windows support)
function Install-Lynis {
    Write-Status "Setting up Lynis (Linux subsystem required for full functionality)..."
    Write-Warning "Lynis has limited Windows support. Consider using WSL for full functionality."
    
    # For Windows, we'll skip Lynis installation but note it in the config
    Write-Status "Skipping Lynis installation on Windows. Use WSL or Linux environment for Lynis."
}

# Setup cache directories
function Setup-CacheDirectories {
    Write-Status "Setting up cache directories..."
    
    try {
        $cacheDir = "$env:ProgramData\SecureDevOps\cache"
        $configDir = "$env:ProgramData\SecureDevOps\config"
        $logsDir = "$env:ProgramData\SecureDevOps\logs"
        
        # Create directories
        New-Item -ItemType Directory -Path "$cacheDir\trivy" -Force | Out-Null
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
        New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
        
        # Set environment variables
        [Environment]::SetEnvironmentVariable("TRIVY_CACHE_DIR", "$cacheDir\trivy", [EnvironmentVariableTarget]::Machine)
        [Environment]::SetEnvironmentVariable("SECUREDEVOPS_CONFIG_DIR", $configDir, [EnvironmentVariableTarget]::Machine)
        [Environment]::SetEnvironmentVariable("SECUREDEVOPS_LOGS_DIR", $logsDir, [EnvironmentVariableTarget]::Machine)
        
        Write-Success "Cache directories created"
    }
    catch {
        Write-Error "Failed to setup cache directories: $_"
        throw
    }
}

# Configure Trivy database
function Configure-Trivy {
    Write-Status "Configuring Trivy database..."
    
    try {
        $cacheDir = "$env:ProgramData\SecureDevOps\cache\trivy"
        
        # Download initial database
        $env:TRIVY_CACHE_DIR = $cacheDir
        & trivy image --download-db-only --cache-dir $cacheDir
        
        Write-Success "Trivy database configured"
    }
    catch {
        Write-Warning "Trivy database configuration failed: $_"
    }
}

# Setup custom configurations
function Setup-CustomConfigs {
    Write-Status "Setting up custom security configurations..."
    
    try {
        $configDir = "$env:ProgramData\SecureDevOps\config"
        $sourceConfigDir = "backend\configs"
        
        if (Test-Path $sourceConfigDir) {
            Copy-Item -Path "$sourceConfigDir\*" -Destination $configDir -Recurse -Force
            
            # Set environment variables for custom configs
            [Environment]::SetEnvironmentVariable("CUSTOM_GITLEAKS_CONFIG", "$configDir\gitleaks-custom.toml", [EnvironmentVariableTarget]::Machine)
            [Environment]::SetEnvironmentVariable("CUSTOM_SEMGREP_RULES", "$configDir\custom-semgrep-rules.yaml", [EnvironmentVariableTarget]::Machine)
            
            Write-Success "Custom configurations set up"
        } else {
            Write-Warning "Custom configuration directory not found: $sourceConfigDir"
        }
    }
    catch {
        Write-Error "Failed to setup custom configurations: $_"
        throw
    }
}

# Verify installations
function Test-Installations {
    Write-Status "Verifying all security tool installations..."
    
    $tools = @(
        @{Name="bandit"; Command="bandit --version"},
        @{Name="safety"; Command="safety --version"},
        @{Name="semgrep"; Command="semgrep --version"},
        @{Name="trivy"; Command="trivy --version"},
        @{Name="gitleaks"; Command="gitleaks version"}
    )
    
    $allOk = $true
    
    foreach ($tool in $tools) {
        try {
            Invoke-Expression $tool.Command | Out-Null
            Write-Success "$($tool.Name): ✓"
        }
        catch {
            Write-Error "$($tool.Name): ✗"
            $allOk = $false
        }
    }
    
    if ($allOk) {
        Write-Success "All security tools installed and verified!"
        return $true
    } else {
        Write-Error "Some tools failed verification. Please check the installation."
        return $false
    }
}

# Create health check script
function New-HealthCheckScript {
    Write-Status "Creating health check script..."
    
    $healthCheckScript = @"
# SecureDevOps Security Tools Health Check Script for Windows

Write-Host "🔍 SecureDevOps Security Tools Health Check" -ForegroundColor Blue
Write-Host "===========================================" -ForegroundColor Blue

`$tools = @("bandit", "safety", "semgrep", "trivy", "gitleaks")
`$failedTools = @()

foreach (`$tool in `$tools) {
    if (Get-Command `$tool -ErrorAction SilentlyContinue) {
        Write-Host "✓ `$tool`: Available" -ForegroundColor Green
    } else {
        Write-Host "✗ `$tool`: Not available" -ForegroundColor Red
        `$failedTools += `$tool
    }
}

if (`$failedTools.Count -eq 0) {
    Write-Host ""
    Write-Host "✅ All security tools are available and healthy!" -ForegroundColor Green
    exit 0
} else {
    Write-Host ""
    Write-Host "❌ Failed tools: `$(`$failedTools -join ', ')" -ForegroundColor Red
    Write-Host "Please reinstall the missing tools." -ForegroundColor Red
    exit 1
}
"@

    $healthCheckPath = "$env:ProgramData\SecureDevOps\health_check.ps1"
    $healthCheckScript | Out-File -FilePath $healthCheckPath -Encoding UTF8
    
    Write-Success "Health check script created at $healthCheckPath"
}

# Main installation function
function Main {
    Write-Status "Starting SecureDevOps security tools installation..."
    
    if (-not (Test-Administrator)) {
        Write-Error "This script must be run as Administrator. Please restart PowerShell as Administrator."
        exit 1
    }
    
    try {
        Install-PythonTools
        Install-Trivy
        Install-GitLeaks
        Install-Lynis
        Setup-CacheDirectories
        Configure-Trivy
        Setup-CustomConfigs
        New-HealthCheckScript
        
        Write-Host ""
        Write-Status "Installation Summary:" -ForegroundColor Blue
        
        if (-not $SkipVerification -and (Test-Installations)) {
            Write-Host ""
            Write-Success "🎉 All security tools have been installed successfully!"
            Write-Status "You can now run: PowerShell -ExecutionPolicy Bypass -File `"$env:ProgramData\SecureDevOps\health_check.ps1`" to verify the installation"
            Write-Status "Please restart your PowerShell session to load new environment variables"
        } else {
            Write-Host ""
            Write-Warning "Installation completed. Some tools may need manual verification."
        }
    }
    catch {
        Write-Host ""
        Write-Error "❌ Installation failed: $_"
        exit 1
    }
}

# Run main function
Main
