# File: backend/app/api/routes.py

import logging
import json
import uuid
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import List, Optional

import pytz
from fastapi import APIRouter, HTTPException, File, UploadFile, Query, Request
from fastapi import status, Body
from sqlalchemy import text

from app.schemas.report import TrivyReport
from app.storage.factory import get_storage
from app.core.database import engine
from app.core.config import settings

# --- Setup ---
logger = logging.getLogger(__name__)
router = APIRouter()
storage = get_storage()

# --- Constants ---
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = (".json", ".spdx.json", ".cdx.json", ".tar")
MAX_FILENAME_LENGTH = 100
UPLOAD_RATE_LIMIT = 10
_upload_attempts: dict = {}


# --- Helper Functions ---
def now_utc() -> str:
    """Return current UTC time as ISO8601 string."""
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()


def format_timestamp(ts: str) -> str:
    """Format UTC ISO string to local timezone formatted string."""
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts)
        if settings.TIMEZONE:
            tzinfo = pytz.timezone(settings.TIMEZONE)
            dt = dt.astimezone(tzinfo)
        else:
            dt = dt.astimezone()
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error(f"Failed to format timestamp: {e}")
        return ts


def get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def fallback_artifact_name(name: Optional[str], fallback_filename: str) -> str:
    if not name or name.strip() in [".", ""]:
        return fallback_filename
    return re.sub(r"[^a-zA-Z0-9_\\-\\.]", "_", name.strip()) or fallback_filename


def sanitize_json(data: dict) -> dict:
    allowed_keys = {"ArtifactName", "Results", "_meta", "CreatedAt"}
    return {k: v for k, v in data.items() if k in allowed_keys}


def sanitize_filename(filename: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\\-\\.]", "_", filename.strip())[:MAX_FILENAME_LENGTH]


def rate_limit_check(client_ip: str):
    now = datetime.utcnow().timestamp()
    _upload_attempts.setdefault(client_ip, [])
    _upload_attempts[client_ip] = [
        t for t in _upload_attempts[client_ip] if now - t < 60
    ]
    if len(_upload_attempts[client_ip]) >= UPLOAD_RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many uploads, slow down.")
    _upload_attempts[client_ip].append(now)


# --- Routes ---
@router.get("/")
def root():
    return {"message": "Trivy UI backend is alive"}


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/db-health")
async def db_health_check():
    if engine is None:
        return {"database": "not configured (filesystem backend)"}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"database": "healthy"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")


@router.post("/report")
async def upload_report(report: TrivyReport):
    report_id = str(uuid.uuid4())
    artifact_name = fallback_artifact_name(report.ArtifactName, "artifact-from-api")
    report_dict = report.dict()

    if "_meta" not in report_dict:
        report_dict["_meta"] = {}

    report_dict["_meta"]["timestamp"] = now_utc()
    report_dict["_meta"]["id"] = report_id
    report_dict["ArtifactName"] = artifact_name

    await storage.save_report(report_id, report_dict)
    return {"id": report_id, "artifact": artifact_name}


