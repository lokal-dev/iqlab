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


def estimate_formants_lpc(frame: np.ndarray, sample_rate: int, order: int = 12) -> list[float]:
    """
    Estimates the formant frequencies of a speech frame using Linear Predictive Coding (LPC).
    """
    from scipy.linalg import solve_toeplitz
    
    # 1. Pre-emphasis filter (high-pass to flatten the spectral tilt)
    x = frame[1:] - 0.97 * frame[:-1]
    
    # 2. Windowing
    x = x * np.hamming(len(x))
    
    # 3. Compute autocorrelation
    r = np.correlate(x, x, mode='full')
    r = r[len(r)//2 : len(r)//2 + order + 1]
    
    if r[0] == 0:
        return []
        
    # 4. Solve Yule-Walker equations using Toeplitz solver
    try:
        a = solve_toeplitz(r[:-1], r[1:])
        lpc_coeffs = np.concatenate(([1.0], -a))
    except Exception:
        # Fallback if Toeplitz solver fails
        return []
        
    # 5. Find roots of the LPC polynomial
    roots = np.roots(lpc_coeffs)
    
    # 6. Keep roots on the upper half of the Z-plane (positive frequency)
    roots = [rt for rt in roots if np.imag(rt) > 0]
    
    # 7. Convert roots to frequencies
    angles = np.arctan2(np.imag(roots), np.real(roots))
    freqs = angles * (sample_rate / (2 * np.pi))
    
    # 8. Filter frequencies in the vowel formant range (250 Hz - 4000 Hz)
    formants = sorted([f for f in freqs if 250 <= f <= 4000])
    
    return formants


def analyze_makhraj_ayn(wav_path: str, start_sec: float, end_sec: float) -> dict:
    """
    Analyzes the pronunciation of 'ع' (Ayn) vs 'أ' (Hamzah) in the word 'العالمين'.
    Uses LPC Formant Estimation to measure pharyngeal constriction.
    Returns:
        {
            "status": "pass" | "fail" | "error",
            "f1": float,
            "f2": float,
            "gap": float,
            "message": str
        }
    """
    try:
        if not os.path.exists(wav_path):
            return {"status": "error", "message": "Audio file not found"}

        # 1. Load WAV file
        sample_rate, data = wavfile.read(wav_path)
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32768.0
            
        # 2. Extract segment
        start_sample = int(start_sec * sample_rate)
        end_sample = int(end_sec * sample_rate)
        start_sample = max(0, start_sample)
        end_sample = min(len(data), end_sample)
        
        if end_sample - start_sample < sample_rate * 0.1:
            return {"status": "error", "message": "Segment too short"}
            
        word_audio = data[start_sample:end_sample]
        
        # 3. Locate the voiced transition of 'ع' (between 20% and 55% of 'العالمين')
        # We analyze the segment where the pharyngeal constriction occurs.
        search_start = int(len(word_audio) * 0.20)
        search_end = int(len(word_audio) * 0.55)
        frame_size = int(0.030 * sample_rate)  # 30ms window
        hop_size = frame_size // 2
        
        f1_list = []
        f2_list = []
        
        for i in range(search_start, search_end - frame_size, hop_size):
            frame = word_audio[i:i+frame_size]
            
            # Ensure the frame has sufficient energy (is voiced, not silence)
            energy = np.sum(frame ** 2) / frame_size
            if energy > 0.001:
                formants = estimate_formants_lpc(frame, sample_rate, order=12)
                if len(formants) >= 2:
                    f1_list.append(formants[0])
                    f2_list.append(formants[1])
                    
        if not f1_list or not f2_list:
            return {"status": "error", "message": "Could not track formants in voiced segment"}
            
        # 4. Calculate average F1, F2, and the formant gap
        avg_f1 = float(np.median(f1_list))
        avg_f2 = float(np.median(f2_list))
        gap = avg_f2 - avg_f1
        
        # 5. Classification Threshold
        # Pharyngeal constriction for 'ع' brings F1 and F2 very close together (small gap).
        # A normal open-throat vowel 'أ' has a wide gap.
        # Threshold: 620 Hz is the acoustic boundary.
        threshold = 620.0
        
        if gap < threshold:
            return {
                "status": "pass",
                "f1": round(avg_f1, 1),
                "f2": round(avg_f2, 1),
                "gap": round(gap, 1),
                "message": f"Makhraj Sempurna! Lafal 'ع' fasih dengan penyempitan tenggorokan (gap: {gap:.1f}Hz)."
            }
        else:
            return {
                "status": "fail",
                "f1": round(avg_f1, 1),
                "f2": round(avg_f2, 1),
                "gap": round(gap, 1),
                "message": f"Hampir tepat! Lafal 'ع' terdengar seperti 'أ' (Hamzah). Coba tekan pangkal lidah ke belakang tenggorokan (gap: {gap:.1f}Hz)."
            }
            
    except Exception as e:
        return {"status": "error", "message": f"DSP processing error: {str(e)}"}

