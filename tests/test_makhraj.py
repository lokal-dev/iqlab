import os
import sys

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.makhraj import analyze_makhraj_ha, analyze_makhraj_ayn, analyze_makhraj_sad, analyze_makhraj_kha, analyze_makhraj_dhal
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
        end_sec=0.65
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
        end_sec=0.65
    )
    print("\n[TEST] Incorrect 'س' (thin) result:")
    print(f"  Status:    {sad_incorrect_result['status']}")
    print(f"  Centroid:  {sad_incorrect_result.get('centroid')} Hz")
    print(f"  Message:   {sad_incorrect_result['message']}")
    assert sad_incorrect_result["status"] == "fail", f"Expected 'fail', got '{sad_incorrect_result['status']}'"
    
    # ─── SECTION 4: 'خ' vs 'ك' / 'ه' (Kha vs Kaf/Haa) ───
    print("\n--- Testing 'خ' vs 'ك' / 'ه' (Kha vs Kaf/Haa) ---")
    
    # Test correct 'خ'
    kha_correct = analyze_makhraj_kha(
        "/home/backdoor/projects/iqlab-dev/tests/test_kha_correct.wav",
        start_sec=0.1,
        end_sec=0.65
    )
    print("\n[TEST] Correct 'خ' result:")
    print(f"  Status:  {kha_correct['status']}")
    print(f"  PAER:    {kha_correct.get('paer')}")
    print(f"  Ratio:   {kha_correct.get('ratio')}")
    print(f"  Message: {kha_correct['message']}")
    assert kha_correct["status"] == "pass", f"Expected 'pass', got '{kha_correct['status']}'"
    
    # Test incorrect 'ك' (sounds like Kaf - stop plosive)
    kha_incorrect_kaf = analyze_makhraj_kha(
        "/home/backdoor/projects/iqlab-dev/tests/test_kha_incorrect_kaf.wav",
        start_sec=0.1,
        end_sec=0.65
    )
    print("\n[TEST] Incorrect 'ك' (sounds like Kaf) result:")
    print(f"  Status:  {kha_incorrect_kaf['status']}")
    print(f"  PAER:    {kha_incorrect_kaf.get('paer')}")
    print(f"  Message: {kha_incorrect_kaf['message']}")
    assert kha_incorrect_kaf["status"] == "fail", f"Expected 'fail', got '{kha_incorrect_kaf['status']}'"
    
    # Test incorrect 'ه' (sounds like Haa - glottal breath)
    kha_incorrect_haa = analyze_makhraj_kha(
        "/home/backdoor/projects/iqlab-dev/tests/test_kha_incorrect_haa.wav",
        start_sec=0.1,
        end_sec=0.65
    )
    print("\n[TEST] Incorrect 'ه' (sounds like Haa) result:")
    print(f"  Status:  {kha_incorrect_haa['status']}")
    print(f"  Ratio:   {kha_incorrect_haa.get('ratio')}")
    print(f"  Message: {kha_incorrect_haa['message']}")
    assert kha_incorrect_haa["status"] == "fail", f"Expected 'fail', got '{kha_incorrect_haa['status']}'"
    
    # ─── SECTION 5: 'ذ' vs 'ز' / 'د' (Dhal vs Zay/Dal) ───
    print("\n--- Testing 'ذ' vs 'ز' / 'د' (Dhal vs Zay/Dal) ---")
    
    # Test correct 'ذ'
    dhal_correct = analyze_makhraj_dhal(
        "/home/backdoor/projects/iqlab-dev/tests/test_dhal_correct.wav",
        start_sec=0.1,
        end_sec=0.60
    )
    print("\n[TEST] Correct 'ذ' result:")
    print(f"  Status:   {dhal_correct['status']}")
    print(f"  PAER:     {dhal_correct.get('paer')}")
    print(f"  Desisan:  {dhal_correct.get('energy_ratio')}")
    print(f"  Message:  {dhal_correct['message']}")
    assert dhal_correct["status"] == "pass", f"Expected 'pass', got '{dhal_correct['status']}'"
    
    # Test incorrect 'د' (sounds like Dal - stop plosive)
    dhal_incorrect_dal = analyze_makhraj_dhal(
        "/home/backdoor/projects/iqlab-dev/tests/test_dhal_incorrect_dal.wav",
        start_sec=0.1,
        end_sec=0.60
    )
    print("\n[TEST] Incorrect 'د' (sounds like Dal) result:")
    print(f"  Status:   {dhal_incorrect_dal['status']}")
    print(f"  PAER:     {dhal_incorrect_dal.get('paer')}")
    print(f"  Message:  {dhal_incorrect_dal['message']}")
    assert dhal_incorrect_dal["status"] == "fail", f"Expected 'fail', got '{dhal_incorrect_dal['status']}'"
    
    # Test incorrect 'ز' (sounds like Zay - loud sibilant)
    dhal_incorrect_zay = analyze_makhraj_dhal(
        "/home/backdoor/projects/iqlab-dev/tests/test_dhal_incorrect_zay.wav",
        start_sec=0.1,
        end_sec=0.60
    )
    print("\n[TEST] Incorrect 'ز' (sounds like Zay) result:")
    print(f"  Status:   {dhal_incorrect_zay['status']}")
    print(f"  Desisan:  {dhal_incorrect_zay.get('energy_ratio')}")
    print(f"  Message:  {dhal_incorrect_zay['message']}")
    assert dhal_incorrect_zay["status"] == "fail", f"Expected 'fail', got '{dhal_incorrect_zay['status']}'"
    
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
