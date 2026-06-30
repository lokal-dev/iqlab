import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.makhraj import analyze_makhraj_ha, analyze_makhraj_ayn, analyze_makhraj_sad
from tests.generate_test_audio import create_test_suite_audio

def run_tests():
    print("=== Running Makhraj DSP Unit Tests ===")
    
    # 1. Generate synthetic audio files if they don't exist
    create_test_suite_audio()
    
    # ─── SECTION 1: 'ح' vs 'ه' (Spectral Energy Ratio) ───
    print("\n--- Testing 'ح' vs 'ه' (Ha vs Haa) ---")
    
    # Test correct 'ح' pronunciation
    correct_result = analyze_makhraj_ha(
        "/home/backdoor/projects/iqlab-dev/tests/test_ha_correct.wav", 
        start_sec=0.1, 
        end_sec=1.0
    )
    print("\n[TEST] Correct 'ح' (pharyngeal) result:")
    print(f"  Status:  {correct_result['status']}")
    print(f"  Ratio:   {correct_result['ratio']}")
    print(f"  Message: {correct_result['message']}")
    assert correct_result["status"] == "pass", f"Expected 'pass', got '{correct_result['status']}'"
    
    # Test incorrect 'ه' pronunciation
    incorrect_result = analyze_makhraj_ha(
        "/home/backdoor/projects/iqlab-dev/tests/test_ha_incorrect.wav", 
        start_sec=0.1, 
        end_sec=1.0
    )
    print("\n[TEST] Incorrect 'ه' (glottal) result:")
    print(f"  Status:  {incorrect_result['status']}")
    print(f"  Ratio:   {incorrect_result['ratio']}")
    print(f"  Message: {incorrect_result['message']}")
    assert incorrect_result["status"] == "fail", f"Expected 'fail', got '{incorrect_result['status']}'"
    
    # ─── SECTION 2: 'ع' vs 'أ' (LPC Formant Gap) ───
    print("\n--- Testing 'ع' vs 'أ' (Ayn vs Hamzah) ---")
    
    # Test correct 'ع' pronunciation
    ayn_correct_result = analyze_makhraj_ayn(
        "/home/backdoor/projects/iqlab-dev/tests/test_ayn_correct.wav",
        start_sec=0.1,
        end_sec=1.1
    )
    print("\n[TEST] Correct 'ع' (pharyngeal) result:")
    print(f"  Status:  {ayn_correct_result['status']}")
    print(f"  F1/F2:   {ayn_correct_result.get('f1')}/{ayn_correct_result.get('f2')} Hz")
    print(f"  Gap:     {ayn_correct_result.get('gap')} Hz")
    print(f"  Message: {ayn_correct_result['message']}")
    assert ayn_correct_result["status"] == "pass", f"Expected 'pass', got '{ayn_correct_result['status']}'"
    
    # Test incorrect 'أ' pronunciation
    ayn_incorrect_result = analyze_makhraj_ayn(
        "/home/backdoor/projects/iqlab-dev/tests/test_ayn_incorrect.wav",
        start_sec=0.1,
        end_sec=1.1
    )
    print("\n[TEST] Incorrect 'أ' (glottal) result:")
    print(f"  Status:  {ayn_incorrect_result['status']}")
    print(f"  F1/F2:   {ayn_incorrect_result.get('f1')}/{ayn_incorrect_result.get('f2')} Hz")
    print(f"  Gap:     {ayn_incorrect_result.get('gap')} Hz")
    print(f"  Message: {ayn_incorrect_result['message']}")
    assert ayn_incorrect_result["status"] == "fail", f"Expected 'fail', got '{ayn_incorrect_result['status']}'"
    
    # ─── SECTION 3: 'ص' vs 'س' (Spectral Centroid) ───
    print("\n--- Testing 'ص' vs 'س' (Sad vs Sin) ---")
    
    # Test correct 'ص' pronunciation (Tafkhim / thick sibilant)
    sad_correct_result = analyze_makhraj_sad(
        "/home/backdoor/projects/iqlab-dev/tests/test_sad_correct.wav",
        start_sec=0.1,
        end_sec=1.1
    )
    print("\n[TEST] Correct 'ص' (thick) result:")
    print(f"  Status:    {sad_correct_result['status']}")
    print(f"  Centroid:  {sad_correct_result.get('centroid')} Hz")
    print(f"  Message:   {sad_correct_result['message']}")
    assert sad_correct_result["status"] == "pass", f"Expected 'pass', got '{sad_correct_result['status']}'"
    
    # Test incorrect 'س' pronunciation (Tarqiq / thin sibilant)
    sad_incorrect_result = analyze_makhraj_sad(
        "/home/backdoor/projects/iqlab-dev/tests/test_sad_incorrect.wav",
        start_sec=0.1,
        end_sec=1.1
    )
    print("\n[TEST] Incorrect 'س' (thin) result:")
    print(f"  Status:    {sad_incorrect_result['status']}")
    print(f"  Centroid:  {sad_incorrect_result.get('centroid')} Hz")
    print(f"  Message:   {sad_incorrect_result['message']}")
    assert sad_incorrect_result["status"] == "fail", f"Expected 'fail', got '{sad_incorrect_result['status']}'"
    
    print("\n✅ ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    try:
        run_tests()
    except AssertionError as e:
        print(f"\n❌ TEST FAILURE: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        sys.exit(1)
