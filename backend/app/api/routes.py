# File: backend/app/api/routes/reports.py

import json
import uuid
import re
from datetime import datetime, timezone
from typing import List, Optional, Dict
from collections import defaultdict
from fastapi import (
    APIRouter,
    HTTPException,
    File,
    UploadFile,
    Query,
    Request,
    Body,
    status,
)
import pytz

from app.schemas.report import TrivyReport
from app.storage.factory import get_storage
from app.core.config import get_settings
from app.core.config import settings
from app.core.logging import logger

# Constants
ALLOWED_EXTENSIONS = {".json", ".txt"}
MAX_FILENAME_LENGTH = 255
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
UPLOAD_RATE_LIMIT = 10
RATE_LIMIT_WINDOW = 60  # seconds


# Initialize router and storage
router = APIRouter()
storage = get_storage()


# Rate limiting state manager
class RateLimiter:
    def __init__(self):
        self.attempts = defaultdict(list)

    def check(self, client_ip: str) -> None:
        now_ts = datetime.now(timezone.utc).timestamp()
        # Prune old attempts
        self.attempts[client_ip] = [
            t for t in self.attempts[client_ip] if now_ts - t < RATE_LIMIT_WINDOW
        ]
        if len(self.attempts[client_ip]) >= UPLOAD_RATE_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {UPLOAD_RATE_LIMIT} uploads per {RATE_LIMIT_WINDOW} seconds.",
            )
        self.attempts[client_ip].append(now_ts)


rate_limiter = RateLimiter()


# Utility Functions
def now_utc() -> str:
    utc = datetime.now(timezone.utc)
    if settings.TIMEZONE:
        tz = pytz.timezone(settings.TIMEZONE)
        return utc.astimezone(tz).isoformat()
    return utc.isoformat()


def format_timestamp(ts: str) -> str:
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


def sanitize_json(data: dict) -> dict:
    allowed_keys = {"ArtifactName", "Results", "_meta", "CreatedAt"}
    return {k: v for k, v in data.items() if k in allowed_keys}


def sanitize_filename(filename: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-\.]", "_", filename.strip())[:MAX_FILENAME_LENGTH]


def fallback_artifact_name(name: Optional[str], fallback_filename: str) -> str:
    if not name or name.strip() in [".", ""]:
        return fallback_filename
    return re.sub(r"[^a-zA-Z0-9_\-\.]", "_", name.strip()) or fallback_filename


# Routes
@router.get("/")
def root():
    return {"message": "Trivy UI backend is alive"}


@router.get("/reports")
async def list_reports(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    artifact: Optional[str] = Query(None),
    min_critical: int = Query(default=0, ge=0),
    min_high: int = Query(default=0, ge=0),
    min_medium: int = Query(default=0, ge=0),
    min_low: int = Query(default=0, ge=0),
):
    """List vulnerability reports with filtering and pagination."""
    try:
        # Get all reports from storage
        logger.info("Attempting to retrieve reports from storage...")
        reports_data = await storage.list_reports()
        logger.info(f"Retrieved {len(reports_data) if reports_data else 0} reports from storage")

        # Handle empty reports case
        if not reports_data:
            logger.warning("No reports found in storage")
            return {
                "_debug": {
                    "total_reports": 0,
                    "backend_working": True,
                    "timestamp": now_utc()
                },
                "reports": []
            }

        filtered_reports = []
        
        for data in reports_data:
            if not isinstance(data, dict):
                logger.warning(f"Invalid report data format: {type(data)}")
                continue

            # Ensure _meta.id exists
            meta = data.get("_meta", {})
            if not meta.get("id"):
                logger.warning(f"Report missing _meta.id: {data.get('ArtifactName', 'unknown')}")
                # Try to add a default ID if missing
                if "_meta" not in data:
                    data["_meta"] = {}
                if not data["_meta"].get("id"):
                    data["_meta"]["id"] = str(uuid.uuid4())
                    logger.info(f"Added missing ID to report: {data['_meta']['id']}")

            # Apply artifact filter if specified
            if artifact:
                artifact_name = data.get("ArtifactName", "").lower()
                if artifact.lower() not in artifact_name:
                    continue

            filtered_reports.append(data)

        # Sort and return the raw reports data (frontend expects raw format)
        filtered_reports.sort(key=lambda x: x.get("_meta", {}).get("timestamp", ""), reverse=True)
        
        logger.info(f"Returning {len(filtered_reports)} reports to frontend")
        for i, report in enumerate(filtered_reports[:5]):  # Log first 5 reports
            meta = report.get("_meta", {})
            logger.info(f"Report {i+1}: ID={meta.get('id')}, Artifact={report.get('ArtifactName')}")
        
        # Add a special marker in the response for debugging
        response_data = {
            "_debug": {
                "total_reports": len(filtered_reports),
                "backend_working": True,
                "timestamp": now_utc()
            },
            "reports": filtered_reports
        }
        
        return response_data

    except Exception as e:
        logger.error(f"Failed to retrieve reports: {str(e)}")
        return {
            "_debug": {
                "total_reports": 0,
                "backend_working": False,
                "error": str(e),
                "timestamp": now_utc()
            },
            "reports": []
        }


