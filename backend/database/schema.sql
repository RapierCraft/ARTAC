-- ARTAC Enhanced Database Schema
-- Code artifacts, git history, deployment tracking, and project management

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enhanced Projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_name VARCHAR(255) NOT NULL,
    description TEXT,
    complexity VARCHAR(50) NOT NULL, -- simple, moderate, complex, enterprise
    status VARCHAR(50) NOT NULL DEFAULT 'planning', -- planning, in_progress, completed, cancelled
    estimated_hours INTEGER,
    actual_hours INTEGER DEFAULT 0,
    budget_allocated DECIMAL(10,2),
    budget_spent DECIMAL(10,2) DEFAULT 0,
    workspace_path TEXT,
    git_repository_url TEXT,
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Indexes
    INDEX idx_projects_status (status),
    INDEX idx_projects_created_at (created_at),
    INDEX idx_projects_complexity (complexity)
);

-- Code Artifacts table - stores all agent-generated code
CREATE TABLE IF NOT EXISTS code_artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    agent_id VARCHAR(255) NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    artifact_type VARCHAR(50) NOT NULL, -- source_code, configuration, documentation, test_file, etc.
    content TEXT NOT NULL,
    content_hash CHAR(64) NOT NULL, -- SHA-256 hash
    file_size INTEGER NOT NULL DEFAULT 0,
    line_count INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- draft, review_pending, approved, deployed, archived
    version INTEGER NOT NULL DEFAULT 1,
    parent_version UUID REFERENCES code_artifacts(id),
    commit_sha CHAR(40), -- Git commit SHA
    task_id UUID,
    description TEXT,
    review_notes TEXT,
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Indexes
    INDEX idx_artifacts_project_id (project_id),
    INDEX idx_artifacts_agent_id (agent_id),
    INDEX idx_artifacts_file_path (project_id, file_path),
    INDEX idx_artifacts_status (status),
    INDEX idx_artifacts_type (artifact_type),
    INDEX idx_artifacts_content_hash (content_hash),
    INDEX idx_artifacts_created_at (created_at),
    
    -- Full-text search on content
    INDEX idx_artifacts_content_fts USING gin(to_tsvector('english', content))
);

-- File Versions table - tracks all versions of files
CREATE TABLE IF NOT EXISTS file_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    artifact_id UUID NOT NULL REFERENCES code_artifacts(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_hash CHAR(64) NOT NULL,
    content_diff TEXT, -- Diff from previous version
    changes_summary TEXT,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    commit_sha CHAR(40),
    
    -- Indexes
    INDEX idx_file_versions_artifact_id (artifact_id),
    INDEX idx_file_versions_version (artifact_id, version_number),
    INDEX idx_file_versions_created_at (created_at),
    
    -- Ensure unique version numbers per artifact
    UNIQUE(artifact_id, version_number)
);

-- Git Commits table - tracks all git activity
CREATE TABLE IF NOT EXISTS git_commits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    commit_sha CHAR(40) NOT NULL UNIQUE,
    commit_message TEXT NOT NULL,
    author_name VARCHAR(255) NOT NULL,
    author_email VARCHAR(255) NOT NULL,
    committer_name VARCHAR(255),
    committer_email VARCHAR(255),
    branch_name VARCHAR(255) NOT NULL DEFAULT 'main',
    parent_commits TEXT[], -- Array of parent commit SHAs
    files_changed TEXT[] NOT NULL, -- Array of file paths
    insertions INTEGER NOT NULL DEFAULT 0,
    deletions INTEGER NOT NULL DEFAULT 0,
    total_changes INTEGER NOT NULL DEFAULT 0,
    commit_date TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Indexes
    INDEX idx_git_commits_project_id (project_id),
    INDEX idx_git_commits_sha (commit_sha),
    INDEX idx_git_commits_branch (project_id, branch_name),
    INDEX idx_git_commits_author (author_email),
    INDEX idx_git_commits_date (commit_date),
    INDEX idx_git_commits_files USING gin(files_changed)
);

