from fastapi import FastAPI
from app.configs.database import Base, engine
from app.controller.resume_controller import router as resume_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Resume Shortlister Agent")

app.include_router(resume_router, prefix="/api/resume", tags=["Resume Screening"])
