"""
Unit tests for ChatGPT analyzer.

Tests OpenAI API integration, prompt management, analysis generation, and error handling.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from models.config import OpenAICredentials
from models.metrics import (
    ProductivityMetrics, CommitMetrics, PRMetrics, ReviewMetrics, 
    IssueMetrics, VelocityPoint, AnalysisReport, Anomaly
)
from utils.chatgpt_analyzer import (
    ChatGPTAnalyzer, PromptManager, ProductivityInsightGenerator
)


class TestPromptManager(unittest.TestCase):
    """Test cases for PromptManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.metrics = self._create_test_metrics()
        self.prompt_manager = PromptManager()
    
    def _create_test_metrics(self) -> ProductivityMetrics:
        """Create test productivity metrics."""
        commit_metrics = CommitMetrics(
            total_commits=50,
            commit_frequency={'daily': 2, 'weekly': 14},
            average_additions=25.5,
            average_deletions=10.2,
            average_files_changed=3.1,
            most_active_hours=[9, 10, 14, 15],
            commit_message_length_avg=45.2
        )
        
        pr_metrics = PRMetrics(
            total_prs=10,
            merged_prs=8,
            closed_prs=1,
            open_prs=1,
            average_time_to_merge=24.5,
            average_additions=125.0,
            average_deletions=45.0,
            average_commits_per_pr=3.2,
            merge_rate=80.0
        )
        
        review_metrics = ReviewMetrics(
            total_reviews_given=15,
            total_reviews_received=12,
            average_review_time=4.5,
            approval_rate=75.0,
            change_request_rate=20.0,
            review_participation_rate=85.0
        )
        
        issue_metrics = IssueMetrics(
            total_issues=8,
            closed_issues=6,
            open_issues=2,
            average_time_to_close=48.0,
            resolution_rate=75.0,
            issues_created=3,
            issues_assigned=5
        )
        
        velocity_points = [
            VelocityPoint(
                timestamp=datetime.now() - timedelta(days=i),
                commits=2,
                additions=50,
                deletions=20,
                pull_requests=1,
                issues_closed=1
            )
            for i in range(7)
        ]
        
        return ProductivityMetrics(
            period_start=datetime.now() - timedelta(days=30),
            period_end=datetime.now(),
            commit_metrics=commit_metrics,
            pr_metrics=pr_metrics,
            review_metrics=review_metrics,
            issue_metrics=issue_metrics,
            velocity_trends=velocity_points
        )
    
    def test_get_productivity_analysis_prompt(self):
        """Test productivity analysis prompt generation."""
        prompt = self.prompt_manager.get_productivity_analysis_prompt(self.metrics)
        
        self.assertIsInstance(prompt, str)
        self.assertIn("productivity analyst", prompt.lower())
        self.assertIn("50", prompt)  # total commits
        self.assertIn("80.0", prompt)  # merge rate
        self.assertIn("JSON", prompt)
        self.assertIn("summary", prompt)
        self.assertIn("key_insights", prompt)
        self.assertIn("recommendations", prompt)
        self.assertIn("anomalies", prompt)
    
    def test_get_trend_analysis_prompt(self):
        """Test trend analysis prompt generation."""
        prompt = self.prompt_manager.get_trend_analysis_prompt(self.metrics)
        
        self.assertIsInstance(prompt, str)
        self.assertIn("trend", prompt.lower())
        self.assertIn("velocity", prompt.lower())
        self.assertIn("JSON", prompt)
        self.assertIn("trend_direction", prompt)
        self.assertIn("key_patterns", prompt)
        self.assertIn("inflection_points", prompt)
    
    def test_get_user_question_prompt(self):
        """Test user question prompt generation."""
        question = "How is my commit frequency?"
        prompt = self.prompt_manager.get_user_question_prompt(question, self.metrics)
        
        self.assertIsInstance(prompt, str)
        self.assertIn(question, prompt)
        self.assertIn("productivity", prompt.lower())
        self.assertIn("50", prompt)  # total commits from context
    
    def test_get_anomaly_detection_prompt(self):
        """Test anomaly detection prompt generation."""
        prompt = self.prompt_manager.get_anomaly_detection_prompt(self.metrics)
        
        self.assertIsInstance(prompt, str)
        self.assertIn("anomaly", prompt.lower())
        self.assertIn("unusual", prompt.lower())
        self.assertIn("JSON", prompt)
        self.assertIn("anomalies", prompt)
        self.assertIn("severity", prompt)


