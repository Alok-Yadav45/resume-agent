from fastapi import APIRouter, UploadFile, Form, Depends
from sqlalchemy.orm import Session
from app.service.resume_service import process_resume
from app.configs.database import get_db

router = APIRouter()

@router.post("/analyze_resume/")
async def analyze_resume(
    job_description: str = Form(...),
    file: UploadFile = None,
    db: Session = Depends(get_db)
):
    """
    Upload a resume and provide a job description together in one request.
    The API:
    1. Reads job description and resume.
    2. Extracts text from the resume (PDF/DOCX/TXT).
    3. Uses LLM to compare against the JD.
    4. Stores candidate if fit.
    5. Returns analysis result.
    """
    return process_resume(file.file, file.filename, db, job_description)
