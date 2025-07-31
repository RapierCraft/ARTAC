@echo off
REM ARTAC Dependencies Installer - Manual approach

echo Installing ARTAC Backend Dependencies...
echo This will take several minutes. Please be patient.

wsl.exe -d Ubuntu -- bash -l -c "cd /home/mrdubey/projects/ARTAC/ARTAC/backend && echo 'Creating virtual environment...' && python3 -m venv venv && source venv/bin/activate && echo 'Installing core dependencies...' && pip install --upgrade pip && echo 'Installing web framework...' && pip install fastapi uvicorn gunicorn && echo 'Installing utilities...' && pip install pydantic pydantic-settings python-dotenv httpx aiofiles python-slugify && echo 'Installing database...' && pip install asyncpg sqlalchemy alembic psycopg2-binary pgvector && echo 'Installing AI libraries (this takes longest)...' && pip install openai anthropic tiktoken sentence-transformers && echo 'Installing langchain...' && pip install langchain langchain-openai langchain-anthropic && echo 'Installing monitoring...' && pip install psutil structlog prometheus-client && echo 'Installing websockets...' && pip install python-socketio websockets && echo 'Installing auth...' && pip install python-jose[cryptography] passlib[bcrypt] python-multipart cryptography && echo 'Installing voice...' && pip install elevenlabs pydub numpy && echo 'Installing git...' && pip install PyGithub gitpython && echo 'Installing redis...' && pip install redis[hiredis] aioredis && echo 'All dependencies installed!' && touch venv/.installed"

echo.
echo Dependencies installation completed!
echo You can now run start.bat to start ARTAC
pause