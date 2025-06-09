from typing import Any, Dict, List, Optional
import json
from datetime import datetime
from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.base import StorageBackend
from app.db.session import get_session
from app.models.report import ReportModel


class PostgresStorage(StorageBackend):
    async def save_report(self, report_id: str, report_data: Dict[str, Any]) -> None:
        async with get_session() as session:
            async with session.begin():
                serialized = json.dumps(report_data)
                session.add(
                    ReportModel(
                        id=report_id,
                        artifact=report_data.get("ArtifactName", ""),
                        data=serialized,
                        # created_at via server_default
                    )
                )

    async def get_report(self, report_id: str) -> Dict[str, Any]:
        async with get_session() as session:
            res = await session.execute(
                select(ReportModel).where(ReportModel.id == report_id)
            )
            rpt = res.scalar_one_or_none()
            if not rpt:
                raise FileNotFoundError(f"Report {report_id} not found")
            return json.loads(rpt.data)

    async def list_reports(
        self, filters: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        if filters is None:
            filters = {}

        async with get_session() as session:
            query = select(ReportModel).order_by(ReportModel.created_at.desc())

            # Apply filters if provided
            if filters:
                conditions = [
                    getattr(ReportModel, key) == value for key, value in filters.items()
                ]
                query = query.where(and_(*conditions))

            res = await session.execute(query)
            rows = res.scalars().all()
            out: List[Dict[str, Any]] = []
            for r in rows:
                parsed = json.loads(r.data)
                parsed["_meta"] = {
                    "id": r.id,
                    "artifact": r.artifact,
                    "timestamp": (
                        r.created_at.isoformat() if r.created_at is not None else ""
                    ),
                }
                out.append(parsed)
            return out

    async def delete_report(self, report_id: str) -> None:
        async with get_session() as session:
            async with session.begin():
                await session.execute(
                    delete(ReportModel).where(ReportModel.id == report_id)
                )

    async def count_reports(self) -> int:
        async with get_session() as session:
            res = await session.execute(select(func.count(ReportModel.id)))
            return res.scalar() or 0
