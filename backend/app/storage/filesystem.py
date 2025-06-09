# File: backend/app/storage/filesystem.py

from app.storage.base import StorageBackend
from typing import Dict, Any, List
from pathlib import Path
import os
import json


class FilesystemStorage(StorageBackend):
    def __init__(self):
        # Always store reports under the `app/storage/reports` directory
        self.reports_dir = Path(__file__).parent / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    async def save_report(self, report_id: str, report_data: Dict[str, Any]) -> None:
        file_path = self.reports_dir / f"{report_id}.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

    async def get_report(self, report_id: str) -> Dict[str, Any]:
        file_path = self.reports_dir / f"{report_id}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Report {report_id} not found")
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    async def list_reports(self, filters: Dict[str, Any] = {}) -> List[Dict[str, Any]]:
        reports = []
        for path in self.reports_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    reports.append(json.load(f))
            except Exception:
                continue
        return reports

    async def delete_report(self, report_id: str) -> None:
        file_path = self.reports_dir / f"{report_id}.json"
        if file_path.exists():
            file_path.unlink()

    async def count_reports(self) -> int:
        try:
            return len(
                [
                    name
                    for name in os.listdir(self.reports_dir)
                    if os.path.isfile(os.path.join(self.reports_dir, name))
                    and name.endswith(".json")
                ]
            )
        except Exception:
            return 0
