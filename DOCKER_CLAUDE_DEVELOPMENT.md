# Docker-Based Claude Code Development Environment

## Overview

Instead of having Claude Code sessions work directly on the host system (where they can conflict with running services), we use Docker containers to provide isolated development environments. This approach offers:

- **Complete Isolation**: No conflicts with running backend services
- **Consistency**: Same environment for all Claude Code sessions
- **Resource Management**: Easy to monitor and control resources
- **Clean Cleanup**: Simple container removal when done

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Host System                          │
│                                                          │
│  ┌─────────────────┐        ┌──────────────────────┐   │
│  │ Running Backend │        │  Claude Dev Manager  │   │
│  │  (Port 8000)    │        │    (Orchestrator)    │   │
│  └─────────────────┘        └──────────────────────┘   │
│                                        │                 │
│  ┌─────────────────────────────────────┼──────────────┐ │
│  │              Docker Environment     │              │ │
│  │                                     ▼              │ │
│  │  ┌─────────────────┐    ┌───────────────────┐    │ │
│  │  │ Claude Dev      │    │ Claude Agent 1    │    │ │
│  │  │ Container       │    │ Container         │    │ │
│  │  │ (Main Dev Env)  │    │ (Isolated Agent)  │    │ │
│  │  └─────────────────┘    └───────────────────┘    │ │
│  │                                                    │ │
│  │  ┌─────────────────┐    ┌───────────────────┐    │ │
│  │  │ PostgreSQL Dev  │    │ Redis Dev         │    │ │
│  │  │ (Port 5433)     │    │ (Port 6380)       │    │ │
│  │  └─────────────────┘    └───────────────────┘    │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Start Development Environment

```bash
cd "context manager"
./claude-dev-manager.sh start
```

This will:
- Build the Claude development Docker image
- Start development containers (PostgreSQL, Redis, main dev container)
- Set up networking between containers
- Mount the project directory into containers

### 2. Enter Development Container

```bash
# Enter the main development container
./claude-dev-manager.sh enter

# Or directly with Docker
docker exec -it raisc-claude-dev bash
```

### 3. Work Inside Container

Once inside the container:
```bash
# You're in /workspace/artac (the mounted project)
cd backend
source /home/developer/venv/bin/activate
python main.py  # This won't conflict with host backend!
```

## Claude Code Integration

### Option 1: Manual Agent Containers

Create isolated containers for each Claude agent:

```bash
# Create a new agent container
./claude-dev-manager.sh create agent-001

# Enter the agent container
./claude-dev-manager.sh enter claude-agent-001
```

### Option 2: Programmatic Integration

Update your `AgentManager` to use `ClaudeCodeDockerService`:

```python
from services.claude_code_docker_service import claude_code_docker_service

# Execute Claude command in isolated container
result = await claude_code_docker_service.execute_for_agent(
    agent_id="agent-001",
    command="create a new FastAPI endpoint",
    is_claude_command=True
)
```

## Container Management

### List All Containers
```bash
./claude-dev-manager.sh list
```

### View Container Logs
```bash
./claude-dev-manager.sh logs raisc-claude-dev
```

### Clean Up Stopped Containers
```bash
./claude-dev-manager.sh cleanup
```

### Stop Everything
```bash
./claude-dev-manager.sh stop
```

## Benefits Over Direct Host Development

### 1. No File Watching Conflicts
- Host backend can run with `--reload`
- Container modifications don't trigger host restarts
- Multiple Claude sessions can work simultaneously

### 2. Process Isolation
- No port conflicts (dev uses 5433 for PostgreSQL, 6380 for Redis)
- No process interference
- Clean process management

### 3. Environment Consistency
- All dependencies pre-installed
- Same Python version across all sessions
- Consistent tool versions

### 4. Easy Cleanup
- Simply remove containers when done
- No orphaned processes
- No leftover temporary files on host

## Advanced Usage

### Custom Docker Image

Modify `claude-dev/Dockerfile` to add tools:

```dockerfile
# Add your custom tools
RUN pip install your-package
RUN apt-get install -y your-tool
```

Rebuild:
```bash
./claude-dev-manager.sh build
```

### Persistent Workspaces

Create named volumes for persistent agent workspaces:

```yaml
# In docker-compose.claude-dev.yml
volumes:
  - agent_workspace:/workspace/agent_data
```

### Network Isolation

Create separate networks for different agent groups:

```bash
docker network create raisc-agent-network-1
docker network create raisc-agent-network-2
```

## Troubleshooting

### Container Won't Start
- Check Docker daemon: `docker info`
- Check logs: `docker logs raisc-claude-dev`
- Ensure ports aren't in use: `netstat -tlnp | grep -E '5433|6380'`

### Permission Issues
- Ensure user is in docker group: `groups`
- Add user to docker group: `sudo usermod -aG docker $USER`
- Logout and login again

### Build Failures
- Check Dockerfile syntax
- Ensure base image is accessible
- Clear Docker cache: `docker system prune`

### Connection Issues
- Verify network exists: `docker network ls`
- Check container is on network: `docker inspect raisc-claude-dev`
- Test connectivity: `docker exec raisc-claude-dev ping postgres-dev`

## Best Practices

1. **One Container Per Agent**: Keep agents isolated
2. **Use Named Containers**: Easy identification and management
3. **Regular Cleanup**: Remove stopped containers
4. **Monitor Resources**: Use `docker stats` to watch resource usage
5. **Commit Changes**: Use Docker commit for important container states

## Security Considerations

- Containers have Docker socket access (for Docker-in-Docker)
- Use read-only mounts where possible
- Don't expose unnecessary ports
- Regularly update base images
- Use secrets management for API keys