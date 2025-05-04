from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class Vulnerability(BaseModel):
    VulnerabilityID: str
    PkgName: str
    Severity: str


class Result(BaseModel):
    Target: str
    Vulnerabilities: Optional[List[Vulnerability]] = []


class TrivyReport(BaseModel):
    ArtifactName: str
    Results: List[Result]


# Optional: if you use this in GET responses
class TrivyReportOut(BaseModel):
    id: str
    artifact: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
