# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ARTAC (Autonomous RAG-Enabled AI Software Company) is a hierarchical AI development organization where multiple Claude Code CLI sessions operate autonomously. The system features voice control, real-time monitoring, and RAG-based context management.

## Development Commands

### Backend (Python/FastAPI)
```bash
# Navigate to backend
cd backend/

# Activate virtual environment
source venv/bin/activate

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Code quality checks
black .           # Format code
isort .          # Sort imports
flake8           # Lint
mypy .           # Type check
pytest           # Run tests (when implemented)

# Run a single test
pytest tests/test_specific.py::test_function_name -v
```

### Frontend (TypeScript/Next.js)
```bash
# Navigate to frontend
cd frontend/

# Development server
npm run dev

# Production build
npm run build
npm run start

# Code quality
npm run lint        # ESLint
npm run type-check  # TypeScript check
npm run format      # Prettier formatting
```

### Infrastructure
```bash
# From root directory
cd .

# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d postgres redis

# View logs
docker-compose logs -f [service]

# Stop services
docker-compose down
docker-compose down -v  # Also remove volumes
```

## Architecture Overview

### Core System Design
The system implements **Multi-Agent Claude Code Session Management** where each AI agent runs in its own headless Claude Code CLI session.

**Key Services:**
- **ClaudeCodeService** (`backend/services/claude_code_service.py`): Manages headless Claude Code sessions with `--no-interactive --quiet` flags
- **AgentManager** (`backend/services/agent_manager.py`): Orchestrates the agent hierarchy (Executive → Management → Development → Execution)
- **ProcessManager** (`backend/services/process_manager.py`): Monitors all Claude Code processes
- **RAGService** (`backend/services/rag_service.py`): Provides context from pgvector embeddings

**Agent Working Directories:** `/tmp/raisc-agent-{agent_id}-{uuid}/`

### Database Schema (PostgreSQL + pgvector)
- `agents`: Hierarchical agent records with performance metrics
- `tasks`: Task delegation and tracking
- `embeddings`: RAG context storage (pgvector)
- `audit_logs`: Immutable event tracking with cryptographic hashing
- `conversations`: Voice interface history

### Frontend Architecture
- **Framework**: Next.js 14 with App Router
- **State Management**: Zustand (`src/stores/system-store.ts`)
- **UI Components**: shadcn/ui (Radix UI based)
- **Real-time Updates**: Socket.io client
- **Styling**: Tailwind CSS with custom animations

### Critical Implementation Details
1. Each agent maintains persistent state in isolated working directories
2. Claude Code processes run detached from terminal (`start_new_session=True`)
3. All agent actions are logged in the immutable audit trail
4. Voice commands processed through Whisper STT → Agent hierarchy → TTS response
5. WebSocket connections provide real-time dashboard updates

## Environment Requirements

```bash
# Required API Keys
CLAUDE_CODE_PATH=claude              # Path to Claude Code CLI
OPENAI_API_KEY=your_key             # For embeddings and Whisper
ELEVENLABS_API_KEY=your_key         # For TTS (optional)

# Database
DATABASE_URL=postgresql://raisc_user:raisc_password@localhost:5432/raisc_db
REDIS_URL=redis://localhost:6379

# Application
ENVIRONMENT=development
DEBUG=true
```

## Key Development Notes

1. **Claude Code Integration**: Always use `ClaudeCodeService` for agent interactions. Sessions run headless - no terminal UI appears.

2. **Agent Hierarchy**:
   - Executive: CEO, CTO, CQO (strategic decisions)
   - Management: Tech leads, project managers (task delegation)
   - Development: Senior developers (implementation)
   - Execution: Junior developers (specific tasks)

3. **Voice Interface**: Whisper STT in Mission Control header → Commands delegated through hierarchy → ElevenLabs TTS responses

4. **Security**: All actions logged with cryptographic hashing, process isolation for Claude Code sessions

5. **File Paths**: All components are now in the root directory for easier navigation.

## Access Points
- Mission Control: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Grafana: http://localhost:3001 (admin/admin)