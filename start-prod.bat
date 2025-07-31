@echo off
REM ARTAC Production Mode - Full rebuild and optimized for production

echo Starting ARTAC in Production Mode...

echo Checking Docker and Docker Compose availability...
wsl.exe -d Ubuntu -- bash -l -c "command -v docker && command -v docker-compose" >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker or Docker Compose not found in WSL. Please install Docker Desktop for Windows.
    pause
    exit /b 1
)

echo Building and starting ARTAC stack (production build - includes rebuild)...
start "ARTAC Production Stack" wsl.exe -d Ubuntu -- bash -l -c "cd /home/mrdubey/projects/ARTAC/ARTAC && echo 'Starting ARTAC Production stack...' && docker-compose up --build; read -p 'ARTAC Stack stopped. Press Enter to exit...'"

echo.
echo ARTAC Production Mode:
echo - Full rebuild ensures latest dependencies
echo - Optimized for production deployment
echo - No live reload (stable performance)
echo.
echo Services:
echo - Database (PostgreSQL): localhost:5432
echo - Redis Cache: localhost:6379  
echo - Backend API: http://localhost:8000 (production mode)
echo - Frontend Web: http://localhost:3000 (production build)
echo.
echo Production deployment ready!
echo Press Ctrl+C in the terminal to stop all services.
pause