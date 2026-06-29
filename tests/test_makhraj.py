import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.makhraj import analyze_makhraj_ha
from tests.generate_test_audio import create_test_suite_audio

def run_tests():
    print("=== Running Makhraj DSP Unit Tests ===")
    
    # 1. Generate synthetic audio files if they don't exist
    create_test_suite_audio()
    
    # 2. Test correct 'ح' pronunciation
    # Word starts at 0.1s and ends around 1.0s
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
    
    # 3. Test incorrect 'ه' pronunciation
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
