from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

# Initialize FastAPI app with metadata for automatic docs
app = FastAPI(
    title="Trivy UI Backend",
    description="API for managing Trivy UI scan results and operations",
    version="0.1.0",
)


# Sample data model for a scan result
class ScanResult(BaseModel):
    id: int
    company_name: str
    vulnerabilities: List[str]


# In-memory store for demonstration (replace with database later)
scan_results = [
    ScanResult(
        id=1, company_name="Example Inc.", vulnerabilities=["CVE-1234", "CVE-5678"]
    ),
    ScanResult(id=2, company_name="Another Co.", vulnerabilities=["CVE-9012"]),
]


@app.get("/")
async def read_root():
    """
    Root endpoint returning a welcome message.
    """
    return {"message": "Welcome to Trivy UI FastAPI Backend"}


@app.get("/scans", response_model=List[ScanResult])
async def get_scan_results():
    """
    Retrieve all scan results.
    """
    return scan_results


@app.get("/scans/{scan_id}", response_model=ScanResult)
async def get_scan_result(scan_id: int):
    """
    Retrieve a single scan result by its ID.
    """
    result = next((scan for scan in scan_results if scan.id == scan_id), None)
    if not result:
        raise HTTPException(status_code=404, detail="Scan result not found")
    return result


@app.post("/scans", status_code=201, response_model=ScanResult)
async def create_scan_result(scan: ScanResult):
    """
    Create a new scan result.
    """
    # In a real application, you would persist this data (e.g., in a database).
    scan_results.append(scan)
    return scan
