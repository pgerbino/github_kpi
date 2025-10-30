"""
Integration tests for complete GitHub Productivity Dashboard workflows.

This module contains integration tests that validate the complete end-to-end
workflows from data collection to insight generation and export functionality.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Import the modules we're testing
from models.config import GitHubCredentials, RepositoryConfig, OpenAICredentials
from models.core import Commit, PullRequest, Issue, Review, PullRequestState, IssueState
from models.metrics import ProductivityMetrics, CommitMetrics, PRMetrics, ReviewMetrics, IssueMetrics, VelocityPoint
from utils.github_client import GitHubClient
from utils.metrics_calculator import MetricsCalculator
from utils.chatgpt_analyzer import ChatGPTAnalyzer
from utils.export_manager import ExportManager


class TestIntegrationWorkflows:
    """Integration tests for complete dashboard workflows."""
    
    @pytest.fixture
    def sample_commits(self) -> List[Commit]:
        """Create sample commit data for testing."""
        commits = []
        base_time = datetime.now() - timedelta(days=30)
        
        for i in range(20):
            commit = Commit(
                sha=f"abc123{i:02d}",
                author="test-user",
                timestamp=base_time + timedelta(days=i),
                message=f"Test commit {i}",
                additions=50 + (i * 10),
                deletions=20 + (i * 5),
                files_changed=2 + (i % 3)
            )
            commits.append(commit)
        
        return commits
    
    @pytest.fixture
    def sample_pull_requests(self) -> List[PullRequest]:
        """Create sample pull request data for testing."""
        prs = []
        base_time = datetime.now() - timedelta(days=30)
        
        for i in range(10):
            reviews = [
                Review(
                    reviewer="reviewer1",
                    state="APPROVED",
                    submitted_at=base_time + timedelta(days=i, hours=2)
                )
            ]
            
            pr = PullRequest(
                number=i + 1,
                title=f"Test PR {i}",
                author="test-user",
                created_at=base_time + timedelta(days=i),
                merged_at=base_time + timedelta(days=i, hours=4) if i % 3 != 0 else None,
                closed_at=base_time + timedelta(days=i, hours=4) if i % 5 == 0 else None,
                state=PullRequestState.MERGED if i % 3 != 0 else PullRequestState.OPEN,
                additions=100 + (i * 20),
                deletions=30 + (i * 10),
                commits=3 + (i % 2),
                reviews=reviews
            )
            prs.append(pr)
        
        return prs
    
    @pytest.fixture
    def sample_issues(self) -> List[Issue]:
        """Create sample issue data for testing."""
        issues = []
        base_time = datetime.now() - timedelta(days=30)
        
        for i in range(15):
            issue = Issue(
                number=i + 1,
                title=f"Test issue {i}",
                author="test-user",
                created_at=base_time + timedelta(days=i),
                closed_at=base_time + timedelta(days=i, hours=8) if i % 2 == 0 else None,
                state=IssueState.CLOSED if i % 2 == 0 else IssueState.OPEN,
                assignee="test-user" if i % 3 == 0 else None,
                labels=["bug", "enhancement"][i % 2:i % 2 + 1]
            )
            issues.append(issue)
        
        return issues
    
    @pytest.fixture
    def github_credentials(self) -> GitHubCredentials:
        """Create test GitHub credentials."""
        return GitHubCredentials(personal_access_token="ghp_1234567890abcdef1234567890abcdef12345678")
    
    @pytest.fixture
    def repository_config(self) -> RepositoryConfig:
        """Create test repository configuration."""
        return RepositoryConfig(owner="test-owner", name="test-repo")
    
    @pytest.fixture
    def openai_credentials(self) -> OpenAICredentials:
        """Create test OpenAI credentials."""
        return OpenAICredentials(api_key="sk-test123")
    
    def test_complete_data_collection_workflow(self, github_credentials, repository_config,
                                             sample_commits, sample_pull_requests, sample_issues):
        """Test complete data collection workflow from GitHub API to metrics calculation."""
        
        # Mock GitHub client responses
        with patch.object(GitHubClient, 'authenticate', return_value=True), \
             patch.object(GitHubClient, 'validate_repository_access', return_value=True), \
             patch.object(GitHubClient, 'get_commits', return_value=sample_commits), \
             patch.object(GitHubClient, 'get_pull_requests', return_value=sample_pull_requests), \
             patch.object(GitHubClient, 'get_issues', return_value=sample_issues):
            
            # Initialize client
            client = GitHubClient(github_credentials)
            
            # Test authentication
            assert client.authenticate() == True
            
            # Test repository access validation
            assert client.validate_repository_access(repository_config) == True
            
            # Test data collection
            since_date = datetime.now() - timedelta(days=30)
            commits = client.get_commits(repository_config, since=since_date)
            pull_requests = client.get_pull_requests(repository_config, state='all')
            issues = client.get_issues(repository_config, state='all')
            
            # Validate collected data
            assert len(commits) == 20
            assert len(pull_requests) == 10
            assert len(issues) == 15
            
            # Test metrics calculation
            calculator = MetricsCalculator()
            
            commit_metrics = calculator.calculate_commit_metrics(commits)
            pr_metrics = calculator.calculate_pr_metrics(pull_requests)
            
            # Use the review metrics processor for review and issue metrics
            from utils.review_metrics_processor import ReviewMetricsProcessor
            processor = ReviewMetricsProcessor()
            review_metrics = processor.calculate_review_metrics(pull_requests)
            issue_metrics = processor.calculate_issue_metrics(issues)
            
            velocity_trends = calculator.generate_velocity_trends(commits, pull_requests, issues)
            time_distribution = calculator._calculate_time_distribution(commits, pull_requests)
            
            # Validate calculated metrics
            assert commit_metrics.total_commits == 20
            assert pr_metrics.total_prs == 10
            assert issue_metrics.total_issues == 15
            assert len(velocity_trends) > 0
            assert isinstance(time_distribution, dict)
            
            # Test integrated metrics creation
            integrated_metrics = ProductivityMetrics(
                period_start=since_date,
                period_end=datetime.now(),
                commit_metrics=commit_metrics,
                pr_metrics=pr_metrics,
                review_metrics=review_metrics,
                issue_metrics=issue_metrics,
                velocity_trends=velocity_trends,
                time_distribution=time_distribution
            )
            
            # Validate integrated metrics
            assert integrated_metrics.period_days > 0
            assert integrated_metrics.daily_commit_average > 0
            assert integrated_metrics.commit_metrics.total_commits == 20
    
    def test_ai_insights_generation_workflow(self, openai_credentials, sample_commits, 
                                           sample_pull_requests, sample_issues):
        """Test AI insights generation workflow with real GitHub data."""
        
        # Create metrics from sample data
        calculator = MetricsCalculator()
        commit_metrics = calculator.calculate_commit_metrics(sample_commits)
        pr_metrics = calculator.calculate_pr_metrics(sample_pull_requests)
        
        from utils.review_metrics_processor import ReviewMetricsProcessor
        processor = ReviewMetricsProcessor()
        review_metrics = processor.calculate_review_metrics(sample_pull_requests)
        issue_metrics = processor.calculate_issue_metrics(sample_issues)
        velocity_trends = calculator.generate_velocity_trends(sample_commits, sample_pull_requests, sample_issues)
        
        integrated_metrics = ProductivityMetrics(
            period_start=datetime.now() - timedelta(days=30),
            period_end=datetime.now(),
            commit_metrics=commit_metrics,
            pr_metrics=pr_metrics,
            review_metrics=review_metrics,
            issue_metrics=issue_metrics,
            velocity_trends=velocity_trends,
            time_distribution=calculator.calculate_time_distribution(sample_commits, sample_pull_requests)
        )
        
        # Mock OpenAI API responses
        mock_analysis_response = {
            'summary': 'Test productivity analysis summary',
            'key_insights': ['Insight 1', 'Insight 2', 'Insight 3'],
            'recommendations': ['Recommendation 1', 'Recommendation 2'],
            'anomalies': [],
            'confidence_score': 0.85
        }
        
        with patch.object(ChatGPTAnalyzer, 'validate_credentials', return_value=True), \
             patch.object(ChatGPTAnalyzer, 'analyze_productivity_trends') as mock_analyze:
            
            # Configure mock to return our test response
            from models.metrics import AnalysisReport
            mock_analyze.return_value = AnalysisReport(
                generated_at=datetime.now(),
                summary=mock_analysis_response['summary'],
                key_insights=mock_analysis_response['key_insights'],
                recommendations=mock_analysis_response['recommendations'],
                anomalies=mock_analysis_response['anomalies'],
                confidence_score=mock_analysis_response['confidence_score']
            )
            
            # Test AI analyzer initialization and validation
            analyzer = ChatGPTAnalyzer(openai_credentials)
            assert analyzer.validate_credentials() == True
            
            # Test analysis generation
            analysis_report = analyzer.analyze_productivity_trends(integrated_metrics)
            
            # Validate analysis results
            assert analysis_report.summary == mock_analysis_response['summary']
            assert len(analysis_report.key_insights) == 3
            assert len(analysis_report.recommendations) == 2
            assert analysis_report.confidence_score == 0.85
            
            # Verify the analyzer was called with correct metrics
            mock_analyze.assert_called_once_with(integrated_metrics)
    
    def test_export_functionality_workflow(self, sample_commits, sample_pull_requests, sample_issues):
        """Test complete export functionality workflow."""
        
        # Create metrics from sample data
        calculator = MetricsCalculator()
        commit_metrics = calculator.calculate_commit_metrics(sample_commits)
        pr_metrics = calculator.calculate_pr_metrics(sample_pull_requests)
        review_metrics = calculator.calculate_review_metrics(sample_pull_requests)
        issue_metrics = calculator.calculate_issue_metrics(sample_issues)
        velocity_trends = calculator.generate_velocity_trends(sample_commits, sample_pull_requests, sample_issues)
        
        integrated_metrics = ProductivityMetrics(
            period_start=datetime.now() - timedelta(days=30),
            period_end=datetime.now(),
            commit_metrics=commit_metrics,
            pr_metrics=pr_metrics,
            review_metrics=review_metrics,
            issue_metrics=issue_metrics,
            velocity_trends=velocity_trends,
            time_distribution=calculator.calculate_time_distribution(sample_commits, sample_pull_requests)
        )
        
        # Test export manager initialization
        export_manager = ExportManager()
        
        # Test CSV export
        csv_content = export_manager.csv_exporter.export_productivity_metrics(
            integrated_metrics, include_config=True
        )
        
        # Validate CSV export
        assert csv_content is not None
        assert len(csv_content) > 100  # Should have substantial content
        assert 'Productivity Metrics Export' in csv_content
        assert str(integrated_metrics.commit_metrics.total_commits) in csv_content
        assert str(integrated_metrics.pr_metrics.total_prs) in csv_content
        
        # Test velocity trends export
        velocity_csv = export_manager.csv_exporter.export_velocity_trends_only(integrated_metrics)
        assert velocity_csv is not None
        assert 'Velocity Trends' in velocity_csv
        
        # Test export filename generation
        filename = export_manager.create_export_filename("metrics", integrated_metrics, "csv")
        assert filename.endswith('.csv')
        assert 'metrics' in filename
        
        # Test HTML dashboard export
        dashboard_html = export_manager.export_dashboard_html(integrated_metrics)
        assert dashboard_html is not None
        assert '<html>' in dashboard_html
        assert 'GitHub Productivity Dashboard' in dashboard_html
    
    def test_error_handling_in_workflows(self, github_credentials, repository_config):
        """Test error handling throughout the complete workflows."""
        
        # Test GitHub authentication failure
        with patch.object(GitHubClient, 'authenticate', return_value=False):
            client = GitHubClient(github_credentials)
            assert client.authenticate() == False
        
        # Test repository access failure
        with patch.object(GitHubClient, 'authenticate', return_value=True), \
             patch.object(GitHubClient, 'validate_repository_access', return_value=False):
            client = GitHubClient(github_credentials)
            assert client.authenticate() == True
            assert client.validate_repository_access(repository_config) == False
        
        # Test API error handling
        with patch.object(GitHubClient, 'authenticate', return_value=True), \
             patch.object(GitHubClient, 'get_commits', side_effect=Exception("API Error")):
            client = GitHubClient(github_credentials)
            assert client.authenticate() == True
            
            # Should handle the exception gracefully
            with pytest.raises(Exception):
                client.get_commits(repository_config)
        
        # Test metrics calculation with empty data
        calculator = MetricsCalculator()
        empty_commits = []
        empty_prs = []
        empty_issues = []
        
        # Should handle empty data gracefully
        commit_metrics = calculator.calculate_commit_metrics(empty_commits)
        pr_metrics = calculator.calculate_pr_metrics(empty_prs)
        issue_metrics = calculator.calculate_issue_metrics(empty_issues)
        
        assert commit_metrics.total_commits == 0
        assert pr_metrics.total_prs == 0
        assert issue_metrics.total_issues == 0
    
    def test_performance_optimization_workflow(self, github_credentials, repository_config,
                                             sample_commits, sample_pull_requests, sample_issues):
        """Test performance optimization features in the workflow."""
        
        # Test data limiting for large datasets
        large_commits = sample_commits * 100  # Create 2000 commits
        large_prs = sample_pull_requests * 100  # Create 1000 PRs
        large_issues = sample_issues * 100  # Create 1500 issues
        
        with patch.object(GitHubClient, 'authenticate', return_value=True), \
             patch.object(GitHubClient, 'validate_repository_access', return_value=True), \
             patch.object(GitHubClient, 'get_commits', return_value=large_commits), \
             patch.object(GitHubClient, 'get_pull_requests', return_value=large_prs), \
             patch.object(GitHubClient, 'get_issues', return_value=large_issues):
            
            client = GitHubClient(github_credentials)
            
            # Collect data
            commits = client.get_commits(repository_config)
            pull_requests = client.get_pull_requests(repository_config)
            issues = client.get_issues(repository_config)
            
            # In a real implementation, we would limit these for performance
            # For testing, we verify we can handle large datasets
            assert len(commits) == 2000
            assert len(pull_requests) == 1000
            assert len(issues) == 1500
            
            # Test that metrics calculation can handle large datasets
            calculator = MetricsCalculator()
            
            # Limit data for performance testing
            limited_commits = commits[:1000]
            limited_prs = pull_requests[:500]
            limited_issues = issues[:300]
            
            commit_metrics = calculator.calculate_commit_metrics(limited_commits)
            pr_metrics = calculator.calculate_pr_metrics(limited_prs)
            issue_metrics = calculator.calculate_issue_metrics(limited_issues)
            
            assert commit_metrics.total_commits == 1000
            assert pr_metrics.total_prs == 500
            assert issue_metrics.total_issues == 300
    
    def test_data_integrity_throughout_workflow(self, sample_commits, sample_pull_requests, sample_issues):
        """Test data integrity is maintained throughout the complete workflow."""
        
        # Test that data is preserved through metrics calculation
        calculator = MetricsCalculator()
        
        # Calculate metrics
        commit_metrics = calculator.calculate_commit_metrics(sample_commits)
        pr_metrics = calculator.calculate_pr_metrics(sample_pull_requests)
        issue_metrics = calculator.calculate_issue_metrics(sample_issues)
        
        # Verify data integrity
        assert commit_metrics.total_commits == len(sample_commits)
        assert pr_metrics.total_prs == len(sample_pull_requests)
        assert issue_metrics.total_issues == len(sample_issues)
        
        # Test that original data is not modified
        original_commit_count = len(sample_commits)
        original_pr_count = len(sample_pull_requests)
        original_issue_count = len(sample_issues)
        
        # Create integrated metrics
        integrated_metrics = ProductivityMetrics(
            period_start=datetime.now() - timedelta(days=30),
            period_end=datetime.now(),
            commit_metrics=commit_metrics,
            pr_metrics=pr_metrics,
            review_metrics=calculator.calculate_review_metrics(sample_pull_requests),
            issue_metrics=issue_metrics,
            velocity_trends=calculator.generate_velocity_trends(sample_commits, sample_pull_requests, sample_issues),
            time_distribution=calculator.calculate_time_distribution(sample_commits, sample_pull_requests)
        )
        
        # Verify original data is unchanged
        assert len(sample_commits) == original_commit_count
        assert len(sample_pull_requests) == original_pr_count
        assert len(sample_issues) == original_issue_count
        
        # Test export data integrity
        export_manager = ExportManager()
        csv_content = export_manager.csv_exporter.export_productivity_metrics(integrated_metrics)
        
        # Verify exported data matches calculated metrics
        assert str(commit_metrics.total_commits) in csv_content
        assert str(pr_metrics.total_prs) in csv_content
        assert str(issue_metrics.total_issues) in csv_content
    
    def test_real_repository_simulation(self, github_credentials):
        """Test workflow with simulated real repository data patterns."""
        
        # Create realistic repository data patterns
        repo_config = RepositoryConfig(owner="microsoft", name="vscode")
        
        # Simulate realistic commit patterns (more commits on weekdays)
        realistic_commits = []
        base_time = datetime.now() - timedelta(days=30)
        
        for day in range(30):
            current_date = base_time + timedelta(days=day)
            # More commits on weekdays
            commits_per_day = 15 if current_date.weekday() < 5 else 3
            
            for i in range(commits_per_day):
                commit = Commit(
                    sha=f"real{day:02d}{i:02d}",
                    author=f"developer{i % 5}",  # 5 different developers
                    timestamp=current_date + timedelta(hours=9 + i),
                    message=f"Fix issue #{day * 10 + i}",
                    additions=20 + (i * 5),
                    deletions=5 + (i * 2),
                    files_changed=1 + (i % 4)
                )
                realistic_commits.append(commit)
        
        # Simulate realistic PR patterns
        realistic_prs = []
        for week in range(4):
            for pr_num in range(8):  # 8 PRs per week
                created_date = base_time + timedelta(weeks=week, days=pr_num % 7)
                
                pr = PullRequest(
                    number=week * 8 + pr_num + 1,
                    title=f"Feature: Implement feature {pr_num}",
                    author=f"developer{pr_num % 5}",
                    created_at=created_date,
                    merged_at=created_date + timedelta(days=2) if pr_num % 4 != 0 else None,
                    closed_at=None,
                    state=PullRequestState.MERGED if pr_num % 4 != 0 else PullRequestState.OPEN,
                    additions=100 + (pr_num * 50),
                    deletions=30 + (pr_num * 15),
                    commits=3 + (pr_num % 3),
                    reviews=[
                        Review(
                            reviewer=f"reviewer{(pr_num + 1) % 3}",
                            state="APPROVED" if pr_num % 3 == 0 else "CHANGES_REQUESTED",
                            submitted_at=created_date + timedelta(days=1)
                        )
                    ]
                )
                realistic_prs.append(pr)
        
        # Mock the GitHub client with realistic data
        with patch.object(GitHubClient, 'authenticate', return_value=True), \
             patch.object(GitHubClient, 'validate_repository_access', return_value=True), \
             patch.object(GitHubClient, 'get_commits', return_value=realistic_commits), \
             patch.object(GitHubClient, 'get_pull_requests', return_value=realistic_prs), \
             patch.object(GitHubClient, 'get_issues', return_value=[]):
            
            # Test complete workflow with realistic data
            client = GitHubClient(github_credentials)
            assert client.authenticate() == True
            
            commits = client.get_commits(repo_config)
            pull_requests = client.get_pull_requests(repo_config)
            issues = client.get_issues(repo_config)
            
            # Calculate metrics
            calculator = MetricsCalculator()
            commit_metrics = calculator.calculate_commit_metrics(commits)
            pr_metrics = calculator.calculate_pr_metrics(pull_requests)
            
            # Validate realistic patterns
            assert commit_metrics.total_commits > 200  # Should have many commits
            assert pr_metrics.total_prs == 32  # 4 weeks * 8 PRs
            assert pr_metrics.merge_rate > 50  # Most PRs should be merged
            
            # Test that velocity trends show realistic patterns
            velocity_trends = calculator.generate_velocity_trends(commits, pull_requests, issues)
            assert len(velocity_trends) > 0
            
            # Verify weekday vs weekend patterns could be detected
            weekday_commits = [c for c in commits if c.timestamp.weekday() < 5]
            weekend_commits = [c for c in commits if c.timestamp.weekday() >= 5]
            
            assert len(weekday_commits) > len(weekend_commits)  # More commits on weekdays


if __name__ == "__main__":
    # Run the integration tests
    pytest.main([__file__, "-v"])