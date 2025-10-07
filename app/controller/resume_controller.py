from fastapi import APIRouter, UploadFile, Depends
from sqlalchemy.orm import Session
from app.schemas.resume_schema import JDRequest
from app.service.resume_service import set_job_description, process_resume
from app.configs.database import get_db

router = APIRouter()

@router.post("/set_jd/")
async def set_jd(request: JDRequest):
    """
    Set the job description for resume screening
    """
    return set_job_description(request.job_description)

@router.post("/upload_resume/")
async def upload_resume(file: UploadFile, db: Session = Depends(get_db)):
    """
    Upload a candidate's resume and process it.
    Delegates all logic to the service layer.
    """
    return process_resume(file.file, file.filename, db)