@router.post("/upload-report")
async def upload_report_file(request: Request, file: UploadFile = File(...)):
    client_ip = get_client_ip(request)
    rate_limit_check(client_ip)

    filename = (file.filename or "").strip().lower()
    if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Only {', '.join(ALLOWED_EXTENSIONS)} files are accepted",
        )
    if len(filename) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413, detail="File too large. Max allowed size is 5MB."
        )

    contents = await file.read()
    try:
        data = json.loads(contents.decode("utf-8", errors="ignore"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Uploaded file is not valid JSON")

    if (
        not isinstance(data, dict)
        or "Results" not in data
        or not isinstance(data["Results"], list)
    ):
        raise HTTPException(
            status_code=400, detail="Uploaded JSON must contain 'Results' field as list"
        )

    sanitized_data = sanitize_json(data)

    try:
        report = TrivyReport(**sanitized_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Trivy report format: {e}")

    report_id = str(uuid.uuid4())
    artifact_name = fallback_artifact_name(
        report.ArtifactName, sanitize_filename(filename)
    )

    if "_meta" not in sanitized_data:
        sanitized_data["_meta"] = {}

    sanitized_data["_meta"]["timestamp"] = now_utc()
    sanitized_data["_meta"]["id"] = report_id
    sanitized_data["ArtifactName"] = artifact_name

    await storage.save_report(report_id, sanitized_data)
    return {"id": report_id, "artifact": artifact_name}


@router.get("/report/{report_id}")
async def get_report(
    report_id: str,
    severity: Optional[List[str]] = Query(None),
    pkgName: Optional[str] = Query(None),
    vulnId: Optional[str] = Query(None),
):
    try:
        report_data = await storage.get_report(report_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    report = TrivyReport(**report_data)
    severity_filter = [s.upper() for s in severity] if severity else None
    pkg_filter = pkgName.lower() if pkgName else None
    vuln_filter = vulnId.lower() if vulnId else None

    severity_count = defaultdict(int)
    filtered_results = []

    for result in report.Results:
        vulns = result.Vulnerabilities or []
        for vuln in vulns:
            severity_count[vuln.Severity.upper()] += 1

        def matches_filters(v):
            if not v.VulnerabilityID.upper().startswith("CVE-"):
                return False
            if severity_filter and v.Severity.upper() not in severity_filter:
                return False
            if pkg_filter and pkg_filter not in v.PkgName.lower():
                return False
            if vuln_filter and vuln_filter not in v.VulnerabilityID.lower():
                return False
            return True

        filtered_vulns = [v for v in vulns if matches_filters(v)]
        filtered_results.append(
            {"Target": result.Target, "Vulnerabilities": filtered_vulns}
        )

    summary = {
        "artifact": report.ArtifactName,
        "timestamp": format_timestamp(
            report.dict().get("_meta", {}).get("timestamp", "")
        ),
        "critical": severity_count.get("CRITICAL", 0),
        "high": severity_count.get("HIGH", 0),
        "medium": severity_count.get("MEDIUM", 0),
        "low": severity_count.get("LOW", 0),
        "unknown": severity_count.get("UNKNOWN", 0),
        "total": sum(severity_count.values()),
    }

    return {
        "artifact": report.ArtifactName,
        "summary": summary,
        "results": filtered_results,
    }


@router.get("/reports")
async def list_reports(
    skip: int = 0,
    limit: int = 20,
    artifact: Optional[str] = Query(None),
    min_critical: int = 0,
    min_high: int = 0,
    min_medium: int = 0,
    min_low: int = 0,
):
    reports_data = await storage.list_reports()
    reports_with_meta = []

    for data in reports_data:
        try:
            report = TrivyReport(**data)
            raw_ts = data.get("_meta", {}).get("timestamp", "")
            formatted_ts = format_timestamp(raw_ts)
            report_id = data.get("_meta", {}).get("id")
            if not report_id:
                continue

            severity_count = defaultdict(int)
            for result in report.Results:
                for vuln in result.Vulnerabilities or []:
                    severity_count[vuln.Severity.upper()] += 1

            reports_with_meta.append(
                {
                    "id": report_id,
                    "artifact": report.ArtifactName,
                    "timestamp": formatted_ts,
                    "critical": severity_count.get("CRITICAL", 0),
                    "high": severity_count.get("HIGH", 0),
                    "medium": severity_count.get("MEDIUM", 0),
                    "low": severity_count.get("LOW", 0),
                }
            )
        except Exception as e:
            logger.warning(f"Skipping invalid report during listing: {e}")

    def passes_filters(r):
        if artifact and artifact.lower() not in r["artifact"].lower():
            return False
        if r["critical"] < min_critical:
            return False
        if r["high"] < min_high:
            return False
        if r["medium"] < min_medium:
            return False
        if r["low"] < min_low:
            return False
        return True

    filtered = list(filter(passes_filters, reports_with_meta))
    sorted_reports = sorted(
        filtered, key=lambda r: r.get("timestamp", ""), reverse=True
    )
    paginated = sorted_reports[skip : skip + limit]

    return {
        "total": len(filtered),
        "skip": skip,
        "limit": limit,
        "results": paginated,
    }


@router.delete("/reports")
async def delete_reports(request: Request, body: dict = Body(...)):
    report_ids: List[str] = body.get("report_ids", [])
    if not isinstance(report_ids, list) or not all(
        isinstance(rid, str) for rid in report_ids
    ):
        raise HTTPException(status_code=400, detail="Invalid report_ids payload")

    deleted = 0
    for report_id in report_ids:
        try:
            await storage.delete_report(report_id)
            deleted += 1
        except FileNotFoundError:
            continue  # It's okay if some reports were already missing

    return {"deleted": deleted}


@router.get("/metrics")
async def metrics():
    try:
        total = await storage.count_reports()
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"error": str(e)}
    return {"reports_count": total}
