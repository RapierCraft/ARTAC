"""
ARTAC Embed System
Creates rich embeds for git commits, deployments, code artifacts, and other project elements
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess

from core.logging import get_logger
from services.code_artifact_manager import CodeArtifact, ArtifactType, ArtifactStatus

logger = get_logger(__name__)


class EmbedType(str, Enum):
    GIT_COMMIT = "git_commit"
    DEPLOYMENT = "deployment"
    CODE_ARTIFACT = "code_artifact"
    TEST_RESULT = "test_result"
    PULL_REQUEST = "pull_request"
    ISSUE = "issue"
    TASK_UPDATE = "task_update"
    AGENT_STATUS = "agent_status"
    SYSTEM_ALERT = "system_alert"
    PERFORMANCE_METRIC = "performance_metric"


class EmbedStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"
    INFO = "info"
    PENDING = "pending"


@dataclass
class EmbedField:
    """A field within an embed"""
    name: str
    value: str
    inline: bool = False


@dataclass
class EmbedFooter:
    """Footer information for an embed"""
    text: str
    icon_url: Optional[str] = None


@dataclass
class EmbedAuthor:
    """Author information for an embed"""
    name: str
    icon_url: Optional[str] = None
    url: Optional[str] = None


@dataclass
class RichEmbed:
    """Rich embed for displaying structured information in channels"""
    id: str
    embed_type: EmbedType
    title: str
    description: Optional[str]
    color: str  # Hex color code
    status: EmbedStatus
    fields: List[EmbedField]
    author: Optional[EmbedAuthor]
    footer: Optional[EmbedFooter]
    thumbnail_url: Optional[str]
    image_url: Optional[str]
    timestamp: datetime
    url: Optional[str]  # Link to related resource
    metadata: Dict[str, Any]


class EmbedSystem:
    """System for creating and managing rich embeds"""
    
    def __init__(self):
        self.embeds: Dict[str, RichEmbed] = {}
        
        # Color schemes for different embed types and statuses
        self.colors = {
            EmbedStatus.SUCCESS: "#00ff00",
            EmbedStatus.FAILURE: "#ff0000", 
            EmbedStatus.WARNING: "#ffaa00",
            EmbedStatus.INFO: "#0088ff",
            EmbedStatus.PENDING: "#888888"
        }
        
        # Embed type specific colors
        self.type_colors = {
            EmbedType.GIT_COMMIT: "#ff6b35",
            EmbedType.DEPLOYMENT: "#00c851",
            EmbedType.CODE_ARTIFACT: "#2e7aff",
            EmbedType.TEST_RESULT: "#ff3547",
            EmbedType.PULL_REQUEST: "#6f42c1",
            EmbedType.ISSUE: "#d73a49",
            EmbedType.TASK_UPDATE: "#28a745",
            EmbedType.AGENT_STATUS: "#17a2b8",
            EmbedType.SYSTEM_ALERT: "#ffc107",
            EmbedType.PERFORMANCE_METRIC: "#6610f2"
        }
        
        # Icons for different embed types
        self.type_icons = {
            EmbedType.GIT_COMMIT: "🔀",
            EmbedType.DEPLOYMENT: "🚀",
            EmbedType.CODE_ARTIFACT: "📄",
            EmbedType.TEST_RESULT: "🧪",
            EmbedType.PULL_REQUEST: "🔄",
            EmbedType.ISSUE: "🐛",
            EmbedType.TASK_UPDATE: "✅",
            EmbedType.AGENT_STATUS: "🤖",
            EmbedType.SYSTEM_ALERT: "⚠️",
            EmbedType.PERFORMANCE_METRIC: "📊"
        }
    
    async def create_git_commit_embed(
        self,
        commit_sha: str,
        commit_message: str,
        author_name: str,
        author_email: str,
        files_changed: List[str],
        insertions: int,
        deletions: int,
        repository_url: Optional[str] = None,
        branch: str = "main"
    ) -> RichEmbed:
        """Create an embed for a git commit"""
        
        embed_id = f"embed_{uuid.uuid4().hex[:8]}"
        
        # Parse commit message for title and description
        lines = commit_message.strip().split('\n')
        title = lines[0][:50] + "..." if len(lines[0]) > 50 else lines[0]
        description = '\n'.join(lines[1:]).strip() if len(lines) > 1 else None
        
        fields = [
            EmbedField("Commit", f"`{commit_sha[:8]}`", True),
            EmbedField("Branch", f"`{branch}`", True),
            EmbedField("Files Changed", str(len(files_changed)), True),
            EmbedField("Changes", f"+{insertions} -{deletions}", True)
        ]
        
        if files_changed:
            files_preview = ', '.join(files_changed[:3])
            if len(files_changed) > 3:
                files_preview += f" and {len(files_changed) - 3} more..."
            fields.append(EmbedField("Modified Files", f"`{files_preview}`", False))
        
        author = EmbedAuthor(
            name=f"{author_name} ({author_email})",
            icon_url="https://github.com/favicon.ico"
        )
        
        footer = EmbedFooter(
            text=f"Git • {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        )
        
        embed = RichEmbed(
            id=embed_id,
            embed_type=EmbedType.GIT_COMMIT,
            title=f"{self.type_icons[EmbedType.GIT_COMMIT]} {title}",
            description=description,
            color=self.type_colors[EmbedType.GIT_COMMIT],
            status=EmbedStatus.INFO,
            fields=fields,
            author=author,
            footer=footer,
            thumbnail_url=None,
            image_url=None,
            timestamp=datetime.utcnow(),
            url=f"{repository_url}/commit/{commit_sha}" if repository_url else None,
            metadata={
                "commit_sha": commit_sha,
                "author_email": author_email,
                "files_changed": files_changed,
                "insertions": insertions,
                "deletions": deletions,
                "branch": branch
            }
        )
        
        self.embeds[embed_id] = embed
        
        logger.log_system_event("git_commit_embed_created", {
            "embed_id": embed_id,
            "commit_sha": commit_sha,
            "author": author_name,
            "files_changed": len(files_changed)
        })
        
        return embed
    
    async def create_deployment_embed(
        self,
        deployment_id: str,
        environment: str,
        status: EmbedStatus,
        commit_sha: str,
        deployed_by: str,
        deployment_url: Optional[str] = None,
        build_time: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> RichEmbed:
        """Create an embed for a deployment"""
        
        embed_id = f"embed_{uuid.uuid4().hex[:8]}"
        
        status_emoji = {
            EmbedStatus.SUCCESS: "✅",
            EmbedStatus.FAILURE: "❌",
            EmbedStatus.PENDING: "⏳",
            EmbedStatus.WARNING: "⚠️"
        }
        
        title = f"{self.type_icons[EmbedType.DEPLOYMENT]} Deployment to {environment.title()}"
        if status == EmbedStatus.SUCCESS:
            title += " Successful"
        elif status == EmbedStatus.FAILURE:
            title += " Failed"
        elif status == EmbedStatus.PENDING:
            title += " In Progress"
        
        fields = [
            EmbedField("Environment", environment.title(), True),
            EmbedField("Status", f"{status_emoji.get(status, '❓')} {status.value.title()}", True),
            EmbedField("Commit", f"`{commit_sha[:8]}`", True),
            EmbedField("Deployed By", deployed_by, True)
        ]
        
        if build_time:
            fields.append(EmbedField("Build Time", f"{build_time}s", True))
        
        if deployment_url:
            fields.append(EmbedField("URL", deployment_url, False))
        
        description = None
        if error_message and status == EmbedStatus.FAILURE:
            description = f"```\n{error_message[:500]}{'...' if len(error_message) > 500 else ''}\n```"
        
        author = EmbedAuthor(
            name=deployed_by,
            icon_url="https://github.com/favicon.ico"
        )
        
        footer = EmbedFooter(
            text=f"Deployment • {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        )
        
        embed = RichEmbed(
            id=embed_id,
            embed_type=EmbedType.DEPLOYMENT,
            title=title,
            description=description,
            color=self.colors[status],
            status=status,
            fields=fields,
            author=author,
            footer=footer,
            thumbnail_url=None,
            image_url=None,
            timestamp=datetime.utcnow(),
            url=deployment_url,
            metadata={
                "deployment_id": deployment_id,
                "environment": environment,
                "commit_sha": commit_sha,
                "build_time": build_time,
                "error_message": error_message
            }
        )
        
        self.embeds[embed_id] = embed
        
        logger.log_system_event("deployment_embed_created", {
            "embed_id": embed_id,
            "deployment_id": deployment_id,
            "environment": environment,
            "status": status.value
        })
        
        return embed
    
    async def create_code_artifact_embed(
        self,
        artifact: CodeArtifact,
        changes_summary: Optional[str] = None
    ) -> RichEmbed:
        """Create an embed for a code artifact"""
        
        embed_id = f"embed_{uuid.uuid4().hex[:8]}"
        
        # Status-based colors and emojis
        status_info = {
            ArtifactStatus.DRAFT: {"emoji": "📝", "color": "#6c757d", "status": EmbedStatus.PENDING},
            ArtifactStatus.REVIEW_PENDING: {"emoji": "👀", "color": "#ffc107", "status": EmbedStatus.WARNING},
            ArtifactStatus.APPROVED: {"emoji": "✅", "color": "#28a745", "status": EmbedStatus.SUCCESS},
            ArtifactStatus.DEPLOYED: {"emoji": "🚀", "color": "#17a2b8", "status": EmbedStatus.SUCCESS},
            ArtifactStatus.ARCHIVED: {"emoji": "📦", "color": "#6c757d", "status": EmbedStatus.INFO}
        }
        
        info = status_info.get(artifact.status, status_info[ArtifactStatus.DRAFT])
        
        title = f"{self.type_icons[EmbedType.CODE_ARTIFACT]} {artifact.file_name}"
        
        fields = [
            EmbedField("Type", artifact.artifact_type.value.replace("_", " ").title(), True),
            EmbedField("Status", f"{info['emoji']} {artifact.status.value.replace('_', ' ').title()}", True),
            EmbedField("Version", f"v{artifact.version}", True),
            EmbedField("Agent", artifact.agent_name, True),
            EmbedField("Path", f"`{artifact.file_path}`", False)
        ]
        
        if artifact.task_id:
            fields.append(EmbedField("Task ID", f"`{artifact.task_id}`", True))
        
        if changes_summary:
            fields.append(EmbedField("Changes", changes_summary, False))
        
        # Add code preview for small files
        if len(artifact.content) < 500:
            # Detect language for syntax highlighting
            language = self._detect_language(artifact.file_name)
            code_preview = f"```{language}\n{artifact.content}\n```"
            fields.append(EmbedField("Code Preview", code_preview, False))
        elif len(artifact.content) > 0:
            lines = artifact.content.split('\n')
            fields.append(EmbedField("Lines of Code", str(len(lines)), True))
        
        author = EmbedAuthor(
            name=artifact.agent_name,
            icon_url="https://github.com/favicon.ico"
        )
        
        footer = EmbedFooter(
            text=f"Code Artifact • {artifact.updated_at.strftime('%Y-%m-%d %H:%M UTC')}"
        )
        
        embed = RichEmbed(
            id=embed_id,
            embed_type=EmbedType.CODE_ARTIFACT,
            title=title,
            description=artifact.description if artifact.description else None,
            color=info['color'],
            status=info['status'],
            fields=fields,
            author=author,
            footer=footer,
            thumbnail_url=None,
            image_url=None,
            timestamp=artifact.updated_at,
            url=None,  # Could link to artifact viewer
            metadata={
                "artifact_id": artifact.id,
                "project_id": artifact.project_id,
                "agent_id": artifact.agent_id,
                "file_path": artifact.file_path,
                "content_hash": artifact.content_hash
            }
        )
        
        self.embeds[embed_id] = embed
        
        logger.log_system_event("code_artifact_embed_created", {
            "embed_id": embed_id,
            "artifact_id": artifact.id,
            "project_id": artifact.project_id,
            "agent_id": artifact.agent_id
        })
        
        return embed
    
    async def create_test_result_embed(
        self,
        test_suite: str,
        total_tests: int,
        passed_tests: int,
        failed_tests: int,
        skipped_tests: int,
        execution_time: float,
        coverage_percentage: Optional[float] = None,
        failed_test_details: List[Dict[str, str]] = None
    ) -> RichEmbed:
        """Create an embed for test results"""
        
        embed_id = f"embed_{uuid.uuid4().hex[:8]}"
        
        # Determine status based on results
        if failed_tests == 0:
            status = EmbedStatus.SUCCESS
            status_emoji = "✅"
        elif failed_tests > 0:
            status = EmbedStatus.FAILURE
            status_emoji = "❌"
        else:
            status = EmbedStatus.WARNING
            status_emoji = "⚠️"
        
        title = f"{self.type_icons[EmbedType.TEST_RESULT]} Test Results: {test_suite}"
        
        fields = [
            EmbedField("Total Tests", str(total_tests), True),
            EmbedField("Passed", f"✅ {passed_tests}", True),
            EmbedField("Failed", f"❌ {failed_tests}", True),
            EmbedField("Skipped", f"⏭️ {skipped_tests}", True),
            EmbedField("Execution Time", f"{execution_time:.2f}s", True),
            EmbedField("Status", f"{status_emoji} {status.value.title()}", True)
        ]
        
        if coverage_percentage is not None:
            coverage_emoji = "✅" if coverage_percentage >= 80 else "⚠️" if coverage_percentage >= 60 else "❌"
            fields.append(EmbedField("Coverage", f"{coverage_emoji} {coverage_percentage:.1f}%", True))
        
        description = None
        if failed_test_details and failed_tests > 0:
            failure_summary = []
            for i, failure in enumerate(failed_test_details[:3]):  # Show first 3 failures
                failure_summary.append(f"• {failure.get('test_name', 'Unknown')}: {failure.get('error', 'No details')}")
            
            if len(failed_test_details) > 3:
                failure_summary.append(f"... and {len(failed_test_details) - 3} more failures")
            
            description = "**Failed Tests:**\n" + "\n".join(failure_summary)
        
        footer = EmbedFooter(
            text=f"Test Suite • {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        )
        
        embed = RichEmbed(
            id=embed_id,
            embed_type=EmbedType.TEST_RESULT,
            title=title,
            description=description,
            color=self.colors[status],
            status=status,
            fields=fields,
            author=None,
            footer=footer,
            thumbnail_url=None,
            image_url=None,
            timestamp=datetime.utcnow(),
            url=None,
            metadata={
                "test_suite": test_suite,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "execution_time": execution_time,
                "coverage_percentage": coverage_percentage,
                "failed_test_details": failed_test_details or []
            }
        )
        
        self.embeds[embed_id] = embed
        
        logger.log_system_event("test_result_embed_created", {
            "embed_id": embed_id,
            "test_suite": test_suite,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests
        })
        
        return embed
    
    async def create_agent_status_embed(
        self,
        agent_id: str,
        agent_name: str,
        agent_role: str,
        status: str,
        current_task: Optional[str] = None,
        tasks_completed: int = 0,
        uptime: Optional[str] = None,
        performance_metrics: Dict[str, Any] = None
    ) -> RichEmbed:
        """Create an embed for agent status updates"""
        
        embed_id = f"embed_{uuid.uuid4().hex[:8]}"
        
        status_info = {
            "online": {"emoji": "🟢", "color": "#28a745", "embed_status": EmbedStatus.SUCCESS},
            "busy": {"emoji": "🟡", "color": "#ffc107", "embed_status": EmbedStatus.WARNING},
            "idle": {"emoji": "🔵", "color": "#17a2b8", "embed_status": EmbedStatus.INFO},
            "offline": {"emoji": "🔴", "color": "#dc3545", "embed_status": EmbedStatus.FAILURE}
        }
        
        info = status_info.get(status.lower(), status_info["offline"])
        
        title = f"{self.type_icons[EmbedType.AGENT_STATUS]} {agent_name} Status Update"
        
        fields = [
            EmbedField("Role", agent_role, True),
            EmbedField("Status", f"{info['emoji']} {status.title()}", True),
            EmbedField("Tasks Completed", str(tasks_completed), True)
        ]
        
        if current_task:
            fields.append(EmbedField("Current Task", current_task, False))
        
        if uptime:
            fields.append(EmbedField("Uptime", uptime, True))
        
        if performance_metrics:
            for metric, value in performance_metrics.items():
                fields.append(EmbedField(metric.title(), str(value), True))
        
        author = EmbedAuthor(
            name=agent_name,
            icon_url="https://github.com/favicon.ico"
        )
        
        footer = EmbedFooter(
            text=f"Agent Status • {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        )
        
        embed = RichEmbed(
            id=embed_id,
            embed_type=EmbedType.AGENT_STATUS,
            title=title,
            description=None,
            color=info['color'],
            status=info['embed_status'],
            fields=fields,
            author=author,
            footer=footer,
            thumbnail_url=None,
            image_url=None,
            timestamp=datetime.utcnow(),
            url=None,
            metadata={
                "agent_id": agent_id,
                "agent_role": agent_role,
                "status": status,
                "current_task": current_task,
                "performance_metrics": performance_metrics or {}
            }
        )
        
        self.embeds[embed_id] = embed
        
        logger.log_system_event("agent_status_embed_created", {
            "embed_id": embed_id,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "status": status
        })
        
        return embed
    
    def _detect_language(self, filename: str) -> str:
        """Detect programming language based on file extension"""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.sh': 'bash',
            '.dockerfile': 'dockerfile'
        }
        
        for ext, lang in extension_map.items():
            if filename.lower().endswith(ext):
                return lang
        
        return 'text'
    
    async def get_embed(self, embed_id: str) -> Optional[RichEmbed]:
        """Get an embed by ID"""
        return self.embeds.get(embed_id)
    
    async def get_embeds_by_type(self, embed_type: EmbedType) -> List[RichEmbed]:
        """Get all embeds of a specific type"""
        return [embed for embed in self.embeds.values() if embed.embed_type == embed_type]
    
    def to_dict(self, embed: RichEmbed) -> Dict[str, Any]:
        """Convert embed to dictionary for API responses"""
        return {
            "id": embed.id,
            "type": embed.embed_type.value,
            "title": embed.title,
            "description": embed.description,
            "color": embed.color,
            "status": embed.status.value,
            "fields": [asdict(field) for field in embed.fields],
            "author": asdict(embed.author) if embed.author else None,
            "footer": asdict(embed.footer) if embed.footer else None,
            "thumbnail_url": embed.thumbnail_url,
            "image_url": embed.image_url,
            "timestamp": embed.timestamp.isoformat(),
            "url": embed.url,
            "metadata": embed.metadata
        }


# Global instance
embed_system = EmbedSystem()