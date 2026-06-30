import numpy as np
from scipy.io import wavfile
import os

def analyze_makhraj_ha(wav_path: str, start_sec: float, end_sec: float, relative_pos: float = 0.2) -> dict:
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
        # Center the search window around the letter's relative position
        window_start = int(len(word_audio) * max(0.0, relative_pos - 0.25))
        window_end = int(len(word_audio) * min(1.0, relative_pos + 0.25))
        
        # We use a sliding window of 25ms (400 samples at 16kHz) with 50% overlap
        frame_size = int(0.025 * sample_rate)
        hop_size = frame_size // 2
        
        best_fricative_score = -1
        best_frame_data = None
        
        for i in range(window_start, window_end - frame_size, hop_size):
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


def analyze_makhraj_ayn(wav_path: str, start_sec: float, end_sec: float, relative_pos: float = 0.3) -> dict:
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
        
        # 3. Locate the voiced transition of 'ع'
        # Center the search window around the letter's relative position
        search_start = int(len(word_audio) * max(0.0, relative_pos - 0.20))
        search_end = int(len(word_audio) * min(1.0, relative_pos + 0.20))
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


def analyze_makhraj_sad(wav_path: str, start_sec: float, end_sec: float, relative_pos: float = 0.5) -> dict:
    """
    Analyzes the pronunciation of 'ص' (Sad) vs 'س' (Sin) in the audio segment.
    Uses Spectral Centroid to measure the thickness (Tafkhim/velarization) of the sibilant.
    Returns:
        {
            "status": "pass" | "fail" | "error",
            "centroid": float,
            "message": str
        }
    """
    try:
        if not os.path.exists(wav_path):
            return {"status": "error", "centroid": 0.0, "message": "Audio file not found"}

        # 1. Load WAV file (16kHz, mono, 16-bit PCM expected)
        sample_rate, data = wavfile.read(wav_path)
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32768.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483648.0
            
        # 2. Extract the word segment
        start_sample = int(start_sec * sample_rate)
        end_sample = int(end_sec * sample_rate)
        start_sample = max(0, start_sample)
        end_sample = min(len(data), end_sample)
        
        if end_sample - start_sample < sample_rate * 0.1:  # Less than 100ms
            return {"status": "error", "centroid": 0.0, "message": "Segment too short"}
            
        word_audio = data[start_sample:end_sample]
        
        # 3. Locate the sibilant segment (high ZCR, high energy)
        search_start = int(len(word_audio) * max(0.0, relative_pos - 0.25))
        search_end = int(len(word_audio) * min(1.0, relative_pos + 0.25))
        frame_size = int(0.025 * sample_rate)  # 25ms window
        hop_size = frame_size // 2
        
        best_sibilant_score = -1
        best_frame = None
        
        for i in range(search_start, search_end - frame_size, hop_size):
            frame = word_audio[i:i+frame_size]
            
            # Short-Time Energy (STE)
            ste = np.sum(frame ** 2) / frame_size
            
            # Zero Crossing Rate (ZCR)
            zero_crossings = np.nonzero(np.diff(np.sign(frame)))[0]
            zcr = len(zero_crossings) / frame_size
            
            # Sibilants have extremely high ZCR (typically > 0.25 at 16kHz) and high energy
            if ste > 0.0005:
                score = zcr * ste
                if score > best_sibilant_score:
                    best_sibilant_score = score
                    best_frame = frame
                    
        if best_frame is None:
            return {"status": "error", "centroid": 0.0, "message": "Could not isolate sibilant segment"}
            
        # 4. Compute Spectral Centroid
        # Apply Hamming window to reduce spectral leakage
        windowed_frame = best_frame * np.hamming(len(best_frame))
        fft_data = np.abs(np.fft.rfft(windowed_frame))
        frequencies = np.fft.rfftfreq(len(windowed_frame), 1.0 / sample_rate)
        
        sum_fft = np.sum(fft_data)
        if sum_fft == 0:
            return {"status": "error", "centroid": 0.0, "message": "Silent frame"}
            
        centroid = float(np.sum(frequencies * fft_data) / sum_fft)
        
        # 5. Differentiate Sad vs Sin
        # Plain 'س' has a very high centroid (typically > 5000 Hz)
        # Emphatic 'ص' has a lower centroid (typically 2000 - 4500 Hz) due to Tafkhim
        threshold = 4900.0
        
        if centroid < threshold:
            return {
                "status": "pass",
                "centroid": round(centroid, 1),
                "message": f"Makhraj Sempurna! Lafal 'ص' tebal dan tepat (Tafkhim) (centroid: {centroid:.1f}Hz)."
            }
        else:
            return {
                "status": "fail",
                "centroid": round(centroid, 1),
                "message": f"Hampir tepat! Huruf 'ص' terdengar tipis seperti 'س'. Coba tebalkan dengan mengangkat pangkal lidah dan penuhi rongga mulut (centroid: {centroid:.1f}Hz)."
            }
    except Exception as e:
        return {"status": "error", "centroid": 0.0, "message": f"DSP processing error: {str(e)}"}


