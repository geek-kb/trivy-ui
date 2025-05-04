# File: backend/app/storage/postgres.py

import os
import json
from typing import Dict, Any, List
from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.base import StorageBackend
from app.core.database import get_session, Base
from app.models.report import ReportModel


class PostgresStorage(StorageBackend):
    def __init__(self):
        pass

    async def save_report(self, report_id: str, report_data: Dict[str, Any]) -> None:
        session: AsyncSession = get_session()
        async with session.begin():
            artifact_name = report_data.get("artifact", "")
            serialized_data = json.dumps(report_data)
            report = ReportModel(
                id=report_id,
                artifact=artifact_name,
                data=serialized_data,
                # created_at is set automatically by server_default
            )
            session.add(report)

    async def get_report(self, report_id: str) -> Dict[str, Any]:
        session: AsyncSession = get_session()
        async with session.begin():
            result = await session.execute(
                select(ReportModel).where(ReportModel.id == report_id)
            )
            report = result.scalar_one_or_none()
            if not report:
                raise FileNotFoundError(f"Report {report_id} not found")
            if not isinstance(report.data, str):
                raise ValueError(f"Invalid report data type for report {report_id}")
            return json.loads(report.data)

    async def list_reports(self, filters: Dict[str, Any] = {}) -> List[Dict[str, Any]]:
        session: AsyncSession = get_session()
        async with session.begin():
            result = await session.execute(
                select(ReportModel).order_by(ReportModel.created_at.desc())
            )
            reports = result.scalars().all()
            parsed_reports = []
            for r in reports:
                if isinstance(r.data, str):
                    parsed = json.loads(r.data)
                    # Ensure _meta exists and include timestamp of creation
                    parsed_meta = parsed.setdefault("_meta", {})
                    parsed_meta.update({
                        "id": r.id,
                        "artifact": r.artifact,
                        "timestamp": r.created_at.isoformat() if r.created_at else ""
                    })
                    parsed_reports.append(parsed)
            return parsed_reports

    async def delete_report(self, report_id: str) -> None:
        session: AsyncSession = get_session()
        async with session.begin():
            await session.execute(
                delete(ReportModel).where(ReportModel.id == report_id)
            )

    async def count_reports(self) -> int:
        async with get_session() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM reports"))
            count = result.scalar()
            return count or 0