class TestChatGPTAnalyzer(unittest.TestCase):
    """Test cases for ChatGPTAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.credentials = OpenAICredentials(
            api_key="sk-test1234567890abcdef1234567890abcdef1234567890abcdef",
            model="gpt-3.5-turbo",
            max_tokens=2000,
            temperature=0.7
        )
        self.analyzer = ChatGPTAnalyzer(self.credentials)
        self.metrics = self._create_test_metrics()
    
    def _create_test_metrics(self) -> ProductivityMetrics:
        """Create test productivity metrics."""
        commit_metrics = CommitMetrics(
            total_commits=50,
            commit_frequency={'daily': 2, 'weekly': 14},
            average_additions=25.5,
            average_deletions=10.2,
            average_files_changed=3.1,
            most_active_hours=[9, 10, 14, 15],
            commit_message_length_avg=45.2
        )
        
        pr_metrics = PRMetrics(
            total_prs=10,
            merged_prs=8,
            closed_prs=1,
            open_prs=1,
            average_time_to_merge=24.5,
            average_additions=125.0,
            average_deletions=45.0,
            average_commits_per_pr=3.2,
            merge_rate=80.0
        )
        
        review_metrics = ReviewMetrics(
            total_reviews_given=15,
            total_reviews_received=12,
            average_review_time=4.5,
            approval_rate=75.0,
            change_request_rate=20.0,
            review_participation_rate=85.0
        )
        
        issue_metrics = IssueMetrics(
            total_issues=8,
            closed_issues=6,
            open_issues=2,
            average_time_to_close=48.0,
            resolution_rate=75.0,
            issues_created=3,
            issues_assigned=5
        )
        
        return ProductivityMetrics(
            period_start=datetime.now() - timedelta(days=30),
            period_end=datetime.now(),
            commit_metrics=commit_metrics,
            pr_metrics=pr_metrics,
            review_metrics=review_metrics,
            issue_metrics=issue_metrics,
            velocity_trends=[]
        )
    
    def _create_mock_chat_completion(self, content: str) -> ChatCompletion:
        """Create a mock ChatCompletion response."""
        message = ChatCompletionMessage(
            role="assistant",
            content=content
        )
        choice = Choice(
            index=0,
            message=message,
            finish_reason="stop"
        )
        return ChatCompletion(
            id="test-completion",
            object="chat.completion",
            created=int(datetime.now().timestamp()),
            model="gpt-3.5-turbo",
            choices=[choice]
        )
    
    @patch('utils.chatgpt_analyzer.OpenAI')
    def test_analyzer_initialization(self, mock_openai):
        """Test analyzer initialization with credentials."""
        analyzer = ChatGPTAnalyzer(self.credentials)
        
        self.assertEqual(analyzer.credentials, self.credentials)
        mock_openai.assert_called_once_with(
            api_key=self.credentials.api_key,
            organization=self.credentials.organization_id
        )
        self.assertIsInstance(analyzer.prompt_manager, PromptManager)
    
    @patch.object(ChatGPTAnalyzer, '_make_api_call')
    def test_analyze_productivity_trends_success(self, mock_api_call):
        """Test successful productivity trends analysis."""
        mock_response = {
            "summary": "Overall productivity is good with consistent commit patterns.",
            "key_insights": [
                "High merge rate indicates good code quality",
                "Consistent daily commit pattern shows good habits"
            ],
            "recommendations": [
                "Continue current development practices",
                "Consider increasing code review participation"
            ],
            "anomalies": [
                {
                    "metric_name": "commit_frequency",
                    "description": "Slight dip in commits last week",
                    "severity": "LOW"
                }
            ],
            "confidence_score": 0.85
        }
        mock_api_call.return_value = json.dumps(mock_response)
        
        result = self.analyzer.analyze_productivity_trends(self.metrics)
        
        self.assertIsInstance(result, AnalysisReport)
        self.assertEqual(result.summary, mock_response["summary"])
        self.assertEqual(len(result.key_insights), 2)
        self.assertEqual(len(result.recommendations), 2)
        self.assertEqual(len(result.anomalies), 1)
        self.assertEqual(result.confidence_score, 0.85)
        mock_api_call.assert_called_once()
    
    @patch.object(ChatGPTAnalyzer, '_make_api_call')
    def test_analyze_productivity_trends_invalid_json(self, mock_api_call):
        """Test productivity analysis with invalid JSON response."""
        mock_api_call.return_value = "Invalid JSON response"
        
        with self.assertRaises(ValueError) as context:
            self.analyzer.analyze_productivity_trends(self.metrics)
        
        self.assertIn("Invalid response format", str(context.exception))
    
    @patch.object(ChatGPTAnalyzer, '_make_api_call')
    def test_analyze_productivity_trends_api_failure(self, mock_api_call):
        """Test productivity analysis with API failure."""
        mock_api_call.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.analyzer.analyze_productivity_trends(self.metrics)
        
        self.assertIn("Failed to get response", str(context.exception))
    
    @patch.object(ChatGPTAnalyzer, '_make_api_call')
    def test_identify_anomalies_success(self, mock_api_call):
        """Test successful anomaly identification."""
        mock_response = {
            "anomalies": [
                {
                    "metric_name": "commits_per_day",
                    "date": "2023-01-15",
                    "expected_value": 2.5,
                    "actual_value": 0.1,
                    "severity": "HIGH",
                    "description": "Significant drop in daily commit activity"
                }
            ],
            "overall_assessment": "Concerning",
            "confidence_score": 0.90
        }
        mock_api_call.return_value = json.dumps(mock_response)
        
        result = self.analyzer.identify_anomalies(self.metrics)
        
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Anomaly)
        self.assertEqual(result[0].metric_name, "commits_per_day")
        self.assertEqual(result[0].severity, "HIGH")
        self.assertEqual(result[0].expected_value, 2.5)
        self.assertEqual(result[0].actual_value, 0.1)
    
    @patch.object(ChatGPTAnalyzer, '_make_api_call')
    def test_identify_anomalies_empty_response(self, mock_api_call):
        """Test anomaly identification with empty response."""
        mock_response = {"anomalies": []}
        mock_api_call.return_value = json.dumps(mock_response)
        
        result = self.analyzer.identify_anomalies(self.metrics)
        
        self.assertEqual(len(result), 0)
    
    @patch.object(ChatGPTAnalyzer, '_make_api_call')
    def test_identify_anomalies_json_error(self, mock_api_call):
        """Test anomaly identification with JSON parsing error."""
        mock_api_call.return_value = "Invalid JSON"
        
        result = self.analyzer.identify_anomalies(self.metrics)
        
        self.assertEqual(len(result), 0)  # Should return empty list on error
    
    @patch.object(ChatGPTAnalyzer, 'analyze_productivity_trends')
    def test_generate_recommendations_success(self, mock_analyze):
        """Test successful recommendation generation."""
        mock_report = AnalysisReport(
            generated_at=datetime.now(),
            summary="Test summary",
            key_insights=["Insight 1"],
            recommendations=["Recommendation 1", "Recommendation 2"],
            anomalies=[],
            confidence_score=0.8
        )
        mock_analyze.return_value = mock_report
        
        result = self.analyzer.generate_recommendations(self.metrics)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "Recommendation 1")
        self.assertEqual(result[1], "Recommendation 2")
    
    @patch.object(ChatGPTAnalyzer, 'analyze_productivity_trends')
    def test_generate_recommendations_error(self, mock_analyze):
        """Test recommendation generation with error."""
        mock_analyze.side_effect = Exception("API Error")
        
        result = self.analyzer.generate_recommendations(self.metrics)
        
        self.assertEqual(len(result), 3)  # Should return fallback recommendations
        self.assertIn("consistent commit patterns", result[0])
    
    @patch.object(ChatGPTAnalyzer, '_make_api_call')
    def test_answer_user_question_success(self, mock_api_call):
        """Test successful user question answering."""
        mock_api_call.return_value = "Your commit frequency is quite good with an average of 2 commits per day."
        
        result = self.analyzer.answer_user_question("How is my commit frequency?", self.metrics)
        
        self.assertIsInstance(result, str)
        self.assertIn("commit frequency", result)
        mock_api_call.assert_called_once()
    
    @patch.object(ChatGPTAnalyzer, '_make_api_call')
    def test_answer_user_question_json_response(self, mock_api_call):
        """Test user question answering with JSON response."""
        mock_response = {"answer": "Your productivity metrics show consistent patterns."}
        mock_api_call.return_value = json.dumps(mock_response)
        
        result = self.analyzer.answer_user_question("How am I doing?", self.metrics)
        
        self.assertEqual(result, "Your productivity metrics show consistent patterns.")
    
    @patch.object(ChatGPTAnalyzer, '_make_api_call')
    def test_answer_user_question_error(self, mock_api_call):
        """Test user question answering with error."""
        mock_api_call.side_effect = Exception("API Error")
        
        result = self.analyzer.answer_user_question("Test question", self.metrics)
        
        self.assertIn("error", result.lower())
        self.assertIn("API Error", result)
    
    @patch.object(ChatGPTAnalyzer, '_make_api_call')
    def test_analyze_trends_success(self, mock_api_call):
        """Test successful trend analysis."""
        mock_response = {
            "trend_direction": "increasing",
            "key_patterns": ["Consistent growth in commits", "Improving PR merge rate"],
            "inflection_points": [
                {
                    "date": "2023-01-15",
                    "description": "Started new project",
                    "impact": "positive"
                }
            ],
            "predictions": ["Continued growth expected"],
            "confidence_score": 0.80
        }
        mock_api_call.return_value = json.dumps(mock_response)
        
        result = self.analyzer.analyze_trends(self.metrics)
        
        self.assertEqual(result["trend_direction"], "increasing")
        self.assertEqual(len(result["key_patterns"]), 2)
        self.assertEqual(len(result["inflection_points"]), 1)
        self.assertEqual(result["confidence_score"], 0.80)
    
    @patch.object(ChatGPTAnalyzer, '_make_api_call')
    def test_analyze_trends_error(self, mock_api_call):
        """Test trend analysis with error."""
        mock_api_call.side_effect = Exception("API Error")
        
        result = self.analyzer.analyze_trends(self.metrics)
        
        self.assertEqual(result["trend_direction"], "unknown")
        self.assertIn("Analysis error", result["key_patterns"][0])
        self.assertEqual(result["confidence_score"], 0.0)
    
    @patch('utils.chatgpt_analyzer.OpenAI')
    def test_validate_credentials_success(self, mock_openai_class):
        """Test successful credential validation."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = self._create_mock_chat_completion("OK")
        mock_client.chat.completions.create.return_value = mock_response
        
        analyzer = ChatGPTAnalyzer(self.credentials)
        result = analyzer.validate_credentials()
        
        self.assertTrue(result)
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('utils.chatgpt_analyzer.OpenAI')
    def test_validate_credentials_failure(self, mock_openai_class):
        """Test credential validation failure."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Invalid API key")
        
        analyzer = ChatGPTAnalyzer(self.credentials)
        result = analyzer.validate_credentials()
        
        self.assertFalse(result)
    
    @patch('utils.chatgpt_analyzer.OpenAI')
    def test_make_api_call_success(self, mock_openai_class):
        """Test successful API call."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = self._create_mock_chat_completion("Test response")
        mock_client.chat.completions.create.return_value = mock_response
        
        analyzer = ChatGPTAnalyzer(self.credentials)
        result = analyzer._make_api_call("Test prompt")
        
        self.assertEqual(result, "Test response")
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('utils.chatgpt_analyzer.OpenAI')
    def test_make_api_call_retry_success(self, mock_openai_class):
        """Test API call with retry on failure."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # First call fails, second succeeds
        mock_client.chat.completions.create.side_effect = [
            Exception("Temporary error"),
            self._create_mock_chat_completion("Success after retry")
        ]
        
        analyzer = ChatGPTAnalyzer(self.credentials)
        result = analyzer._make_api_call("Test prompt")
        
        self.assertEqual(result, "Success after retry")
        self.assertEqual(mock_client.chat.completions.create.call_count, 2)
    
    @patch('utils.chatgpt_analyzer.OpenAI')
    def test_make_api_call_max_retries_exceeded(self, mock_openai_class):
        """Test API call failure after max retries."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Persistent error")
        
        analyzer = ChatGPTAnalyzer(self.credentials)
        
        with self.assertRaises(Exception) as context:
            analyzer._make_api_call("Test prompt")
        
        self.assertIn("Persistent error", str(context.exception))
        self.assertEqual(mock_client.chat.completions.create.call_count, 3)  # max_retries = 3


