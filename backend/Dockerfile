FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Node.js for Claude CLI
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    ffmpeg \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install the real Claude CLI
RUN npm install -g @anthropic-ai/claude-code

# Verify Claude CLI installation and configure
RUN which claude || echo "Claude CLI not found in PATH"
RUN claude --version || echo "Claude CLI version check failed"

# Copy requirements first for better caching
COPY requirements.txt requirements.txt

# Install Python dependencies in stages to avoid timeouts
RUN pip install --no-cache-dir --upgrade pip

# Install core packages first (fast)
RUN pip install --no-cache-dir \
    fastapi==0.116.1 \
    uvicorn[standard]==0.35.0 \
    pydantic==2.11.7 \
    pydantic-settings==2.10.1 \
    python-dotenv==1.1.1 \
    httpx==0.28.1 \
    aiofiles==24.1.0 \
    psutil==7.0.0 \
    structlog==25.4.0

# Install database packages
RUN pip install --no-cache-dir \
    asyncpg==0.30.0 \
    sqlalchemy[asyncio]==2.0.42 \
    alembic==1.16.4 \
    psycopg2-binary==2.9.10 \
    pgvector==0.4.1

# Install AI packages with timeout protection
RUN pip install --no-cache-dir --timeout 300 \
    openai==1.98.0 \
    anthropic==0.60.0 \
    tiktoken==0.9.0 \
    ollama==0.5.1

# Install remaining packages
RUN pip install --no-cache-dir \
    redis[hiredis]==6.2.0 \
    python-socketio==5.13.0 \
    websockets==15.0.1 \
    python-jose[cryptography]==3.5.0 \
    passlib[bcrypt]==1.7.4 \
    python-multipart==0.0.20

# Install collaboration system dependencies first
RUN pip install --no-cache-dir --timeout 300 \
    aiosqlite==0.20.0 \
    numpy==2.0.0

# Install ML packages in small batches to avoid timeouts
# Use --retries and --timeout to handle network issues
RUN pip install --no-cache-dir --timeout 600 --retries 3 faiss-cpu==1.9.0
RUN pip install --no-cache-dir --timeout 600 --retries 3 sentence-transformers==5.0.0

# Install voice processing packages
RUN pip install --no-cache-dir --timeout 300 \
    elevenlabs==2.8.1 \
    pydub==0.25.1

# Install whisper separately as it's large and can timeout
RUN pip install --no-cache-dir --timeout 1200 --retries 2 openai-whisper==20250625

# Copy application code
COPY . .

# Create non-root user for security with same UID as host user
RUN useradd --create-home --shell /bin/bash --uid 1000 artac

# Set up Claude CLI configuration directory with proper permissions
RUN mkdir -p /home/artac/.claude && chown -R artac:artac /home/artac/.claude

# Copy and run setup script as root before switching user
COPY scripts/setup_claude_auth.sh /tmp/setup_claude_auth.sh
RUN chmod +x /tmp/setup_claude_auth.sh

RUN chown -R artac:artac /app
USER artac

# Set Claude home directory
ENV CLAUDE_HOME=/home/artac/.claude

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]