-- Deployments table - tracks deployment history
CREATE TABLE IF NOT EXISTS deployments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    deployment_name VARCHAR(255) NOT NULL,
    environment VARCHAR(100) NOT NULL, -- development, staging, production, etc.
    status VARCHAR(50) NOT NULL, -- pending, in_progress, success, failure, cancelled
    commit_sha CHAR(40) NOT NULL,
    deployed_by VARCHAR(255) NOT NULL,
    deployment_url TEXT,
    build_time_seconds INTEGER,
    deployment_config JSONB DEFAULT '{}'::jsonb,
    environment_variables JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,
    error_logs TEXT,
    deployment_logs TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    rollback_deployment_id UUID REFERENCES deployments(id),
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Indexes
    INDEX idx_deployments_project_id (project_id),
    INDEX idx_deployments_environment (project_id, environment),
    INDEX idx_deployments_status (status),
    INDEX idx_deployments_commit_sha (commit_sha),
    INDEX idx_deployments_deployed_by (deployed_by),
    INDEX idx_deployments_started_at (started_at)
);

-- Project Channels table - structured communication channels
CREATE TABLE IF NOT EXISTS project_channels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    channel_type VARCHAR(50) NOT NULL, -- general, git_commits, deployments, code_review, etc.
    name VARCHAR(255) NOT NULL,
    description TEXT,
    auto_notifications BOOLEAN DEFAULT true,
    participants TEXT[] DEFAULT '{}', -- Array of agent/user IDs
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMP WITH TIME ZONE,
    settings JSONB DEFAULT '{}'::jsonb,
    
    -- Indexes
    INDEX idx_project_channels_project_id (project_id),
    INDEX idx_project_channels_type (project_id, channel_type),
    INDEX idx_project_channels_participants USING gin(participants),
    
    -- Ensure unique channel types per project
    UNIQUE(project_id, channel_type)
);

-- Channel Messages table - enhanced messages with embeds
CREATE TABLE IF NOT EXISTS channel_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel_id UUID NOT NULL REFERENCES project_channels(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    sender_id VARCHAR(255) NOT NULL,
    sender_name VARCHAR(255) NOT NULL,
    sender_type VARCHAR(50) NOT NULL, -- agent, user, system
    content TEXT NOT NULL,
    message_type VARCHAR(50) NOT NULL DEFAULT 'text', -- text, embed, notification, announcement
    embeds JSONB DEFAULT '[]'::jsonb, -- Array of embed objects
    thread_id UUID REFERENCES channel_messages(id),
    reply_to UUID REFERENCES channel_messages(id),
    edited_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Indexes
    INDEX idx_channel_messages_channel_id (channel_id),
    INDEX idx_channel_messages_project_id (project_id),
    INDEX idx_channel_messages_sender_id (sender_id),
    INDEX idx_channel_messages_type (message_type),
    INDEX idx_channel_messages_created_at (created_at),
    INDEX idx_channel_messages_thread_id (thread_id),
    
    -- Full-text search on content
    INDEX idx_channel_messages_content_fts USING gin(to_tsvector('english', content))
);

-- Workspace Allocations table - tracks agent workspace access
CREATE TABLE IF NOT EXISTS workspace_allocations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    agent_id VARCHAR(255) NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    workspace_path TEXT NOT NULL,
    git_branch VARCHAR(255) NOT NULL,
    allocated_files TEXT[] DEFAULT '{}',
    permissions JSONB NOT NULL DEFAULT '{"read": true, "write": false, "create": false, "delete": false}'::jsonb,
    allocated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes
    INDEX idx_workspace_allocations_project_id (project_id),
    INDEX idx_workspace_allocations_agent_id (agent_id),
    INDEX idx_workspace_allocations_branch (git_branch),
    INDEX idx_workspace_allocations_allocated_at (allocated_at)
);

