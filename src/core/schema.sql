-- ROSTR Agent Framework — Database Schema (PGLite compatible)

CREATE TABLE IF NOT EXISTS pages (
  slug TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  type TEXT DEFAULT 'note',
  content TEXT NOT NULL DEFAULT '',
  compiled_truth TEXT DEFAULT '',
  timeline TEXT DEFAULT '',
  tags TEXT[] DEFAULT '{}',
  metadata JSONB DEFAULT '{}',
  word_count INTEGER DEFAULT 0,
  version INTEGER DEFAULT 1,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS embeddings (
  id SERIAL PRIMARY KEY,
  page_slug TEXT NOT NULL,
  chunk_index INTEGER DEFAULT 0,
  chunk_text TEXT NOT NULL,
  embedding vector(1536),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS links (
  id SERIAL PRIMARY KEY,
  source_slug TEXT NOT NULL,
  target_slug TEXT NOT NULL,
  link_type TEXT DEFAULT 'mentions',
  context TEXT DEFAULT '',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY,
  project TEXT DEFAULT '',
  summary TEXT DEFAULT '',
  duration_estimate TEXT DEFAULT 'medium',
  tools_used TEXT[] DEFAULT '{}',
  files_created TEXT[] DEFAULT '{}',
  files_modified TEXT[] DEFAULT '{}',
  skills_invoked TEXT[] DEFAULT '{}',
  what_worked TEXT[] DEFAULT '{}',
  what_failed TEXT[] DEFAULT '{}',
  decisions_made TEXT[] DEFAULT '{}',
  open_questions TEXT[] DEFAULT '{}',
  next_steps TEXT[] DEFAULT '{}',
  blockers TEXT[] DEFAULT '{}',
  tags TEXT[] DEFAULT '{}',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT DEFAULT '',
  npao_category TEXT DEFAULT 'opportunity',
  phase TEXT DEFAULT 'pre_d',
  urgency_score REAL DEFAULT 0.0,
  dependency_score REAL DEFAULT 0.0,
  business_score REAL DEFAULT 0.0,
  resource_score REAL DEFAULT 0.0,
  priority_score REAL DEFAULT 0.0,
  status TEXT DEFAULT 'open',
  dependencies TEXT[] DEFAULT '{}',
  assigned_agent TEXT DEFAULT '',
  tags TEXT[] DEFAULT '{}',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS config (
  key TEXT PRIMARY KEY,
  value JSONB NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS activity_log (
  id SERIAL PRIMARY KEY,
  action TEXT NOT NULL,
  details JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);
