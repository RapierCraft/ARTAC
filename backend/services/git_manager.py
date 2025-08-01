"""
ARTAC Git Manager
Advanced Git operations for multi-agent collaboration
"""

import asyncio
import json
import os
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import re

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


class GitConflictResolver:
    """AI-powered Git conflict resolution"""
    
    def __init__(self):
        self.conflict_strategies = {
            "code": self._resolve_code_conflict,
            "config": self._resolve_config_conflict,
            "docs": self._resolve_docs_conflict,
            "test": self._resolve_test_conflict
        }
    
    async def resolve_conflict(self, file_path: str, conflict_content: str) -> Optional[str]:
        """Resolve Git merge conflict using AI"""
        try:
            file_type = self._get_file_type(file_path)
            strategy = self.conflict_strategies.get(file_type, self._resolve_generic_conflict)
            
            resolved_content = await strategy(file_path, conflict_content)
            
            if resolved_content:
                logger.log_system_event("conflict_resolved", {
                    "file_path": file_path,
                    "file_type": file_type,
                    "resolution_strategy": strategy.__name__
                })
            
            return resolved_content
            
        except Exception as e:
            logger.log_error(e, {
                "action": "resolve_conflict",
                "file_path": file_path
            })
            return None
    
    def _get_file_type(self, file_path: str) -> str:
        """Determine file type for conflict resolution strategy"""
        if file_path.endswith(('.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.cpp', '.c')):
            return "code"
        elif file_path.endswith(('.json', '.yaml', '.yml', '.toml', '.ini')):
            return "config"
        elif file_path.endswith(('.md', '.txt', '.rst')):
            return "docs"
        elif file_path.endswith(('.test.py', '.test.js', '.spec.js', '.spec.ts')):
            return "test"
        return "generic"
    
    async def _resolve_code_conflict(self, file_path: str, conflict_content: str) -> Optional[str]:
        """Resolve code conflicts with intelligent merging"""
        # Parse conflict markers
        conflicts = self._parse_conflict_markers(conflict_content)
        resolved_content = conflict_content
        
        for conflict in conflicts:
            # Analyze both versions
            current_version = conflict["current"]
            incoming_version = conflict["incoming"]
            
            # Smart merge based on code patterns
            if self._is_import_section(current_version, incoming_version):
                merged = self._merge_imports(current_version, incoming_version)
            elif self._is_function_definition(current_version, incoming_version):
                merged = self._merge_functions(current_version, incoming_version)
            else:
                # Default to incoming version for now
                merged = incoming_version
            
            # Replace conflict with merged version
            resolved_content = resolved_content.replace(
                f"<<<<<<< HEAD\n{current_version}=======\n{incoming_version}>>>>>>> ",
                merged
            )
        
        return resolved_content
    
    async def _resolve_config_conflict(self, file_path: str, conflict_content: str) -> Optional[str]:
        """Resolve configuration file conflicts"""
        if file_path.endswith('.json'):
            return await self._resolve_json_conflict(conflict_content)
        else:
            return await self._resolve_generic_conflict(file_path, conflict_content)
    
    async def _resolve_json_conflict(self, conflict_content: str) -> Optional[str]:
        """Resolve JSON configuration conflicts"""
        try:
            conflicts = self._parse_conflict_markers(conflict_content)
            resolved_content = conflict_content
            
            for conflict in conflicts:
                try:
                    current_json = json.loads(conflict["current"])
                    incoming_json = json.loads(conflict["incoming"])
                    
                    # Merge JSON objects
                    merged_json = self._deep_merge_json(current_json, incoming_json)
                    merged_str = json.dumps(merged_json, indent=2)
                    
                    # Replace conflict with merged JSON
                    resolved_content = resolved_content.replace(
                        f"<<<<<<< HEAD\n{conflict['current']}=======\n{conflict['incoming']}>>>>>>> ",
                        merged_str
                    )
                except json.JSONDecodeError:
                    # If JSON parsing fails, use incoming version
                    resolved_content = resolved_content.replace(
                        f"<<<<<<< HEAD\n{conflict['current']}=======\n{conflict['incoming']}>>>>>>> ",
                        conflict["incoming"]
                    )
            
            return resolved_content
            
        except Exception as e:
            logger.log_error(e, {"action": "resolve_json_conflict"})
            return None
    
    async def _resolve_docs_conflict(self, file_path: str, conflict_content: str) -> Optional[str]:
        """Resolve documentation conflicts"""
        # For docs, usually prefer the more comprehensive version
        conflicts = self._parse_conflict_markers(conflict_content)
        resolved_content = conflict_content
        
        for conflict in conflicts:
            current_lines = conflict["current"].split('\n')
            incoming_lines = conflict["incoming"].split('\n')
            
            # Choose the version with more content
            if len(incoming_lines) > len(current_lines):
                merged = conflict["incoming"]
            else:
                merged = conflict["current"]
            
            resolved_content = resolved_content.replace(
                f"<<<<<<< HEAD\n{conflict['current']}=======\n{conflict['incoming']}>>>>>>> ",
                merged
            )
        
        return resolved_content
    
    async def _resolve_test_conflict(self, file_path: str, conflict_content: str) -> Optional[str]:
        """Resolve test file conflicts"""
        # For tests, merge both test cases
        conflicts = self._parse_conflict_markers(conflict_content)
        resolved_content = conflict_content
        
        for conflict in conflicts:
            # Combine both test versions
            merged = f"{conflict['current']}\n\n{conflict['incoming']}"
            
            resolved_content = resolved_content.replace(
                f"<<<<<<< HEAD\n{conflict['current']}=======\n{conflict['incoming']}>>>>>>> ",
                merged
            )
        
        return resolved_content
    
    async def _resolve_generic_conflict(self, file_path: str, conflict_content: str) -> Optional[str]:
        """Generic conflict resolution"""
        # Default to incoming version
        conflicts = self._parse_conflict_markers(conflict_content)
        resolved_content = conflict_content
        
        for conflict in conflicts:
            resolved_content = resolved_content.replace(
                f"<<<<<<< HEAD\n{conflict['current']}=======\n{conflict['incoming']}>>>>>>> ",
                conflict["incoming"]
            )
        
        return resolved_content
    
    def _parse_conflict_markers(self, content: str) -> List[Dict[str, str]]:
        """Parse Git conflict markers"""
        conflicts = []
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            if lines[i].startswith('<<<<<<< '):
                # Found conflict start
                current_lines = []
                incoming_lines = []
                i += 1
                
                # Read current version
                while i < len(lines) and not lines[i].startswith('======='):
                    current_lines.append(lines[i])
                    i += 1
                
                if i < len(lines):
                    i += 1  # Skip =======
                
                # Read incoming version
                while i < len(lines) and not lines[i].startswith('>>>>>>> '):
                    incoming_lines.append(lines[i])
                    i += 1
                
                conflicts.append({
                    "current": '\n'.join(current_lines),
                    "incoming": '\n'.join(incoming_lines)
                })
            
            i += 1
        
        return conflicts
    
    def _is_import_section(self, current: str, incoming: str) -> bool:
        """Check if conflict is in import section"""
        return ("import " in current or "from " in current) and ("import " in incoming or "from " in incoming)
    
    def _is_function_definition(self, current: str, incoming: str) -> bool:
        """Check if conflict is in function definition"""
        return ("def " in current or "function " in current) and ("def " in incoming or "function " in incoming)
    
    def _merge_imports(self, current: str, incoming: str) -> str:
        """Merge import statements"""
        current_imports = set(line.strip() for line in current.split('\n') if line.strip())
        incoming_imports = set(line.strip() for line in incoming.split('\n') if line.strip())
        
        all_imports = sorted(current_imports | incoming_imports)
        return '\n'.join(all_imports)
    
    def _merge_functions(self, current: str, incoming: str) -> str:
        """Merge function definitions - prefer incoming version"""
        return incoming
    
    def _deep_merge_json(self, obj1: Dict, obj2: Dict) -> Dict:
        """Deep merge two JSON objects"""
        result = obj1.copy()
        
        for key, value in obj2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge_json(result[key], value)
            else:
                result[key] = value
        
        return result


