import numpy as np
from scipy.io import wavfile
import scipy.signal as signal
import os

def generate_noise(duration: float, sample_rate: int, low_freq: float, high_freq: float) -> np.ndarray:
    """Generates band-limited white noise."""
    samples = int(duration * sample_rate)
    noise = np.random.normal(0, 1, samples)
    
    # Simple frequency domain filtering
    fft_vals = np.fft.rfft(noise)
    frequencies = np.fft.rfftfreq(samples, 1.0 / sample_rate)
    
    # Filter out frequencies outside [low_freq, high_freq]
    band_filter = (frequencies >= low_freq) & (frequencies <= high_freq)
    fft_vals[~band_filter] *= 0.01  # attenuate heavily
    
    filtered_noise = np.fft.irfft(fft_vals)
    # Normalize amplitude
    filtered_noise = filtered_noise / np.max(np.abs(filtered_noise)) * 0.2
    return filtered_noise

def generate_vowel(duration: float, sample_rate: int, f0: float) -> np.ndarray:
    """Generates a synthetic vowel-like sound (sine wave + harmonics)."""
    t = np.linspace(0, duration, int(duration * sample_rate), endpoint=False)
    y = np.sin(2 * np.pi * f0 * t) * 0.3
    y += np.sin(2 * np.pi * (f0 * 2) * t) * 0.15
    y += np.sin(2 * np.pi * (f0 * 3) * t) * 0.08
    y += np.sin(2 * np.pi * (f0 * 4) * t) * 0.04
    fade = int(0.02 * sample_rate)
    window = np.ones_like(y)
    window[:fade] = np.linspace(0, 1, fade)
    window[-fade:] = np.linspace(1, 0, fade)
    return y * window

def generate_resonance_vowel(duration: float, sample_rate: int, f0: float, f1: float, f2: float) -> np.ndarray:
    """
    Generates a synthetic vowel with specific F1 and F2 formants
    using two second-order bandpass resonators (IIR filters).
    """
    samples = int(duration * sample_rate)
    
    # 1. Generate excitation signal (pulse train at f0 + soft white noise)
    excitation = np.zeros(samples)
    period = int(sample_rate / f0)
    excitation[::period] = 1.0
    excitation += np.random.normal(0, 0.05, samples)
    
    # 2. Filter with F1 resonator (bandwidth r=0.95)
    r = 0.95
    theta1 = 2 * np.pi * f1 / sample_rate
    b1 = [1.0]
    a1 = [1.0, -2 * r * np.cos(theta1), r * r]
    y1 = signal.lfilter(b1, a1, excitation)
    
    # 3. Filter with F2 resonator
    theta2 = 2 * np.pi * f2 / sample_rate
    b2 = [1.0]
    a2 = [1.0, -2 * r * np.cos(theta2), r * r]
    y2 = signal.lfilter(b2, a2, y1)
    
    # Normalize
    y2 = y2 / np.max(np.abs(y2)) * 0.3
    
    # Fade in/out
    fade = int(0.02 * sample_rate)
    window = np.ones_like(y2)
    window[:fade] = np.linspace(0, 1, fade)
    window[-fade:] = np.linspace(1, 0, fade)
    
    return y2 * window

def generate_synthetic_word(is_correct_ha: bool, sample_rate: int = 16000) -> np.ndarray:
    """Synthesizes the word 'Al-Hamdu' for 'ح' vs 'ه' testing."""
    vowel_a = generate_vowel(0.15, sample_rate, f0=150.0)
    consonant_l = generate_vowel(0.08, sample_rate, f0=120.0) * 0.5
    
    if is_correct_ha:
        fricative = generate_noise(0.20, sample_rate, 1800.0, 4000.0)
    else:
        fricative = generate_noise(0.20, sample_rate, 100.0, 800.0)
        
    vowel_a2 = generate_vowel(0.15, sample_rate, f0=140.0)
    nasal_m = generate_vowel(0.10, sample_rate, f0=100.0) * 0.4
    stop_silence = np.zeros(int(0.05 * sample_rate))
    stop_burst = np.random.normal(0, 0.05, int(0.03 * sample_rate))
    vowel_u = generate_vowel(0.15, sample_rate, f0=130.0)
    
    audio = np.concatenate([
        vowel_a,
        consonant_l,
        fricative,
        vowel_a2,
        nasal_m,
        stop_silence,
        stop_burst,
        vowel_u
    ])
    
    silence = np.zeros(int(0.1 * sample_rate))
    return np.concatenate([silence, audio, silence])

