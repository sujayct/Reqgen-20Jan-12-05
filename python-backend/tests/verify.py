
import sys
import os
from unittest.mock import MagicMock, patch

# 1. Setup Environment
print("--- Setting up environment ---")
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../')

# Mock system dependencies
sys.modules['whisper'] = MagicMock()
sys.modules['pyannote'] = MagicMock()
sys.modules['pyannote.audio'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['gc'] = MagicMock()

# Configure Torch Mocks to avoid format errors
sys.modules['torch'].cuda.is_available.return_value = False # Force CPU path to avoid GPU print logic
# OR set values for GPU path:
# sys.modules['torch'].cuda.get_device_properties.return_value.total_memory = 16 * 1e9

# Mock Config
import config
config.HUGGINGFACE_TOKEN = "fake_token_123"
config.MIN_SPEAKERS = 1
config.MAX_SPEAKERS = 5

# Mock shutil.which to pass ffmpeg check
with patch('shutil.which', return_value='/usr/bin/ffmpeg'):
    print("--- Importing document_generator ---")
    try:
        import document_generator
        print("✅ Import successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("--- Instantiating Generator ---")
    try:
        # Mock Pipeline inside document_generator
        with patch('document_generator.Pipeline') as MockPipeline:
            generator = document_generator.SmartT5LargeDocumentGenerator(whisper_model="base", t5_model="base")
            print("✅ Instantiation successful")
            
            # Verify Pipeline loaded
            if generator.diarization_pipeline:
                print("✅ Diarization pipeline loaded")
            else:
                print("❌ Diarization pipeline NOT loaded")
                
    except Exception as e:
        print(f"❌ Instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("--- Testing Merge Logic ---")
    try:
        # Use the generator instance created above? 
        # No, create new one or reuse.
        # But we need to keep the patch active for initialization.
        pass 
    except Exception:
        pass

# Re-instantiate for logic tests (outside the init patch scope if needed, or just mock manually)
# Since __init__ runs on instantiation, we need to patch shutil.which globally or around init.

def run_logic_test():
    with patch('shutil.which', return_value='/usr/bin/ffmpeg'), \
         patch('document_generator.Pipeline'):
        
        generator = document_generator.SmartT5LargeDocumentGenerator(whisper_model="base", t5_model="base")
        
        # Test Format
        print("--- Testing Format ---")
        merged = [
            {'speaker': 'Speaker 1', 'text': 'Hello'},
            {'speaker': 'Speaker 2', 'text': 'Hi'}
        ]
        formatted = generator.format_transcript_with_speakers(merged)
        print(f"Formatted: {formatted}")
        if "Speaker 1: Hello" in formatted and "Speaker 2: Hi" in formatted:
            print("✅ Format Logic Passed")
        else:
            print("❌ Format Logic Failed")

        # Test Merge
        print("--- Testing Merge ---")
        w_segs = [{'start':0, 'end':5, 'text':'A'}]
        s_segs = [{'start':0, 'end':5, 'speaker':'SPK_1'}]
        merged_res = generator.merge_transcription_with_diarization(w_segs, s_segs)
        print(f"Merged: {merged_res}")
        if len(merged_res) > 0 and 'Speaker' in merged_res[0]['speaker']:
            print("✅ Merge Logic Passed")
        else:
            print("❌ Merge Logic Failed")

print("--- Running Logic Tests ---")
try:
    run_logic_test()
    print("ALL TESTS PASSED")
except Exception as e:
    print(f"❌ Logic Tests Failed: {e}")
    import traceback
    traceback.print_exc()