-- Task Assignments table - enhanced task tracking
CREATE TABLE IF NOT EXISTS task_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    agent_id VARCHAR(255) NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    agent_role VARCHAR(100) NOT NULL,
    task_title VARCHAR(500) NOT NULL,
    task_description TEXT,
    task_type VARCHAR(50) NOT NULL,
    priority VARCHAR(50) NOT NULL DEFAULT 'medium',
    estimated_hours INTEGER NOT NULL DEFAULT 1,
    actual_hours INTEGER DEFAULT 0,
    allocated_files TEXT[] DEFAULT '{}',
    workspace_allocation_id UUID REFERENCES workspace_allocations(id),
    status VARCHAR(50) NOT NULL DEFAULT 'assigned', -- assigned, in_progress, review_pending, completed, cancelled
    deliverables TEXT[] DEFAULT '{}',
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    due_date TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Indexes
    INDEX idx_task_assignments_task_id (task_id),
    INDEX idx_task_assignments_project_id (project_id),
    INDEX idx_task_assignments_agent_id (agent_id),
    INDEX idx_task_assignments_status (status),
    INDEX idx_task_assignments_priority (priority),
    INDEX idx_task_assignments_assigned_at (assigned_at),
    INDEX idx_task_assignments_due_date (due_date)
);

-- Codebase Snapshots table - point-in-time codebase captures
CREATE TABLE IF NOT EXISTS codebase_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    snapshot_name VARCHAR(255) NOT NULL,
    description TEXT,
    commit_sha CHAR(40) NOT NULL,
    artifact_ids UUID[] NOT NULL, -- Array of included artifact IDs
    total_files INTEGER NOT NULL DEFAULT 0,
    total_lines INTEGER NOT NULL DEFAULT 0,
    compressed_size_bytes BIGINT,
    archive_path TEXT, -- Path to ZIP archive
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Indexes
    INDEX idx_codebase_snapshots_project_id (project_id),
    INDEX idx_codebase_snapshots_commit_sha (commit_sha),
    INDEX idx_codebase_snapshots_created_at (created_at),
    INDEX idx_codebase_snapshots_tags USING gin(tags)
);

-- Rich Embeds table - stores structured embed data
CREATE TABLE IF NOT EXISTS rich_embeds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    embed_type VARCHAR(50) NOT NULL, -- git_commit, deployment, code_artifact, etc.
    title VARCHAR(500) NOT NULL,
    description TEXT,
    color CHAR(7) NOT NULL, -- Hex color code
    status VARCHAR(50) NOT NULL, -- success, failure, warning, info, pending
    fields JSONB DEFAULT '[]'::jsonb, -- Array of field objects
    author JSONB,
    footer JSONB,
    thumbnail_url TEXT,
    image_url TEXT,
    url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Indexes
    INDEX idx_rich_embeds_type (embed_type),
    INDEX idx_rich_embeds_status (status),
    INDEX idx_rich_embeds_created_at (created_at),
    
    -- Full-text search on title and description
    INDEX idx_rich_embeds_search_fts USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')))
);

-- Performance Metrics table - tracks system and agent performance
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_type VARCHAR(100) NOT NULL, -- agent_performance, system_health, project_metrics
    entity_id VARCHAR(255) NOT NULL, -- agent_id, project_id, or 'system'
    entity_type VARCHAR(50) NOT NULL, -- agent, project, system
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    metric_unit VARCHAR(50),
    measurement_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Indexes
    INDEX idx_performance_metrics_type (metric_type),
    INDEX idx_performance_metrics_entity (entity_type, entity_id),
    INDEX idx_performance_metrics_name (metric_name),
    INDEX idx_performance_metrics_time (measurement_time),
    INDEX idx_performance_metrics_value (metric_value)
);

-- Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for automatic timestamp updates
CREATE TRIGGER update_projects_updated_at 
    BEFORE UPDATE ON projects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_code_artifacts_updated_at 
    BEFORE UPDATE ON code_artifacts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries

-- Active projects with stats
CREATE OR REPLACE VIEW active_projects_stats AS
SELECT 
    p.*,
    COUNT(DISTINCT ca.id) as total_artifacts,
    COUNT(DISTINCT ta.id) as total_assignments,
    COUNT(DISTINCT wa.agent_id) as total_agents,
    COUNT(DISTINCT gc.id) as total_commits,
    COUNT(DISTINCT d.id) as total_deployments,
    MAX(ca.updated_at) as last_code_change,
    MAX(gc.commit_date) as last_commit,
    MAX(d.completed_at) as last_deployment
