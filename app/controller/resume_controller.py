from fastapi import APIRouter, UploadFile, Depends
from sqlalchemy.orm import Session
from app.schemas.resume_schema import JDRequest
from app.service.resume_service import set_job_description, process_resume, retrieve_candidates_from_db, get_ranked_candidates_from_db, find_best_candidates
from app.configs.database import get_db

router = APIRouter()

@router.post("/set_jd/")
async def set_jd(request: JDRequest):
    return set_job_description(request.job_description)

@router.post("/upload_resume/")
async def upload_resume(file: UploadFile, db: Session = Depends(get_db)):
    return process_resume(file.file, file.filename, db)

@router.get("/top_candidates/")
async def top_candidates(db: Session = Depends(get_db)):
    return {"top_candidates": find_best_candidates(db)}

@router.post("/rag_match/")
async def rag_match(request: JDRequest, db: Session = Depends(get_db)):
    top_candidates_list = retrieve_candidates_from_db(request.job_description, db)
    analysis = get_ranked_candidates_from_db(request.job_description, top_candidates_list)
    return {"result": analysis}