# File: backend/app/api/routes.py

import logging
import json
import uuid
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import List, Optional

import pytz
from fastapi import (
    APIRouter,
    HTTPException,
    File,
    UploadFile,
    Query,
    Request,
    status,
    Body,
)

from app.schemas.report import TrivyReport
from app.storage.factory import get_storage
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
storage = get_storage()

MAX_UPLOAD_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = (".json", ".spdx.json", ".cdx.json", ".tar")
MAX_FILENAME_LENGTH = 100
UPLOAD_RATE_LIMIT = 10
_upload_attempts: dict = {}


def now_utc() -> str:
    utc = datetime.utcnow().replace(tzinfo=timezone.utc)
    if settings.TIMEZONE:
        tz = pytz.timezone(settings.TIMEZONE)
        return utc.astimezone(tz).isoformat()
    return utc.isoformat()


def format_timestamp(ts: str) -> str:
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        try:
            dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")
        except Exception:
            return ts
    try:
        if settings.TIMEZONE:
            dt = dt.astimezone(pytz.timezone(settings.TIMEZONE))
        else:
            dt = dt.astimezone()
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return dt.isoformat()


def get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def fallback_artifact_name(name: Optional[str], fallback_filename: str) -> str:
    if not name or name.strip() in [".", ""]:
        return fallback_filename
    return re.sub(r"[^a-zA-Z0-9_\-\.]", "_", name.strip()) or fallback_filename


def sanitize_json(data: dict) -> dict:
    allowed_keys = {"ArtifactName", "Results", "_meta", "CreatedAt"}
    return {k: v for k, v in data.items() if k in allowed_keys}


def sanitize_filename(filename: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-\.]", "_", filename.strip())[:MAX_FILENAME_LENGTH]


def rate_limit_check(client_ip: str):
    now = datetime.utcnow().timestamp()
    _upload_attempts.setdefault(client_ip, [])
    _upload_attempts[client_ip] = [
        t for t in _upload_attempts[client_ip] if now - t < 60
    ]
    if len(_upload_attempts[client_ip]) >= UPLOAD_RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many uploads, slow down.")
    _upload_attempts[client_ip].append(now)


@router.post("/report")
async def upload_report(report: TrivyReport):
    report_id = str(uuid.uuid4())
    artifact_name = fallback_artifact_name(report.ArtifactName, "artifact-from-api")
    report_dict = report.dict()
    report_dict.setdefault("_meta", {})["timestamp"] = now_utc()
    report_dict["_meta"]["id"] = report_id
    report_dict["ArtifactName"] = artifact_name
    await storage.save_report(report_id, report_dict)
    return {"id": report_id, "artifact": artifact_name}


@router.post("/upload-report")
async def upload_report_file(request: Request, file: UploadFile = File(...)):
    client_ip = get_client_ip(request)
    rate_limit_check(client_ip)
    filename = sanitize_filename(file.filename or "")

    if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Only {', '.join(ALLOWED_EXTENSIONS)} files are accepted",
        )

    if len(filename) > MAX_FILENAME_LENGTH:
        raise HTTPException(status_code=413, detail="Filename too long.")

    contents = await file.read()
    try:
        data = json.loads(contents.decode("utf-8", errors="ignore"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Uploaded file is not valid JSON")

    if not isinstance(data, dict) or "Results" not in data or not isinstance(
        data["Results"], list
    ):
        raise HTTPException(
            status_code=400, detail="Uploaded JSON must contain 'Results' field as list"
        )

    sanitized_data = sanitize_json(data)
    report = TrivyReport(**sanitized_data)
    report_id = str(uuid.uuid4())
    artifact_name = fallback_artifact_name(report.ArtifactName, filename)
    sanitized_data.setdefault("_meta", {})["timestamp"] = now_utc()
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
            return (
                v.VulnerabilityID.upper().startswith("CVE-")
                and (not severity_filter or v.Severity.upper() in severity_filter)
                and (not pkg_filter or pkg_filter in v.PkgName.lower())
                and (not vuln_filter or vuln_filter in v.VulnerabilityID.lower())
            )

        filtered_vulns = [v for v in vulns if matches_filters(v)]
        filtered_results.append({"Target": result.Target, "Vulnerabilities": filtered_vulns})

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

    return {"artifact": report.ArtifactName, "summary": summary, "results": filtered_results}


@router.get("/reports")
async def list_reports(skip: int = 0, limit: int = 20):
    reports_data = await storage.list_reports()
    reports = []

    for data in reports_data:
        try:
            report = TrivyReport(**data)
            ts = data.get("_meta", {}).get("timestamp", "")
            rid = data.get("_meta", {}).get("id")
            if not rid:
                continue

            sev = defaultdict(int)
            for result in report.Results:
                for vuln in result.Vulnerabilities or []:
                    sev[vuln.Severity.upper()] += 1

            reports.append(
                {
                    "id": rid,
                    "artifact": report.ArtifactName,
                    "timestamp": format_timestamp(ts),
                    "critical": sev["CRITICAL"],
                    "high": sev["HIGH"],
                    "medium": sev["MEDIUM"],
                    "low": sev["LOW"],
                }
            )
        except Exception as e:
            logger.warning(f"Invalid report skipped: {e}")

    reports.sort(key=lambda r: r["timestamp"], reverse=True)
    return {
        "total": len(reports),
        "skip": skip,
        "limit": limit,
        "results": reports[skip : skip + limit],
    }


@router.delete("/reports")
async def delete_reports(request: Request, body: dict = Body(...)):
    ids: List[str] = body.get("report_ids", [])
    if not isinstance(ids, list) or not all(isinstance(rid, str) for rid in ids):
        raise HTTPException(status_code=400, detail="Invalid report_ids payload")
    deleted = 0
    for rid in ids:
        try:
            await storage.delete_report(rid)
            deleted += 1
        except FileNotFoundError:
            continue
    return {"deleted": deleted}


@router.get("/metrics")
async def metrics():
    try:
        total = await storage.count_reports()
        return {"reports_count": total}
    except Exception as e:
        return {"error": str(e)}
