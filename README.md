# 🤖 ARTAC - Agentic Runtime & Task Allocation Controller

**A fully autonomous, hierarchical AI development organization that operates 24/7 with minimal human oversight.**

## 🎯 Project Overview

ARTAC creates a complete AI-powered software company featuring:
- **Hierarchical AI Agents** (Executive → Management → Development → Execution)
- **Voice-Controlled Management** via Whisper STT + TTS
- **RAG-Based Context Management** for codebase understanding
- **Enterprise Security** with IAM and audit trails
- **Mission Control Dashboard** for human oversight

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           MISSION CONTROL               │
│  Voice Interface + Real-time Dashboard  │
├─────────────────────────────────────────┤
│              AGENT HIERARCHY            │
│  CEO → CTO → CQO → HR → Research        │
│    ↓                                    │
│  Senior Agents (Tech Leads)             │
│    ↓                                    │
│  Mid-Level Agents (Senior Devs)         │
│    ↓                                    │
│  Junior Agents (Developers)             │
├─────────────────────────────────────────┤
│               RAG SYSTEM                │
│  Codebase + External Data + Learning    │
├─────────────────────────────────────────┤
│            INFRASTRUCTURE               │
│  PostgreSQL + Redis + Kubernetes        │
└─────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

Before installing ARTAC, ensure you have the following:

- **Python 3.12+** with pip
- **Node.js 18+** with npm
- **Docker Desktop** with WSL integration (for Windows users)
- **Ollama** for local AI model inference
- **Git** for version control

### Installation Steps

#### 1. Clone the Repository

```bash
git clone https://github.com/RapierCraft/ARTAC.git
cd ARTAC
```

#### 2. Install Ollama and Required Model

```bash
# Install Ollama (if not already installed)
# Visit https://ollama.com for installation instructions

# Pull the required model
ollama pull llama3.2:3b
```

#### 3. Backend Setup

```bash
cd backend

# Install Python virtual environment package (Ubuntu/Debian)
sudo apt update && sudo apt install -y python3.12-venv

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (use minimal requirements for faster setup)
pip install -r requirements-minimal.txt
# For full installation: pip install -r requirements.txt
```

#### 4. Frontend Setup

```bash
cd ../frontend

# Install dependencies with legacy peer deps flag (due to React 19 compatibility)
npm install --legacy-peer-deps
```

#### 5. Docker Setup (Optional)

If you have Docker Desktop installed:

**For Windows/WSL users:**
1. Open Docker Desktop Settings
2. Go to Resources → WSL Integration
3. Enable integration with your WSL distribution
4. Apply & Restart

```bash
# Verify Docker is working
docker --version
docker compose version
```

#### 6. Running the Application

**Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm run dev
```

Access the Mission Control Dashboard at: http://localhost:3000

### Common Issues & Solutions

1. **Python venv error**: Install `python3.12-venv` package
2. **React peer dependency conflicts**: Use `--legacy-peer-deps` flag
3. **Docker not found in WSL**: Enable WSL integration in Docker Desktop
4. **Ollama connection failed**: Ensure Ollama is running (`ollama serve`)
5. **Port already in use**: Check for existing processes on ports 8000 (backend) and 3000 (frontend)

### Configuration

Create a `.env` file in the backend directory with your API keys:

```bash
cd backend
cp .env.example .env  # If example exists, otherwise create new
```

Add the following environment variables as needed:

```env
# Claude API (if using Claude directly)
ANTHROPIC_API_KEY=your_anthropic_api_key

# OpenAI API (for alternative LLM support)
OPENAI_API_KEY=your_openai_api_key

# ElevenLabs (for voice synthesis)
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# Ollama configuration
OLLAMA_BASE_URL=http://localhost:11434

# Database (optional for basic functionality)
DATABASE_URL=postgresql://user:password@localhost/artac
```

## 📋 Development Phases

- **Phase 1** (Weeks 1-8): Foundation & Infrastructure
- **Phase 2** (Weeks 9-18): Intelligence & Voice Interface  
- **Phase 3** (Weeks 19-26): Production & Security
- **Phase 4** (Weeks 27-30): Enhancement & Optimization

## 🎯 Success Metrics

- **300%** faster development velocity
- **80%** cost reduction
- **99.9%** system uptime
- **95%** voice command accuracy

---

## 🎯 Current Status

**Status**: ✅ **Phase 1 Complete** - Foundation & Core Dashboard Ready
**Version**: 0.1.0-alpha
**Last Updated**: January 2025

### 📦 Dependencies & Requirements

- **Backend**: FastAPI, SQLAlchemy, Langchain, Ollama integration
- **Frontend**: Next.js 14, React 19, shadcn/ui, TailwindCSS
- **AI Models**: Ollama with llama3.2:3b (2GB download)
- **Voice**: Whisper STT, ElevenLabs TTS
- **Infrastructure**: Docker (optional), PostgreSQL (optional), Redis (optional)

### ✅ Completed Features
- **Complete Project Architecture** - Full system design and PRD
- **Backend Infrastructure** - FastAPI with Claude Code CLI integration
- **Database Schema** - PostgreSQL with pgvector for RAG
- **Mission Control Dashboard** - Next.js with shadcn/ui
- **Voice Interface** - Whisper STT integration with personality-based responses
- **Agent Hierarchy Management** - Executive → Management → Development → Execution
- **Real-time Monitoring** - System health and performance metrics
- **Docker Infrastructure** - Complete containerization setup

### 🔧 Ready for Development
- All core components implemented and functional
- Claude Code integration with your Max plan
- Production-ready architecture with security best practices
- Comprehensive setup and deployment guides

### 📖 Getting Started
1. **Read Setup Guide**: See `SETUP.md` for detailed installation steps
2. **Install Dependencies**: Backend (Python) + Frontend (Node.js) + Docker
3. **Configure Environment**: Add your API keys and settings
4. **Launch System**: `docker-compose up -d` + development servers
5. **Access Dashboard**: http://localhost:3000

### 🚀 Next Development Phases
- **Phase 2**: WebSocket real-time updates, enhanced voice features
- **Phase 3**: Advanced simulation center, security monitoring
- **Phase 4**: Full autonomous operation with self-healing capabilities

**Your autonomous AI software company foundation is ready for deployment!**