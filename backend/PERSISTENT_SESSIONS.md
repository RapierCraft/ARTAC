# Persistent Claude Code Sessions

## Overview
By default, when the ARTAC backend shuts down, it terminates all Claude Code CLI sessions to prevent resource leaks. However, you can configure the system to keep Claude Code sessions running even after the backend stops.

## Configuration

### Environment Variable
Set the following environment variable to enable persistent sessions:

```bash
export PERSIST_CLAUDE_SESSIONS=true
```

Or add it to your `.env` file:
```
PERSIST_CLAUDE_SESSIONS=true
```

### How It Works
When `PERSIST_CLAUDE_SESSIONS=true`:

1. **On Backend Shutdown**: Claude Code sessions are detached but not terminated
2. **Process Management**: Sessions are not monitored or cleaned up by the ProcessManager
3. **Session Lifecycle**: Sessions continue running independently of the backend

When `PERSIST_CLAUDE_SESSIONS=false` (default):
1. **On Backend Shutdown**: All Claude Code sessions are gracefully terminated
2. **Process Management**: Active monitoring and cleanup of orphaned processes
3. **Session Lifecycle**: Sessions are tied to backend lifecycle

## Important Notes

### Resource Management
- Persistent sessions will continue consuming system resources
- You'll need to manually manage these processes if they become orphaned
- Monitor system resources when using persistent sessions

### Process Cleanup
To manually clean up persistent Claude Code sessions:

```bash
# Find all Claude processes
ps aux | grep claude

# Kill specific process
kill -TERM <PID>

# Kill all Claude processes (use with caution)
pkill -f claude
```

### Security Considerations
- Persistent sessions maintain their working directories and state
- Ensure proper access controls on agent working directories
- Consider security implications of long-running processes

## Use Cases

### Development & Testing
Enable persistent sessions during development to:
- Keep agent contexts between backend restarts
- Debug agent behavior without losing state
- Test long-running agent tasks

### Production
In production, it's generally recommended to keep `PERSIST_CLAUDE_SESSIONS=false` to:
- Ensure clean resource management
- Prevent orphaned processes
- Maintain predictable system behavior

## Troubleshooting

### Sessions Not Persisting
1. Verify environment variable is set correctly
2. Check logs for "Claude sessions persisted" message on shutdown
3. Ensure proper file permissions for session directories

### Too Many Orphaned Processes
1. List all Claude processes: `ps aux | grep claude`
2. Kill orphaned processes: `pkill -f "claude.*--no-interactive"`
3. Consider setting `PERSIST_CLAUDE_SESSIONS=false`