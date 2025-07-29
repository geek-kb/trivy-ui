from typing import Any, Dict, List, Optional
import json
from datetime import datetime
from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.base import StorageBackend
from app.core.database import get_session
from app.models.report import ReportModel


class PostgresStorage(StorageBackend):
    async def save_report(self, report_id: str, report_data: Dict[str, Any]) -> None:
        async for session in get_session():
            serialized = json.dumps(report_data)
            session.add(
                ReportModel(
                    id=report_id,
                    artifact=report_data.get("ArtifactName", ""),
                    data=serialized,
                    # created_at via server_default
                )
            )
            await session.commit()
            break

    async def get_report(self, report_id: str) -> Dict[str, Any]:
        async for session in get_session():
            res = await session.execute(
                select(ReportModel).where(ReportModel.id == report_id)
            )
            rpt = res.scalar_one_or_none()
            if not rpt:
                raise FileNotFoundError(f"Report {report_id} not found")
            report_data = json.loads(rpt.data)
            # Add _meta field to match filesystem storage format
            report_data["_meta"] = {
                "id": rpt.id,
                "uploaded_at": rpt.created_at.isoformat() if rpt.created_at else ""
            }
            return report_data

    async def list_reports(self) -> List[Dict[str, Any]]:
        async for session in get_session():
            res = await session.execute(select(ReportModel))
            rpms = res.scalars().all()
            reports = []
            for rpt in rpms:
                report_data = json.loads(rpt.data)
                # Add _meta field to match filesystem storage format
                report_data["_meta"] = {
                    "id": rpt.id,
                    "uploaded_at": rpt.created_at.isoformat() if rpt.created_at else ""
                }
                reports.append(report_data)
            return reports

    async def delete_report(self, report_id: str) -> bool:
        async for session in get_session():
            res = await session.execute(
                select(ReportModel).where(ReportModel.id == report_id)
            )
            rpt = res.scalar_one_or_none()
            if not rpt:
                return False
            await session.delete(rpt)
            await session.commit()  # Actually commit the deletion
            return True

    async def count_reports(self) -> int:
        async for session in get_session():
            res = await session.execute(select(func.count(ReportModel.id)))
            return res.scalar() or 0