@router.post("/report")
async def upload_report(report: TrivyReport):
    report_id = str(uuid.uuid4())
    artifact_name = fallback_artifact_name(report.ArtifactName, "artifact-from-api")
    report_dict = report.model_dump()
    report_dict.setdefault("_meta", {})
    report_dict["_meta"].update(
        {"timestamp": now_utc(), "id": report_id, "uploaded_at": now_utc()}
    )
    report_dict["ArtifactName"] = artifact_name
    await storage.save_report(report_id, report_dict)
    return {"id": report_id, "artifact": artifact_name}


@router.post("/upload-report")
async def upload_report_file(request: Request, file: UploadFile = File(...)):
    # Get client IP and apply rate limiting
    client_ip = get_client_ip(request)
    rate_limiter.check(client_ip)

    filename = (file.filename or "").strip().lower()
    if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {', '.join(ALLOWED_EXTENSIONS)} files are accepted",
        )

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max allowed size is {MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB.",
        )
    await file.seek(0)

    try:
        data = json.loads(contents.decode("utf-8", errors="ignore"))
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not valid JSON",
        )

    if (
        not isinstance(data, dict)
        or "Results" not in data
        or not isinstance(data["Results"], list)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded JSON must contain 'Results' field as list",
        )

    sanitized_data = sanitize_json(data)
    try:
        report = TrivyReport(**sanitized_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Trivy report format: {e}",
        )

    report_id = str(uuid.uuid4())
    artifact_name = fallback_artifact_name(
        report.ArtifactName, sanitize_filename(filename)
    )
    sanitized_data.setdefault("_meta", {})
    sanitized_data["_meta"].update(
        {"timestamp": now_utc(), "id": report_id, "uploaded_at": now_utc()}
    )
    sanitized_data["ArtifactName"] = artifact_name
    
    # Add debug logging for upload
    logger.info(f"Saving report with ID: {report_id}, artifact: {artifact_name}")
    await storage.save_report(report_id, sanitized_data)
    logger.info(f"Successfully saved report {report_id}")
    
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )

    report = TrivyReport(**report_data)
    severity_filter = [s.upper() for s in severity] if severity else None
    pkg_filter = pkgName.lower() if pkgName else None
    vuln_filter = vulnId.lower() if vulnId else None

    severity_count: Dict[str, int] = defaultdict(int)
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
            report_data.get("_meta", {}).get("uploaded_at")
            or report_data.get("_meta", {}).get("timestamp", "")
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


@router.delete("/reports")
async def delete_reports(request: Request, body: dict = Body(...)):
    report_ids: List[str] = body.get("report_ids", [])
    if not isinstance(report_ids, list) or not all(
        isinstance(rid, str) for rid in report_ids
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid report_ids payload"
        )

    deleted = 0
    for report_id in report_ids:
        try:
            await storage.delete_report(report_id)
            deleted += 1
        except FileNotFoundError:
            continue

    return {"deleted": deleted}


@router.get("/metrics")
async def metrics():
    try:
        total = await storage.count_reports()
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    return {"reports_count": total}


@router.get("/config", summary="Get system configuration")
async def get_config():
    settings = get_settings()
    config_dict = settings.dict()

    return {
        "environment": {
            "env": config_dict["ENV"],
            "debug": config_dict["DEBUG"],
            "timezone": config_dict["TIMEZONE"],
        },
        "api": {
            "version": config_dict["API_V1_STR"],
            "project_name": config_dict["PROJECT_NAME"],
            "cors_origins": config_dict["CORS_ORIGINS"],
        },
        "storage": {
            "backend": config_dict["DB_BACKEND"],
            "database": (
                {
                    "server": config_dict["POSTGRES_SERVER"],
                    "port": config_dict["POSTGRES_PORT"],
                    "user": config_dict["POSTGRES_USER"],
                    "database": config_dict["POSTGRES_DB"],
                }
                if config_dict["DB_BACKEND"] == "postgres"
                else None
            ),
        },
    }


@router.get("/test-storage")
async def test_storage():
    """Test endpoint to debug storage issues"""
    try:
        test_data = {
            "ArtifactName": "test-artifact",
            "Results": [],
            "SchemaVersion": 2
        }
        
        # Try to save a test report
        await storage.save_report("test-debug-123", test_data)
        
        # Try to list reports
        reports = await storage.list_reports()
        
        return {
            "status": "success",
            "message": "Storage test passed",
            "reports_count": len(reports),
            "sample_reports": reports[:3] if reports else "No reports found yet"
        }
    except Exception as e:
        import traceback
        return {
            "status": "error", 
            "error": str(e),
            "traceback": traceback.format_exc()
        }
