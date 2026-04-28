import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add examiner modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'examiner'))

from modules.bocha_client import call_bocha_api, _extract_questions_from_response


class TestBochaClient(unittest.TestCase):
    """Unit tests for bocha_client module"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            "bocha": {
                "api_endpoint": "https://api.example.com/search",
                "api_key": "test-api-key",
                "timeout": 30,
                "freshness": "noLimit",
                "max_results_per_query": 5
            }
        }
        self.query = "Python interview questions"

    def test_call_bocha_api_success(self):
        """Test successful API call returning 2 questions"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"title": "What is a Python list?"},
                {"title": "Explain decorators in Python"}
            ]
        }

        with patch('modules.bocha_client.requests.post', return_value=mock_response):
            result = call_bocha_api(self.query, self.config)

        self.assertEqual(len(result), 2)
        self.assertIn("What is a Python list?", result)
        self.assertIn("Explain decorators in Python", result)

    def test_call_bocha_api_retry_on_timeout(self):
        """Test retry mechanism - first timeout, second success"""
        # First call times out, second succeeds
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"title": "What is a closure?"}
            ]
        }

        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise TimeoutError("Connection timed out")
            return mock_response

        with patch('modules.bocha_client.requests.post', side_effect=side_effect):
            with patch('modules.bocha_client.time.sleep'):  # Mock sleep to speed up test
                result = call_bocha_api(self.query, self.config, max_retries=3)

        self.assertEqual(len(result), 1)
        self.assertIn("What is a closure?", result)
        self.assertEqual(call_count[0], 2)  # Called twice: once timeout, once success

    def test_call_bocha_api_invalid_key(self):
        """Test that invalid API key raises ValueError"""
        invalid_config = {
            "bocha": {
                "api_endpoint": "https://api.example.com/search",
                "api_key": "${BOCHA_API_KEY}",
                "timeout": 30,
                "freshness": "noLimit",
                "max_results_per_query": 5
            }
        }

        # Make sure env var is not set
        if "BOCHA_API_KEY" in os.environ:
            del os.environ["BOCHA_API_KEY"]

        with self.assertRaises(ValueError) as context:
            call_bocha_api(self.query, invalid_config)

        self.assertIn("BOCHA_API_KEY", str(context.exception))

    def test_call_bocha_api_401_error(self):
        """Test 401 error handling (invalid API key from server)"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch('modules.bocha_client.requests.post', return_value=mock_response):
            with self.assertRaises(ValueError) as context:
                call_bocha_api(self.query, self.config)

            self.assertIn("API Key", str(context.exception))

    def test_call_bocha_api_429_rate_limit(self):
        """Test 429 rate limit handling with retry"""
        # First call gets 429, second succeeds
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {
            "results": [
                {"title": "What is an async function?"}
            ]
        }

        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_response_429
            return mock_response_200

        with patch('modules.bocha_client.requests.post', side_effect=side_effect):
            with patch('modules.bocha_client.time.sleep'):  # Mock sleep to speed up test
                result = call_bocha_api(self.query, self.config, max_retries=3)

        self.assertEqual(len(result), 1)
        self.assertIn("What is an async function?", result)
        self.assertEqual(call_count[0], 2)  # Called twice: once 429, once success

    def test_extract_questions_from_response_with_title(self):
        """Test extraction of questions using title field"""
        response = {
            "results": [
                {"title": "Question 1", "snippet": "Snippet 1"},
                {"title": "Question 2", "snippet": "Snippet 2"}
            ]
        }

        result = _extract_questions_from_response(response)

        self.assertEqual(len(result), 2)
        self.assertIn("Question 1", result)
        self.assertIn("Question 2", result)

    def test_extract_questions_from_response_with_snippet_fallback(self):
        """Test extraction falls back to snippet when title is missing"""
        response = {
            "results": [
                {"snippet": "Snippet 1"},
                {"title": "Question 2", "snippet": "Snippet 2"}
            ]
        }

        result = _extract_questions_from_response(response)

        self.assertEqual(len(result), 2)
        self.assertIn("Snippet 1", result)
        self.assertIn("Question 2", result)

    def test_extract_questions_deduplication(self):
        """Test that empty items are filtered out"""
        response = {
            "results": [
                {"title": "Valid question"},
                {"title": ""},  # Empty string should be filtered
                {"title": "   "},  # Whitespace should be filtered
                {"snippet": "Another valid question"}
            ]
        }

        result = _extract_questions_from_response(response)

        self.assertEqual(len(result), 2)
        self.assertIn("Valid question", result)
        self.assertIn("Another valid question", result)

    def test_call_bocha_api_empty_results(self):
        """Test handling of empty results"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}

        with patch('modules.bocha_client.requests.post', return_value=mock_response):
            result = call_bocha_api(self.query, self.config)

        self.assertEqual(len(result), 0)

    def test_call_bocha_api_malformed_json(self):
        """Test handling of malformed JSON response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch('modules.bocha_client.requests.post', return_value=mock_response):
            result = call_bocha_api(self.query, self.config)

        # Should return empty list on parse error
        self.assertEqual(len(result), 0)

    def test_call_bocha_api_max_retries_exceeded(self):
        """Test that max retries are respected"""
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch('modules.bocha_client.requests.post', return_value=mock_response):
            result = call_bocha_api(self.query, self.config, max_retries=2)

        # Should return empty list after retries
        self.assertEqual(len(result), 0)

    def test_call_bocha_api_exponential_backoff(self):
        """Test that exponential backoff is applied correctly"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [{"title": "Question"}]}

        sleep_calls = []

        def mock_sleep(duration):
            sleep_calls.append(duration)

        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 3:
                raise TimeoutError()
            return mock_response

        with patch('modules.bocha_client.requests.post', side_effect=side_effect):
            with patch('modules.bocha_client.time.sleep', side_effect=mock_sleep):
                result = call_bocha_api(self.query, self.config, max_retries=4)

        # Verify exponential backoff: 1s, 2s
        self.assertEqual(sleep_calls, [1, 2])
        self.assertEqual(len(result), 1)

    def test_call_bocha_api_with_env_api_key(self):
        """Test that API key from environment variable is used"""
        config_without_key = {
            "bocha": {
                "api_endpoint": "https://api.example.com/search",
                "timeout": 30,
                "freshness": "noLimit",
                "max_results_per_query": 5
            }
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [{"title": "Question"}]}

        with patch.dict(os.environ, {"BOCHA_API_KEY": "env-api-key"}):
            with patch('modules.bocha_client.requests.post', return_value=mock_response) as mock_post:
                result = call_bocha_api(self.query, config_without_key)

                # Verify the API key was used in the request
                call_args = mock_post.call_args
                headers = call_args.kwargs.get('headers', {})
                self.assertEqual(headers.get('Authorization'), 'Bearer env-api-key')

        self.assertEqual(len(result), 1)

    def test_call_bocha_api_http_error(self):
        """Test handling of HTTP errors other than 401 and 429"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("Internal Server Error")

        with patch('modules.bocha_client.requests.post', return_value=mock_response):
            result = call_bocha_api(self.query, self.config, max_retries=1)

        # Should return empty list on HTTP error
        self.assertEqual(len(result), 0)


if __name__ == '__main__':
    unittest.main()