def analyze_makhraj_kha(wav_path: str, start_sec: float, end_sec: float, relative_pos: float = 0.5) -> dict:
    """
    Analyzes the pronunciation of 'خ' (Kha) vs 'ك' (Kaf) / 'ه' (Haa) in the audio segment.
    Uses Peak-to-Average Energy Ratio (PAER) to detect stops (Kaf) and Spectral Energy Ratio to detect glottals (Haa).
    Returns:
        {
            "status": "pass" | "fail" | "error",
            "paer": float,
            "ratio": float,
            "message": str
        }
    """
    try:
        if not os.path.exists(wav_path):
            return {"status": "error", "paer": 0.0, "ratio": 0.0, "message": "Audio file not found"}

        # 1. Load WAV file (16kHz, mono, 16-bit PCM expected)
        sample_rate, data = wavfile.read(wav_path)
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32768.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483648.0
            
        # 2. Extract the word segment
        start_sample = int(start_sec * sample_rate)
        end_sample = int(end_sec * sample_rate)
        start_sample = max(0, start_sample)
        end_sample = min(len(data), end_sample)
        
        if end_sample - start_sample < sample_rate * 0.1:  # Less than 100ms
            return {"status": "error", "paer": 0.0, "ratio": 0.0, "message": "Segment too short"}
            
        word_audio = data[start_sample:end_sample]
        
        # 3. Locate the consonant segment (using sliding window)
        # Narrow the window to 10% to completely isolate the consonant from surrounding high-energy vowels
        search_start = int(len(word_audio) * max(0.0, relative_pos - 0.10))
        search_end = int(len(word_audio) * min(1.0, relative_pos + 0.10))
        
        frame_size = int(0.020 * sample_rate)  # 20ms window
        hop_size = frame_size // 2
        
        ste_list = []
        best_fricative_score = -1
        best_frame = None
        
        for i in range(search_start, search_end - frame_size, hop_size):
            frame = word_audio[i:i+frame_size]
            ste = np.sum(frame ** 2) / frame_size
            ste_list.append(ste)
            
            zero_crossings = np.nonzero(np.diff(np.sign(frame)))[0]
            zcr = len(zero_crossings) / frame_size
            
            if ste > 0.0001:
                score = zcr * (1.0 / (1.0 + ste * 5.0))
                if score > best_fricative_score:
                    best_fricative_score = score
                    best_frame = frame
                    
        if not ste_list:
            return {"status": "error", "paer": 0.0, "ratio": 0.0, "message": "No active frames"}
            
        # 4. Compute Peak-to-Average Energy Ratio (PAER) to detect stops (Kaf)
        max_ste = max(ste_list)
        mean_ste = np.mean(ste_list)
        # Add a regularizer (1e-4) to prevent high PAER on quiet signals/breath
        paer = float(max_ste / (mean_ste + 1e-4))
        
        # 5. Compute Spectral Energy Ratio to detect glottals (Haa)
        if best_frame is None:
            return {"status": "error", "paer": paer, "ratio": 0.0, "message": "Could not isolate fricative"}
            
        windowed_frame = best_frame * np.hamming(len(best_frame))
        fft_data = np.abs(np.fft.rfft(windowed_frame))
        frequencies = np.fft.rfftfreq(len(windowed_frame), 1.0 / sample_rate)
        
        # 'ه' is low-frequency breath (100 - 800 Hz)
        # 'خ' is mid-frequency scraping friction (1000 - 3500 Hz)
        low_band = (frequencies >= 100) & (frequencies <= 800)
        high_band = (frequencies >= 1000) & (frequencies <= 3500)
        
        low_energy = np.sum(fft_data[low_band])
        high_energy = np.sum(fft_data[high_band])
        
        if low_energy == 0:
            low_energy = 1e-6
        ratio = float(high_energy / low_energy)
        
        # 6. Classification
        paer_threshold = 3.5
        ratio_threshold = 0.50
        
        if paer >= paer_threshold:
            return {
                "status": "fail",
                "paer": round(paer, 2),
                "ratio": round(ratio, 2),
                "message": f"Hampir tepat! Huruf 'خ' terdengar seperti 'ك' (Kaf) akibat hentakan udara (PAER: {paer:.2f}). Coba alirkan suara scraping tenggorokan secara kontinu tanpa menahan udara."
            }
        elif ratio < ratio_threshold:
            return {
                "status": "fail",
                "paer": round(paer, 2),
                "ratio": round(ratio, 2),
                "message": f"Hampir tepat! Huruf 'خ' terdengar seperti 'ه' (Haa) (ratio: {ratio:.2f}). Coba gesekkan pangkal lidah ke langit-langit lunak untuk menghasilkan suara parau/scraping."
            }
        else:
            return {
                "status": "pass",
                "paer": round(paer, 2),
                "ratio": round(ratio, 2),
                "message": f"Makhraj Sempurna! Lafal 'خ' bersih dengan gesekan tenggorokan yang kontinu (PAER: {paer:.2f}, ratio: {ratio:.2f})."
            }
    except Exception as e:
        return {"status": "error", "paer": 0.0, "ratio": 0.0, "message": f"DSP processing error: {str(e)}"}


