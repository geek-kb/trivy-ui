#!/usr/bin/env python3
import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import get_session
from app.models.report import ReportModel
from sqlalchemy import select

async def test_db():
    try:
        print("Testing database connection...")
        async for session in get_session():
            print("✓ Database session created successfully")
            
            # Test a simple query
            result = await session.execute(select(ReportModel).limit(1))
            print("✓ Database query executed successfully")
            
            # Test count
            from sqlalchemy import func
            count_result = await session.execute(select(func.count(ReportModel.id)))
            count = count_result.scalar() or 0
            print(f"✓ Found {count} reports in database")
            break
        
        print("✓ All database tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_db())