def generate_synthetic_ayn_word(is_correct_ayn: bool, sample_rate: int = 16000) -> np.ndarray:
    """
    Synthesizes the word 'Al-Alamin' for 'ع' vs 'أ' testing.
    If is_correct_ayn is True, F1/F2 have a small gap (constricted).
    If False, F1/F2 have a wide gap (open glottal).
    """
    # 'Al-' prefix
    vowel_a = generate_vowel(0.12, sample_rate, f0=140.0)
    consonant_l = generate_vowel(0.08, sample_rate, f0=120.0) * 0.5
    
    # 'Ayn' consonant / vowel transition (250ms)
    if is_correct_ayn:
        # 'ع' (pharyngeal) -> F1 elevated, F2 depressed (gap = 400Hz)
        vowel_ayn = generate_resonance_vowel(0.25, sample_rate, f0=130.0, f1=800.0, f2=1200.0)
    else:
        # 'أ' (glottal) -> F1 normal, F2 normal (gap = 1000Hz)
        vowel_ayn = generate_resonance_vowel(0.25, sample_rate, f0=130.0, f1=500.0, f2=1500.0)
        
    # '-lamin' suffix
    consonant_l2 = generate_vowel(0.08, sample_rate, f0=120.0) * 0.5
    vowel_aa = generate_vowel(0.15, sample_rate, f0=110.0)
    nasal_m = generate_vowel(0.10, sample_rate, f0=100.0) * 0.4
    vowel_ii = generate_vowel(0.15, sample_rate, f0=95.0)
    nasal_n = generate_vowel(0.12, sample_rate, f0=90.0) * 0.4
    
    audio = np.concatenate([
        vowel_a,
        consonant_l,
        vowel_ayn,
        consonant_l2,
        vowel_aa,
        nasal_m,
        vowel_ii,
        nasal_n
    ])
    
    silence = np.zeros(int(0.1 * sample_rate))
    return np.concatenate([silence, audio, silence])

def generate_synthetic_sad_word(is_correct_sad: bool, sample_rate: int = 16000) -> np.ndarray:
    """
    Synthesizes a word containing 'ص' (Sad) vs 'س' (Sin) testing.
    If is_correct_sad is True, the noise is band-limited to 2000-4200 Hz (Sad).
    If False, the noise is band-limited to 5800-7800 Hz (Sin).
    """
    vowel_pre = generate_vowel(0.15, sample_rate, f0=130.0)
    
    if is_correct_sad:
        # 'ص' (emphatic sibilant: lower frequency)
        fricative = generate_noise(0.25, sample_rate, 2000.0, 4200.0)
    else:
        # 'س' (plain sibilant: higher frequency)
        fricative = generate_noise(0.25, sample_rate, 5800.0, 7800.0)
        
    vowel_post = generate_vowel(0.15, sample_rate, f0=120.0)
    
    audio = np.concatenate([vowel_pre, fricative, vowel_post])
    silence = np.zeros(int(0.1 * sample_rate))
    return np.concatenate([silence, audio, silence])

def generate_synthetic_kha_word(type_kha: str, sample_rate: int = 16000) -> np.ndarray:
    """
    Synthesizes a word containing 'خ' (Kha) vs 'ك' (Kaf) / 'ه' (Haa) testing.
    types: 'correct' (Kha), 'incorrect_kaf' (stop), 'incorrect_haa' (low-frequency glottal)
    """
    vowel_pre = generate_vowel(0.15, sample_rate, f0=140.0)
    
    if type_kha == 'correct':
        # 'خ' (continuous velar noise)
        fricative = generate_noise(0.25, sample_rate, 1200.0, 3200.0)
        audio = np.concatenate([vowel_pre, fricative])
    elif type_kha == 'incorrect_haa':
        # 'ه' (low-frequency glottal noise, very quiet)
        fricative = generate_noise(0.25, sample_rate, 100.0, 600.0) * 0.4
        audio = np.concatenate([vowel_pre, fricative])
    else:
        # 'ك' (stop consonant: silence + burst)
        silence_gap = np.zeros(int(0.08 * sample_rate))
        burst = np.random.normal(0, 0.25, int(0.02 * sample_rate))
        decay = np.random.normal(0, 0.02, int(0.15 * sample_rate))
        audio = np.concatenate([vowel_pre, silence_gap, burst, decay])
        
    vowel_post = generate_vowel(0.15, sample_rate, f0=130.0)
    audio = np.concatenate([audio, vowel_post])
    silence = np.zeros(int(0.1 * sample_rate))
    return np.concatenate([silence, audio, silence])

