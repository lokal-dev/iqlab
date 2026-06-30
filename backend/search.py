import re
import unicodedata
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.db import Verse
from sentence_transformers import SentenceTransformer

# Load the embedding model
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-base"
print(f"Loading embedding model '{EMBEDDING_MODEL_NAME}'...")
embedder = SentenceTransformer(EMBEDDING_MODEL_NAME, device="cpu")
print("Embedding model loaded.")


# ── Arabic text normalization ──────────────────────────────────────
# Whisper typically outputs Arabic WITHOUT harakat (diacritics).
# Our database stores Arabic WITH harakat (Uthmani script).
# We strip harakat from both sides before comparison so they can match.

# Arabic Unicode ranges for diacritics (harakat) to strip (excluding \u0670 superscript alef)
_HARAKAT = re.compile(
    r'[\u064B-\u065F\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]'
)
# Normalize different forms of Arabic letters (e.g. alef variants)
_ALEF = re.compile(r'[أإآٱ]')
_YEH = re.compile(r'[ىئ]')
_WAW = re.compile(r'[ؤ]')
_TA_MARB = re.compile(r'[ة]')


def normalize_arabic(text: str) -> str:
    """
    Strips harakat, normalizes alef/yeh variants, and lowercases.
    Makes Whisper output (bare consonants) comparable to Uthmani DB text.
    """
    # 1. Replace 'ىٰ' (alef maksura + superscript alef) in the middle of a word with normal alef 'ا'
    t = re.sub(r'ى\u0670(?=[\u0600-\u06FF])', 'ا', text)
    # 2. Replace 'ىٰ' at the end of a word with 'ى' (strip the superscript alef)
    t = re.sub(r'ى\u0670', 'ى', t)
    # 3. Replace any other superscript alef (e.g. in مَـٰلِكِ) with 'ا'
    t = t.replace('\u0670', 'ا')
    # 4. Remove tatweel (cosmetic letter stretching)
    t = t.replace('\u0640', '')
    
    # Strip other diacritics
    t = _HARAKAT.sub('', t)
    t = _ALEF.sub('ا', t)
    t = _YEH.sub('ي', t)
    t = _WAW.sub('و', t)
    t = _TA_MARB.sub('ه', t)
    # Remove non-Arabic characters (punctuation, latin, numbers)
    t = re.sub(r'[^\u0600-\u06FF\s]', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def embed_text(text: str) -> list[float]:
    """Generates embedding vector for the given text."""
    return embedder.encode(text).tolist()


def search_verses(db: Session, raw_text: str, top_k: int = 3):
    """
    Hybrid search: vector similarity + trigram (pg_trgm) similarity.
    Both comparisons use harakat-stripped text for fair matching against
    Whisper's diacritic-free output.

    Final score = 0.5 * vector_score + 0.5 * trgm_score
    """
    if not raw_text:
        return []

    # Normalize both query and DB text for comparison
    query_normalized = normalize_arabic(raw_text)
    print(f"[search] raw transcript: {raw_text!r}")
    print(f"[search] normalized query: {query_normalized!r}")

    if not query_normalized:
        return []

    # ── 1. Vector similarity search ─────────────────────────────
    # E5 models require a "query: " prefix for the query text
    query_embedding = embed_text("query: " + query_normalized)

    vector_results = db.query(
        Verse,
        Verse.embedding.cosine_distance(query_embedding).label("vec_dist")
    ).order_by(
        Verse.embedding.cosine_distance(query_embedding)
    ).limit(top_k * 3).all()  # fetch wider pool for re-ranking

    # ── 2. Trigram similarity search ─────────────────────────────
    # Use pg_trgm similarity() on the pre-normalized normalized_text column.
    trgm_sql = text("""
        SELECT id,
               similarity(normalized_text, :query) AS trgm_score
        FROM verses
        ORDER BY trgm_score DESC
        LIMIT :limit
    """)
    trgm_rows = db.execute(trgm_sql, {"query": query_normalized, "limit": top_k * 3}).fetchall()
    trgm_by_id = {row.id: float(row.trgm_score) for row in trgm_rows}

    # ── 3. Merge and re-rank ──────────────────────────────────────
    verse_scores: dict[int, dict] = {}

    for verse, vec_dist in vector_results:
        vec_score = max(0.0, 1.0 - float(vec_dist))  # convert distance → similarity
        trgm_score = trgm_by_id.get(verse.id, 0.0)
        
        # If there is very little lexical overlap (trigram < 10%), penalize the semantic score.
        # This prevents semantically close but lexically unrelated verses (e.g. other Islamic phrases)
        # from showing up with high confidence.
        trgm_threshold = 0.10
        penalty = min(1.0, trgm_score / trgm_threshold)
        effective_vec_score = vec_score * penalty
        
        # Blend scores: weight trigram (lexical) higher for precise matching
        combined = 0.3 * effective_vec_score + 0.7 * trgm_score
        
        verse_scores[verse.id] = {
            "verse": verse,
            "combined": combined,
        }
        print(f"  [{verse.surah_number}:{verse.ayah_number}] vec={vec_score:.3f} (eff={effective_vec_score:.3f}) trgm={trgm_score:.3f} combined={combined:.3f}")

    # Sort by combined score descending
    ranked = sorted(verse_scores.values(), key=lambda x: x["combined"], reverse=True)[:top_k]

    # Return list of (verse, confidence_score)
    return [(r["verse"], r["combined"]) for r in ranked]
