# Start all backend services (Django + 2 FastAPI) in background
Write-Host "🚀 Starting PaisaPro Backend Services..." -ForegroundColor Cyan

# Activate virtual environment
. .\venv\Scripts\Activate.ps1

# Start Django in background
Write-Host "1️⃣  Starting Django (Port 8000)..." -ForegroundColor Yellow
$django = Start-Process -FilePath "python" -ArgumentList "manage.py", "runserver" -PassThru -NoNewWindow

Start-Sleep -Seconds 3

# Start Price Comparison API in background
Write-Host "2️⃣  Starting Price Comparison API (Port 8001)..." -ForegroundColor Yellow
$priceApi = Start-Process -FilePath "python" -ArgumentList "sda_app\fastapi_backend.py" -PassThru -NoNewWindow

Start-Sleep -Seconds 3

# Start Shopping Cart API in foreground (keeps terminal open)
Write-Host "3️⃣  Starting Shopping Cart API (Port 8002)..." -ForegroundColor Yellow
Write-Host ""
Write-Host "✅ All backend services starting!" -ForegroundColor Green
Write-Host "   Django:        http://localhost:8000" -ForegroundColor White
Write-Host "   Price API:     http://localhost:8001" -ForegroundColor White
Write-Host "   Shopping Cart: http://localhost:8002" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Run shopping cart in foreground
python sda_app\shopping_cart_backend.py

# Cleanup when shopping cart stops
Write-Host "`nStopping all backend services..." -ForegroundColor Yellow
Stop-Process -Id $django.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $priceApi.Id -Force -ErrorAction SilentlyContinue
Write-Host "All services stopped." -ForegroundColor Green
