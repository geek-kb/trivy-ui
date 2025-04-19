# File: backend/app/storage/base.py

from typing import Dict, Any, List
from abc import ABC, abstractmethod


class StorageBackend(ABC):
    @abstractmethod
    async def save_report(self, report_id: str, report_data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def get_report(self, report_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def list_reports(self, filters: Dict[str, Any] = {}) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def delete_report(self, report_id: str) -> None:
        pass

    @abstractmethod
    async def count_reports(self) -> int:
        """Return the total number of reports."""
        pass
