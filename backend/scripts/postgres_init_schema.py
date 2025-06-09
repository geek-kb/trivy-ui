import os
import asyncio
from urllib.parse import quote_plus
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text, inspect
from app.core.database import Base

# ---------- Configuration ----------
# Admin (superuser) credentials
admin_user = os.getenv("DB_ROOT_USER") or os.getenv("POSTGRES_USER")
admin_pass = os.getenv("DB_ROOT_PASSWORD") or os.getenv("POSTGRES_PASSWORD")
# Application user credentials
db_app_user = os.getenv("DB_APP_USER")
db_app_pass = os.getenv("DB_APP_PASSWORD")
# Connection details
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

if not all(
    [admin_user, admin_pass, db_app_user, db_app_pass, db_host, db_port, db_name]
):
    raise EnvironmentError("Missing one or more required environment variables")

# Strip any tcp:// prefix from port
if db_port is None:
    db_port = "5432"
elif db_port.startswith("tcp://"):
    host_part, port_part = db_port.split("//", 1)[1].rsplit(":", 1)
    db_port = port_part

# Build URL with superuser credentials
encoded_admin_pass = quote_plus(str(admin_pass))
db_url = f"postgresql+asyncpg://{admin_user}:{encoded_admin_pass}@{db_host}:{db_port}/{db_name}"
print(f"Connecting to database at {db_url}")

engine = create_async_engine(db_url, echo=False, future=True)


async def create_postgres_users(conn):
    print("→ Creating application user if not exists…")
    await conn.execute(
        text(
            """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT FROM pg_catalog.pg_roles WHERE rolname = :username
            ) THEN
                EXECUTE format(
                    'CREATE ROLE %I WITH LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION',
                    :username, :password
                );
            END IF;
        END
        $$;
        """
        ),
        {"username": db_app_user, "password": db_app_pass},
    )


async def grant_privileges(conn):
    print("→ Granting privileges to application user…")
    statements = [
        f'GRANT CONNECT ON DATABASE "{db_name}" TO "{db_app_user}"',
        f'GRANT USAGE ON SCHEMA public TO "{db_app_user}"',
        f'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "{db_app_user}"',
        f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "{db_app_user}"',
    ]
    for stmt in statements:
        await conn.execute(text(stmt))


async def create_schema(conn):
    print("→ Creating tables from Base metadata…")
    await conn.run_sync(Base.metadata.create_all)


async def ensure_created_at_column(conn):
    print("→ Ensuring 'created_at' column exists in 'reports' table…")

    def _alter_if_needed(sync_conn):
        inspector = inspect(sync_conn)
        if "reports" in inspector.get_table_names(schema="public"):
            cols = [
                c["name"] for c in inspector.get_columns("reports", schema="public")
            ]
            if "created_at" not in cols:
                print("   • Adding 'created_at' column…")
                sync_conn.execute(
                    text(
                        """
                    ALTER TABLE public.reports
                    ADD COLUMN created_at TIMESTAMPTZ;
                    """
                    ),
                )

    await conn.run_sync(_alter_if_needed)


async def init_schema():
    async with engine.begin() as conn:
        await create_postgres_users(conn)
        await grant_privileges(conn)
        await create_schema(conn)
        await ensure_created_at_column(conn)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_schema())
