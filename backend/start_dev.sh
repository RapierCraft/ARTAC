#!/bin/bash

# RAISC Development Startup Script
# One-stop script to start backend and frontend services

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[RAISC]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[RAISC]${NC} ✅ $1"
}

print_warning() {
    echo -e "${YELLOW}[RAISC]${NC} ⚠️  $1"
}

print_error() {
    echo -e "${RED}[RAISC]${NC} ❌ $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to cleanup on script exit
cleanup() {
    print_status "Shutting down services..."
    
    # Kill all background processes started by this script
    if [[ -n ${BACKEND_PID:-} ]]; then
        print_status "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [[ -n ${FRONTEND_PID:-} ]]; then
        print_status "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Stop Docker services
    print_status "Stopping Docker services..."
    cd "$(dirname "$0")/.." && docker compose down 2>/dev/null || true
    
    print_success "Cleanup completed"
    exit 0
}

# Setup signal handlers
trap cleanup SIGINT SIGTERM

print_status "🚀 Starting RAISC Development Environment..."

# Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists python3; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

if ! command_exists node; then
    print_error "Node.js is required but not installed"
    exit 1
fi

if ! command_exists npm; then
    print_error "npm is required but not installed"
    exit 1
fi

DOCKER_AVAILABLE=false
if command_exists docker; then
    # Check if we can actually use docker compose from project root
    cd "$PROJECT_ROOT" 2>/dev/null || cd "$(dirname "$SCRIPT_DIR")"
    if docker compose version >/dev/null 2>&1; then
        DOCKER_AVAILABLE=true
        print_success "Docker Compose found and accessible - will start full infrastructure"
    else
        print_warning "Docker found but not accessible - you may need to log out/in or run 'newgrp docker'"
    fi
else
    print_warning "Docker not found - starting in basic mode (backend + frontend only)"
fi

if ! command_exists claude; then
    print_warning "Claude Code CLI not found in PATH. Please ensure it's installed and configured."
fi

print_success "All prerequisites found"

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$SCRIPT_DIR"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

print_status "Project root: $PROJECT_ROOT"
print_status "Backend dir: $BACKEND_DIR"
print_status "Frontend dir: $FRONTEND_DIR"

# Start Docker infrastructure if available
if [[ "$DOCKER_AVAILABLE" == "true" ]]; then
    print_status "Starting Docker infrastructure (PostgreSQL, Redis, Prometheus, Grafana)..."
    cd "$PROJECT_ROOT"
    if docker compose up -d postgres redis prometheus grafana 2>/dev/null; then
        print_success "Docker services started successfully"
        
        # Wait for database to be ready
        print_status "Waiting for database to be ready..."
        sleep 10
        
        # Check if services are running
        print_status "Checking Docker services status..."
        docker compose ps 2>/dev/null || true
    else
        print_warning "Failed to start Docker services - falling back to basic mode"
        print_warning "You may need to run 'sudo usermod -aG docker $USER' and logout/login"
        DOCKER_AVAILABLE=false
    fi
fi

if [[ "$DOCKER_AVAILABLE" == "false" ]]; then
    print_status "Setting up SQLite database for basic mode..."
    
    # Create basic database directory
    mkdir -p "$PROJECT_ROOT/data"
    
    # Set environment variables for SQLite
    export DATABASE_URL="sqlite:///$PROJECT_ROOT/data/raisc.db"
    export REDIS_URL="redis://localhost:6379"
    export ENVIRONMENT="development"
    export DEBUG="true"
    
    print_success "Basic mode database setup completed"
    print_status "Using SQLite database at: $PROJECT_ROOT/data/raisc.db"
fi

# Setup backend
print_status "Setting up backend..."
cd "$BACKEND_DIR"

# Check if virtual environment exists
if [[ ! -d "venv" ]]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install/update Python dependencies
print_status "Installing/updating Python dependencies..."
./venv/bin/pip install -q --upgrade pip

if ./venv/bin/pip install -q -r requirements.txt; then
    print_success "Python dependencies installed successfully"
else
    print_warning "Some dependencies failed to install - attempting minimal installation..."
    # Install core dependencies for basic functionality
    ./venv/bin/pip install -q fastapi uvicorn sqlalchemy python-dotenv pydantic psutil aiosqlite
fi

# Setup frontend
print_status "Setting up frontend..."
cd "$FRONTEND_DIR"

# Install/update Node.js dependencies
if [[ ! -d "node_modules" ]] || [[ "package.json" -nt "node_modules" ]]; then
    print_status "Installing/updating Node.js dependencies..."
    npm install --silent
else
    print_status "Node.js dependencies are up to date"
fi

# Start services
print_status "Starting services..."

# Check if --no-reload flag was passed
NO_RELOAD=false
for arg in "$@"; do
    if [[ "$arg" == "--no-reload" ]]; then
        NO_RELOAD=true
        break
    fi
done

# Start backend
print_status "Starting backend server on http://localhost:8000..."
cd "$BACKEND_DIR"
source venv/bin/activate

if [[ "$NO_RELOAD" == "true" ]]; then
    print_warning "Starting without auto-reload (safer for Claude Code sessions)"
    uvicorn main:app --host 0.0.0.0 --port 8000 &
else
    print_status "Starting with auto-reload enabled"
    # Exclude Claude Code working directories from reload watching
    uvicorn main:app --reload --host 0.0.0.0 --port 8000 \
        --reload-exclude '/tmp/raisc-agent-*' \
        --reload-exclude '**/venv/**' \
        --reload-exclude '**/__pycache__/**' &
fi
BACKEND_PID=$!

# Give backend time to start
sleep 3

# Start frontend
print_status "Starting frontend server on http://localhost:3000..."
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

# Give frontend time to start
sleep 3

# Print status
print_success "🎉 RAISC Development Environment Started Successfully!"
echo ""
print_status "📊 Access Points:"
echo "   • Mission Control Dashboard: http://localhost:3000"
echo "   • Backend API: http://localhost:8000"
echo "   • API Documentation: http://localhost:8000/docs"
echo "   • Grafana Monitoring: http://localhost:3001 (admin/admin)"
echo "   • Prometheus Metrics: http://localhost:9090"
echo ""
print_status "🔧 Process IDs:"
echo "   • Backend PID: $BACKEND_PID"
echo "   • Frontend PID: $FRONTEND_PID"
echo ""
print_status "📝 Logs:"
echo "   • Backend logs: Active in this terminal"
echo "   • Frontend logs: Check separate terminal or docker-compose logs -f frontend"
echo "   • Docker logs: docker-compose logs -f [service]"
echo ""
print_warning "Press Ctrl+C to stop all services"

# Wait for background processes and show their output
wait $BACKEND_PID $FRONTEND_PID