FROM projects p
LEFT JOIN code_artifacts ca ON p.id = ca.project_id
LEFT JOIN task_assignments ta ON p.id = ta.project_id
LEFT JOIN workspace_allocations wa ON p.id = wa.project_id AND wa.revoked_at IS NULL
LEFT JOIN git_commits gc ON p.id = gc.project_id
LEFT JOIN deployments d ON p.id = d.project_id
WHERE p.status != 'cancelled'
GROUP BY p.id;

-- Agent productivity view
CREATE OR REPLACE VIEW agent_productivity AS
SELECT 
    ta.agent_id,
    ta.agent_name,
    ta.agent_role,
    COUNT(*) as total_assignments,
    COUNT(CASE WHEN ta.status = 'completed' THEN 1 END) as completed_assignments,
    COUNT(CASE WHEN ta.status = 'in_progress' THEN 1 END) as active_assignments,
    AVG(ta.actual_hours) as avg_hours_per_task,
    SUM(ta.actual_hours) as total_hours_worked,
    COUNT(DISTINCT ca.id) as artifacts_created,
    MAX(ta.completed_at) as last_completion
FROM task_assignments ta
LEFT JOIN code_artifacts ca ON ta.agent_id = ca.agent_id
GROUP BY ta.agent_id, ta.agent_name, ta.agent_role;

-- Project health dashboard
CREATE OR REPLACE VIEW project_health_dashboard AS
SELECT 
    p.id,
    p.project_name,
    p.status,
    p.complexity,
    p.estimated_hours,
    p.actual_hours,
    CASE 
        WHEN p.estimated_hours > 0 THEN (p.actual_hours::float / p.estimated_hours * 100)
        ELSE 0 
    END as progress_percentage,
    COUNT(DISTINCT ta.agent_id) as team_size,
    COUNT(CASE WHEN ta.status = 'completed' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN ta.status = 'in_progress' THEN 1 END) as active_tasks,
    COUNT(CASE WHEN ta.due_date < CURRENT_TIMESTAMP AND ta.status != 'completed' THEN 1 END) as overdue_tasks,
    COUNT(DISTINCT ca.id) as total_files,
    SUM(ca.line_count) as total_lines_of_code,
    COUNT(DISTINCT d.id) as total_deployments,
    MAX(d.completed_at) as last_deployment_date
FROM projects p
LEFT JOIN task_assignments ta ON p.id = ta.project_id
LEFT JOIN code_artifacts ca ON p.id = ca.project_id AND ca.status IN ('approved', 'deployed')
LEFT JOIN deployments d ON p.id = d.project_id AND d.status = 'success'
GROUP BY p.id, p.project_name, p.status, p.complexity, p.estimated_hours, p.actual_hours;

-- Comments
COMMENT ON TABLE projects IS 'Core project information and metadata';
COMMENT ON TABLE code_artifacts IS 'All code files and artifacts generated by agents';
COMMENT ON TABLE file_versions IS 'Version history for all code files';
COMMENT ON TABLE git_commits IS 'Git commit history and metadata';
COMMENT ON TABLE deployments IS 'Deployment history and status tracking';
COMMENT ON TABLE project_channels IS 'Project-specific communication channels';
COMMENT ON TABLE channel_messages IS 'Messages within project channels with embed support';
COMMENT ON TABLE workspace_allocations IS 'Agent workspace access and permissions';
COMMENT ON TABLE task_assignments IS 'Enhanced task assignments with workspace integration';
COMMENT ON TABLE codebase_snapshots IS 'Point-in-time snapshots of entire codebases';
COMMENT ON TABLE rich_embeds IS 'Structured embed data for rich communication';
COMMENT ON TABLE performance_metrics IS 'Performance tracking for agents and system';

COMMENT ON VIEW active_projects_stats IS 'Active projects with comprehensive statistics';
COMMENT ON VIEW agent_productivity IS 'Agent productivity and performance metrics';
COMMENT ON VIEW project_health_dashboard IS 'Project health and progress overview';