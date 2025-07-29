import os
import asyncio
from urllib.parse import quote_plus
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text, inspect
from app.core.database import Base

# ---------- Configuration ----------
# Admin (superuser) credentials
admin_user = os.getenv("DB_ROOT_USER") or os.getenv("POSTGRES_USER") or "postgres"
admin_pass = os.getenv("DB_ROOT_PASSWORD") or os.getenv("POSTGRES_PASSWORD") or "postgres"
# Application user credentials
db_app_user = os.getenv("DB_APP_USER") or os.getenv("POSTGRES_USER") or "trivyuser"
db_app_pass = os.getenv("DB_APP_PASSWORD") or os.getenv("POSTGRES_PASSWORD") or "snd&sA21Bq"
# Connection details
db_host = os.getenv("DB_HOST") or os.getenv("POSTGRES_SERVER") or "postgres"
db_port = os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT") or "5432"
db_name = os.getenv("DB_NAME") or os.getenv("POSTGRES_DB") or "trivydb"

print(f"Config: admin_user={admin_user}, db_app_user={db_app_user}, db_host={db_host}, db_port={db_port}, db_name={db_name}")

if not all([admin_user, admin_pass, db_app_user, db_app_pass, db_host, db_port, db_name]):
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
# URL for postgres database (to create the target database)
postgres_url = f"postgresql+asyncpg://{admin_user}:{encoded_admin_pass}@{db_host}:{db_port}/postgres"
print(f"Connecting to database at {db_url}")

engine = create_async_engine(db_url, echo=False, future=True)
postgres_engine = create_async_engine(postgres_url, echo=False, future=True)

# Track results
results = []

async def log_step(step_name, success, message=""):
    status = "✓ SUCCESS" if success else "✗ FAILED"
    full_message = f"{status}: {step_name}"
    if message:
        full_message += f" - {message}"
    print(full_message)
    results.append({"step": step_name, "success": success, "message": message})

async def create_database_if_not_exists():
    try:
        async with postgres_engine.begin() as conn:
            # Check if database exists
            result = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": db_name}
            )
            if not result.fetchone():
                # Close the transaction before creating database
                await conn.commit()
                # Create database (can't be done in a transaction)
                await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                await log_step(f"Create database '{db_name}'", True, "Database created")
            else:
                await log_step(f"Create database '{db_name}'", True, "Database already exists")
    except Exception as e:
        await log_step(f"Create database '{db_name}'", False, str(e))
    finally:
        await postgres_engine.dispose()

async def create_postgres_users():
    try:
        async with engine.begin() as conn:
            # Simple approach - use direct SQL without parameters in DO block
            await conn.execute(text(f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '{db_app_user}') THEN
                        CREATE ROLE "{db_app_user}" WITH LOGIN PASSWORD '{db_app_pass}' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
                    END IF;
                END
                $$;
            """))
            await log_step(f"Create user '{db_app_user}'", True, "User created or already exists")
    except Exception as e:
        await log_step(f"Create user '{db_app_user}'", False, str(e))

async def create_reports_table():
    try:
        # Connect as postgres superuser to create table
        postgres_pass = os.getenv('DB_ROOT_PASSWORD') or os.getenv('POSTGRES_PASSWORD') or admin_pass
        postgres_db_url = f"postgresql+asyncpg://postgres:{quote_plus(postgres_pass)}@{db_host}:{db_port}/{db_name}"
        postgres_db_engine = create_async_engine(postgres_db_url, echo=False, future=True)
        
        async with postgres_db_engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS reports (
                    id VARCHAR PRIMARY KEY,
                    artifact VARCHAR,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            await log_step("Create reports table", True, "Table created or already exists")
        
        await postgres_db_engine.dispose()
    except Exception as e:
        await log_step("Create reports table", False, str(e))

async def grant_privileges():
    try:
        # Connect as postgres superuser to grant permissions
        postgres_pass = os.getenv('DB_ROOT_PASSWORD') or os.getenv('POSTGRES_PASSWORD') or admin_pass
        postgres_db_url = f"postgresql+asyncpg://postgres:{quote_plus(postgres_pass)}@{db_host}:{db_port}/{db_name}"
        postgres_db_engine = create_async_engine(postgres_db_url, echo=False, future=True)
        
        async with postgres_db_engine.begin() as conn:
            # Grant database privileges
            await conn.execute(text(f'GRANT CONNECT ON DATABASE "{db_name}" TO "{db_app_user}"'))
            await log_step(f"Grant CONNECT on database to {db_app_user}", True)
        
        async with postgres_db_engine.begin() as conn:
            # Grant schema privileges
            await conn.execute(text(f'GRANT USAGE ON SCHEMA public TO "{db_app_user}"'))
            await log_step(f"Grant USAGE on schema to {db_app_user}", True)
        
        async with postgres_db_engine.begin() as conn:
            # Grant table privileges
            await conn.execute(text(f'GRANT ALL PRIVILEGES ON TABLE reports TO "{db_app_user}"'))
            await log_step(f"Grant ALL on reports table to {db_app_user}", True)
        
        async with postgres_db_engine.begin() as conn:
            # Grant sequence privileges
            await conn.execute(text(f'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "{db_app_user}"'))
            await log_step(f"Grant ALL on sequences to {db_app_user}", True)
        
        async with postgres_db_engine.begin() as conn:
            # Grant default privileges for future objects
            await conn.execute(text(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "{db_app_user}"'))
            await conn.execute(text(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "{db_app_user}"'))
            await log_step(f"Grant default privileges to {db_app_user}", True)
        
        await postgres_db_engine.dispose()
    except Exception as e:
        await log_step("Grant privileges", False, str(e))

async def init_schema():
    print("=== PostgreSQL Database Initialization ===")
    
    # Step 1: Create database
    await create_database_if_not_exists()
    
    # Step 2: Create user
    await create_postgres_users()
    
    # Step 3: Create tables
    await create_reports_table()
    
    # Step 4: Grant privileges
    await grant_privileges()
    
    await engine.dispose()
    
    # Print summary
    print("\n=== INITIALIZATION SUMMARY ===")
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    print(f"Completed {success_count}/{total_count} steps successfully")
    
    for result in results:
        status = "✓" if result["success"] else "✗"
        message = f" ({result['message']})" if result["message"] else ""
        print(f"{status} {result['step']}{message}")
    
    if success_count == total_count:
        print("\n🎉 All initialization steps completed successfully!")
    else:
        print(f"\n⚠️  {total_count - success_count} steps failed. Check errors above.")
    
    return success_count == total_count


if __name__ == "__main__":
    asyncio.run(init_schema())