def analyze_makhraj_dhal(wav_path: str, start_sec: float, end_sec: float, relative_pos: float = 0.5) -> dict:
    """
    Analyzes the pronunciation of 'ذ' (Dhal) vs 'ز' (Zay) / 'د' (Dal) in the audio segment.
    Uses Peak-to-Average Energy Ratio (PAER) to detect stops (Dal) and Fricative-to-Word Energy Ratio to detect sibilance (Zay).
    Returns:
        {
            "status": "pass" | "fail" | "error",
            "paer": float,
            "energy_ratio": float,
            "message": str
        }
    """
    try:
        if not os.path.exists(wav_path):
            return {"status": "error", "paer": 0.0, "energy_ratio": 0.0, "message": "Audio file not found"}

        # 1. Load WAV file (16kHz, mono, 16-bit PCM expected)
        sample_rate, data = wavfile.read(wav_path)
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32768.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483648.0
            
        # 2. Extract the word segment
        start_sample = int(start_sec * sample_rate)
        end_sample = int(end_sec * sample_rate)
        start_sample = max(0, start_sample)
        end_sample = min(len(data), end_sample)
        
        if end_sample - start_sample < sample_rate * 0.1:  # Less than 100ms
            return {"status": "error", "paer": 0.0, "energy_ratio": 0.0, "message": "Segment too short"}
            
        word_audio = data[start_sample:end_sample]
        
        # 3. Analyze frames across the entire segment
        frame_size = int(0.020 * sample_rate)
        hop_size = frame_size // 2
        
        ste_list = []
        zcr_list = []
        
        for i in range(0, len(word_audio) - frame_size, hop_size):
            frame = word_audio[i:i+frame_size]
            ste = np.sum(frame ** 2) / frame_size
            ste_list.append(ste)
            
            zero_crossings = np.nonzero(np.diff(np.sign(frame)))[0]
            zcr = len(zero_crossings) / frame_size
            zcr_list.append(zcr)
            
        if not ste_list:
            return {"status": "error", "paer": 0.0, "energy_ratio": 0.0, "message": "No active frames"}
            
        mean_ste = np.mean(ste_list)
            
        # 4. Isolate the consonant region (around the relative position)
        # Narrow the window to 10% to completely isolate the consonant from surrounding high-energy vowels
        search_start = int(len(ste_list) * max(0.0, relative_pos - 0.10))
        search_end = int(len(ste_list) * min(1.0, relative_pos + 0.10))
        
        fricative_ste = ste_list[search_start:search_end]
        fricative_zcr = zcr_list[search_start:search_end]
        
        if not fricative_ste:
            return {"status": "error", "paer": 0.0, "energy_ratio": 0.0, "message": "Fricative region empty"}
            
        # Compute PAER (for Dal detection) using ONLY the consonant region
        max_fric_ste = max(fricative_ste)
        mean_fric_ste = np.mean(fricative_ste)
        # Add a regularizer (1e-4) to prevent high PAER on quiet signals/breath
        paer = float(max_fric_ste / (mean_fric_ste + 1e-4))
        
        mean_fricative_ste = np.mean(fricative_ste)
        mean_fricative_zcr = np.mean(fricative_zcr)
        
        energy_ratio = float(mean_fricative_ste / mean_ste)
        
        # 6. Classification
        paer_threshold = 3.5
        sibilant_energy_threshold = 0.35
        sibilant_zcr_threshold = 0.22
        
        if paer >= paer_threshold:
            return {
                "status": "fail",
                "paer": round(paer, 2),
                "energy_ratio": round(energy_ratio, 2),
                "message": f"Hampir tepat! Huruf 'ذ' terdengar seperti 'د' (Dal) akibat tertahannya aliran udara (PAER: {paer:.2f}). Coba alirkan udara dengan meletakkan ujung lidah di ujung gigi seri atas."
            }
        elif energy_ratio >= sibilant_energy_threshold and mean_fricative_zcr >= sibilant_zcr_threshold:
            return {
                "status": "fail",
                "paer": round(paer, 2),
                "energy_ratio": round(energy_ratio, 2),
                "message": f"Hampir tepat! Huruf 'ذ' terdengar mendesis seperti 'ز' (Zay) (desisan: {energy_ratio:.2f}). Hindari menekan lidah terlalu kuat ke gigi agar desisan berkurang."
            }
        else:
            return {
                "status": "pass",
                "paer": round(paer, 2),
                "energy_ratio": round(energy_ratio, 2),
                "message": f"Makhraj Sempurna! Lafal 'ذ' lembut dan tepat tanpa desisan berlebih (PAER: {paer:.2f}, desisan: {energy_ratio:.2f})."
            }
    except Exception as e:
        return {"status": "error", "paer": 0.0, "energy_ratio": 0.0, "message": f"DSP processing error: {str(e)}"}


