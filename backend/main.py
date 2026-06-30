import os
import shutil
import tempfile
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import subprocess

from backend.db import get_db, init_db
from backend.models import IdentifyResponse, VerseResponse
from backend.asr import transcribe_audio
from backend.search import search_verses, normalize_arabic
from backend.makhraj import (
    analyze_makhraj_ha, analyze_makhraj_ayn, analyze_makhraj_sad, 
    analyze_makhraj_kha, analyze_makhraj_dhal, analyze_makhraj_tha, 
    analyze_makhraj_tah, analyze_makhraj_zha, analyze_makhraj_dad, 
    analyze_makhraj_ghayn, analyze_makhraj_qaf
)

app = FastAPI(title="iq.lab API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to iqlab.lokalatdev.cloud
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

def trim_audio(input_path: str, output_path: str, duration: int = 10):
    """Trims audio to `duration` seconds and converts to 16kHz Mono WAV using ffmpeg."""
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", input_path, "-t", str(duration),
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", output_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        raise Exception("Audio trimming failed.")

@app.post("/api/identify", response_model=IdentifyResponse)
async def identify_audio(audio: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Identifies Quran verse from uploaded audio and performs Makhraj grading.
    1. Trims and converts audio to 16kHz WAV.
    2. Transcribes with word-level timestamps.
    3. Searches with pgvector.
    4. Performs Makhraj analysis on 'ح' in 'الحمد' for Surah 1 Ayah 2.
    """
    if not audio.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio file.")

    # Create temporary files (.wav for the trimmed file to load in scipy)
    fd, temp_input_path = tempfile.mkstemp(suffix=".webm")
    fd_out, temp_trimmed_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    os.close(fd_out)

    try:
        # Save uploaded file
        with open(temp_input_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        # Trim and convert to 16kHz WAV
        trim_audio(temp_input_path, temp_trimmed_path, duration=10)
        
        # Transcribe (returns dict with text and words)
        asr_result = transcribe_audio(temp_trimmed_path)
        transcript = asr_result["text"]
        print(f"Transcript: {transcript}")
        
        if not transcript:
            return IdentifyResponse(results=[])

        # Search DB
        search_results = search_verses(db, transcript, top_k=3)
        
        # Format response
        if not search_results:
            return IdentifyResponse(results=[])

        response_data = []
        for verse, confidence in search_results:
            # Skip results with extremely low confidence (< 5%)
            if confidence < 0.05:
                continue
                
            # ── Generalized Makhraj Grading ──
            html_words = verse.tajweed_html.split()
            for idx, html_word in enumerate(html_words):
                # Check if this word contains any of our supported target letters
                has_ha = 'ح' in html_word
                has_ayn = 'ع' in html_word
                has_sad = 'ص' in html_word
                has_kha = 'خ' in html_word
                has_dhal = 'ذ' in html_word
                has_tha = 'ث' in html_word
                has_tah = 'ط' in html_word
                has_zha = 'ظ' in html_word
                has_dad = 'ض' in html_word
                has_ghayn = 'غ' in html_word
                has_qaf = 'ق' in html_word
                
                if not (has_ha or has_ayn or has_sad or has_kha or has_dhal or 
                        has_tha or has_tah or has_zha or has_dad or has_ghayn or has_qaf):
                    continue
                    
                # Normalize the Uthmani word for comparison
                norm_word = normalize_arabic(html_word)
                if not norm_word:
                    continue
                
                # Find the corresponding word in the ASR word list
                target_asr_word = None
                for w in asr_result["words"]:
                    asr_norm = normalize_arabic(w["word"])
                    # Check for exact match or high overlap/substring match
                    if asr_norm and (asr_norm in norm_word or norm_word in asr_norm or 
                                     (len(asr_norm) > 2 and len(norm_word) > 2 and 
                                      (asr_norm[1:-1] in norm_word or norm_word[1:-1] in asr_norm))):
                        target_asr_word = w
                        break
                        
                if target_asr_word:
                    start_sec = target_asr_word["start"]
                    end_sec = target_asr_word["end"]
                    
                    # 1. Ha (ح)
                    if has_ha:
                        char_idx = norm_word.find('ح')
                        rel_pos = char_idx / len(norm_word) if len(norm_word) > 0 and char_idx != -1 else 0.2
                        makhraj_res = analyze_makhraj_ha(temp_trimmed_path, start_sec, end_sec, relative_pos=rel_pos)
                        if makhraj_res["status"] in ["pass", "fail"]:
                            status = makhraj_res["status"]
                            msg = makhraj_res["message"]
                            highlighted = (
                                f'<span class="makhraj-highlight makhraj-{status}" '
                                f'title="{msg}" '
                                f'data-start="{start_sec}" '
                                f'data-end="{end_sec}">ح</span>'
                            )
                            html_words[idx] = html_word.replace('ح', highlighted, 1)
                            
                    # 2. Ayn (ع)
                    elif has_ayn:
                        char_idx = norm_word.find('ع')
                        rel_pos = char_idx / len(norm_word) if len(norm_word) > 0 and char_idx != -1 else 0.3
                        makhraj_res = analyze_makhraj_ayn(temp_trimmed_path, start_sec, end_sec, relative_pos=rel_pos)
                        if makhraj_res["status"] in ["pass", "fail"]:
                            status = makhraj_res["status"]
                            msg = makhraj_res["message"]
                            highlighted = (
                                f'<span class="makhraj-highlight makhraj-{status}" '
                                f'title="{msg}" '
                                f'data-start="{start_sec}" '
                                f'data-end="{end_sec}">ع</span>'
                            )
                            html_words[idx] = html_word.replace('ع', highlighted, 1)
                            
                    # 3. Sad (ص)
                    elif has_sad:
                        char_idx = norm_word.find('ص')
                        rel_pos = char_idx / len(norm_word) if len(norm_word) > 0 and char_idx != -1 else 0.5
                        makhraj_res = analyze_makhraj_sad(temp_trimmed_path, start_sec, end_sec, relative_pos=rel_pos)
                        if makhraj_res["status"] in ["pass", "fail"]:
                            status = makhraj_res["status"]
                            msg = makhraj_res["message"]
                            highlighted = (
                                f'<span class="makhraj-highlight makhraj-{status}" '
                                f'title="{msg}" '
                                f'data-start="{start_sec}" '
                                f'data-end="{end_sec}">ص</span>'
                            )
                            html_words[idx] = html_word.replace('ص', highlighted, 1)
                            
                    # 4. Kha (خ)
                    elif has_kha:
                        char_idx = norm_word.find('خ')
                        rel_pos = char_idx / len(norm_word) if len(norm_word) > 0 and char_idx != -1 else 0.5
                        makhraj_res = analyze_makhraj_kha(temp_trimmed_path, start_sec, end_sec, relative_pos=rel_pos)
                        if makhraj_res["status"] in ["pass", "fail"]:
                            status = makhraj_res["status"]
                            msg = makhraj_res["message"]
                            highlighted = (
                                f'<span class="makhraj-highlight makhraj-{status}" '
                                f'title="{msg}" '
                                f'data-start="{start_sec}" '
                                f'data-end="{end_sec}">خ</span>'
                            )
                            html_words[idx] = html_word.replace('خ', highlighted, 1)
                            
                    # 5. Dhal (ذ)
                    elif has_dhal:
                        char_idx = norm_word.find('ذ')
                        rel_pos = char_idx / len(norm_word) if len(norm_word) > 0 and char_idx != -1 else 0.5
                        makhraj_res = analyze_makhraj_dhal(temp_trimmed_path, start_sec, end_sec, relative_pos=rel_pos)
                        if makhraj_res["status"] in ["pass", "fail"]:
                            status = makhraj_res["status"]
                            msg = makhraj_res["message"]
                            highlighted = (
                                f'<span class="makhraj-highlight makhraj-{status}" '
                                f'title="{msg}" '
                                f'data-start="{start_sec}" '
                                f'data-end="{end_sec}">ذ</span>'
                            )
                            html_words[idx] = html_word.replace('ذ', highlighted, 1)
                            
                    # 6. Tha (ث)
                    elif has_tha:
                        char_idx = norm_word.find('ث')
                        rel_pos = char_idx / len(norm_word) if len(norm_word) > 0 and char_idx != -1 else 0.5
                        makhraj_res = analyze_makhraj_tha(temp_trimmed_path, start_sec, end_sec, relative_pos=rel_pos)
                        if makhraj_res["status"] in ["pass", "fail"]:
                            status = makhraj_res["status"]
                            msg = makhraj_res["message"]
                            highlighted = (
                                f'<span class="makhraj-highlight makhraj-{status}" '
                                f'title="{msg}" '
                                f'data-start="{start_sec}" '
                                f'data-end="{end_sec}">ث</span>'
                            )
                            html_words[idx] = html_word.replace('ث', highlighted, 1)
                            
                    # 7. Tah (ط)
                    elif has_tah:
                        char_idx = norm_word.find('ط')
                        rel_pos = char_idx / len(norm_word) if len(norm_word) > 0 and char_idx != -1 else 0.5
                        makhraj_res = analyze_makhraj_tah(temp_trimmed_path, start_sec, end_sec, relative_pos=rel_pos)
                        if makhraj_res["status"] in ["pass", "fail"]:
                            status = makhraj_res["status"]
                            msg = makhraj_res["message"]
                            highlighted = (
                                f'<span class="makhraj-highlight makhraj-{status}" '
                                f'title="{msg}" '
                                f'data-start="{start_sec}" '
                                f'data-end="{end_sec}">ط</span>'
                            )
                            html_words[idx] = html_word.replace('ط', highlighted, 1)
                            
                    # 8. Zha (ظ)
                    elif has_zha:
                        char_idx = norm_word.find('ظ')
                        rel_pos = char_idx / len(norm_word) if len(norm_word) > 0 and char_idx != -1 else 0.5
                        makhraj_res = analyze_makhraj_zha(temp_trimmed_path, start_sec, end_sec, relative_pos=rel_pos)
                        if makhraj_res["status"] in ["pass", "fail"]:
                            status = makhraj_res["status"]
                            msg = makhraj_res["message"]
                            highlighted = (
                                f'<span class="makhraj-highlight makhraj-{status}" '
                                f'title="{msg}" '
                                f'data-start="{start_sec}" '
                                f'data-end="{end_sec}">ظ</span>'
                            )
                            html_words[idx] = html_word.replace('ظ', highlighted, 1)
                            
                    # 9. Dad (ض)
                    elif has_dad:
                        char_idx = norm_word.find('ض')
                        rel_pos = char_idx / len(norm_word) if len(norm_word) > 0 and char_idx != -1 else 0.5
                        makhraj_res = analyze_makhraj_dad(temp_trimmed_path, start_sec, end_sec, relative_pos=rel_pos)
                        if makhraj_res["status"] in ["pass", "fail"]:
                            status = makhraj_res["status"]
                            msg = makhraj_res["message"]
                            highlighted = (
                                f'<span class="makhraj-highlight makhraj-{status}" '
                                f'title="{msg}" '
                                f'data-start="{start_sec}" '
                                f'data-end="{end_sec}">ض</span>'
                            )
                            html_words[idx] = html_word.replace('ض', highlighted, 1)
                            
                    # 10. Ghayn (غ)
                    elif has_ghayn:
                        char_idx = norm_word.find('غ')
                        rel_pos = char_idx / len(norm_word) if len(norm_word) > 0 and char_idx != -1 else 0.5
                        makhraj_res = analyze_makhraj_ghayn(temp_trimmed_path, start_sec, end_sec, relative_pos=rel_pos)
                        if makhraj_res["status"] in ["pass", "fail"]:
                            status = makhraj_res["status"]
                            msg = makhraj_res["message"]
                            highlighted = (
                                f'<span class="makhraj-highlight makhraj-{status}" '
                                f'title="{msg}" '
                                f'data-start="{start_sec}" '
                                f'data-end="{end_sec}">غ</span>'
                            )
                            html_words[idx] = html_word.replace('غ', highlighted, 1)
                            
                    # 11. Qaf (ق)
                    elif has_qaf:
                        char_idx = norm_word.find('ق')
                        rel_pos = char_idx / len(norm_word) if len(norm_word) > 0 and char_idx != -1 else 0.5
                        makhraj_res = analyze_makhraj_qaf(temp_trimmed_path, start_sec, end_sec, relative_pos=rel_pos)
                        if makhraj_res["status"] in ["pass", "fail"]:
                            status = makhraj_res["status"]
                            msg = makhraj_res["message"]
                            highlighted = (
                                f'<span class="makhraj-highlight makhraj-{status}" '
                                f'title="{msg}" '
                                f'data-start="{start_sec}" '
                                f'data-end="{end_sec}">ق</span>'
                            )
                            html_words[idx] = html_word.replace('ق', highlighted, 1)
            
            tajweed_html = " ".join(html_words)
            
            response_data.append(VerseResponse(
                id=verse.id,
                surahNumber=verse.surah_number,
                ayahNumber=verse.ayah_number,
                surahName=verse.surah_name,
                surahNameAr=verse.surah_name_ar,
                arabicText=verse.arabic_text,
                tajweedHtml=tajweed_html,  # Returns the highlighted version
                translation=verse.translation,
                confidence=round(confidence, 2)
            ))

        return IdentifyResponse(results=response_data)
        
    except Exception as e:
        print(f"Error processing audio: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
        
    finally:
        # Cleanup
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        if os.path.exists(temp_trimmed_path):
            os.remove(temp_trimmed_path)

@app.get("/api/health")
def health_check():
    return {"status": "ok"}


