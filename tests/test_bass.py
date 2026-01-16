import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Mock pydub before import
sys.modules["pydub"] = MagicMock()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.bass_service import BassService

class TestBassService(unittest.TestCase):
    def setUp(self):
        self.service = BassService(temp_dir="/tmp/test_autoplex_bass")

    def tearDown(self):
        self.service.cleanup()

    @patch("services.bass_service.subprocess.run")
    @patch("services.bass_service.AudioSegment")
    def test_process_track(self, mock_audio_segment, mock_subprocess):
        # Mock inputs
        input_file = "/tmp/test_autoplex_bass/test_song.flac"
        
        # Mock AudioSegment loading and operations
        mock_segment_instance = MagicMock()
        mock_audio_segment.from_wav.return_value = mock_segment_instance
        mock_segment_instance.__add__.return_value = mock_segment_instance # Mock boosting
        mock_segment_instance.__sub__.return_value = mock_segment_instance # Mock normalization reduction
        mock_segment_instance.overlay.return_value = mock_segment_instance # Mock mixing
        mock_segment_instance.max_dBFS = -3.0  # Mock peak amplitude (no normalization needed)
        
        # Run method
        output_path = self.service.process_track(input_file)
        
        # Assertions
        # 1. Check Demucs call
        mock_subprocess.assert_called_once()
        args = mock_subprocess.call_args[0][0]
        self.assertIn("demucs", args)
        self.assertIn(input_file, args)
        
        # 2. Check AudioSegment calls
        # Should load 4 stems
        self.assertEqual(mock_audio_segment.from_wav.call_count, 4)
        
        # 3. Check Export
        mock_segment_instance.export.assert_called_once()
        self.assertTrue(output_path.endswith("(Bass Boosted).mp3"))

    @patch("services.bass_service.subprocess.run")
    @patch("services.bass_service.AudioSegment")
    def test_process_track_with_normalization(self, mock_audio_segment, mock_subprocess):
        """Test that loud audio gets normalized to prevent clipping."""
        input_file = "/tmp/test_autoplex_bass/test_song.flac"

        # Mock AudioSegment
        mock_segment_instance = MagicMock()
        mock_audio_segment.from_wav.return_value = mock_segment_instance
        mock_segment_instance.__add__.return_value = mock_segment_instance
        mock_segment_instance.__sub__.return_value = mock_segment_instance
        mock_segment_instance.overlay.return_value = mock_segment_instance
        mock_segment_instance.max_dBFS = 2.0  # Clipping! Needs normalization

        # Run method
        output_path = self.service.process_track(input_file)

        # Should have called subtraction for normalization (2.0 + 1.0 = 3.0 dB reduction)
        mock_segment_instance.__sub__.assert_called_with(3.0)

if __name__ == '__main__':
    unittest.main()
