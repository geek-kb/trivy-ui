from typing import List, Optional
from pydantic import BaseModel


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
