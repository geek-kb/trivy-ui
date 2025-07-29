#!/usr/bin/env python3
"""
Database initialization script for Trivy UI.
This script creates the necessary tables for PostgreSQL backend.
"""

import asyncio
import sys
import os

# Add the parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import init_db_engine, Base
from app.core.config import get_settings
from app.models.report import ReportModel  # Import to register the model
from app.core.logging import logger


async def create_tables():
    """Create all database tables."""
    settings = get_settings()
    
    if settings.DB_BACKEND != "postgres":
        logger.error(f"This script is for PostgreSQL backend only. Current backend: {settings.DB_BACKEND}")
        return False
    
    try:
        logger.info("Initializing database connection...")
        engine = await init_db_engine()
        
        if engine is None:
            logger.error("Failed to initialize database engine")
            return False
        
        logger.info("Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False


async def main():
    """Main function."""
    success = await create_tables()
    if not success:
        sys.exit(1)
    
    print("✅ Database initialization completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
