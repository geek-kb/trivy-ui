# File: backend/scripts/postgres_init_schema.py

import os
import asyncio
from urllib.parse import quote_plus
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text, inspect
from app.core.database import Base

# ---------- Configuration ----------
db_user = os.getenv("POSTGRES_USER")
db_pass = os.getenv("POSTGRES_PASSWORD")
db_host = os.getenv("POSTGRES_HOST")
db_port = os.getenv("POSTGRES_PORT")
db_name = os.getenv("POSTGRES_DB")
db_app_user = os.getenv("DB_APP_USER")
db_app_pass = os.getenv("DB_APP_PASSWORD")

if not all([db_user, db_pass, db_host, db_port, db_name, db_app_user, db_app_pass]):
    raise EnvironmentError("Missing one or more required environment variables")

db_url = f"postgresql+asyncpg://{db_user}:{quote_plus(str(db_pass))}@{db_host}:{db_port}/{db_name}"

print(f"Connecting to database at {db_url}")

engine = create_async_engine(db_url, echo=False)


# ---------- Schema Setup Logic ----------
async def create_postgres_users(conn):
    print("Creating application user if not exists...")
    await conn.execute(
        text(
            f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT FROM pg_catalog.pg_roles WHERE rolname = :username
            ) THEN
                CREATE ROLE "{db_app_user}" WITH LOGIN PASSWORD :password NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
            END IF;
        END
        $$;
    """
        ),
        {"username": db_app_user, "password": db_app_pass},
    )


async def grant_privileges(conn):
    print("Granting privileges to application user...")
    await conn.execute(
        text(
            f"""
        GRANT CONNECT ON DATABASE {db_name} TO "{db_app_user}";
        GRANT USAGE ON SCHEMA public TO "{db_app_user}";
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "{db_app_user}";
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "{db_app_user}";
    """
        )
    )


async def create_schema(conn):
    print("Creating tables from Base metadata...")
    await conn.run_sync(Base.metadata.create_all)


async def ensure_created_at_column(conn):
    print("Ensuring 'created_at' column exists in 'reports' table...")

    def alter_if_needed(sync_conn):
        inspector = inspect(sync_conn)
        if "reports" in inspector.get_table_names(schema="public"):
            cols = [
                col["name"] for col in inspector.get_columns("reports", schema="public")
            ]
            if "created_at" not in cols:
                print("Adding 'created_at' column...")
                sync_conn.execute(
                    text(
                        """
                    ALTER TABLE public.reports
                    ADD COLUMN created_at TIMESTAMPTZ;
                """
                    )
                )

    await conn.run_sync(alter_if_needed)


# ---------- Main Entrypoint ----------
async def init_schema():
    async with engine.begin() as conn:
        await create_postgres_users(conn)
        await grant_privileges(conn)
        await create_schema(conn)
        await ensure_created_at_column(conn)


if __name__ == "__main__":
    asyncio.run(init_schema())
