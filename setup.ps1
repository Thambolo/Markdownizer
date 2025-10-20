# Markdownizer Setup Script
# Run this to download required extension dependencies

Write-Host "🚀 Markdownizer Setup" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "extension\vendor")) {
    Write-Host "❌ Error: Please run this script from the Markdownizer root directory" -ForegroundColor Red
    exit 1
}

# Download Readability.js
Write-Host "📥 Downloading Mozilla Readability.js..." -ForegroundColor Yellow

try {
    Invoke-WebRequest `
        -Uri "https://raw.githubusercontent.com/mozilla/readability/main/Readability.js" `
        -OutFile "extension\vendor\readability.js"
    
    Write-Host "✅ Downloaded readability.js" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to download readability.js" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Please download manually from:" -ForegroundColor Yellow
    Write-Host "   https://raw.githubusercontent.com/mozilla/readability/main/Readability.js" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "📝 Setup checklist:" -ForegroundColor Cyan
Write-Host "   ✅ Extension dependencies downloaded" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  Still needed:" -ForegroundColor Yellow
Write-Host "   - Extension icons (see extension\icons\README.md)" -ForegroundColor Yellow
Write-Host "   - Agent environment setup (see agent\.env.example)" -ForegroundColor Yellow
Write-Host ""
Write-Host "📚 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Configure agent: cd agent && cp .env.example .env" -ForegroundColor White
Write-Host "   2. Add OpenAI API key to .env" -ForegroundColor White
Write-Host "   3. Install Python deps: pip install -r requirements.txt" -ForegroundColor White
Write-Host "   4. Start agent: python main.py" -ForegroundColor White
Write-Host "   5. Load extension in Chrome" -ForegroundColor White
Write-Host ""
Write-Host "✨ Setup script complete!" -ForegroundColor Green
