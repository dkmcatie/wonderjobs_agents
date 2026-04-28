import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add examiner modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'examiner'))

from modules.query_generator import generate_search_queries


class TestQueryGenerator(unittest.TestCase):
    """Unit tests for query_generator module"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            "qwen": {
                "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "api_key": "test-api-key",
                "model": "qwen-omni-mini",
                "timeout": 30
            }
        }
        self.prompts = {
            "generate_search_queries": {
                "system": "你是一个面试题搜索专家。",
                "user": "请为以下岗位生成搜索词。公司: {company}\n岗位: {position}\n岗位描述:\n{jd}"
            }
        }
        self.jd = "需要Python和Django经验，5年以上Web开发经验"
        self.company = "TechCorp"
        self.position = "Senior Python Engineer"

    def test_generate_search_queries_success(self):
        """Test successful query generation returning 3 queries"""
        mock_response = MagicMock()
        expected_queries = ["TechCorp Python工程师面试题", "Senior Django开发面试题", "Web开发面试经验分享"]
        mock_response.return_value = '["TechCorp Python工程师面试题", "Senior Django开发面试题", "Web开发面试经验分享"]'

        with patch('modules.query_generator.call_api', return_value=mock_response.return_value):
            result = generate_search_queries(
                self.jd, self.company, self.position, self.prompts, self.config
            )

        self.assertEqual(len(result), 3)
        self.assertEqual(result, expected_queries)

    def test_generate_search_queries_with_markdown_json_format(self):
        """Test parsing JSON wrapped in markdown code blocks"""
        mock_response = '```json\n["搜索词1", "搜索词2", "搜索词3"]\n```'

        with patch('modules.query_generator.call_api', return_value=mock_response):
            result = generate_search_queries(
                self.jd, self.company, self.position, self.prompts, self.config
            )

        self.assertEqual(len(result), 3)
        self.assertIn("搜索词1", result)
        self.assertIn("搜索词2", result)
        self.assertIn("搜索词3", result)

    def test_generate_search_queries_invalid_json_dict(self):
        """Test handling of invalid JSON response (dict instead of list)"""
        mock_response = '{"query": "搜索词"}'

        with patch('modules.query_generator.call_api', return_value=mock_response):
            result = generate_search_queries(
                self.jd, self.company, self.position, self.prompts, self.config
            )

        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)

    def test_generate_search_queries_missing_prompt(self):
        """Test handling of missing prompt definition"""
        empty_prompts = {}

        with patch('modules.query_generator.call_api') as mock_call:
            result = generate_search_queries(
                self.jd, self.company, self.position, empty_prompts, self.config
            )

        # Should not call API if prompt is missing
        mock_call.assert_not_called()
        self.assertEqual(len(result), 0)

    def test_generate_search_queries_none_prompts(self):
        """Test handling of None prompts"""
        with patch('modules.query_generator.call_api') as mock_call:
            result = generate_search_queries(
                self.jd, self.company, self.position, None, self.config
            )

        # Should not call API if prompts is None
        mock_call.assert_not_called()
        self.assertEqual(len(result), 0)

    def test_generate_search_queries_json_decode_error(self):
        """Test handling of JSON parse error"""
        mock_response = 'this is not json'

        with patch('modules.query_generator.call_api', return_value=mock_response):
            result = generate_search_queries(
                self.jd, self.company, self.position, self.prompts, self.config
            )

        self.assertEqual(len(result), 0)

    def test_generate_search_queries_api_exception(self):
        """Test handling of API call exception"""
        with patch('modules.query_generator.call_api', side_effect=Exception("API error")):
            result = generate_search_queries(
                self.jd, self.company, self.position, self.prompts, self.config
            )

        self.assertEqual(len(result), 0)

    def test_generate_search_queries_returns_empty_list(self):
        """Test function returns List[str] on error"""
        mock_response = '{"invalid": "format"}'

        with patch('modules.query_generator.call_api', return_value=mock_response):
            result = generate_search_queries(
                self.jd, self.company, self.position, self.prompts, self.config
            )

        # Should always return a list, even on error
        self.assertIsInstance(result, list)

    def test_generate_search_queries_prompt_template_formatting(self):
        """Test that prompt template is correctly formatted with parameters"""
        mock_response = '["query1", "query2"]'

        with patch('modules.query_generator.call_api') as mock_call:
            generate_search_queries(
                self.jd, self.company, self.position, self.prompts, self.config
            )

        # Verify call_api was called with correctly formatted user prompt
            call_args = mock_call.call_args
            user_prompt = call_args[0][1]
            self.assertIn(self.company, user_prompt)
            self.assertIn(self.position, user_prompt)
            self.assertIn(self.jd, user_prompt)

    def test_generate_search_queries_returns_strings(self):
        """Test that all elements in returned list are strings"""
        mock_response = '["query1", "query2", "query3"]'

        with patch('modules.query_generator.call_api', return_value=mock_response):
            result = generate_search_queries(
                self.jd, self.company, self.position, self.prompts, self.config
            )

        for query in result:
            self.assertIsInstance(query, str)

    def test_generate_search_queries_various_markdown_formats(self):
        """Test handling of variations in markdown JSON format"""
        test_cases = [
            '```json\n["q1", "q2"]\n```',
            '```json\n["q1", "q2"]```',
            '```json["q1", "q2"]```',
            '```json\n\n["q1", "q2"]\n\n```'
        ]

        for mock_response in test_cases:
            with patch('modules.query_generator.call_api', return_value=mock_response):
                result = generate_search_queries(
                    self.jd, self.company, self.position, self.prompts, self.config
                )
                self.assertEqual(len(result), 2, f"Failed for format: {repr(mock_response)}")

    def test_generate_search_queries_empty_list(self):
        """Test handling of empty JSON array response"""
        mock_response = '[]'

        with patch('modules.query_generator.call_api', return_value=mock_response):
            result = generate_search_queries(
                self.jd, self.company, self.position, self.prompts, self.config
            )

        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)

    def test_generate_search_queries_single_query(self):
        """Test handling of single query in list"""
        mock_response = '["single-query"]'

        with patch('modules.query_generator.call_api', return_value=mock_response):
            result = generate_search_queries(
                self.jd, self.company, self.position, self.prompts, self.config
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "single-query")

    def test_generate_search_queries_max_count(self):
        """Test handling of maximum expected queries (5)"""
        mock_response = '["q1", "q2", "q3", "q4", "q5"]'

        with patch('modules.query_generator.call_api', return_value=mock_response):
            result = generate_search_queries(
                self.jd, self.company, self.position, self.prompts, self.config
            )

        self.assertEqual(len(result), 5)

    def test_generate_search_queries_with_special_characters(self):
        """Test handling queries with special characters and unicode"""
        mock_response = '["Python/Django工程师", "前端+后端全栈", "面试题:AI相关"]'

        with patch('modules.query_generator.call_api', return_value=mock_response):
            result = generate_search_queries(
                self.jd, self.company, self.position, self.prompts, self.config
            )

        self.assertEqual(len(result), 3)
        self.assertIn("Python/Django工程师", result)
        self.assertIn("前端+后端全栈", result)
        self.assertIn("面试题:AI相关", result)


if __name__ == '__main__':
    unittest.main()
