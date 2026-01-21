#!/usr/bin/env pwsh
<#
.SYNOPSIS
    ReqGen Complete System Startup Script (PowerShell)
    
.DESCRIPTION
    Starts all required services for ReqGen development:
    - Node.js backend on localhost:5027
    - Python backend on localhost:5000
    - MySQL database (must be running separately)
    - Opens browser to http://localhost:5173
    
.PARAMETER Help
    Shows this help message
    
.EXAMPLE
    PS> .\START_REQGEN_ALL.ps1
    
.NOTES
    Requires: Node.js v18+, Python 3.8+, MySQL running
    Run as Administrator if you have permission issues
#>

param(
    [switch]$Help
)

if ($Help) {
    Get-Help $PSCommandPath -Detailed
    exit 0
}

# Configuration
$ProjectRoot = "c:\Users\sujay.palande\Downloads\Reqgen 20Jan-12-05"
$NodePort = 5027
$PythonPort = 5000
$MySQLPort = 3306
$BrowserUrl = "http://localhost:5173"

# Colors for output
function Write-Status { Write-Host "`n[*] $args" -ForegroundColor Cyan }
function Write-Success { Write-Host "[✓] $args" -ForegroundColor Green }
function Write-Error { Write-Host "[✗] $args" -ForegroundColor Red }
function Write-Warning { Write-Host "[!] $args" -ForegroundColor Yellow }

Clear-Host

Write-Host "
╔════════════════════════════════════════════════════╗
║          ReqGen System Startup (PowerShell)         ║
║                                                    ║
║  This script will start all required services      ║
╚════════════════════════════════════════════════════╝
" -ForegroundColor Cyan

# Validate project directory
if (-not (Test-Path $ProjectRoot)) {
    Write-Error "Project directory not found: $ProjectRoot"
    Write-Status "Please update the `$ProjectRoot variable in this script"
    exit 1
}

# Change to project root
Set-Location $ProjectRoot
Write-Success "Working directory: $ProjectRoot"

# Verify required tools
Write-Status "Checking prerequisites..."

# Check Node.js
$NodeVersion = node --version 2>$null
if (-not $NodeVersion) {
    Write-Error "Node.js not found in PATH"
    Write-Status "Install from https://nodejs.org/ (v18 or higher)"
    exit 1
}
Write-Success "Node.js $NodeVersion"

# Check Python
$PythonVersion = python --version 2>$null
if (-not $PythonVersion) {
    Write-Error "Python not found in PATH"
    Write-Status "Install from https://python.org/ (3.8 or higher)"
    exit 1
}
Write-Success "$PythonVersion"

# Check npm
$NpmVersion = npm --version 2>$null
if (-not $NpmVersion) {
    Write-Error "npm not found"
    exit 1
}
Write-Success "npm v$NpmVersion"

# Check git
$GitVersion = git --version 2>$null
if (-not $GitVersion) {
    Write-Warning "git not found (optional, but recommended)"
}

# Check if MySQL is running
Write-Status "Checking MySQL on port $MySQLPort..."
$MySQLCheck = Test-Connection -ComputerName localhost -TcpPort $MySQLPort -ErrorAction SilentlyContinue
if ($MySQLCheck) {
    Write-Success "MySQL is running"
} else {
    Write-Warning "MySQL not detected on port $MySQLPort"
    Write-Status "Please start MySQL separately (XAMPP or MySQL service)"
}

# Install npm dependencies if needed
if (-not (Test-Path "node_modules")) {
    Write-Status "Installing Node.js dependencies..."
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install Node dependencies"
        exit 1
    }
    Write-Success "Node dependencies installed"
}

# Check Python venv
Write-Status "Checking Python virtual environment..."
$VenvPath = "python-backend\venv"
if (-not (Test-Path $VenvPath)) {
    Write-Status "Creating Python virtual environment..."
    python -m venv $VenvPath
    Write-Success "Virtual environment created"
} else {
    Write-Success "Virtual environment found"
}

# Activate venv and check packages
Write-Status "Checking Python packages..."
& $VenvPath\Scripts\pip.exe install --upgrade pip 2>&1 | Out-Null
$RequiredPackages = @("flask", "flask-cors", "transformers", "torch", "librosa")
$MissingPackages = @()

