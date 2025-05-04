# File: backend/scripts/fix_timestamps.py

import os
import asyncio
from datetime import datetime, timezone

import pytz

from app.storage.factory import get_storage
from app.schemas.report import TrivyReport
from app.core.config import settings


async def migrate_timestamps():
    storage = get_storage()
    reports = await storage.list_reports()

    tzinfo = pytz.timezone(settings.TIMEZONE) if settings.TIMEZONE else None

    updated = 0
    skipped = 0

    for data in reports:
        try:
            report_id = data.get("_meta", {}).get("id")
            timestamp = data.get("_meta", {}).get("timestamp")

            if not report_id or not timestamp:
                skipped += 1
                continue

            # Parse existing timestamp assuming it was saved incorrectly as naive UTC
            if timestamp.endswith("Z"):
                timestamp = timestamp.replace("Z", "+00:00")

            dt = datetime.fromisoformat(timestamp)

            # Force treat as UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            # Convert to desired timezone
            if tzinfo:
                dt = dt.astimezone(tzinfo)
            else:
                dt = dt.astimezone()

            corrected_timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")

            # Load full report
            report = TrivyReport(**data)
            report_dict = report.dict()

            # Update
            report_dict["_meta"]["timestamp"] = corrected_timestamp

            await storage.save_report(report_id, report_dict)
            updated += 1
        except Exception as e:
            print(f"Failed to fix report {data.get('_meta', {}).get('id')}: {e}")
            skipped += 1

    print(f"Finished migration. Updated: {updated}, Skipped: {skipped}")


if __name__ == "__main__":
    asyncio.run(migrate_timestamps())
