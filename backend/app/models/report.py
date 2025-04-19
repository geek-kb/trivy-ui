# backend/app/models/report.py

from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Text

Base = declarative_base()


class ReportModel(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, index=True)
    artifact = Column(String, nullable=True)
    data = Column(Text, nullable=False)