def analyze_makhraj_tha(wav_path: str, start_sec: float, end_sec: float, relative_pos: float = 0.5) -> dict:
    """
    Analyzes the pronunciation of 'ث' (Tha) vs 'س' (Sin) / 'ت' (Ta).
    Similar to 'ذ' but voiceless.
    Returns:
        {
            "status": "pass" | "fail" | "error",
            "paer": float,
            "energy_ratio": float,
            "message": str
        }
    """
    try:
        res = analyze_makhraj_dhal(wav_path, start_sec, end_sec, relative_pos)
        if res["status"] == "error":
            return res
        
        if res["paer"] >= 3.5:
            return {
                "status": "fail",
                "paer": res["paer"],
                "energy_ratio": res["energy_ratio"],
                "message": f"Hampir tepat! Huruf 'ث' terdengar seperti 'ت' (Ta) akibat aliran udara tertahan (PAER: {res['paer']:.2f}). Hembuskan udara dengan meletakkan ujung lidah di ujung gigi seri atas."
            }
        elif res["energy_ratio"] >= 0.35:
            return {
                "status": "fail",
                "paer": res["paer"],
                "energy_ratio": res["energy_ratio"],
                "message": f"Hampir tepat! Huruf 'ث' terdengar mendesis tajam seperti 'س' (Sin) (desisan: {res['energy_ratio']:.2f}). Sentuhkan lidah dengan lembut saja tanpa tekanan kuat."
            }
        else:
            return {
                "status": "pass",
                "paer": res["paer"],
                "energy_ratio": res["energy_ratio"],
                "message": f"Makhraj Sempurna! Lafal 'ث' lembut dan tepat tanpa desisan berlebih (PAER: {res['paer']:.2f}, desisan: {res['energy_ratio']:.2f})."
            }
    except Exception as e:
        return {"status": "error", "paer": 0.0, "energy_ratio": 0.0, "message": f"DSP processing error: {str(e)}"}


