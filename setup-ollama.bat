@echo off
REM ARTAC Ollama Setup - Pull required models

echo Setting up Ollama models for ARTAC...
echo This will download AI models (several GB). Please be patient.

echo Checking if Ollama is running...
wsl.exe -d Ubuntu -- bash -l -c "cd /home/mrdubey/projects/ARTAC/ARTAC && docker-compose ps ollama" | findstr "running" >nul
if %errorlevel% neq 0 (
    echo Ollama container not running. Starting services first...
    wsl.exe -d Ubuntu -- bash -l -c "cd /home/mrdubey/projects/ARTAC/ARTAC && docker-compose up -d ollama"
    echo Waiting for Ollama to start...
    timeout /t 10 /nobreak >nul
)

echo Pulling Llama 3.2 model (recommended for agents)...
wsl.exe -d Ubuntu -- bash -l -c "cd /home/mrdubey/projects/ARTAC/ARTAC && docker-compose exec ollama ollama pull llama3.2:3b"

echo Pulling CodeLlama model (for code generation)...
wsl.exe -d Ubuntu -- bash -l -c "cd /home/mrdubey/projects/ARTAC/ARTAC && docker-compose exec ollama ollama pull codellama:7b"

echo Pulling Mistral model (fast and efficient)...
wsl.exe -d Ubuntu -- bash -l -c "cd /home/mrdubey/projects/ARTAC/ARTAC && docker-compose exec ollama ollama pull mistral:7b"

echo.
echo Ollama models installed successfully!
echo Available models:
wsl.exe -d Ubuntu -- bash -l -c "cd /home/mrdubey/projects/ARTAC/ARTAC && docker-compose exec ollama ollama list"

echo.
echo Models are ready for ARTAC agent generation!
pause