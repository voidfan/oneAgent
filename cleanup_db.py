"""
One-time database cleanup script.
Drops all stale PostgreSQL composite types and tables left by failed migrations.
Run this ONCE inside the backend container or from a machine with DB access:

    python cleanup_db.py

Or via docker exec:
    docker exec xagent-backend python /app/cleanup_db.py
"""
import asyncio
import os

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://xagent:xagent_secret@localhost:5432/xagent"
)

# All table names and enum type names that may have stale composite types
STALE_NAMES = [
    # Tables (composite types auto-created by PG)
    "workflows", "workflow_sessions",
    "tenants", "agents", "agent_executions", "agent_steps",
    "conversations", "messages",
    "memory_entries",
    "tools", "tool_executions",
    "users",
    "tenant_tools", "tenant_mcp_configs", "tenant_skills",
    # Named ENUM types
    "tenantstatus", "agentstatus", "steptype",
    "messagerole", "memorytype", "tooltype",
]


async def cleanup():
    engine = create_async_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        for name in STALE_NAMES:
            try:
                await conn.execute(text(f"DROP TYPE IF EXISTS {name} CASCADE"))
                print(f"  Dropped type: {name}")
            except Exception as e:
                print(f"  Skip {name}: {e}")
        # Also drop tables if they exist (in correct dependency order)
        drop_tables_sql = """
        DROP TABLE IF EXISTS workflow_sessions CASCADE;
        DROP TABLE IF EXISTS workflows CASCADE;
        DROP TABLE IF EXISTS agent_steps CASCADE;
        DROP TABLE IF EXISTS agent_executions CASCADE;
        DROP TABLE IF EXISTS tool_executions CASCADE;
        DROP TABLE IF EXISTS tools CASCADE;
        DROP TABLE IF EXISTS memory_entries CASCADE;
        DROP TABLE IF EXISTS messages CASCADE;
        DROP TABLE IF EXISTS conversations CASCADE;
        DROP TABLE IF EXISTS agents CASCADE;
        DROP TABLE IF EXISTS tenant_tools CASCADE;
        DROP TABLE IF EXISTS tenant_mcp_configs CASCADE;
        DROP TABLE IF EXISTS tenant_skills CASCADE;
        DROP TABLE IF EXISTS tenants CASCADE;
        DROP TABLE IF EXISTS users CASCADE;
        """
        for stmt in drop_tables_sql.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    await conn.execute(text(stmt))
                    print(f"  Executed: {stmt[:60]}")
                except Exception as e:
                    print(f"  Skip: {e}")
    await engine.dispose()
    print("\nCleanup complete. Now restart the backend to recreate all tables.")


if __name__ == "__main__":
    asyncio.run(cleanup())
