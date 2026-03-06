-- API Gateway v10 baseline migration (documentary SQL for dev mode)
CREATE TABLE IF NOT EXISTS tools (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    creator_agent_id TEXT NOT NULL,
    tags TEXT,
    manifest_json TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tools_name ON tools(name);
CREATE INDEX IF NOT EXISTS idx_tools_creator ON tools(creator_agent_id);

CREATE TABLE IF NOT EXISTS tool_versions (
    id TEXT PRIMARY KEY,
    tool_id TEXT NOT NULL,
    version TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS usage_logs (
    id TEXT PRIMARY KEY,
    tool_id TEXT NOT NULL,
    caller_agent_id TEXT NOT NULL,
    status TEXT NOT NULL,
    cost REAL NOT NULL,
    hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ratings (
    tool_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    score INTEGER NOT NULL,
    review TEXT,
    PRIMARY KEY(tool_id, agent_id)
);

CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    model TEXT NOT NULL,
    amount REAL NOT NULL
);
