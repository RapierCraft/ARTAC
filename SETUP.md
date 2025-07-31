# 🚀 RAISC Setup Guide

**RAG-Enabled AI Software Company - Complete Installation & Launch Instructions**

## 📋 Prerequisites

### Required Software
```bash
# Node.js (18.17.0 or higher)
node --version
npm --version

# Python (3.11 or higher)  
python --version
pip --version

# Docker & Docker Compose
docker --version
docker-compose --version

# Claude Code CLI
claude --version
```

### Required API Keys
- **Claude Code CLI**: Must be logged in with Max plan
- **OpenAI API Key**: For embeddings and Whisper STT
- **ElevenLabs API Key**: For TTS voice responses (optional)

## 🛠️ Installation Steps

### 1. Project Setup
```bash
# Clone or navigate to project
cd "/home/mrdubey/Documents/projects/context manager"

# Create environment file
cp .env.example .env

# Edit environment variables
nano .env
```

### 2. Environment Configuration
Update `.env` with your settings:
```bash
# AI Services
CLAUDE_CODE_PATH=claude
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Database
DATABASE_URL=postgresql://raisc_user:raisc_password@localhost:5432/raisc_db
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET_KEY=your_jwt_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here

# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

### 3. Backend Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Verify Claude Code access
claude --version
```

### 4. Frontend Setup
```bash
# Navigate to frontend
cd ../frontend

# Install dependencies
npm install

# Build initial assets
npm run build
```

### 5. Infrastructure Launch
```bash
# From project root
cd ..

# Start infrastructure services
docker-compose up -d postgres redis prometheus grafana

# Verify services are running
docker-compose ps
```

## 🚀 Launch Commands

### Development Mode

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Production Mode
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

## 🌐 Access Points

Once running, access these URLs:

- **Mission Control Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Grafana Monitoring**: http://localhost:3001 (admin/admin)
- **Prometheus Metrics**: http://localhost:9090

## ✅ Verification Steps

### 1. Health Checks
```bash
# Backend health
curl http://localhost:8000/health

# System status
curl http://localhost:8000/api/v1/system/status

# Frontend accessibility
curl http://localhost:3000
```

### 2. Claude Code Integration
```bash
# Test Claude Code CLI
claude --version

# Verify in application logs
tail -f backend/logs/app.log
```

### 3. Database Connection
```bash
# Check database
docker exec -it raisc-postgres psql -U raisc_user -d raisc_db -c "SELECT COUNT(*) FROM agents;"
```

## 🔧 Troubleshooting

### Common Issues

**1. Claude Code CLI Not Found**
```bash
# Install Claude Code CLI
# Ensure it's in PATH
which claude
```

**2. Database Connection Failed**
```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres
```

**3. Port Already in Use**
```bash
# Find process using port
lsof -i :3000
lsof -i :8000

# Kill process or change ports in config
```

**4. NPM Dependencies Issues**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**5. Python Dependencies Issues**
```bash
cd backend
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

## 📊 System Monitoring

### Log Locations
- **Backend Logs**: `backend/logs/`
- **Docker Logs**: `docker-compose logs [service]`
- **System Logs**: Available in Grafana dashboard

### Key Metrics to Monitor
- Agent response times
- Claude Code session health
- Database connection pool
- Memory and CPU usage
- API endpoint performance

## 🔄 Development Workflow

### Making Changes
```bash
# Backend changes - auto-reload enabled
# Edit files in backend/
# Changes reflected immediately

# Frontend changes - hot reload enabled  
# Edit files in frontend/src/
# Browser updates automatically

# Database schema changes
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Adding New Agents
1. Use Mission Control UI to deploy agents
2. Or via API: `POST /api/v1/agents`
3. Monitor in sidebar hierarchy
4. Check Claude Code sessions in logs

## 🛡️ Security Notes

- **Never commit API keys** to version control
- **Use strong JWT secrets** in production
- **Enable HTTPS** for production deployment
- **Regularly rotate credentials**
- **Monitor audit logs** for suspicious activity

## 📚 Additional Resources

- **Architecture Overview**: See `README.md`
- **API Documentation**: http://localhost:8000/docs
- **Component Storybook**: `npm run storybook` (if implemented)
- **Database Schema**: `backend/models/`

## 🚨 Emergency Procedures

### Emergency Stop
1. Use red "STOP" button in Mission Control header
2. Or: `docker-compose down`
3. Or: Kill processes manually

### System Reset
```bash
# Full reset (destructive)
docker-compose down -v
rm -rf backend/logs/*
docker-compose up -d
```

### Backup & Recovery
```bash
# Database backup
docker exec raisc-postgres pg_dump -U raisc_user raisc_db > backup.sql

# Restore database
docker exec -i raisc-postgres psql -U raisc_user raisc_db < backup.sql
```

---

## 🎉 Success!

If all steps completed successfully, you should see:

✅ Mission Control dashboard at http://localhost:3000
✅ Agent hierarchy in left sidebar
✅ Voice interface working in header
✅ Real-time system metrics
✅ Claude Code sessions active

**Welcome to your autonomous AI software company!**

For issues or questions, check the troubleshooting section or review application logs.