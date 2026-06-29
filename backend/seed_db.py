import re
import requests
from sqlalchemy.orm import Session
from backend.db import SessionLocal, Verse, init_db
from backend.search import embed_text, normalize_arabic

# Strip footnote elements entirely (tag + content), then any remaining stray tags
_FOOTNOTE_ELEM = re.compile(r'<sup[^>]*>.*?</sup>', re.IGNORECASE | re.DOTALL)
_HTML_TAG = re.compile(r'<[^>]+>')

def clean_translation(text: str) -> str:
    """Remove HTML footnote elements (including content) injected by the quran.com API."""
    t = _FOOTNOTE_ELEM.sub('', text)   # remove <sup ...>1</sup> entirely
    t = _HTML_TAG.sub('', t)           # strip any remaining stray tags
    return t.strip()

def fetch_quran_data():
    print("Fetching Surah Al-Fatihah from quran.com API...")
    # Translation id 33 = Kemenag RI Indonesian
    url = "https://api.quran.com/api/v4/verses/by_chapter/1?language=id&words=true&translations=33&fields=text_uthmani"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    verses = []
    for verse_data in data["verses"]:
        ayah_number = verse_data["verse_number"]
        arabic_text = verse_data["text_uthmani"]
        raw_translation = verse_data["translations"][0]["text"]
        translation = clean_translation(raw_translation)

        print(f"  [{ayah_number}] translation: {translation!r}")

        tajweed_html = (
            f'<span class="tj-default">{arabic_text}</span>'
            f'<span class="waqf waqf-ayah" data-waqf="ayah">۝</span>'
        )

        verses.append({
            "surah_number": 1,
            "ayah_number": ayah_number,
            "surah_name": "Al-Fatihah",
            "surah_name_ar": "الفاتحة",
            "arabic_text": arabic_text,
            "tajweed_html": tajweed_html,
            "translation": translation,
            "search_text": arabic_text,
        })
    return verses

def seed_database():
    print("Initializing database schema...")
    init_db()
    
    db: Session = SessionLocal()
    
    # Check if already seeded
    if db.query(Verse).count() > 0:
        print("Database already seeded. Skipping.")
        return

    verses_data = fetch_quran_data()
    
    print(f"Embedding and inserting {len(verses_data)} verses...")
    for idx, v_data in enumerate(verses_data):
        print(f"Processing 1:{v_data['ayah_number']}...")
        # Embed the NORMALIZED text (no harakat) — same space as Whisper output
        normalized = normalize_arabic(v_data['search_text'])
        print(f"  normalized: {normalized!r}")
        embedding = embed_text(normalized)
        
        db_verse = Verse(
            surah_number=v_data['surah_number'],
            ayah_number=v_data['ayah_number'],
            surah_name=v_data['surah_name'],
            surah_name_ar=v_data['surah_name_ar'],
            arabic_text=v_data['arabic_text'],
            normalized_text=normalized,
            tajweed_html=v_data['tajweed_html'],
            translation=v_data['translation'],
            embedding=embedding
        )
        db.add(db_verse)
        
        # Avoid rate limits on embeddings if using external API (we are using local so it's fine)
        # time.sleep(0.1) 
        
    db.commit()
    print("Database seeding complete!")
    db.close()

if __name__ == "__main__":
    seed_database()
