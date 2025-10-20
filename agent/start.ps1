# Quick Start Script for Markdownizer Agent
# Run this from the agent directory

Write-Host "Starting Markdownizer Agent..." -ForegroundColor Cyan
Write-Host ""

# Check if in correct directory
if (!(Test-Path "main.py")) {
    Write-Host "Error: Run this script from the agent/ directory" -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
if (Test-Path "venv\Scripts\Activate.ps1") {
    & ".\venv\Scripts\Activate.ps1"
} else {
    Write-Host "Error: Virtual environment not found" -ForegroundColor Red
    Write-Host "Run: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Check for .env file
if (!(Test-Path ".env")) {
    Write-Host "Info: No .env file found - using ConnectOnion free tier" -ForegroundColor Cyan
    Write-Host "Creating .env from template..." -ForegroundColor Cyan
    Copy-Item .env.example .env -ErrorAction SilentlyContinue
    Write-Host ""
}

# Check OPENAI_API_KEY (optional now)
$envContent = Get-Content .env -ErrorAction SilentlyContinue | Out-String
if ($envContent -notmatch "OPENAI_API_KEY=sk-" -or $envContent -match "sk-your-actual-openai-key-here") {
    Write-Host "Info: OpenAI API key not configured (using free tier)" -ForegroundColor Cyan
    Write-Host "Agent will use ConnectOnion's free tier (100k tokens/month)" -ForegroundColor Cyan
    Write-Host ""
}

# Start the agent
Write-Host "Starting Markdownizer Agent on http://127.0.0.1:5050..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""
python main.py
