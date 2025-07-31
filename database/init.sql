-- ARTAC Database Initialization
-- PostgreSQL with pgvector setup

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create agents table
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    role VARCHAR(100) NOT NULL,
    level VARCHAR(50) NOT NULL, -- executive, management, development, execution
    status VARCHAR(50) NOT NULL DEFAULT 'active', -- active, suspended, terminated
    model_name VARCHAR(100) NOT NULL,
    specialization TEXT[],
    performance_score FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create agent hierarchy relationships
CREATE TABLE IF NOT EXISTS agent_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_agent_id UUID REFERENCES agents(id),
    child_agent_id UUID REFERENCES agents(id),
    relationship_type VARCHAR(50) NOT NULL, -- supervisor, mentor, peer
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, in_progress, completed, failed
    priority VARCHAR(20) NOT NULL DEFAULT 'medium', -- low, medium, high, critical
    assigned_agent_id UUID REFERENCES agents(id),
    created_by_agent_id UUID REFERENCES agents(id),
    parent_task_id UUID REFERENCES tasks(id),
    estimated_hours FLOAT,
    actual_hours FLOAT,
    git_branch VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create RAG embeddings table
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_type VARCHAR(100) NOT NULL, -- code, documentation, conversation, external
    content_id VARCHAR(255),
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI embedding dimension
    source_url TEXT,
    source_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create audit log table (immutable)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    agent_id UUID REFERENCES agents(id),
    entity_type VARCHAR(100), -- task, agent, code, deployment
    entity_id UUID,
    action VARCHAR(100) NOT NULL,
    details JSONB NOT NULL,
    hash VARCHAR(256) NOT NULL, -- Cryptographic hash for integrity
    previous_hash VARCHAR(256), -- Link to previous log for chain integrity
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Create conversations table for voice interface
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    session_id UUID NOT NULL,
    message_type VARCHAR(50) NOT NULL, -- user_voice, user_text, agent_response
    content TEXT NOT NULL,
    agent_id UUID REFERENCES agents(id),
    confidence_score FLOAT,
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create performance metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agents(id),
    metric_type VARCHAR(100) NOT NULL, -- code_quality, task_completion, response_time
    metric_value FLOAT NOT NULL,
    measurement_period VARCHAR(50) NOT NULL, -- hourly, daily, weekly, monthly
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    details JSONB DEFAULT '{}'::jsonb
);

-- Create git repositories table
CREATE TABLE IF NOT EXISTS repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    branch VARCHAR(255) NOT NULL DEFAULT 'main',
    last_sync TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_role ON agents(role);
CREATE INDEX IF NOT EXISTS idx_agents_level ON agents(level);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_agent ON tasks(assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_embeddings_content_type ON embeddings(content_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_agent_id ON audit_logs(agent_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_agent ON performance_metrics(agent_id);

-- Vector similarity search index
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Insert initial executive agents
INSERT INTO agents (name, role, level, model_name, specialization) VALUES
('CEO-001', 'CEO', 'executive', 'claude-3-5-sonnet-20241022', ARRAY['strategic_planning', 'team_management']),
('CTO-001', 'CTO', 'executive', 'claude-3-5-sonnet-20241022', ARRAY['technical_architecture', 'innovation']),
('CQO-001', 'CQO', 'executive', 'claude-3-5-sonnet-20241022', ARRAY['quality_assurance', 'production_gates']),
('HR-001', 'HR', 'executive', 'claude-3-5-sonnet-20241022', ARRAY['agent_management', 'performance_evaluation']),
('RESEARCH-001', 'Research', 'executive', 'claude-3-5-sonnet-20241022', ARRAY['innovation', 'competitive_analysis']);

-- Create trigger for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_embeddings_updated_at BEFORE UPDATE ON embeddings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();