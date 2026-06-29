import numpy as np
from scipy.io import wavfile
import os

def analyze_makhraj_ha(wav_path: str, start_sec: float, end_sec: float) -> dict:
    """
    Analyzes the pronunciation of the letter 'ح' vs 'ه' in the audio segment.
    Returns:
        {
            "status": "pass" | "fail" | "error",
            "ratio": float,
            "message": str
        }
    """
    try:
        if not os.path.exists(wav_path):
            return {"status": "error", "ratio": 0.0, "message": "Audio file not found"}

        # 1. Load WAV file (16kHz, mono, 16-bit PCM expected)
        sample_rate, data = wavfile.read(wav_path)
        
        # If stereo, convert to mono
        if len(data.shape) > 1:
            data = data.mean(axis=1)
            
        # Normalize audio to [-1.0, 1.0]
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32768.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483648.0
            
        # 2. Extract the word segment
        start_sample = int(start_sec * sample_rate)
        end_sample = int(end_sec * sample_rate)
        
        # Guard rails
        start_sample = max(0, start_sample)
        end_sample = min(len(data), end_sample)
        
        if end_sample - start_sample < sample_rate * 0.1:  # Less than 100ms
            return {"status": "error", "ratio": 0.0, "message": "Segment too short"}
            
        word_audio = data[start_sample:end_sample]
        
        # 3. Locate the fricative segment (high Zero Crossing Rate, low-medium energy)
        # We restrict the search to the first 60% of the word duration.
        # This is because 'ح' in 'الحمد' occurs early, and we want to avoid
        # picking up the stop-consonant burst 'd' at the end of the word.
        search_limit = int(len(word_audio) * 0.60)
        
        # We use a sliding window of 25ms (400 samples at 16kHz) with 50% overlap
        frame_size = int(0.025 * sample_rate)
        hop_size = frame_size // 2
        
        best_fricative_score = -1
        best_frame_data = None
        
        for i in range(0, search_limit - frame_size, hop_size):
            frame = word_audio[i:i+frame_size]
            
            # Short-Time Energy (STE)
            ste = np.sum(frame ** 2) / frame_size
            
            # Zero Crossing Rate (ZCR)
            zero_crossings = np.nonzero(np.diff(np.sign(frame)))[0]
            zcr = len(zero_crossings) / frame_size
            
            # Fricatives have high ZCR. We want to avoid silence (very low STE)
            # and voiced vowels (very high STE, low ZCR).
            # A good fricative heuristic: high ZCR, and energy within a moderate range.
            if ste > 0.0001:  # Not silence
                # Score favors high ZCR and penalizes excessive voiced energy
                score = zcr * (1.0 / (1.0 + ste * 10.0))
                if score > best_fricative_score:
                    best_fricative_score = score
                    best_frame_data = frame
                    
        if best_frame_data is None:
            return {"status": "error", "ratio": 0.0, "message": "Could not isolate fricative segment"}
            
        # 4. Perform Spectral Analysis (FFT)
        fft_data = np.abs(np.fft.rfft(best_frame_data))
        frequencies = np.fft.rfftfreq(len(best_frame_data), 1.0 / sample_rate)
        
        # Define bands:
        # 'ه' (glottal) is low-frequency breath (100 - 1000 Hz)
        # 'ح' (pharyngeal) is mid-to-high frequency friction (1500 - 4500 Hz)
        low_band_idx = (frequencies >= 100) & (frequencies <= 1000)
        high_band_idx = (frequencies >= 1500) & (frequencies <= 4500)
        
        low_energy = np.sum(fft_data[low_band_idx])
        high_energy = np.sum(fft_data[high_band_idx])
        
        if low_energy == 0:
            low_energy = 1e-6  # Prevent division by zero
            
        ratio = float(high_energy / low_energy)
        
        # 5. Classification Threshold
        # Pharyngeal 'ح' has significantly more high-frequency friction.
        # A threshold of 0.60 is a good starting point based on acoustic analysis of Arabic fricatives.
        threshold = 0.65
        
        if ratio >= threshold:
            return {
                "status": "pass",
                "ratio": round(ratio, 3),
                "message": f"Makhraj Sempurna! Lafal 'ح' bersih dan tepat (ratio: {ratio:.3f})."
            }
        else:
            return {
                "status": "fail",
                "ratio": round(ratio, 3),
                "message": f"Hampir tepat! Huruf 'ح' terdengar seperti 'ه'. Coba hembuskan nafas lebih bersih dari tenggorokan tengah (ratio: {ratio:.3f})."
            }
            
    except Exception as e:
        return {"status": "error", "ratio": 0.0, "message": f"DSP processing error: {str(e)}"}