foreach ($package in $RequiredPackages) {
    $CheckCmd = & $VenvPath\Scripts\pip.exe show $package 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        $MissingPackages += $package
    }
}

if ($MissingPackages.Count -gt 0) {
    Write-Status "Installing missing Python packages: $($MissingPackages -join ', ')..."
    & $VenvPath\Scripts\pip.exe install $MissingPackages 2>&1
    Write-Success "Python packages installed"
} else {
    Write-Success "All Python packages present"
}

# Summary before starting
Write-Host "`n
╔════════════════════════════════════════════════════╗
║              Pre-Launch Summary                    ║
╚════════════════════════════════════════════════════╝
" -ForegroundColor Cyan

Write-Host "
  Services to start:
  ✓ Node.js Backend     → http://localhost:$NodePort
  ✓ Python Backend      → http://localhost:$PythonPort
  ✓ Frontend Browser    → http://localhost:5173
  
  Project Root: $ProjectRoot
  
  Note: MySQL must be running separately
  
  This script will open 3 new terminals and then the browser.
  Close any terminal to stop that service.
  
" -ForegroundColor Green

Write-Host "Press any key to start services..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Start services
Write-Status "Starting Node Backend..."
$NodeProcess = Start-Process powershell -ArgumentList `
    "-NoExit", `
    "-Command", `
    "cd '$ProjectRoot'; npm run dev" `
    -PassThru

Write-Success "Node Backend started (PID: $($NodeProcess.Id))"

Start-Sleep -Seconds 2

Write-Status "Starting Python Backend..."
$PythonProcess = Start-Process powershell -ArgumentList `
    "-NoExit", `
    "-Command", `
    "cd '$ProjectRoot\python-backend'; & '..\python-backend\venv\Scripts\activate.ps1'; python app.py" `
    -PassThru

Write-Success "Python Backend started (PID: $($PythonProcess.Id))"

Start-Sleep -Seconds 2

Write-Status "Waiting for services to be ready..."
Start-Sleep -Seconds 3

# Check services
Write-Status "Verifying services..."
$NodeReady = $false
$PythonReady = $false

for ($i = 0; $i -lt 10; $i++) {
    if (-not $NodeReady) {
        $NodeReady = Test-Connection -ComputerName localhost -TcpPort $NodePort -ErrorAction SilentlyContinue
        if ($NodeReady) { Write-Success "Node Backend is responding" }
    }
    if (-not $PythonReady) {
        $PythonReady = Test-Connection -ComputerName localhost -TcpPort $PythonPort -ErrorAction SilentlyContinue
        if ($PythonReady) { Write-Success "Python Backend is responding" }
    }
    if ($NodeReady -and $PythonReady) { break }
    Start-Sleep -Seconds 1
}

if (-not $NodeReady) { Write-Warning "Node Backend not responding yet (check terminal)" }
if (-not $PythonReady) { Write-Warning "Python Backend not responding yet (check terminal)" }

# Open browser
Write-Status "Opening browser..."
Start-Process $BrowserUrl

Write-Host "`n
╔════════════════════════════════════════════════════╗
║           Services Started Successfully!           ║
╚════════════════════════════════════════════════════╝

✓ Node Backend:     http://localhost:$NodePort
✓ Python Backend:   http://localhost:$PythonPort  
✓ Frontend:         $BrowserUrl
✓ MySQL:            $($MySQLCheck ? 'Running' : 'Not detected - start separately')

Processes Running:
  Node (PID $($NodeProcess.Id))
  Python (PID $($PythonProcess.Id))

To stop all services: Close the terminal windows

Next Steps:
  1. Wait for browser to load
  2. Test audio recording/upload
  3. Test document refinement
  4. Test document generation

For help: See TROUBLESHOOTING_ERRORS.md

" -ForegroundColor Green

# Keep script running to monitor processes
Write-Host "Monitoring services (press Ctrl+C to exit this monitor)..." -ForegroundColor Yellow

while ($true) {
    if (-not (Get-Process -Id $NodeProcess.Id -ErrorAction SilentlyContinue)) {
        Write-Warning "Node Backend has stopped"
    }
    if (-not (Get-Process -Id $PythonProcess.Id -ErrorAction SilentlyContinue)) {
        Write-Warning "Python Backend has stopped"
    }
    Start-Sleep -Seconds 5
}
