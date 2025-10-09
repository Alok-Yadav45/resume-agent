import json
from sqlalchemy.orm import Session
from app.helper.file_extractor import extract_text_from_pdf, extract_text_from_docx
from app.helper.llm_helper import analyze_resume
from app.models.candidate_model import Candidate

def process_resume(file, filename: str, db: Session, job_description: str):
    """
    Process resume and JD together.
    """
    if not job_description.strip():
        return {"error": "Job description is required!"}

    file_bytes = file.read()

    if filename.lower().endswith(".pdf"):
        resume_text = extract_text_from_pdf(file_bytes)
    elif filename.lower().endswith(".docx"):
        resume_text = extract_text_from_docx(file_bytes)
    else:
        resume_text = file_bytes.decode("utf-8", errors="ignore")

    result = analyze_resume(job_description, resume_text)

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
