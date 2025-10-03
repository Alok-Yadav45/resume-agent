from fastapi import FastAPI, UploadFile, File
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
import os
import PyPDF2
import docx
import json
import io
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal
from models import Candidate

load_dotenv()

google_api_key = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2,
    google_api_key=google_api_key
)

app = FastAPI()

Base.metadata.create_all(bind=engine)


class JDRequest(BaseModel):
    job_description: str

job_description_text = ""

@app.post("/set_jd/")
async def set_job_description(request: JDRequest):
    global job_description_text
    job_description_text = request.job_description
    return {"message": "Job description set successfully"}

def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = docx.Document(io.BytesIO(file_bytes))
    text = "\n".join([p.text for p in doc.paragraphs])
    return text

@app.post("/upload_resume/")
async def upload_resume(file: UploadFile = File(...)):
    global job_description_text
    if not job_description_text:
        return {"error": "Please set a job description first!"}

    file_bytes = await file.read()

    if file.filename.endswith(".pdf"):
        resume_text = extract_text_from_pdf(file_bytes)
    elif file.filename.endswith(".docx"):
        resume_text = extract_text_from_docx(file_bytes)
    else:
        resume_text = file_bytes.decode("utf-8", errors="ignore")

    prompt = f"""
    You are a recruitment AI.
    Compare the following resume with the given Job Description.
    Job Description:
    {job_description_text}
    Resume:
    {resume_text}
    Task:
    Return ONLY valid JSON in this format:
    {{
      "fit": "Yes" or "No",
      "match_percentage": number (0-100),
      "name": "candidate name or unknown",
      "contact": "contact details or unknown",
      "skills": ["list", "of", "skills"],
      "reason": "short explanation"
    }}
    """

    response = llm.invoke(prompt)

    response_text = getattr(response, "content", str(response)).strip()

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        text = response_text[response_text.find("{"): response_text.rfind("}") + 1]
        result = json.loads(text)

    if result.get("fit") == "Yes":
        db: Session = SessionLocal()
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
        db.close()

    return result

@app.get("/candidates/")
def get_candidates():
    """Fetch all saved candidates from DB"""
    db: Session = SessionLocal()
    candidates = db.query(Candidate).all()
    db.close()
    return [
        {
            "id": c.id,
            "name": c.name,
            "contact": c.contact,
            "match_percentage": c.match_percentage,
            "skills": json.loads(c.skills),
            "reason": c.reason,
        }
        for c in candidates
    ]
