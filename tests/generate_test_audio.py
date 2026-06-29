import numpy as np
from scipy.io import wavfile
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
    # Fundamental frequency + 3 harmonics
    y = np.sin(2 * np.pi * f0 * t) * 0.3
    y += np.sin(2 * np.pi * (f0 * 2) * t) * 0.15
    y += np.sin(2 * np.pi * (f0 * 3) * t) * 0.08
    y += np.sin(2 * np.pi * (f0 * 4) * t) * 0.04
    # Fade in/out
    fade = int(0.02 * sample_rate)
    window = np.ones_like(y)
    window[:fade] = np.linspace(0, 1, fade)
    window[-fade:] = np.linspace(1, 0, fade)
    return y * window

def generate_synthetic_word(is_correct_ha: bool, sample_rate: int = 16000) -> np.ndarray:
    """
    Synthesizes the word 'Al-Hamdu'.
    If is_correct_ha is True, the fricative part is high-frequency pharyngeal 'ح'.
    If False, the fricative part is low-frequency glottal 'ه'.
    """
    # 1. 'A' vowel (150ms)
    vowel_a = generate_vowel(0.15, sample_rate, f0=150.0)
    
    # 2. 'l' consonant (80ms)
    consonant_l = generate_vowel(0.08, sample_rate, f0=120.0) * 0.5
    
    # 3. 'h' / 'ħ' fricative (200ms)
    if is_correct_ha:
        # 'ح' (pharyngeal) -> energy in 1500 - 4500 Hz
        fricative = generate_noise(0.20, sample_rate, 1800.0, 4000.0)
    else:
        # 'ه' (glottal) -> energy in 100 - 900 Hz
        fricative = generate_noise(0.20, sample_rate, 100.0, 800.0)
        
    # 4. 'a' vowel (150ms)
    vowel_a2 = generate_vowel(0.15, sample_rate, f0=140.0)
    
    # 5. 'm' nasal (100ms)
    nasal_m = generate_vowel(0.10, sample_rate, f0=100.0) * 0.4
    
    # 6. 'd' stop (50ms silence + 30ms burst)
    stop_silence = np.zeros(int(0.05 * sample_rate))
    stop_burst = np.random.normal(0, 0.05, int(0.03 * sample_rate))
    
    # 7. 'u' vowel (150ms)
    vowel_u = generate_vowel(0.15, sample_rate, f0=130.0)
    
    # Concatenate all parts
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
    
    # Add a bit of silence at the start and end (100ms each)
    silence = np.zeros(int(0.1 * sample_rate))
    return np.concatenate([silence, audio, silence])

def create_test_suite_audio():
    os.makedirs("/home/backdoor/projects/iqlab-dev/tests", exist_ok=True)
    
    sample_rate = 16000
    
    # Generate correct 'ح' test file
    correct_audio = generate_synthetic_word(is_correct_ha=True, sample_rate=sample_rate)
    correct_path = "/home/backdoor/projects/iqlab-dev/tests/test_ha_correct.wav"
    # Convert to 16-bit PCM integer WAV
    correct_pcm = (correct_audio * 32767).astype(np.int16)
    wavfile.write(correct_path, sample_rate, correct_pcm)
    print(f"Generated: {correct_path}")
    
    # Generate incorrect 'ه' test file
    incorrect_audio = generate_synthetic_word(is_correct_ha=False, sample_rate=sample_rate)
    incorrect_path = "/home/backdoor/projects/iqlab-dev/tests/test_ha_incorrect.wav"
    incorrect_pcm = (incorrect_audio * 32767).astype(np.int16)
    wavfile.write(incorrect_path, sample_rate, incorrect_pcm)
    print(f"Generated: {incorrect_path}")

if __name__ == "__main__":
    create_test_suite_audio()
