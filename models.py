from sqlalchemy import Column, Integer, String, Float, Text
from database import Base

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    contact = Column(String(255))
    match_percentage = Column(Float)
    skills = Column(Text)   
    reason = Column(Text)
