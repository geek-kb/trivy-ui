# backend/app/api/routes.py

import logging
import json
import uuid
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, File, UploadFile, Query, Request

from app.schemas.report import TrivyReport

# --- Setup ---
logger = logging.getLogger(__name__)
router = APIRouter()

# --- Constants ---
REPORTS_DIR = Path(__file__).parent.parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = (".json", ".spdx.json", ".cdx.json", ".tar")
MAX_FILENAME_LENGTH = 100  # Reasonable filename limit
UPLOAD_RATE_LIMIT = 10  # Max uploads per minute (soft basic in-memory)

# --- Internal memory (simple rate limiter for uploads) ---
_upload_attempts: dict = {}

# --- Helper Functions ---


def get_client_ip(request) -> str:
    """
    Safely retrieve the client's IP address, or 'unknown' if unavailable.
    """
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def fallback_artifact_name(name: Optional[str], fallback_filename: str) -> str:
    if not name or name.strip() in [".", ""]:
        return fallback_filename
    sanitized = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", name.strip())
    return sanitized or fallback_filename


def sanitize_filename(filename: str) -> str:
    sanitized = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", filename.strip())
    return sanitized[:MAX_FILENAME_LENGTH]


def extract_timestamp(data: dict) -> str:
    meta_timestamp = data.get("_meta", {}).get("timestamp")
    created_at = data.get("CreatedAt")
    if meta_timestamp:
        return meta_timestamp
    if created_at:
        return created_at
    return datetime.utcnow().isoformat()


def is_malicious_json(content: str) -> bool:
    # Basic check for <script> or similar injections
    dangerous_patterns = [
        r"<script.*?>",
        r"javascript:",
        r"onerror=",
        r"onload=",
        r"alert\(",
        r"eval\(",
    ]
    lowered = content.lower()
    return any(re.search(p, lowered) for p in dangerous_patterns)


def sanitize_json(data: dict) -> dict:
    # Only keep fields we know
    allowed_keys = {"ArtifactName", "Results", "_meta", "CreatedAt"}
    return {k: v for k, v in data.items() if k in allowed_keys}


def rate_limit_check(client_ip: str):
    now = datetime.utcnow().timestamp()
    _upload_attempts.setdefault(client_ip, [])
    _upload_attempts[client_ip] = [
        t for t in _upload_attempts[client_ip] if now - t < 60
    ]
    if len(_upload_attempts[client_ip]) >= UPLOAD_RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many uploads, slow down.")
    _upload_attempts[client_ip].append(now)


def save_report_to_disk(
    report_id: str, report: TrivyReport, source_filename: Optional[str] = None
):
    file_path = REPORTS_DIR / f"{sanitize_filename(report_id)}.json"
    data = report.dict()

    data["ArtifactName"] = fallback_artifact_name(
        data.get("ArtifactName"), source_filename or "artifact"
    )

    if "_meta" not in data:
        data["_meta"] = {}
    if not data["_meta"].get("timestamp"):
        data["_meta"]["timestamp"] = datetime.utcnow().isoformat()

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_report_from_disk(report_id: str) -> TrivyReport:
    file_path = REPORTS_DIR / f"{sanitize_filename(report_id)}.json"
    if not file_path.exists():
        logger.error(f"Report file not found: {file_path}")
        raise HTTPException(status_code=404, detail="Report not found")
    with open(file_path, encoding="utf-8") as f:
        return TrivyReport(**json.load(f))


# --- Routes ---


@router.get("/")
def root():
    return {"message": "Trivy UI backend is alive"}


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.post("/report")
def upload_report(report: TrivyReport):
    report_id = str(uuid.uuid4())
    report.ArtifactName = fallback_artifact_name(
        report.ArtifactName, "artifact-from-api"
    )
    save_report_to_disk(report_id, report, source_filename=report.ArtifactName)
    return {"id": report_id, "artifact": report.ArtifactName}


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

    if len(filename) > MAX_FILENAME_LENGTH:
        raise HTTPException(status_code=400, detail="Filename too long")

    contents = await file.read()

    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413, detail="File too large. Max allowed size is 5MB."
        )

    content_text = contents.decode("utf-8", errors="ignore")

    if is_malicious_json(content_text):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file contains potentially malicious content",
        )

    try:
        data = json.loads(content_text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Uploaded file is not valid JSON")

    if not isinstance(data, dict) or "Results" not in data:
        raise HTTPException(
            status_code=400, detail="Uploaded JSON must contain 'Results' field"
        )

    if not isinstance(data["Results"], list):
        raise HTTPException(status_code=400, detail="'Results' must be a list")

    sanitized_data = sanitize_json(data)

    try:
        report = TrivyReport(**sanitized_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Trivy report format: {e}")

    report_id = str(uuid.uuid4())

    if "_meta" not in sanitized_data:
        sanitized_data["_meta"] = {}
    if not sanitized_data["_meta"].get("timestamp"):
        sanitized_data["_meta"]["timestamp"] = extract_timestamp(sanitized_data)

    save_report_to_disk(report_id, report)

    return {"id": report_id, "artifact": report.ArtifactName or filename}


@router.get("/report/{report_id}")
def get_report(
    report_id: str,
    severity: Optional[List[str]] = Query(None),
    pkgName: Optional[str] = Query(None),
    vulnId: Optional[str] = Query(None),
):
    report = load_report_from_disk(report_id)

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
        "timestamp": report.dict().get("_meta", {}).get("timestamp", ""),
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


@router.get("/report/{report_id}/summary")
def get_report_summary(report_id: str):
    report = load_report_from_disk(report_id)
    severity_count = defaultdict(int)
    timestamp = report.dict().get("_meta", {}).get("timestamp", "")

    for result in report.Results:
        for vuln in result.Vulnerabilities or []:
            severity = vuln.Severity.upper()
            severity_count[severity] += 1

    return {
        "artifact": report.ArtifactName,
        "timestamp": timestamp,
        "total_vulnerabilities": sum(severity_count.values()),
        "critical": severity_count.get("CRITICAL", 0),
        "high": severity_count.get("HIGH", 0),
        "medium": severity_count.get("MEDIUM", 0),
        "low": severity_count.get("LOW", 0),
        "unknown": severity_count.get("UNKNOWN", 0),
    }


@router.get("/reports")
def list_reports(
    skip: int = 0,
    limit: int = 20,
    artifact: Optional[str] = Query(None),
    min_critical: int = 0,
    min_high: int = 0,
    min_medium: int = 0,
    min_low: int = 0,
):
    report_files = REPORTS_DIR.glob("*.json")
    reports_with_meta = []

    for file_path in report_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
                data["ArtifactName"] = fallback_artifact_name(
                    data.get("ArtifactName"), file_path.stem
                )
                report = TrivyReport(**data)
                timestamp = extract_timestamp(data)

                severity_count = defaultdict(int)
                for result in report.Results:
                    for vuln in result.Vulnerabilities or []:
                        severity = vuln.Severity.upper()
                        severity_count[severity] += 1

                report_summary = {
                    "id": file_path.stem,
                    "artifact": report.ArtifactName,
                    "timestamp": timestamp,
                    "critical": severity_count.get("CRITICAL", 0),
                    "high": severity_count.get("HIGH", 0),
                    "medium": severity_count.get("MEDIUM", 0),
                    "low": severity_count.get("LOW", 0),
                }

                reports_with_meta.append(report_summary)
        except Exception as e:
            logger.warning(f"Skipping invalid report file {file_path.name}: {e}")

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
        "total": len(sorted_reports),
        "skip": skip,
        "limit": limit,
        "results": paginated,
    }
