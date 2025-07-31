@echo off
REM ARTAC Quick Start - Start services while build completes

echo Starting ARTAC services (build may continue in background)...

echo Starting core services first...
start "ARTAC Services" wsl.exe -d Ubuntu -- bash -l -c "cd /home/mrdubey/projects/ARTAC/ARTAC && echo 'Starting services...' && docker-compose up; read -p 'ARTAC stopped. Press Enter to exit...'"

echo.  
echo ARTAC is starting up:
echo - Backend will be available at: http://localhost:8000
echo - Frontend will be available at: http://localhost:3000  
echo - Ollama will be available at: http://localhost:11434
echo.
echo Services are starting in the background.
echo The build may take a few more minutes to complete.
echo.
echo Once ready, run setup-ollama.bat to install AI models.
pause