def analyze_makhraj_tah(wav_path: str, start_sec: float, end_sec: float, relative_pos: float = 0.5) -> dict:
    """
    Analyzes the pronunciation of 'ط' (Tah) vs 'ت' (Ta) in the audio segment.
    Uses Spectral Centroid of the stop burst. Emphatic 'ط' has a lower centroid due to Tafkhim.
    Returns:
        {
            "status": "pass" | "fail" | "error",
            "centroid": float,
            "message": str
        }
    """
    try:
        if not os.path.exists(wav_path):
            return {"status": "error", "centroid": 0.0, "message": "Audio file not found"}

        # 1. Load WAV file
        sample_rate, data = wavfile.read(wav_path)
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32768.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483648.0
            
        # 2. Extract segment
        start_sample = max(0, int(start_sec * sample_rate))
        end_sample = min(len(data), int(end_sec * sample_rate))
        word_audio = data[start_sample:end_sample]
        
        # 3. Locate the burst (highest energy frame in the consonant region)
        search_start = int(len(word_audio) * max(0.0, relative_pos - 0.10))
        search_end = int(len(word_audio) * min(1.0, relative_pos + 0.10))
        frame_size = int(0.015 * sample_rate)  # 15ms window for transient burst
        hop_size = frame_size // 2
        
        best_ste = -1
        best_frame = None
        for i in range(search_start, search_end - frame_size, hop_size):
            frame = word_audio[i:i+frame_size]
            ste = np.sum(frame**2) / frame_size
            if ste > best_ste:
                best_ste = ste
                best_frame = frame
                
        if best_frame is None:
            return {"status": "error", "centroid": 0.0, "message": "Could not locate stop burst"}
            
        # 4. Compute Spectral Centroid of the burst
        windowed = best_frame * np.hamming(len(best_frame))
        fft_data = np.abs(np.fft.rfft(windowed))
        frequencies = np.fft.rfftfreq(len(windowed), 1.0 / sample_rate)
        
        sum_fft = np.sum(fft_data)
        if sum_fft == 0:
            return {"status": "error", "centroid": 0.0, "message": "Silent burst frame"}
            
        centroid = float(np.sum(frequencies * fft_data) / sum_fft)
        
        # 5. Classification
        # Emphatic 'ط' has a lower centroid (< 4000 Hz) due to back-tongue raising.
        # Plain 'ت' has a higher centroid (>= 4000 Hz).
        threshold = 4000.0
        if centroid < threshold:
            return {
                "status": "pass",
                "centroid": round(centroid, 1),
                "message": f"Makhraj Sempurna! Lafal 'ط' tebal dan fasih (Tafkhim) (centroid: {centroid:.1f}Hz)."
            }
        else:
            return {
                "status": "fail",
                "centroid": round(centroid, 1),
                "message": f"Hampir tepat! Huruf 'ط' terdengar tipis seperti 'ت' (Ta) (centroid: {centroid:.1f}Hz). Angkat pangkal lidah ke langit-langit lunak untuk menebalkan suara."
            }
    except Exception as e:
        return {"status": "error", "centroid": 0.0, "message": f"DSP processing error: {str(e)}"}


