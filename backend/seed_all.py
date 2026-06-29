import re
import requests
import time
from sqlalchemy.orm import Session
from backend.db import SessionLocal, Verse, init_db
from backend.search import embed_text, normalize_arabic

# Strip any HTML tags from translation text
_HTML_TAG = re.compile(r'<[^>]+>')
_FOOTNOTE_ELEM = re.compile(r'<sup[^>]*>.*?</sup>', re.IGNORECASE | re.DOTALL)

def clean_translation(text: str) -> str:
    if not text:
        return ""
    t = _FOOTNOTE_ELEM.sub('', text)
    t = _HTML_TAG.sub('', t)
    return t.strip()

def to_arabic_number(n: int) -> str:
    """Converts Western digits to Arabic-Indic digits for the end-of-ayah marker."""
    western_to_arabic = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
    return str(n).translate(western_to_arabic)

def seed_all_surahs():
    print("Initializing database schema...")
    init_db()
    
    db: Session = SessionLocal()
    
    # Check if already seeded (we want a clean slate, so we'll check if it has a lot of verses)
    existing_count = db.query(Verse).count()
    if existing_count > 100:
        print(f"Database already has {existing_count} verses. Skipping seeding.")
        db.close()
        return

    # If there are only a few (like the Al-Fatihah pilot), wipe them to prevent duplicates
    if existing_count > 0:
        print("Wiping existing pilot verses for a clean full seed...")
        db.query(Verse).delete()
        db.commit()

    print("Fetching Surah list from GitHub...")
    surah_list_url = "https://raw.githubusercontent.com/penggguna/QuranJSON/master/quran.json"
    res = requests.get(surah_list_url)
    res.raise_for_status()
    surahs = res.json()
    
    total_verses_seeded = 0
    start_time = time.time()
    
    for surah_info in surahs:
        surah_num = surah_info["number_of_surah"]
        surah_name = surah_info["name"]
        surah_name_ar = surah_info["name_translations"]["ar"]
        
        print(f"Fetching Surah {surah_num}: {surah_name} ({surah_name_ar})...")
        surah_url = f"https://raw.githubusercontent.com/penggguna/QuranJSON/master/surah/{surah_num}.json"
        
        try:
            surah_res = requests.get(surah_url)
            surah_res.raise_for_status()
            surah_data = surah_res.json()
        except Exception as e:
            print(f"Error fetching Surah {surah_num}: {e}. Retrying in 2 seconds...")
            time.sleep(2)
            surah_res = requests.get(surah_url)
            surah_res.raise_for_status()
            surah_data = surah_res.json()

        verses_to_insert = []
        for verse_data in surah_data["verses"]:
            ayah_num = verse_data["number"]
            arabic_text = verse_data["text"].strip()
            raw_translation = verse_data["translation_id"]
            translation = clean_translation(raw_translation)
            
            # Generate normalized text (strips harakat, converts superscript alef to normal alef)
            normalized = normalize_arabic(arabic_text)
            
            # Generate embedding vector
            embedding = embed_text(normalized)
            
            # Generate Uthmani text with the end-of-ayah symbol and Arabic numeral
            arabic_num = to_arabic_number(ayah_num)
            tajweed_html = (
                f'<span class="tj-default">{arabic_text}</span>'
                f'<span class="waqf waqf-ayah" data-waqf="ayah" title="Akhir ayat {ayah_num}">۝{arabic_num}</span>'
            )
            
            db_verse = Verse(
                surah_number=surah_num,
                ayah_number=ayah_num,
                surah_name=surah_name,
                surah_name_ar=surah_name_ar,
                arabic_text=arabic_text,
                normalized_text=normalized,
                tajweed_html=tajweed_html,
                translation=translation,
                embedding=embedding
            )
            verses_to_insert.append(db_verse)
            
        # Bulk insert surah verses
        db.bulk_save_objects(verses_to_insert)
        db.commit()
        
        total_verses_seeded += len(verses_to_insert)
        print(f"  Successfully seeded {len(verses_to_insert)} verses. Total: {total_verses_seeded}/6236")
        
        # Polite throttling
        time.sleep(0.05)
        
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"\nSuccessfully seeded all {total_verses_seeded} verses of the Quran in {elapsed:.1f} seconds!")
    db.close()

if __name__ == "__main__":
    seed_all_surahs()
