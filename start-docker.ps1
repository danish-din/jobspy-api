# Quick startup script for Docker container with optional testing (Windows PowerShell)
# Usage: .\start-docker.ps1

param(
    [switch]$Test = $false,
    [switch]$Logs = $false
)

# Colors
$Green = "Green"
$Blue = "Cyan"
$Yellow = "Yellow"

function Write-Header {
    param([string]$Text)
    Write-Host "╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor $Blue
    Write-Host "║  $($Text.PadRight(65))║" -ForegroundColor $Blue
    Write-Host "╚════════════════════════════════════════════════════════════════════╝" -ForegroundColor $Blue
}

function Write-Step {
    param([string]$Text)
    Write-Host "`nStep: $Text" -ForegroundColor $Blue
}

function Write-Success {
    param([string]$Text)
    Write-Host "✓ $Text" -ForegroundColor $Green
}

function Write-Info {
    param([string]$Text)
    Write-Host "ℹ $Text"
}

# Main script
Clear-Host

Write-Header "JobSpy API - Docker Build & Start Script"

# Change to script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Step "Building Docker image..."
docker-compose build

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Docker build failed" -ForegroundColor Red
    exit 1
}
Write-Success "Docker image built successfully"

Write-Step "Cleaning up existing containers..."
docker-compose down --remove-orphans 2>$null
Write-Success "Old containers removed"

Write-Step "Starting new container..."
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to start container" -ForegroundColor Red
    exit 1
}
Write-Success "Container started"

Write-Step "Waiting for container to be healthy..."
$maxAttempts = 30
$attempt = 0

while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Success "Container is healthy"
            break
        }
    }
    catch {
        # Expected to fail while starting
    }
    
    Write-Host -NoNewline "."
    Start-Sleep -Seconds 1
    $attempt++
}

if ($attempt -eq $maxAttempts) {
    Write-Host ""
    Write-Host "⚠ Container may not be ready yet" -ForegroundColor $Yellow
}

Write-Step "Container Status"
docker-compose ps

Write-Step "Access Information"
Write-Success "API running at: http://localhost:8000"
Write-Success "Swagger UI at: http://localhost:8000/docs"
Write-Success "ReDoc at: http://localhost:8000/redoc"

Write-Step "Recent Container Logs"
docker-compose logs --tail=20 jobspy-api

Write-Step "Available Options"
Write-Info "To run tests:"
Write-Host "  python test_fetch_job.py"
Write-Host ""
Write-Info "To view logs:"
Write-Host "  docker-compose logs -f jobspy-api"
Write-Host ""
Write-Info "To stop container:"
Write-Host "  docker-compose down"
Write-Host ""
Write-Info "To test the new endpoint:"
Write-Host '  curl "http://localhost:8000/api/v1/fetch_job?job_id=3456789"'
Write-Host ""

Write-Header "Ready to use!"

# Optional: Run tests
if ($Test) {
    Write-Step "Running test suite..."
    python test_fetch_job.py
}

# Optional: Show logs
if ($Logs) {
    Write-Step "Showing live logs (Press Ctrl+C to exit)..."
    docker-compose logs -f jobspy-api
}