def generate_synthetic_dhal_word(type_dhal: str, sample_rate: int = 16000) -> np.ndarray:
    """
    Synthesizes a word containing 'ذ' (Dhal) vs 'ز' (Zay) / 'د' (Dal) testing.
    types: 'correct' (Dhal), 'incorrect_dal' (stop), 'incorrect_zay' (sibilant)
    """
    vowel_pre = generate_vowel(0.15, sample_rate, f0=135.0)
    
    if type_dhal == 'correct':
        # 'ذ' (quiet voiced fricative: low amplitude)
        fricative = generate_noise(0.20, sample_rate, 1000.0, 3000.0) * 0.08
        audio = np.concatenate([vowel_pre, fricative])
    elif type_dhal == 'incorrect_zay':
        # 'ز' (loud voiced sibilant: high amplitude)
        fricative = generate_noise(0.20, sample_rate, 3500.0, 7000.0) * 3.5
        audio = np.concatenate([vowel_pre, fricative])
    else:
        # 'د' (stop consonant: silence + burst)
        silence_gap = np.zeros(int(0.08 * sample_rate))
        burst = np.random.normal(0, 0.2, int(0.02 * sample_rate))
        decay = np.random.normal(0, 0.02, int(0.10 * sample_rate))
        audio = np.concatenate([vowel_pre, silence_gap, burst, decay])
        
    vowel_post = generate_vowel(0.15, sample_rate, f0=125.0)
    audio = np.concatenate([audio, vowel_post])
    silence = np.zeros(int(0.1 * sample_rate))
    return np.concatenate([silence, audio, silence])

def create_test_suite_audio():
    os.makedirs("/home/backdoor/projects/iqlab-dev/tests", exist_ok=True)
    sample_rate = 16000
    
    # 1. 'ح' vs 'ه'
    correct_audio = generate_synthetic_word(is_correct_ha=True, sample_rate=sample_rate)
    correct_path = "/home/backdoor/projects/iqlab-dev/tests/test_ha_correct.wav"
    wavfile.write(correct_path, sample_rate, (correct_audio * 32767).astype(np.int16))
    
    incorrect_audio = generate_synthetic_word(is_correct_ha=False, sample_rate=sample_rate)
    incorrect_path = "/home/backdoor/projects/iqlab-dev/tests/test_ha_incorrect.wav"
    wavfile.write(incorrect_path, sample_rate, (incorrect_audio * 32767).astype(np.int16))
    
    # 2. 'ع' vs 'أ'
    ayn_correct_audio = generate_synthetic_ayn_word(is_correct_ayn=True, sample_rate=sample_rate)
    ayn_correct_path = "/home/backdoor/projects/iqlab-dev/tests/test_ayn_correct.wav"
    wavfile.write(ayn_correct_path, sample_rate, (ayn_correct_audio * 32767).astype(np.int16))
    
    ayn_incorrect_audio = generate_synthetic_ayn_word(is_correct_ayn=False, sample_rate=sample_rate)
    ayn_incorrect_path = "/home/backdoor/projects/iqlab-dev/tests/test_ayn_incorrect.wav"
    wavfile.write(ayn_incorrect_path, sample_rate, (ayn_incorrect_audio * 32767).astype(np.int16))
    
    # 3. 'ص' vs 'س'
    sad_correct_audio = generate_synthetic_sad_word(is_correct_sad=True, sample_rate=sample_rate)
    sad_correct_path = "/home/backdoor/projects/iqlab-dev/tests/test_sad_correct.wav"
    wavfile.write(sad_correct_path, sample_rate, (sad_correct_audio * 32767).astype(np.int16))
    
    sad_incorrect_audio = generate_synthetic_sad_word(is_correct_sad=False, sample_rate=sample_rate)
    sad_incorrect_path = "/home/backdoor/projects/iqlab-dev/tests/test_sad_incorrect.wav"
    wavfile.write(sad_incorrect_path, sample_rate, (sad_incorrect_audio * 32767).astype(np.int16))
    
    # 4. 'خ' vs 'ك' / 'ه'
    wavfile.write("/home/backdoor/projects/iqlab-dev/tests/test_kha_correct.wav", sample_rate, 
                  (generate_synthetic_kha_word('correct', sample_rate) * 32767).astype(np.int16))
    wavfile.write("/home/backdoor/projects/iqlab-dev/tests/test_kha_incorrect_kaf.wav", sample_rate, 
                  (generate_synthetic_kha_word('incorrect_kaf', sample_rate) * 32767).astype(np.int16))
    wavfile.write("/home/backdoor/projects/iqlab-dev/tests/test_kha_incorrect_haa.wav", sample_rate, 
                  (generate_synthetic_kha_word('incorrect_haa', sample_rate) * 32767).astype(np.int16))
                  
    # 5. 'ذ' vs 'ز' / 'د'
    wavfile.write("/home/backdoor/projects/iqlab-dev/tests/test_dhal_correct.wav", sample_rate, 
                  (generate_synthetic_dhal_word('correct', sample_rate) * 32767).astype(np.int16))
    wavfile.write("/home/backdoor/projects/iqlab-dev/tests/test_dhal_incorrect_dal.wav", sample_rate, 
                  (generate_synthetic_dhal_word('incorrect_dal', sample_rate) * 32767).astype(np.int16))
    wavfile.write("/home/backdoor/projects/iqlab-dev/tests/test_dhal_incorrect_zay.wav", sample_rate, 
                  (generate_synthetic_dhal_word('incorrect_zay', sample_rate) * 32767).astype(np.int16))
    
    print("All synthetic test audio files generated successfully!")

if __name__ == "__main__":
    create_test_suite_audio()
