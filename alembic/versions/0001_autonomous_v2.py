"""autonomous v2 schema stub"""

revision = "0001_autonomous_v2"
down_revision = None

TABLES = [
    "agents", "companies", "agent_teams", "business_plans", "job_postings", "human_task_outcomes",
    "market_orders", "company_shares", "synthetic_users", "demand_series", "sensing_events",
]


def upgrade() -> list[str]:
    return [f"create table {t}" for t in TABLES]


def downgrade() -> list[str]:
    return [f"drop table {t}" for t in TABLES]
