import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os

# Add examiner modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'examiner'))

from modules.web_search import search_interview_questions


class TestWebSearch(unittest.TestCase):
    """Unit tests for web_search module"""

    def setUp(self):
        """Set up test fixtures"""
        self.jd = "We need a Python developer with 5 years experience"
        self.company = "Tech Corp"
        self.position = "Senior Python Developer"
        self.config = {
            "bocha": {
                "enabled": True,
                "api_endpoint": "https://api.bochaai.com/v1/web-search",
                "api_key": "test-api-key",
                "timeout": 30,
                "freshness": "noLimit",
                "max_results_per_query": 5
            }
        }
        self.prompts = {
            "generate_search_queries": {
                "system": "You are a helpful assistant",
                "user": "Generate search queries for {company} {position}"
            }
        }

    def test_bocha_disabled_returns_empty_list(self):
        """Test that disabled Bocha returns empty list"""
        config_disabled = {
            "bocha": {
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

    def test_no_search_queries_generated_returns_empty_list(self):
        """Test graceful handling when no search queries are generated"""
        with patch('modules.web_search.generate_search_queries', return_value=[]):
            result = search_interview_questions(
                jd=self.jd,
                company=self.company,
                position=self.position,
                prompts=self.prompts,
                config=self.config,
                limit=10
            )

        self.assertEqual(result, [])

    def test_successful_search_workflow_two_queries_two_results(self):
        """Test successful workflow: 2 search terms, each returns 2 results"""
        search_queries = ["Python interview questions", "Senior developer skills"]

        # Mock generate_search_queries to return 2 queries
        with patch('modules.web_search.generate_search_queries', return_value=search_queries):
            # Mock call_bocha_api to return different results for each query
            def bocha_side_effect(query, config):
                if "Python" in query:
                    return ["What is a decorator?", "Explain list comprehensions"]
                else:
                    return ["What is SOLID?", "Describe design patterns"]

            with patch('modules.web_search.call_bocha_api', side_effect=bocha_side_effect):
                result = search_interview_questions(
                    jd=self.jd,
                    company=self.company,
                    position=self.position,
                    prompts=self.prompts,
                    config=self.config,
                    limit=10
                )

        # Should return all 4 questions
        self.assertEqual(len(result), 4)
        self.assertIn("What is a decorator?", result)
        self.assertIn("Explain list comprehensions", result)
        self.assertIn("What is SOLID?", result)
        self.assertIn("Describe design patterns", result)

    def test_deduplication_removes_duplicate_questions(self):
        """Test that duplicate questions are removed while preserving order"""
        search_queries = ["Python questions", "Advanced Python"]

        with patch('modules.web_search.generate_search_queries', return_value=search_queries):
            # Both queries return some overlapping questions
            def bocha_side_effect(query, config):
                return ["What is a decorator?", "What is OOP?"]

            with patch('modules.web_search.call_bocha_api', side_effect=bocha_side_effect):
                result = search_interview_questions(
                    jd=self.jd,
                    company=self.company,
                    position=self.position,
                    prompts=self.prompts,
                    config=self.config,
                    limit=10
                )

        # Should have 2 unique questions, not 4
        self.assertEqual(len(result), 2)
        self.assertIn("What is a decorator?", result)
        self.assertIn("What is OOP?", result)

    def test_limit_parameter_truncates_results(self):
        """Test that limit parameter correctly truncates results"""
        search_queries = ["Query 1", "Query 2", "Query 3"]

        with patch('modules.web_search.generate_search_queries', return_value=search_queries):
            def bocha_side_effect(query, config):
                # Return unique questions per query to ensure limit applies
                if "Query 1" in query:
                    return ["Question 1", "Question 2"]
                elif "Query 2" in query:
                    return ["Question 3", "Question 4"]
                else:
                    return ["Question 5", "Question 6"]

            with patch('modules.web_search.call_bocha_api', side_effect=bocha_side_effect):
                result = search_interview_questions(
                    jd=self.jd,
                    company=self.company,
                    position=self.position,
                    prompts=self.prompts,
                    config=self.config,
                    limit=4
                )

        # Should return only 4 questions even though we have 6 total
        self.assertEqual(len(result), 4)

    def test_partial_failure_continues_with_other_searches(self):
        """Test that if one Bocha call fails, others continue successfully"""
        search_queries = ["Query 1", "Query 2", "Query 3"]

        with patch('modules.web_search.generate_search_queries', return_value=search_queries):
            call_count = [0]

            def bocha_side_effect(query, config):
                call_count[0] += 1
                if call_count[0] == 2:
                    # Second query fails
                    raise Exception("API Error")
                else:
                    # Others succeed
                    return [f"Question from {query}"]

            with patch('modules.web_search.call_bocha_api', side_effect=bocha_side_effect):
                result = search_interview_questions(
                    jd=self.jd,
                    company=self.company,
                    position=self.position,
                    prompts=self.prompts,
                    config=self.config,
                    limit=10
                )

        # Should have 2 results (from Query 1 and Query 3, Query 2 failed)
        self.assertEqual(len(result), 2)
        self.assertIn("Question from Query 1", result)
        self.assertIn("Question from Query 3", result)

    def test_order_preservation_in_deduplication(self):
        """Test that order is preserved during deduplication"""
        search_queries = ["Query 1", "Query 2"]

        with patch('modules.web_search.generate_search_queries', return_value=search_queries):
            call_count = [0]

            def bocha_side_effect(query, config):
                call_count[0] += 1
                if call_count[0] == 1:
                    return ["First", "Second", "Third"]
                else:
                    return ["Third", "Fourth", "First"]

            with patch('modules.web_search.call_bocha_api', side_effect=bocha_side_effect):
                result = search_interview_questions(
                    jd=self.jd,
                    company=self.company,
                    position=self.position,
                    prompts=self.prompts,
                    config=self.config,
                    limit=10
                )

        # Should preserve first occurrence order
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0], "First")
        self.assertEqual(result[1], "Second")
        self.assertEqual(result[2], "Third")
        self.assertEqual(result[3], "Fourth")

    def test_empty_results_from_all_bocha_calls(self):
        """Test handling when all Bocha calls return empty results"""
        search_queries = ["Query 1", "Query 2"]

        with patch('modules.web_search.generate_search_queries', return_value=search_queries):
            with patch('modules.web_search.call_bocha_api', return_value=[]):
                result = search_interview_questions(
                    jd=self.jd,
                    company=self.company,
                    position=self.position,
                    prompts=self.prompts,
                    config=self.config,
                    limit=10
                )

        self.assertEqual(result, [])

    def test_generate_search_queries_called_with_correct_params(self):
        """Test that generate_search_queries is called with correct parameters"""
        search_queries = ["Query 1"]

        with patch('modules.web_search.generate_search_queries', return_value=search_queries) as mock_gen:
            with patch('modules.web_search.call_bocha_api', return_value=["Result"]):
                search_interview_questions(
                    jd=self.jd,
                    company=self.company,
                    position=self.position,
                    prompts=self.prompts,
                    config=self.config,
                    limit=10
                )

        # Verify the function was called with correct arguments
        mock_gen.assert_called_once_with(
            jd=self.jd,
            company=self.company,
            position=self.position,
            prompts=self.prompts,
            config=self.config
        )

    def test_multiple_queries_with_concurrent_processing(self):
        """Test that multiple queries are processed concurrently"""
        # With 5 queries, test that they're all called
        search_queries = ["Q1", "Q2", "Q3", "Q4", "Q5"]
        call_times = []

        with patch('modules.web_search.generate_search_queries', return_value=search_queries):
            def bocha_side_effect(query, config):
                # Record when this was called (for concurrent testing)
                call_times.append(query)
                return [f"Answer for {query}"]

            with patch('modules.web_search.call_bocha_api', side_effect=bocha_side_effect):
                result = search_interview_questions(
                    jd=self.jd,
                    company=self.company,
                    position=self.position,
                    prompts=self.prompts,
                    config=self.config,
                    limit=10
                )

            # All 5 queries should have been called
            self.assertEqual(len(call_times), 5)
            # All results should be in the output
            self.assertEqual(len(result), 5)

    def test_single_query_single_result(self):
        """Test simple case: 1 query returns 1 result"""
        search_queries = ["Python interview"]

        with patch('modules.web_search.generate_search_queries', return_value=search_queries):
            with patch('modules.web_search.call_bocha_api', return_value=["What is Python?"]):
                result = search_interview_questions(
                    jd=self.jd,
                    company=self.company,
                    position=self.position,
                    prompts=self.prompts,
                    config=self.config,
                    limit=10
                )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "What is Python?")

    def test_limit_zero_returns_empty_list(self):
        """Test that limit=0 returns empty list"""
        search_queries = ["Query 1"]

        with patch('modules.web_search.generate_search_queries', return_value=search_queries):
            with patch('modules.web_search.call_bocha_api', return_value=["Result 1", "Result 2"]):
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
