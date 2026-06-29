import os
from faster_whisper import WhisperModel

# Use a small model for the VPS, int8 quantization to save RAM
MODEL_SIZE = os.getenv("WHISPER_MODEL", "small")
COMPUTE_TYPE = "int8"
DEVICE = "cpu"  # Force CPU for the 1-core VPS constraint

print(f"Loading faster-whisper model '{MODEL_SIZE}' on {DEVICE} with {COMPUTE_TYPE}...")
model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
print("ASR model loaded.")

def transcribe_audio(audio_path: str) -> dict:
    """
    Transcribes audio file at `audio_path`.
    Forces Arabic language and returns word-level timestamps.
    """
    segments, info = model.transcribe(
        audio_path,
        language="ar",
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
        word_timestamps=True,
    )
    
    text_segments = []
    words_list = []
    
    for segment in segments:
        text_segments.append(segment.text)
        if segment.words:
            for w in segment.words:
                words_list.append({
                    "word": w.word,
                    "start": w.start,
                    "end": w.end,
                    "probability": w.probability
                })
                
    return {
        "text": " ".join(text_segments).strip(),
        "words": words_list
    }
