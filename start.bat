@echo off
REM ARTAC Development Mode - Fast startup with live reload

echo Starting ARTAC in Development Mode...

echo Checking Docker and Docker Compose availability...
wsl.exe -d Ubuntu -- bash -l -c "command -v docker && command -v docker-compose" >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker or Docker Compose not found in WSL. Please install Docker Desktop for Windows.
    pause
    exit /b 1
)

echo Starting ARTAC stack (development mode - live reload enabled)...
echo NOTE: If this is first run, Docker build may take 5-10 minutes...
start "ARTAC Dev Stack" wsl.exe -d Ubuntu -- bash -l -c "cd /home/mrdubey/projects/ARTAC/ARTAC && echo 'Starting ARTAC Development stack...' && echo 'Building containers (this may take a while on first run)...' && docker-compose up --build || (echo 'Docker Compose failed, trying fallback mode...' && echo 'Backend fallback...' && cd backend && if [ ! -d 'venv' ]; then echo 'Creating virtual environment...' && python3 -m venv venv; fi && source venv/bin/activate && echo 'Installing dependencies manually (this will take a while)...' && pip install fastapi uvicorn pydantic pydantic-settings python-dotenv httpx aiofiles psutil structlog python-socketio websockets && echo 'Starting with minimal dependencies...' && PERSIST_CLAUDE_SESSIONS=true DATABASE_URL=sqlite:///./artac.db python3 main.py); read -p 'ARTAC Stack stopped. Press Enter to exit...'"

echo.
echo ARTAC Development Mode:
echo - Live reload enabled for both backend and frontend
echo - Code changes are reflected immediately (no rebuild needed)
echo - Dependencies cached in volumes for faster startups
echo.
echo Services:
echo - Database (PostgreSQL): localhost:5432
echo - Redis Cache: localhost:6379  
echo - Backend API: http://localhost:8000 (auto-reload enabled)
echo - Frontend Web: http://localhost:3000 (Next.js dev mode)
echo.
echo Make code changes and they'll be reflected automatically!
echo Press Ctrl+C in the terminal to stop all services.
pause