import json
from sqlalchemy.orm import Session
from app.helper.file_extractor import extract_text_from_pdf, extract_text_from_docx
from app.helper.llm_helper import analyze_resume
from app.models.candidate_model import Candidate

job_description_text = ""

def set_job_description(jd_text: str):
    """
    Set the job description for later comparison.
    """
    global job_description_text
    job_description_text = jd_text.strip()
    return {"message": "Job description set successfully"}

def process_resume(file, filename: str, db: Session):
    """
    Process the uploaded resume:
    1. Extract text based on file type.
    2. Analyze the resume against the stored job description using LLM.
    3. Save candidate in DB if fit.
    4. Return analysis result.
    """
    global job_description_text

    if not job_description_text:
        return {"error": "Please set a job description first!"}

    file_bytes = file.read()

    if filename.lower().endswith(".pdf"):
        resume_text = extract_text_from_pdf(file_bytes)
    elif filename.lower().endswith(".docx"):
        resume_text = extract_text_from_docx(file_bytes)
    else:
        resume_text = file_bytes.decode("utf-8", errors="ignore")

    result = analyze_resume(job_description_text, resume_text)

    if result.get("fit", "").lower() == "yes":
        candidate = Candidate(
            name=result.get("name", "unknown"),
            contact=result.get("contact", "unknown"),
            match_percentage=float(result.get("match_percentage", 0)),
            skills=json.dumps(result.get("skills", [])),
            reason=result.get("reason", "")
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        return candidate

    return result
