from fastapi import APIRouter, HTTPException, File, UploadFile, Query
from app.schemas.report import TrivyReport
from collections import defaultdict
from pathlib import Path
from datetime import datetime
import uuid
import json
from typing import List, Optional

router = APIRouter()

# Directory to store report files
REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


# === Helper Functions ===


def fallback_artifact_name(name: Optional[str], fallback_filename: str) -> str:
    if not name or name.strip() in [".", ""]:
        return fallback_filename  # Use full filename with extension
    return name.strip()


def save_report_to_disk(
    report_id: str, report: TrivyReport, source_filename: Optional[str] = None
):
    file_path = REPORTS_DIR / f"{report_id}.json"
    data = report.dict()
    data["ArtifactName"] = fallback_artifact_name(
        data.get("ArtifactName"), source_filename or "artifact"
    )
    data["_meta"] = {"timestamp": datetime.utcnow().isoformat()}
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_report_from_disk(report_id: str) -> TrivyReport:
    file_path = REPORTS_DIR / f"{report_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    with open(file_path, encoding="utf-8") as f:
        return TrivyReport(**json.load(f))


# === Routes ===


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
    vuln_filter = vulnId.upper() if vulnId else None

    severity_count = defaultdict(int)
    filtered_results = []

    for result in report.Results:
        vulns = result.Vulnerabilities or []

        for vuln in vulns:
            severity_count[vuln.Severity.upper()] += 1

        def matches_filters(v):
            if severity_filter and v.Severity.upper() not in severity_filter:
                return False
            if pkg_filter and pkg_filter not in v.PkgName.lower():
                return False
            if vuln_filter and vuln_filter != v.VulnerabilityID.upper():
                return False
            return True

        filtered_vulns = [v for v in vulns if matches_filters(v)]

        filtered_results.append(
            {"Target": result.Target, "Vulnerabilities": filtered_vulns}
        )

    summary = {
        "critical": severity_count.get("CRITICAL", 0),
        "high": severity_count.get("HIGH", 0),
        "medium": severity_count.get("MEDIUM", 0),
        "low": severity_count.get("LOW", 0),
        "unknown": severity_count.get("UNKNOWN", 0),
        "total": sum(severity_count.values()),
    }

    return {
        "artifact": report.ArtifactName,
        "results": filtered_results,
        "summary": summary,
    }


@router.get("/report/{report_id}/summary")
def get_report_summary(report_id: str):
    report = load_report_from_disk(report_id)
    severity_count = defaultdict(int)

    for result in report.Results:
        for vuln in result.Vulnerabilities or []:
            severity = vuln.Severity.upper()
            severity_count[severity] += 1

    return {
        "artifact": report.ArtifactName,
        "total_vulnerabilities": sum(severity_count.values()),
        "critical": severity_count.get("CRITICAL", 0),
        "high": severity_count.get("HIGH", 0),
        "medium": severity_count.get("MEDIUM", 0),
        "low": severity_count.get("LOW", 0),
        "unknown": severity_count.get("UNKNOWN", 0),
    }


@router.post("/upload-report")
async def upload_report_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only .json files are accepted")

    contents = await file.read()

    try:
        data = json.loads(contents)
        data["ArtifactName"] = fallback_artifact_name(
            data.get("ArtifactName"), file.filename
        )
        report = TrivyReport(**data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Trivy report: {e}")

    report_id = str(uuid.uuid4())
    save_report_to_disk(report_id, report, source_filename=file.filename)
    return {"id": report_id, "artifact": report.ArtifactName}


@router.get("/reports")
def list_reports(
    skip: int = 0,
    limit: int = 20,
    artifact: Optional[str] = Query(None, description="Filter by artifact name"),
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
                meta = data.get("_meta", {})

                severity_count = defaultdict(int)
                for result in report.Results:
                    for vuln in result.Vulnerabilities or []:
                        severity = vuln.Severity.upper()
                        severity_count[severity] += 1

                report_summary = {
                    "id": file_path.stem,
                    "artifact": report.ArtifactName,
                    "timestamp": meta.get("timestamp", ""),
                    "critical": severity_count.get("CRITICAL", 0),
                    "high": severity_count.get("HIGH", 0),
                    "medium": severity_count.get("MEDIUM", 0),
                    "low": severity_count.get("LOW", 0),
                }

                reports_with_meta.append(report_summary)
        except Exception as e:
            print(f"Skipping invalid report file {file_path.name}: {e}")
            continue

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

    reports_sorted = sorted(
        filtered, key=lambda r: r.get("timestamp", ""), reverse=True
    )

    paginated = reports_sorted[skip : skip + limit]

    return {
        "total": len(reports_sorted),
        "skip": skip,
        "limit": limit,
        "results": paginated,
    }