class TestProductivityInsightGenerator(unittest.TestCase):
    """Test cases for ProductivityInsightGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.credentials = OpenAICredentials(
            api_key="sk-test1234567890abcdef1234567890abcdef1234567890abcdef",
            model="gpt-3.5-turbo"
        )
        self.analyzer = ChatGPTAnalyzer(self.credentials)
        self.generator = ProductivityInsightGenerator(self.analyzer)
        self.metrics = self._create_test_metrics()
    
    def _create_test_metrics(self) -> ProductivityMetrics:
        """Create test productivity metrics."""
        commit_metrics = CommitMetrics(
            total_commits=60,
            commit_frequency={'daily': 2, 'weekly': 14},
            average_additions=25.5,
            average_deletions=10.2,
            average_files_changed=3.1,
            most_active_hours=[9, 10, 14, 15],
            commit_message_length_avg=45.2
        )
        
        pr_metrics = PRMetrics(
            total_prs=12,
            merged_prs=10,
            closed_prs=1,
            open_prs=1,
            average_time_to_merge=24.5,
            average_additions=125.0,
            average_deletions=45.0,
            average_commits_per_pr=3.2,
            merge_rate=83.3
        )
        
        review_metrics = ReviewMetrics(
            total_reviews_given=18,
            total_reviews_received=15,
            average_review_time=4.5,
            approval_rate=75.0,
            change_request_rate=20.0,
            review_participation_rate=85.0
        )
        
        issue_metrics = IssueMetrics(
            total_issues=10,
            closed_issues=8,
            open_issues=2,
            average_time_to_close=48.0,
            resolution_rate=80.0,
            issues_created=4,
            issues_assigned=6
        )
        
        return ProductivityMetrics(
            period_start=datetime.now() - timedelta(days=30),
            period_end=datetime.now(),
            commit_metrics=commit_metrics,
            pr_metrics=pr_metrics,
            review_metrics=review_metrics,
            issue_metrics=issue_metrics,
            velocity_trends=[]
        )
    
    def test_calculate_performance_score(self):
        """Test performance score calculation."""
        score = self.generator._calculate_performance_score(self.metrics)
        
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)
        # With good metrics, should get a decent score
        self.assertGreater(score, 50.0)
    
    def test_analyze_commit_patterns(self):
        """Test commit pattern analysis."""
        insights = self.generator._analyze_commit_patterns(self.metrics)
        
        self.assertIn('consistency', insights)
        self.assertIn('code_quality_indicator', insights)
        self.assertIn('activity_level', insights)
        self.assertIn('recommendations', insights)
        
        # With 2 commits per day, should be high consistency
        self.assertEqual(insights['consistency'], 'high')
    
    def test_analyze_pr_patterns(self):
        """Test PR pattern analysis."""
        insights = self.generator._analyze_pr_patterns(self.metrics)
        
        self.assertIn('merge_efficiency', insights)
        self.assertIn('pr_size_assessment', insights)
        self.assertIn('collaboration_level', insights)
        self.assertIn('recommendations', insights)
        
        # With 83.3% merge rate, should be excellent
        self.assertEqual(insights['merge_efficiency'], 'excellent')
    
    def test_analyze_review_patterns(self):
        """Test review pattern analysis."""
        insights = self.generator._analyze_review_patterns(self.metrics)
        
        self.assertIn('review_participation', insights)
        self.assertIn('review_quality', insights)
        self.assertIn('team_collaboration', insights)
        self.assertIn('recommendations', insights)
    
    def test_analyze_issue_patterns(self):
        """Test issue pattern analysis."""
        insights = self.generator._analyze_issue_patterns(self.metrics)
        
        self.assertIn('issue_resolution_efficiency', insights)
        self.assertIn('problem_solving_activity', insights)
        self.assertIn('maintenance_focus', insights)
        self.assertIn('recommendations', insights)
        
        # With 80% resolution rate, should be excellent
        self.assertEqual(insights['issue_resolution_efficiency'], 'excellent')
    
    @patch.object(ChatGPTAnalyzer, 'analyze_productivity_trends')
    @patch.object(ChatGPTAnalyzer, 'analyze_trends')
    def test_generate_comprehensive_insights_success(self, mock_analyze_trends, mock_analyze_productivity):
        """Test successful comprehensive insights generation."""
        # Mock analysis report
        mock_report = AnalysisReport(
            generated_at=datetime.now(),
            summary="Good productivity",
            key_insights=["Insight 1", "Insight 2"],
            recommendations=["Rec 1", "Rec 2"],
            anomalies=[],
            confidence_score=0.85
        )
        mock_analyze_productivity.return_value = mock_report
        
        # Mock trend analysis
        mock_trends = {
            "trend_direction": "increasing",
            "key_patterns": ["Pattern 1"],
            "confidence_score": 0.80
        }
        mock_analyze_trends.return_value = mock_trends
        
        result = self.generator.generate_comprehensive_insights(self.metrics)
        
        self.assertIn('overview', result)
        self.assertIn('trends', result)
        self.assertIn('anomalies', result)
        self.assertIn('recommendations', result)
        self.assertIn('performance_score', result)
        self.assertIn('commit_insights', result)
        self.assertIn('pr_insights', result)
        self.assertIn('review_insights', result)
        self.assertIn('issue_insights', result)
        
        self.assertEqual(result['overview']['summary'], "Good productivity")
        self.assertEqual(result['trends']['trend_direction'], "increasing")
        self.assertGreater(result['performance_score'], 0)
    
    @patch.object(ChatGPTAnalyzer, 'analyze_productivity_trends')
    def test_generate_comprehensive_insights_error(self, mock_analyze_productivity):
        """Test comprehensive insights generation with error."""
        mock_analyze_productivity.side_effect = Exception("API Error")
        
        result = self.generator.generate_comprehensive_insights(self.metrics)
        
        self.assertIn('error', result)
        self.assertEqual(result['error'], "API Error")
    
    @patch.object(ChatGPTAnalyzer, '_make_api_call')
    def test_generate_executive_summary_success(self, mock_api_call):
        """Test successful executive summary generation."""
        mock_response = {
            "overall_assessment": "Good",
            "key_achievements": ["High commit rate", "Good merge rate"],
            "concerns": [],
            "strategic_recommendations": ["Continue current practices"],
            "productivity_trend": "Stable",
            "executive_summary": "Developer shows consistent productivity with good metrics."
        }
        mock_api_call.return_value = json.dumps(mock_response)
        
        result = self.generator.generate_executive_summary(self.metrics)
        
        self.assertEqual(result["overall_assessment"], "Good")
        self.assertEqual(len(result["key_achievements"]), 2)
        self.assertEqual(result["productivity_trend"], "Stable")
    
    @patch.object(ChatGPTAnalyzer, '_make_api_call')
    def test_generate_executive_summary_error(self, mock_api_call):
        """Test executive summary generation with error."""
        mock_api_call.side_effect = Exception("API Error")
        
        result = self.generator.generate_executive_summary(self.metrics)
        
        # Should return fallback summary
        self.assertEqual(result["overall_assessment"], "Satisfactory")
        self.assertIn("Stable", result["productivity_trend"])
    
    @patch.object(ChatGPTAnalyzer, '_make_api_call')
    def test_compare_periods_success(self, mock_api_call):
        """Test successful period comparison."""
        mock_response = {
            "overall_trend": "Improving",
            "significant_changes": [
                {
                    "metric": "commits",
                    "change_percentage": 25.0,
                    "direction": "increase",
                    "significance": "high"
                }
            ],
            "insights": ["Commit activity increased significantly"],
            "recommendations": ["Maintain current momentum"]
        }
        mock_api_call.return_value = json.dumps(mock_response)
        
        # Create previous metrics with lower values
        previous_metrics = self._create_test_metrics()
        previous_metrics.commit_metrics.total_commits = 40
        
        result = self.generator.compare_periods(self.metrics, previous_metrics)
        
        self.assertEqual(result["overall_trend"], "Improving")
        self.assertEqual(len(result["significant_changes"]), 1)
        self.assertEqual(result["significant_changes"][0]["metric"], "commits")
    
    @patch.object(ChatGPTAnalyzer, '_make_api_call')
    def test_compare_periods_error(self, mock_api_call):
        """Test period comparison with error."""
        mock_api_call.side_effect = Exception("API Error")
        
        previous_metrics = self._create_test_metrics()
        previous_metrics.commit_metrics.total_commits = 40
        
        result = self.generator.compare_periods(self.metrics, previous_metrics)
        
        # Should return fallback comparison
        self.assertEqual(result["overall_trend"], "Stable")
        self.assertEqual(len(result["significant_changes"]), 1)
        # Should calculate commit change: (60-40)/40 * 100 = 50%
        self.assertEqual(result["significant_changes"][0]["change_percentage"], 50.0)


if __name__ == '__main__':
    unittest.main()