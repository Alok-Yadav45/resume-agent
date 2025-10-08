import json
from sqlalchemy.orm import Session
from app.helper.file_extractor import extract_text_from_pdf, extract_text_from_docx
from app.helper.llm_helper import analyze_resume , rag_invoke
from app.models.candidate_model import Candidate
from app.service.rag_service import index_document, retrieve, build_context_snippet

job_description_text = ""

def set_job_description(jd_text: str):
    
    global job_description_text
    job_description_text = jd_text.strip()
    index_document(doc_id="job_description", text=job_description_text, meta={"type": "job_description"})
    return {"message": "Job description set successfully"}

def process_resume(file, filename: str, db: Session):
    
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

    doc_id = f"resume::{filename}"
    index_document(doc_id=doc_id, text=resume_text, meta={"type": "resume", "filename": filename})

    retrieved_for_jd = retrieve(job_description_text, top_k=5)
    retrieved_for_resume = retrieve(resume_text[:1000], top_k=3)

    combined = (retrieved_for_jd or []) + (retrieved_for_resume or [])
    context = build_context_snippet(combined, max_chars=3000)
    
    instruction = f"Compare the resume below to the job description and return ONLY valid JSON as specified earlier. Resume:\n{resume_text}\n\nYou may use the provided CONTEXT to help your decision."
    rag_response_text = rag_invoke(instruction=instruction, context=context)
   
    try:
        result = json.loads(rag_response_text)
    except Exception:
        result = analyze_resume(job_description_text, resume_text)


    if str(result.get("fit", "")).lower() == "yes":
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

def find_best_candidates(db: Session):
    """Return top 5 candidates sorted by match_percentage."""
    candidates = db.query(Candidate).order_by(Candidate.match_percentage.desc()).limit(5).all()
    result = []
    for c in candidates:
        result.append({
            "id": c.id,
            "name": c.name,
            "contact": c.contact,
            "match_percentage": c.match_percentage,
            "skills": json.loads(c.skills),
            "reason": c.reason
        })
    return result


def retrieve_candidates_from_db(job_description: str, db: Session, top_k: int = 10):
    """
    Retrieve top candidate resumes from DB using vector search + DB filtering.
    Returns Candidate objects along with resume text.
    """
    retrieved = retrieve(job_description, top_k=top_k)
    candidates = []
    for r in retrieved:
        meta = r.get("meta", {})
        if meta.get("type") == "resume":
            candidate = db.query(Candidate).filter(Candidate.name == meta.get("filename")).first()
            if candidate:
                candidates.append({
                    "candidate": candidate,
                    "text": r.get("text"),
                    "score": r.get("score")
                })
    return candidates


def get_ranked_candidates_from_db(job_description: str, candidates: list):
    """
    Use RAG to rank candidate objects based on JD.
    Returns list of JSON-friendly candidate info sorted by match_percentage.
    """
    results = []
    for c in candidates:
        candidate_obj = c["candidate"]
        context = build_context_snippet([{"text": c["text"]}], max_chars=1500)
        instruction = f"Compare the resume to the job description and return valid JSON as before. Resume:\n{c['text']}"
        rag_result_text = rag_invoke(instruction=instruction, context=context)
        try:
            result = json.loads(rag_result_text)
        except Exception:
            result = {
                "fit": "No",
                "match_percentage": 0,
                "name": candidate_obj.name,
                "contact": candidate_obj.contact,
                "skills": json.loads(candidate_obj.skills),
                "reason": "Parsing failed"
            }

        result["name"] = candidate_obj.name
        result["contact"] = candidate_obj.contact
        result["skills"] = json.loads(candidate_obj.skills)
        results.append(result)

    results.sort(key=lambda x: x.get("match_percentage", 0), reverse=True)
    return results