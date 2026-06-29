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
from backend.search import search_verses
from backend.makhraj import analyze_makhraj_ha

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
                
            # ── Makhraj Grading PoC (Surah 1 Ayah 2: 'الحمد') ──
            tajweed_html = verse.tajweed_html
            
            if verse.surah_number == 1 and verse.ayah_number == 2:
                # Find the word "الحمد" or "حمد" in the ASR word list
                target_word = None
                for w in asr_result["words"]:
                    clean_w = w["word"].strip()
                    if "حمد" in clean_w:
                        target_word = w
                        break
                
                if target_word:
                    # Run the DSP analysis on the WAV file
                    makhraj_res = analyze_makhraj_ha(
                        temp_trimmed_path,
                        start_sec=target_word["start"],
                        end_sec=target_word["end"]
                    )
                    
                    if makhraj_res["status"] in ["pass", "fail"]:
                        status = makhraj_res["status"]
                        msg = makhraj_res["message"]
                        
                        # Inject the highlight span into the Uthmani text
                        if status == "pass":
                            highlighted = (
                                f'<span class="makhraj-highlight makhraj-pass" '
                                f'title="{msg}">ح</span>'
                            )
                        else:
                            highlighted = (
                                f'<span class="makhraj-highlight makhraj-fail" '
                                f'title="{msg}">ح</span>'
                            )
                        
                        # Replace the single 'ح' in "الْحَمْدُ"
                        tajweed_html = verse.tajweed_html.replace('ح', highlighted)
            
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