def analyze_makhraj_zha(wav_path: str, start_sec: float, end_sec: float, relative_pos: float = 0.5) -> dict:
    """
    Analyzes the pronunciation of 'ظ' (Zha) vs 'ز' (Zay) / 'د' (Dal) / 'ض' (Dad).
    Emphatic voiced dental fricative.
    Returns:
        {
            "status": "pass" | "fail" | "error",
            "message": str
        }
    """
    try:
        res = analyze_makhraj_dhal(wav_path, start_sec, end_sec, relative_pos)
        if res["status"] == "error":
            return res
            
        if res["paer"] >= 3.5:
            return {
                "status": "fail",
                "message": f"Hampir tepat! Huruf 'ظ' terdengar seperti 'د' atau 'ض' akibat tertahannya aliran udara (PAER: {res['paer']:.2f}). Coba alirkan udara dengan lembut."
            }
        elif res["energy_ratio"] >= 0.35:
            return {
                "status": "fail",
                "message": f"Hampir tepat! Huruf 'ظ' terdengar mendesis tipis seperti 'ز' (Zay) (desisan: {res['energy_ratio']:.2f}). Penuhi rongga mulut dengan gema (Tafkhim) dan angkat pangkal lidah."
            }
        else:
            return {
                "status": "pass",
                "message": f"Makhraj Sempurna! Lafal 'ظ' tebal, lembut, dan tepat."
            }
    except Exception as e:
        return {"status": "error", "message": f"DSP processing error: {str(e)}"}


def analyze_makhraj_dad(wav_path: str, start_sec: float, end_sec: float, relative_pos: float = 0.5) -> dict:
    """
    Analyzes the pronunciation of 'ض' (Dad) vs 'د' (Dal).
    Uses Spectral Centroid. Emphatic 'ض' has a lower centroid than plain 'د'.
    Returns:
        {
            "status": "pass" | "fail" | "error",
            "centroid": float,
            "message": str
        }
    """
    try:
        res = analyze_makhraj_tah(wav_path, start_sec, end_sec, relative_pos)
        if res["status"] == "error":
            return res
            
        centroid = res["centroid"]
        # 'ض' (Dad) is extremely thick, threshold set at 3400 Hz.
        threshold = 3400.0
        if centroid < threshold:
            return {
                "status": "pass",
                "centroid": centroid,
                "message": f"Makhraj Sempurna! Lafal 'ض' tebal dan tepat (centroid: {centroid:.1f}Hz)."
            }
        else:
            return {
                "status": "fail",
                "centroid": centroid,
                "message": f"Hampir tepat! Huruf 'ض' terdengar tipis seperti 'د' (Dal) (centroid: {centroid:.1f}Hz). Tempelkan sisi lidah ke gigi geraham atas untuk menutup aliran suara."
            }
    except Exception as e:
        return {"status": "error", "centroid": 0.0, "message": f"DSP processing error: {str(e)}"}


