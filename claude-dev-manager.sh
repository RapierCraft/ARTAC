#!/bin/bash

# ARTAC Claude Development Environment Manager
# Manages Docker-based development environments for Claude Code sessions

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Functions
print_header() {
    echo -e "\n${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║            ARTAC Claude Development Manager                ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}\n"
}

print_status() {
    echo -e "${BLUE}[CLAUDE-DEV]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[CLAUDE-DEV]${NC} ✅ $1"
}

print_warning() {
    echo -e "${YELLOW}[CLAUDE-DEV]${NC} ⚠️  $1"
}

print_error() {
    echo -e "${RED}[CLAUDE-DEV]${NC} ❌ $1"
}

# Check Docker availability
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running or you don't have permissions."
        print_warning "Try: sudo usermod -aG docker $USER && newgrp docker"
        exit 1
    fi
}

# Build the Claude dev image
build_image() {
    print_status "Building Claude development Docker image..."
    
    if docker build -t raisc-claude-dev:latest ./claude-dev; then
        print_success "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
}

# Start development environment
start_dev_env() {
    print_status "Starting Claude development environment..."
    
    # Ensure main network exists
    docker network create raisc-network 2>/dev/null || true
    
    # Start the development containers
    if docker-compose -f docker-compose.claude-dev.yml up -d; then
        print_success "Development environment started"
        
        # Show container status
        echo -e "\n${BLUE}Active Containers:${NC}"
        docker-compose -f docker-compose.claude-dev.yml ps
        
        echo -e "\n${BLUE}Development Environment Details:${NC}"
        echo "  • Main container: raisc-claude-dev"
        echo "  • PostgreSQL (dev): localhost:5433"
        echo "  • Redis (dev): localhost:6380"
        echo "  • Workspace: /workspace/artac (inside container)"
        
        echo -e "\n${BLUE}To enter the development container:${NC}"
        echo "  docker exec -it raisc-claude-dev bash"
        
    else
        print_error "Failed to start development environment"
        exit 1
    fi
}

# Stop development environment
stop_dev_env() {
    print_status "Stopping Claude development environment..."
    
    if docker-compose -f docker-compose.claude-dev.yml down; then
        print_success "Development environment stopped"
    else
        print_warning "Some containers may not have stopped cleanly"
    fi
}

# Enter development container
enter_container() {
    local container_name="${1:-raisc-claude-dev}"
    
    print_status "Entering container: $container_name"
    
    if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        docker exec -it "$container_name" bash
    else
        print_error "Container '$container_name' is not running"
        print_warning "Start the environment first: $0 start"
        exit 1
    fi
}

# Create a new Claude agent container
create_agent_container() {
    local agent_id="${1:-agent-$(date +%s)}"
    local container_name="claude-agent-$agent_id"
    
    print_status "Creating new Claude agent container: $container_name"
    
    # Ensure image is built
    if ! docker images -q raisc-claude-dev:latest | grep -q .; then
        build_image
    fi
    
    # Create and start container
    docker run -d \
        --name "$container_name" \
        --hostname "$container_name" \
        --network raisc-network \
        -v "$SCRIPT_DIR:/workspace/artac" \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -e "AGENT_ID=$agent_id" \
        -e "ENVIRONMENT=development" \
        raisc-claude-dev:latest \
        tail -f /dev/null
    
    if [ $? -eq 0 ]; then
        print_success "Agent container created: $container_name"
        echo -e "\n${BLUE}To enter this container:${NC}"
        echo "  docker exec -it $container_name bash"
    else
        print_error "Failed to create agent container"
        exit 1
    fi
}

# List all Claude containers
list_containers() {
    print_status "Claude development containers:"
    
    echo -e "\n${BLUE}Development Environment:${NC}"
    docker ps -a --filter "name=raisc-claude-dev" --filter "name=raisc-postgres-dev" --filter "name=raisc-redis-dev" \
        --format "table {{.Names}}\t{{.Status}}\t{{.Created}}"
    
    echo -e "\n${BLUE}Agent Containers:${NC}"
    docker ps -a --filter "name=claude-agent-" \
        --format "table {{.Names}}\t{{.Status}}\t{{.Created}}"
}

# Clean up stopped containers
cleanup_containers() {
    print_status "Cleaning up stopped Claude containers..."
    
    local count=$(docker ps -a -q --filter "name=claude-agent-" --filter "status=exited" | wc -l)
    
    if [ "$count" -gt 0 ]; then
        docker rm $(docker ps -a -q --filter "name=claude-agent-" --filter "status=exited")
        print_success "Removed $count stopped containers"
    else
        print_status "No stopped containers to clean up"
    fi
}

# Show logs
show_logs() {
    local container_name="${1:-raisc-claude-dev}"
    
    print_status "Showing logs for: $container_name"
    docker logs -f "$container_name"
}

# Main menu
show_help() {
    print_header
    
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  build              Build the Claude development Docker image"
    echo "  start              Start the development environment"
    echo "  stop               Stop the development environment"
    echo "  restart            Restart the development environment"
    echo "  enter [name]       Enter a container (default: raisc-claude-dev)"
    echo "  create [agent-id]  Create a new agent container"
    echo "  list               List all Claude containers"
    echo "  logs [name]        Show container logs"
    echo "  cleanup            Remove stopped agent containers"
    echo "  help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start development environment"
    echo "  $0 enter                    # Enter main dev container"
    echo "  $0 create agent-123         # Create agent container"
    echo "  $0 enter claude-agent-123   # Enter specific container"
}

# Main script logic
check_docker

case "${1:-help}" in
    build)
        build_image
        ;;
    start)
        start_dev_env
        ;;
    stop)
        stop_dev_env
        ;;
    restart)
        stop_dev_env
        sleep 2
        start_dev_env
        ;;
    enter)
        enter_container "${2}"
        ;;
    create)
        create_agent_container "${2}"
        ;;
    list)
        list_containers
        ;;
    logs)
        show_logs "${2}"
        ;;
    cleanup)
        cleanup_containers
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac