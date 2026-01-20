
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent dir to path to import document_generator
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../')

# Mock heavy libraries BEFORE importing document_generator
sys.modules['whisper'] = MagicMock()
sys.modules['pyannote'] = MagicMock()
sys.modules['pyannote.audio'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['gc'] = MagicMock()

# Mock config
import config
config.HUGGINGFACE_TOKEN = "fake_token"

from document_generator import SmartT5LargeDocumentGenerator

class TestDiarizationLogic(unittest.TestCase):
    
    @patch('shutil.which')
    @patch('document_generator.Pipeline')
    def test_initialization(self, mock_pipeline, mock_which):
        """Test that diarization pipeline is loaded if token is present"""
        mock_which.return_value = '/usr/bin/ffmpeg' # Mock ffmpeg existence
        generator = SmartT5LargeDocumentGenerator(whisper_model="base", t5_model="base")
        
        # Check if pipeline was loaded
        mock_pipeline.from_pretrained.assert_called_with(
            "pyannote/speaker-diarization-3.1",
            use_auth_token="fake_token"
        )
        self.assertIsNotNone(generator.diarization_pipeline)

    @patch('shutil.which')
    def test_merge_logic(self, mock_which):
        """Test the merging of whisper segments and speaker segments"""
        mock_which.return_value = '/usr/bin/ffmpeg'
        generator = SmartT5LargeDocumentGenerator(whisper_model="base", t5_model="base")
        
        whisper_segments = [
            {'start': 0.0, 'end': 5.0, 'text': 'Hello world'},
            {'start': 5.5, 'end': 10.0, 'text': 'How are you?'}
        ]
        
        speaker_segments = [
            {'start': 0.0, 'end': 4.0, 'speaker': 'SPEAKER_00'},
            {'start': 6.0, 'end': 10.0, 'speaker': 'SPEAKER_01'}
        ]
        
        merged = generator.merge_transcription_with_diarization(whisper_segments, speaker_segments)
        
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0]['speaker'], 'Speaker 1') # SPEAKER_00 -> Speaker 1
        self.assertEqual(merged[1]['speaker'], 'Speaker 2') # SPEAKER_01 -> Speaker 2
        
    @patch('shutil.which')
    def test_format_transcript(self, mock_which):
        """Test formatting of transcript"""
        mock_which.return_value = '/usr/bin/ffmpeg'
        generator = SmartT5LargeDocumentGenerator(whisper_model="base", t5_model="base")
        
        merged = [
            {'speaker': 'Speaker 1', 'text': 'Hello'},
            {'speaker': 'Speaker 1', 'text': 'world'},
            {'speaker': 'Speaker 2', 'text': 'Hi there'}
        ]
        
        formatted = generator.format_transcript_with_speakers(merged)
        
        expected = "Speaker 1: Hello world\n\nSpeaker 2: Hi there"
        self.assertEqual(formatted, expected)

if __name__ == '__main__':
    # Manual test runner to see tracebacks
    import traceback
    
    t = TestDiarizationLogic()
    
    print("\n--- Running test_initialization ---")
    try:
        # Patching manually since we are not using decorators here
        with patch('shutil.which', return_value='/usr/bin/ffmpeg'), \
             patch('document_generator.Pipeline') as mock_pipeline:
            t.test_initialization(mock_pipeline, MagicMock(return_value='/usr/bin/ffmpeg'))
        print("PASS")
    except Exception:
        traceback.print_exc()

    print("\n--- Running test_merge_logic ---")
    try:
        with patch('shutil.which', return_value='/usr/bin/ffmpeg'):
             # Note: test_merge_logic signature in class needs to match what we call here or remove patch arg if unused in body
             # But the method expects an arg because of @patch decorator.
             # Easier way: instantiate loader?
             # Let's just create a quick hacks since unittest runner is failing us.
             pass
    except Exception:
        traceback.print_exc()
        
    # Revert to unittest but with buffer=False might help?
    unittest.main(verbosity=2, buffer=False)
