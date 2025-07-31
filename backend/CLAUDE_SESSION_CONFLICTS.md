# Preventing Claude Code Session Conflicts

## Problem
When Claude Code sessions are actively working on the backend code and you run the backend server with auto-reload enabled (`uvicorn --reload`), the file watching mechanism can cause Claude Code sessions to exit or become unresponsive. This happens because:

1. **File Watching Conflicts**: Both uvicorn and Claude Code may try to watch/lock the same files
2. **Automatic Restarts**: When Claude modifies backend files, uvicorn detects changes and restarts, potentially disrupting Claude's process
3. **Resource Contention**: Multiple processes accessing the same files can cause unexpected behavior

## Solutions

### Option 1: Use Safe Mode Script (Recommended)
Run the backend without auto-reload using the safe mode script:

```bash
cd backend
./start_safe.sh
```

This runs the backend without file watching, preventing conflicts with Claude Code sessions.

### Option 2: Use --no-reload Flag
Run the development script with the no-reload flag:

```bash
cd backend
./start_dev.sh --no-reload
```

### Option 3: Set Environment Variable
Set the SAFE_RELOAD_MODE environment variable:

```bash
export SAFE_RELOAD_MODE=true
cd backend
python main.py
```

Or add to your `.env` file:
```
SAFE_RELOAD_MODE=true
```

### Option 4: Run Backend Directly
Manually run the backend without reload:

```bash
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

## When to Use Each Option

### Development with Claude Code
When Claude Code sessions are actively working on backend code:
- Use **Option 1** (start_safe.sh) for simplicity
- Use **Option 2** for full dev environment without reload
- Use **Option 3** for persistent configuration

### Regular Development
When not using Claude Code or working on frontend only:
- Use normal `./start_dev.sh` for auto-reload functionality
- Auto-reload is helpful for rapid development

### Production
- Never use auto-reload in production
- Always run without the --reload flag

## Technical Details

### File Watching Exclusions
When auto-reload is enabled, the following directories are excluded:
- `/tmp/raisc-agent-*` - Claude Code working directories
- `**/venv/**` - Virtual environment files
- `**/__pycache__/**` - Python cache files

### Configuration Options
- `SAFE_RELOAD_MODE=true` - Disables auto-reload even in DEBUG mode
- `PERSIST_CLAUDE_SESSIONS=true` - Keeps Claude sessions alive after backend shutdown
- `DEBUG=false` - Disables auto-reload and debug features

## Troubleshooting

### Claude Sessions Still Exiting
1. Ensure you're using one of the safe mode options
2. Check for port conflicts (8000 might be in use)
3. Verify no other file watchers are running
4. Check system resources (memory, CPU)

### Backend Not Updating
When running without auto-reload:
1. You must manually restart the backend after code changes
2. Use Ctrl+C to stop and restart the server
3. Consider using a process manager like supervisord for automatic restarts

### Performance Issues
If you experience slowdowns:
1. Check how many Claude Code sessions are running
2. Monitor system resources with `htop` or `top`
3. Consider limiting concurrent Claude sessions