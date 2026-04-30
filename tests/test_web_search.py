import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add examiner modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'examiner'))

from modules.web_search import search_interview_questions


class TestWebSearch(unittest.TestCase):
    """Unit tests for web_search module using Qwen WebSearch"""

    def setUp(self):
        """Set up test fixtures"""
        self.jd = "We need a Python developer with 5 years experience"
        self.company = "Tech Corp"
        self.position = "Senior Python Developer"
        self.config = {
            "web_search": {
                "enabled": True,
                "search_options": {
                    "search_strategy": "turbo"
                }
            },
            "qwen": {
                "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "api_key": "${ALIYUN_API_KEY}",
                "model": "qwen3.5-flash",
                "timeout": 30
            }
        }
        self.prompts = {
            "web_search_questions": {
                "system": "You are a helpful assistant",
                "user": "Generate search queries for {company} {position}"
            }
        }

    def test_web_search_disabled_returns_empty_list(self):
        """Test that disabled web_search returns empty list"""
        config_disabled = {
            "web_search": {
                "enabled": False
            }
        }

        result = search_interview_questions(
            jd=self.jd,
            company=self.company,
            position=self.position,
            prompts=self.prompts,
            config=config_disabled,
            limit=10
        )

        self.assertEqual(result, [])

    def test_successful_search_returns_questions(self):
        """Test successful search returns parsed questions"""
        questions_json = json.dumps([
            {"text": "What is a decorator?"},
            {"text": "Explain list comprehensions"},
            {"text": "What is SOLID?"}
        ])

        with patch('modules.web_search.call_api', return_value=questions_json):
            result = search_interview_questions(
                jd=self.jd,
                company=self.company,
                position=self.position,
                prompts=self.prompts,
                config=self.config,
                limit=10
            )

        self.assertEqual(len(result), 3)
        self.assertIn("What is a decorator?", result)
        self.assertIn("Explain list comprehensions", result)
        self.assertIn("What is SOLID?", result)

    def test_json_with_markdown_fencing(self):
        """Test parsing JSON wrapped in markdown code fences"""
        questions_json = """```json
[
    {"text": "Question 1"},
    {"text": "Question 2"}
]
```"""

        with patch('modules.web_search.call_api', return_value=questions_json):
            result = search_interview_questions(
                jd=self.jd,
                company=self.company,
                position=self.position,
                prompts=self.prompts,
                config=self.config,
                limit=10
            )

        self.assertEqual(len(result), 2)
        self.assertIn("Question 1", result)
        self.assertIn("Question 2", result)

    def test_string_list_response(self):
        """Test parsing when API returns plain string list"""
        questions_json = json.dumps([
            "What is a decorator?",
            "Explain list comprehensions",
            "What is SOLID?"
        ])

        with patch('modules.web_search.call_api', return_value=questions_json):
            result = search_interview_questions(
                jd=self.jd,
                company=self.company,
                position=self.position,
                prompts=self.prompts,
                config=self.config,
                limit=10
            )

        self.assertEqual(len(result), 3)
        self.assertIn("What is a decorator?", result)
        self.assertIn("Explain list comprehensions", result)

    def test_limit_parameter_truncates_results(self):
        """Test that limit parameter correctly truncates results"""
        questions_json = json.dumps([
            {"text": "Question 1"},
            {"text": "Question 2"},
            {"text": "Question 3"},
            {"text": "Question 4"},
            {"text": "Question 5"}
        ])

        with patch('modules.web_search.call_api', return_value=questions_json):
            result = search_interview_questions(
                jd=self.jd,
                company=self.company,
                position=self.position,
                prompts=self.prompts,
                config=self.config,
                limit=3
            )

        self.assertEqual(len(result), 3)

    def test_api_exception_returns_empty_list(self):
        """Test that API exception returns empty list gracefully"""
        with patch('modules.web_search.call_api', side_effect=Exception("API Error")):
            result = search_interview_questions(
                jd=self.jd,
                company=self.company,
                position=self.position,
                prompts=self.prompts,
                config=self.config,
                limit=10
            )

        self.assertEqual(result, [])

    def test_invalid_json_returns_empty_list(self):
        """Test that invalid JSON response returns empty list"""
        with patch('modules.web_search.call_api', return_value="Not valid JSON"):
            result = search_interview_questions(
                jd=self.jd,
                company=self.company,
                position=self.position,
                prompts=self.prompts,
                config=self.config,
                limit=10
            )

        self.assertEqual(result, [])

    def test_non_list_json_response_returns_empty_list(self):
        """Test that non-list JSON response returns empty list"""
        non_list_json = json.dumps({"error": "Something went wrong"})

        with patch('modules.web_search.call_api', return_value=non_list_json):
            result = search_interview_questions(
                jd=self.jd,
                company=self.company,
                position=self.position,
                prompts=self.prompts,
                config=self.config,
                limit=10
            )

        self.assertEqual(result, [])

    def test_empty_list_response(self):
        """Test that empty list response returns empty list"""
        empty_json = json.dumps([])

        with patch('modules.web_search.call_api', return_value=empty_json):
            result = search_interview_questions(
                jd=self.jd,
                company=self.company,
                position=self.position,
                prompts=self.prompts,
                config=self.config,
                limit=10
            )

        self.assertEqual(result, [])

    def test_call_api_parameters(self):
        """Test that call_api is called with correct parameters"""
        questions_json = json.dumps([{"text": "Test"}])

        with patch('modules.web_search.call_api', return_value=questions_json) as mock_call:
            search_interview_questions(
                jd=self.jd,
                company=self.company,
                position=self.position,
                prompts=self.prompts,
                config=self.config,
                limit=5
            )

        # Verify call_api was called with enable_search=True
        mock_call.assert_called_once()
        args, kwargs = mock_call.call_args
        self.assertTrue(kwargs.get('enable_search'))

    def test_mixed_dict_and_string_questions(self):
        """Test handling mixed format responses (dicts and strings)"""
        questions_json = json.dumps([
            {"text": "Question 1"},
            "Question 2",
            {"text": "Question 3"}
        ])

        with patch('modules.web_search.call_api', return_value=questions_json):
            result = search_interview_questions(
                jd=self.jd,
                company=self.company,
                position=self.position,
                prompts=self.prompts,
                config=self.config,
                limit=10
            )

        self.assertEqual(len(result), 3)
        self.assertIn("Question 1", result)
        self.assertIn("Question 2", result)
        self.assertIn("Question 3", result)

    def test_limit_zero_returns_empty_list(self):
        """Test that limit=0 returns empty list"""
        questions_json = json.dumps([{"text": "Question"}])

        with patch('modules.web_search.call_api', return_value=questions_json):
            result = search_interview_questions(
                jd=self.jd,
                company=self.company,
                position=self.position,
                prompts=self.prompts,
                config=self.config,
                limit=0
            )

        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()
