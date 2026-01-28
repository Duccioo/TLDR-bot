import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add src to python path
sys.path.append(os.path.join(os.getcwd(), "src"))

# Mock environment variables before importing modules that use them
os.environ["GEMINI_API_KEY"] = "fake_key"
os.environ["GROQ_API_KEY"] = "fake_key"
os.environ["OPENROUTER_API_KEY"] = "fake_key"
os.environ["TELEGRAM_BOT_TOKEN"] = "fake_token"


# Mock google.genai since we might not have it or want to use real network
sys.modules["google.genai"] = MagicMock()
sys.modules["google.genai.types"] = MagicMock()
sys.modules["dotenv"] = MagicMock()

# Also mock trafilatura and curl_cffi as they are imported by core.extractor -> core.summarizer
sys.modules["trafilatura"] = MagicMock()
sys.modules["curl_cffi"] = MagicMock()
sys.modules["curl_cffi.requests"] = MagicMock()

from core import summarizer

class TestSummarizer(unittest.TestCase):
    def test_call_gemini_api_none_text(self):
        """Test _call_gemini_api when response.text is None."""
        
        # Mock genai.Client
        mock_client = MagicMock()
        mock_response = MagicMock()
        
        # CASE 1: response.text is explicitly None (and hasattr returns True)
        mock_response.text = None
        # Ensure hasattr(response, "text") is True (default for MagicMock)
        
        # Configure client to return this response
        mock_client.models.generate_content.return_value = mock_response
        
        with patch("google.genai.Client", return_value=mock_client):
            result = summarizer._call_gemini_api(
                system_instruction="sys",
                user_prompt="prompt",
                model_name="gemini-1.5-flash"
            )
            
            print(f"Result for None response.text: {result}")
            # Expected: handled error, NOT crash
            
    def test_call_gemini_api_text_none_candidates_none(self):
        """Test when everything is None, checking for crashes."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        
        # response.text is None
        mock_response.text = None
        # response.candidates is None
        mock_response.candidates = None
        
        mock_client.models.generate_content.return_value = mock_response
        
        with patch("google.genai.Client", return_value=mock_client):
            try:
                result = summarizer._call_gemini_api("sys", "prompt", "model")
                print(f"Result for all None: {result}")
            except AttributeError as e:
                print(f"Caught expected crash? {e}")

if __name__ == "__main__":
    unittest.main()
