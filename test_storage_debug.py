#!/usr/bin/env python3
import asyncio
import json
import sys
import os
import traceback

# Add the app directory to Python path
sys.path.insert(0, '/app')

# Set environment to match the container
os.environ['DB_BACKEND'] = 'postgres'
os.environ['POSTGRES_SERVER'] = 'postgres'
os.environ['POSTGRES_PORT'] = '5432'
os.environ['POSTGRES_DB'] = 'trivyui'
os.environ['POSTGRES_USER'] = 'trivyui_app'
os.environ['POSTGRES_PASSWORD'] = 'your_password_here'  # This should match the actual password

async def test_storage():
    try:
        print("Importing modules...")
        from app.storage.factory import get_storage
        from app.core.database import init_db_engine
        
        print("Initializing database engine...")
        await init_db_engine()
        
        print("Getting storage instance...")
        storage = get_storage()
        print(f"Storage type: {type(storage)}")
        
        print("Testing save_report...")
        test_data = {
            "ArtifactName": "test-artifact",
            "Results": []
        }
        await storage.save_report("test-123", test_data)
        print("✓ save_report completed successfully")
        
        print("Testing list_reports...")
        reports = await storage.list_reports()
        print(f"✓ list_reports returned {len(reports)} reports")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print(f"Error type: {type(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_storage())
    sys.exit(0 if result else 1)
