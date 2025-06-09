from app.db.base_class import Base
from app.models.report import ReportModel  # noqa

# Import all the models here for Alembic migrations
__all__ = [
    "ReportModel",
]
