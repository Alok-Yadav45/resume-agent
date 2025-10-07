import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from .config import settings
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}/{settings.DB_NAME}"

def create_db_engine_with_retry(retries=5, delay=5):
    for i in range(retries):
        try:
            engine = create_engine(SQLALCHEMY_DATABASE_URL)
            connection = engine.connect()
            connection.close()
            print(" Database connection successful.")
            return engine
        except OperationalError as e:
            print(f" Database connection failed. Retrying in {delay} seconds... ({i+1}/{retries})")
            time.sleep(delay)
            if i == retries - 1:
                raise e

engine = create_db_engine_with_retry()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
