from pydantic import BaseModel
from typing import List, Optional

class VerseResponse(BaseModel):
    id: int
    surahNumber: int
    ayahNumber: int
    surahName: str
    surahNameAr: str
    arabicText: str
    tajweedHtml: str
    translation: str
    confidence: float

class IdentifyResponse(BaseModel):
    results: List[VerseResponse]
