from pydantic import BaseModel
from typing import List, Optional

class CandidateCreate(BaseModel):
    name: str
    contact: str
    match_percentage: float
    skills: List[str]
    reason: str

class CandidateResponse(CandidateCreate):
    id: int

    class Config:
        from_attributes = True

class JDRequest(BaseModel):
    job_description: str
