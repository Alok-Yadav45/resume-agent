import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

google_api_key = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2,
    google_api_key=google_api_key
)

def analyze_resume(job_description: str, resume_text: str) -> dict:
    prompt = f"""
    You are a recruitment AI.
    Compare the following resume with the given Job Description.
    Job Description:
    {job_description}
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
        return json.loads(response_text)
    except json.JSONDecodeError:
        text = response_text[response_text.find("{"): response_text.rfind("}") + 1]
        return json.loads(text)
    

def rag_invoke(instruction: str, context: str) -> str:
    """Call the LLM with the additional retrieved context provided by the vector DB.
    Returns the LLM text response.
    """
    prompt = f"CONTEXT:\n{context}\n\nINSTRUCTION:\n{instruction}\n\nRespond concisely."
    response = llm.invoke(prompt)
    return getattr(response, "content", str(response)).strip()