def analyze_makhraj_ghayn(wav_path: str, start_sec: float, end_sec: float, relative_pos: float = 0.5) -> dict:
    """
    Analyzes the pronunciation of 'غ' (Ghayn) vs 'خ' (Kha) / 'g' (Indonesian g).
    Uses voicing detection (energy in 50-250Hz) to separate from 'خ', and PAER to separate from stop 'g'.
    Returns:
        {
            "status": "pass" | "fail" | "error",
            "paer": float,
            "message": str
        }
    """
    try:
        if not os.path.exists(wav_path):
            return {"status": "error", "paer": 0.0, "message": "Audio file not found"}

        # 1. Load WAV file
        sample_rate, data = wavfile.read(wav_path)
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32768.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483648.0
            
        # 2. Extract segment
        start_sample = max(0, int(start_sec * sample_rate))
        end_sample = min(len(data), int(end_sec * sample_rate))
        word_audio = data[start_sample:end_sample]
        
        # 3. Analyze consonant region
        search_start = int(len(word_audio) * max(0.0, relative_pos - 0.10))
        search_end = int(len(word_audio) * min(1.0, relative_pos + 0.10))
        frame_size = int(0.020 * sample_rate)
        hop_size = frame_size // 2
        
        ste_list = []
        best_frame = None
        best_ste = -1
        for i in range(search_start, search_end - frame_size, hop_size):
            frame = word_audio[i:i+frame_size]
            ste = np.sum(frame**2) / frame_size
            ste_list.append(ste)
            if ste > best_ste:
                best_ste = ste
                best_frame = frame
                
        if not ste_list or best_frame is None:
            return {"status": "error", "paer": 0.0, "message": "Could not isolate consonant"}
            
        paer = float(max(ste_list) / (np.mean(ste_list) + 1e-4))
        
        # 4. Check voicing (energy in 50-250Hz vs 1000-4000Hz)
        windowed = best_frame * np.hamming(len(best_frame))
        fft_data = np.abs(np.fft.rfft(windowed))
        frequencies = np.fft.rfftfreq(len(windowed), 1.0 / sample_rate)
        
        voice_band = (frequencies >= 50) & (frequencies <= 250)
        fric_band = (frequencies >= 1000) & (frequencies <= 4000)
        
        voice_energy = np.sum(fft_data[voice_band])
        fric_energy = np.sum(fft_data[fric_band])
        
        voicing_ratio = float(voice_energy / (fric_energy + 1e-4))
        
        # 5. Classification
        if paer >= 3.5:
            return {
                "status": "fail",
                "paer": round(paer, 2),
                "message": f"Hampir tepat! Huruf 'غ' terdengar seperti plosif 'g' akibat aliran udara tertahan (PAER: {paer:.2f}). Alirkan suara getaran tenggorokan secara berkesinambungan."
            }
        elif voicing_ratio < 0.8:
            return {
                "status": "fail",
                "paer": round(paer, 2),
                "message": f"Hampir tepat! Huruf 'غ' terdengar tanpa desis pita suara, mirip seperti 'خ' (Kha) (voicing ratio: {voicing_ratio:.2f}). Bunyikan suara dengan getaran pita suara."
            }
        else:
            return {
                "status": "pass",
                "paer": round(paer, 2),
                "message": f"Makhraj Sempurna! Lafal 'غ' tepat dan bergetar di tenggorokan atas (voicing ratio: {voicing_ratio:.2f})."
            }
    except Exception as e:
        return {"status": "error", "paer": 0.0, "message": f"DSP processing error: {str(e)}"}


def analyze_makhraj_qaf(wav_path: str, start_sec: float, end_sec: float, relative_pos: float = 0.5) -> dict:
    """
    Analyzes the pronunciation of 'ق' (Qaf) vs 'ك' (Kaf).
    Uses Spectral Centroid of the stop burst. Uvular 'ق' has a lower centroid than velar 'ك'.
    Returns:
        {
            "status": "pass" | "fail" | "error",
            "centroid": float,
            "message": str
        }
    """
    try:
        res = analyze_makhraj_tah(wav_path, start_sec, end_sec, relative_pos)
        if res["status"] == "error":
            return res
            
        centroid = res["centroid"]
        # Uvular 'ق' has a lower centroid (< 3000 Hz) due to deep throat constriction.
        threshold = 3000.0
        if centroid < threshold:
            return {
                "status": "pass",
                "centroid": centroid,
                "message": f"Makhraj Sempurna! Lafal 'ق' mantap dan tebal di pangkal tenggorokan (centroid: {centroid:.1f}Hz)."
            }
        else:
            return {
                "status": "fail",
                "centroid": centroid,
                "message": f"Hampir tepat! Huruf 'ق' terdengar tipis seperti 'ك' (Kaf) (centroid: {centroid:.1f}Hz). Tekan pangkal lidah lebih dalam ke langit-langit lunak dekat anak tekak."
            }
    except Exception as e:
        return {"status": "error", "centroid": 0.0, "message": f"DSP processing error: {str(e)}"}




