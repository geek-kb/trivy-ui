from app.core.config import settings


class Debug:
    def __init__(self):
        self.debug = settings.DEBUG
        self.env = settings.ENV

        # Only set PostgreSQL URL if using postgres backend
        if settings.DB_BACKEND == "postgres":
            self.postgres_url = self._get_postgres_url()

    def _get_postgres_url(self) -> str:
        """Only called if using PostgreSQL backend"""
        return f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
