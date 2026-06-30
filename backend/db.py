import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from pgvector.sqlalchemy import Vector

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/iqlab"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Verse(Base):
    __tablename__ = "verses"

    id = Column(Integer, primary_key=True, index=True)
    surah_number = Column(Integer, index=True)
    ayah_number = Column(Integer, index=True)
    surah_name = Column(String)
    surah_name_ar = Column(String)
    arabic_text = Column(Text)
    normalized_text = Column(Text)
    tajweed_html = Column(Text)
    translation = Column(Text)
    
    # We will use intfloat/multilingual-e5-base embedding size (768 dimensions)
    embedding = Column(Vector(768))

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