class GitManager:
    """Advanced Git operations manager"""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self.conflict_resolver = GitConflictResolver()
    
    async def initialize_repository(self, repo_path: str) -> bool:
        """Initialize a new Git repository"""
        try:
            result = await self._run_git_command(["git", "init"], cwd=repo_path)
            
            if result["success"]:
                # Create initial commit
                await self._run_git_command(["git", "add", "."], cwd=repo_path)
                await self._run_git_command([
                    "git", "commit", "-m", "Initial commit - ARTAC project setup"
                ], cwd=repo_path)
                
                logger.log_system_event("git_repository_initialized", {
                    "repo_path": repo_path
                })
                return True
            
            return False
            
        except Exception as e:
            logger.log_error(e, {
                "action": "initialize_repository",
                "repo_path": repo_path
            })
            return False
    
    async def clone_repository(self, repo_url: str, target_path: str) -> bool:
        """Clone a remote repository"""
        try:
            result = await self._run_git_command([
                "git", "clone", repo_url, target_path
            ])
            
            if result["success"]:
                logger.log_system_event("git_repository_cloned", {
                    "repo_url": repo_url,
                    "target_path": target_path
                })
                return True
            
            return False
            
        except Exception as e:
            logger.log_error(e, {
                "action": "clone_repository",
                "repo_url": repo_url
            })
            return False
    
    async def create_branch(self, branch_name: str, base_path: str, base_branch: str = "main") -> bool:
        """Create a new branch"""
        try:
            # Switch to base branch
            await self._run_git_command(["git", "checkout", base_branch], cwd=base_path)
            
            # Create new branch
            result = await self._run_git_command([
                "git", "checkout", "-b", branch_name
            ], cwd=base_path)
            
            if result["success"]:
                logger.log_system_event("git_branch_created", {
                    "branch_name": branch_name,
                    "base_branch": base_branch,
                    "base_path": base_path
                })
                return True
            
            return False
            
        except Exception as e:
            logger.log_error(e, {
                "action": "create_branch",
                "branch_name": branch_name
            })
            return False
    
    async def clone_branch(self, branch_name: str, target_path: str) -> bool:
        """Clone a specific branch to target path"""
        try:
            # Copy files from main workspace
            import shutil
            if os.path.exists(target_path):
                shutil.rmtree(target_path)
            
            shutil.copytree(
                os.path.join(self.workspace_path, "main"),
                target_path,
                ignore=shutil.ignore_patterns('.git')
            )
            
            # Initialize git in target
            await self._run_git_command(["git", "init"], cwd=target_path)
            
            logger.log_system_event("git_branch_cloned", {
                "branch_name": branch_name,
                "target_path": target_path
            })
            return True
            
        except Exception as e:
            logger.log_error(e, {
                "action": "clone_branch",
                "branch_name": branch_name
            })
            return False
    
    async def checkout_branch(self, branch_name: str, repo_path: str) -> bool:
        """Checkout a specific branch"""
        try:
            result = await self._run_git_command([
                "git", "checkout", branch_name
            ], cwd=repo_path)
            
            if result["success"]:
                logger.log_system_event("git_branch_checked_out", {
                    "branch_name": branch_name,
                    "repo_path": repo_path
                })
                return True
            
            return False
            
        except Exception as e:
            logger.log_error(e, {
                "action": "checkout_branch",
                "branch_name": branch_name
            })
            return False
    
    async def commit_changes(self, repo_path: str, message: str, agent_id: str) -> bool:
        """Commit changes with agent attribution"""
        try:
            # Add all changes
            await self._run_git_command(["git", "add", "."], cwd=repo_path)
            
            # Commit with agent attribution
            commit_message = f"{message}\n\nAgent: {agent_id}\nTimestamp: {datetime.utcnow().isoformat()}"
            
            result = await self._run_git_command([
                "git", "commit", "-m", commit_message
            ], cwd=repo_path)
            
            if result["success"]:
                # Get commit hash
                hash_result = await self._run_git_command([
                    "git", "rev-parse", "HEAD"
                ], cwd=repo_path)
                
                commit_hash = hash_result["stdout"].strip() if hash_result["success"] else ""
                
                logger.log_system_event("git_changes_committed", {
                    "repo_path": repo_path,
                    "message": message,
                    "agent_id": agent_id,
                    "commit_hash": commit_hash
                })
                return True
            
            return False
            
        except Exception as e:
            logger.log_error(e, {
                "action": "commit_changes",
                "agent_id": agent_id
            })
            return False
    
    async def merge_branch(self, source_branch: str, target_branch: str, repo_path: str, agent_id: str) -> Dict[str, Any]:
        """Merge branches with conflict resolution"""
        try:
            # Checkout target branch
            await self._run_git_command(["git", "checkout", target_branch], cwd=repo_path)
            
            # Attempt merge
            result = await self._run_git_command([
                "git", "merge", source_branch
            ], cwd=repo_path)
            
            if result["success"]:
                logger.log_system_event("git_branch_merged", {
                    "source_branch": source_branch,
                    "target_branch": target_branch,
                    "agent_id": agent_id,
                    "conflicts": False
                })
                return {
                    "success": True,
                    "conflicts": False,
                    "message": "Branch merged successfully"
                }
            else:
                # Check for conflicts
                conflicts = await self._detect_conflicts(repo_path)
                
                if conflicts:
                    # Attempt automatic resolution
                    resolved = await self._resolve_conflicts(conflicts, repo_path, agent_id)
                    
                    if resolved:
                        # Complete merge after resolution
                        await self._run_git_command(["git", "add", "."], cwd=repo_path)
                        await self._run_git_command([
                            "git", "commit", "-m", f"Merge {source_branch} into {target_branch} (auto-resolved by {agent_id})"
                        ], cwd=repo_path)
                        
                        return {
                            "success": True,
                            "conflicts": True,
                            "conflicts_resolved": True,
                            "message": "Branch merged with automatic conflict resolution"
                        }
                    else:
                        return {
                            "success": False,
                            "conflicts": True,
                            "conflicts_resolved": False,
                            "message": "Manual conflict resolution required",
                            "conflict_files": [c["file_path"] for c in conflicts]
                        }
                else:
                    return {
                        "success": False,
                        "conflicts": False,
                        "message": result["stderr"]
                    }
            
        except Exception as e:
            logger.log_error(e, {
                "action": "merge_branch",
                "source_branch": source_branch,
                "target_branch": target_branch
            })
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _detect_conflicts(self, repo_path: str) -> List[Dict[str, Any]]:
        """Detect merge conflicts"""
        try:
            # Get list of conflicted files
            result = await self._run_git_command([
                "git", "diff", "--name-only", "--diff-filter=U"
            ], cwd=repo_path)
            
            if not result["success"]:
                return []
            
            conflict_files = result["stdout"].strip().split('\n') if result["stdout"].strip() else []
            conflicts = []
            
            for file_path in conflict_files:
                if file_path:
                    full_path = os.path.join(repo_path, file_path)
                    if os.path.exists(full_path):
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        conflicts.append({
                            "file_path": file_path,
                            "full_path": full_path,
                            "content": content
                        })
            
            return conflicts
            
        except Exception as e:
            logger.log_error(e, {"action": "detect_conflicts"})
            return []
    
    async def _resolve_conflicts(self, conflicts: List[Dict], repo_path: str, agent_id: str) -> bool:
        """Resolve merge conflicts automatically"""
        try:
            all_resolved = True
            
            for conflict in conflicts:
                resolved_content = await self.conflict_resolver.resolve_conflict(
                    conflict["file_path"],
                    conflict["content"]
                )
                
                if resolved_content:
                    with open(conflict["full_path"], 'w', encoding='utf-8') as f:
                        f.write(resolved_content)
                    
                    logger.log_system_event("conflict_auto_resolved", {
                        "file_path": conflict["file_path"],
                        "agent_id": agent_id
                    })
                else:
                    all_resolved = False
                    logger.log_system_event("conflict_resolution_failed", {
                        "file_path": conflict["file_path"],
                        "agent_id": agent_id
                    })
            
            return all_resolved
            
        except Exception as e:
            logger.log_error(e, {"action": "resolve_conflicts"})
            return False
    
    async def get_status(self, repo_path: str) -> Dict[str, Any]:
        """Get Git repository status"""
        try:
            # Get basic status
            status_result = await self._run_git_command(["git", "status", "--porcelain"], cwd=repo_path)
            
            # Get current branch
            branch_result = await self._run_git_command(["git", "branch", "--show-current"], cwd=repo_path)
            
            # Get commit count
            count_result = await self._run_git_command(["git", "rev-list", "--count", "HEAD"], cwd=repo_path)
            
            # Parse status
            modified_files = []
            untracked_files = []
            
            if status_result["success"] and status_result["stdout"]:
                for line in status_result["stdout"].strip().split('\n'):
                    if line:
                        status_code = line[:2]
                        file_path = line[3:]
                        
                        if status_code.strip() == "??":
                            untracked_files.append(file_path)
                        else:
                            modified_files.append({
                                "file_path": file_path,
                                "status": status_code
                            })
            
            return {
                "success": True,
                "current_branch": branch_result["stdout"].strip() if branch_result["success"] else "",
                "commit_count": int(count_result["stdout"].strip()) if count_result["success"] else 0,
                "modified_files": modified_files,
                "untracked_files": untracked_files,
                "has_changes": len(modified_files) > 0 or len(untracked_files) > 0
            }
            
        except Exception as e:
            logger.log_error(e, {"action": "get_git_status"})
            return {"success": False, "error": str(e)}
    
    async def _run_git_command(self, command: List[str], cwd: str = None) -> Dict[str, Any]:
        """Run a Git command and return result"""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd or self.workspace_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode('utf-8') if stdout else "",
                "stderr": stderr.decode('utf-8') if stderr else "",
                "return_code": process.returncode,
                "command": " ".join(command)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": " ".join(command)
            }