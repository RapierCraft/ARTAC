# Claude Code Development Container
# Provides isolated environment for Claude Code sessions to work on ARTAC

FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install base dependencies
RUN apt-get update && apt-get install -y \
    # Basic tools
    curl wget git vim nano \
    # Build essentials
    build-essential \
    # Python development
    python3 python3-pip python3-venv python3-dev \
    # Node.js setup
    nodejs npm \
    # Database clients
    postgresql-client redis-tools \
    # System utilities
    htop tree jq \
    # Docker CLI (for Docker-in-Docker capability)
    docker.io \
    # SSH for remote development
    openssh-server \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 18.x (LTS)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Create development user
RUN useradd -m -s /bin/bash developer \
    && usermod -aG docker developer

# Set up SSH (for potential remote access)
RUN mkdir /var/run/sshd \
    && echo 'developer:developer' | chpasswd \
    && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Create workspace directory
RUN mkdir -p /workspace && chown developer:developer /workspace

# Switch to developer user
USER developer
WORKDIR /workspace

# Set up Python virtual environment
RUN python3 -m venv /home/developer/venv

# Add venv to PATH
ENV PATH="/home/developer/venv/bin:$PATH"

# Pre-install common Python packages
RUN pip install --upgrade pip && \
    pip install \
    fastapi uvicorn sqlalchemy pydantic \
    pytest black flake8 mypy isort \
    httpx aiofiles python-multipart \
    redis asyncpg psycopg2-binary \
    openai anthropic elevenlabs \
    python-dotenv pydantic-settings

# Set up bash aliases and environment
RUN echo 'alias ll="ls -alF"' >> ~/.bashrc && \
    echo 'alias la="ls -A"' >> ~/.bashrc && \
    echo 'alias l="ls -CF"' >> ~/.bashrc && \
    echo 'export PATH="/home/developer/venv/bin:$PATH"' >> ~/.bashrc && \
    echo 'cd /workspace' >> ~/.bashrc

# Create a marker file to identify this as a Claude dev container
RUN echo "Claude Code Development Container for ARTAC" > /home/developer/.claude-dev-container

# Default command
CMD ["/bin/bash"]