# File: backend/app/models/report.py

from sqlalchemy import Column, String, Text, DateTime, func
from app.core.database import Base


class ReportModel(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, index=True)
    artifact = Column(String, nullable=True)
    data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
