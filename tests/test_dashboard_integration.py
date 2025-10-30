"""
Integration tests for the complete dashboard workflow including main.py functions.

This test validates the end-to-end dashboard functionality including caching,
performance optimization, and the integrated data collection workflow.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import tempfile
import os

# Import dashboard functions
import sys
sys.path.append('.')

from models.core import Commit, PullRequest, Issue, Review, PullRequestState, IssueState
from models.config import GitHubCredentials, RepositoryConfig
from utils.metrics_calculator import MetricsCalculator
from utils.review_metrics_processor import ReviewMetricsProcessor


class MockStreamlitSession:
    """Mock Streamlit session state for testing."""
    
    def __init__(self):
        self.data = {
            'github_data_cache': {},
            'metrics_cache': {},
            'cache_timestamps': {},
            'performance_metrics': {
                'data_load_time': 0,
                'metrics_calc_time': 0,
                'chart_render_time': 0,
                'api_calls_made': 0,
                'cache_hits': 0,
                'cache_misses': 0
            }
        }
    
    def __getattr__(self, name):
        return self.data.get(name)
    
    def __setattr__(self, name, value):
        if name == 'data':
            super().__setattr__(name, value)
        else:
            self.data[name] = value


def test_cache_functionality():
    """Test caching functionality from main.py."""
    
    # Import the caching functions
    from main import create_cache_key, is_cache_valid, get_cached_data, cache_data, clear_expired_cache
    
    # Mock streamlit session state
    mock_session = MockStreamlitSession()
    
    with patch('main.st.session_state', mock_session):
        # Test cache key creation
        cache_key = create_cache_key("owner", "repo", "commits", datetime.now())
        assert isinstance(cache_key, str)
        assert len(cache_key) == 32  # MD5 hash length
        
        # Test cache validity (should be invalid initially)
        assert not is_cache_valid(cache_key)
        
        # Test caching data
        test_data = ["commit1", "commit2", "commit3"]
        cache_data(cache_key, test_data, 'github_data')
        
        # Test cache hit
        cached_result = get_cached_data(cache_key, 'github_data')
        assert cached_result == test_data
        assert mock_session.performance_metrics['cache_hits'] == 1
        
        # Test cache validity after caching
        assert is_cache_valid(cache_key)
        
        # Test expired cache clearing
        # Manually set an old timestamp
        old_time = datetime.now() - timedelta(hours=2)
        mock_session.cache_timestamps[cache_key] = old_time
        
        clear_expired_cache()
        
        # Cache should be cleared
        assert cache_key not in mock_session.github_data_cache
    
    print("✅ Cache functionality test passed!")


def test_integrated_data_collection_workflow():
    """Test the integrated data collection workflow from main.py."""
    
    from main import perform_integrated_data_collection
    
    # Create sample data
    sample_commits = [
        Commit(
            sha="abc123",
            author="test-user",
            timestamp=datetime.now() - timedelta(days=1),
            message="Test commit",
            additions=50,
            deletions=20,
            files_changed=2
        )
    ]
    
    sample_prs = [
        PullRequest(
            number=1,
            title="Test PR",
            author="test-user",
            created_at=datetime.now() - timedelta(days=1),
            state=PullRequestState.MERGED,
            merged_at=datetime.now(),
            additions=80,
            deletions=30,
            commits=1,
            reviews=[]
        )
    ]
    
    sample_issues = [
        Issue(
            number=1,
            title="Test issue",
            author="test-user",
            created_at=datetime.now() - timedelta(days=1),
            state=IssueState.CLOSED,
            closed_at=datetime.now(),
            assignee="test-user",
            labels=["bug"]
        )
    ]
    
    # Mock progress update function
    def mock_update_progress(progress, message):
        print(f"Progress: {progress:.1%} - {message}")
    
    # Mock streamlit session state
    mock_session = MockStreamlitSession()
    
    with patch('main.st.session_state', mock_session), \
         patch('utils.github_client.GitHubClient.authenticate', return_value=True), \
         patch('utils.github_client.GitHubClient.validate_repository_access', return_value=True), \
         patch('utils.github_client.GitHubClient.get_commits', return_value=sample_commits), \
         patch('utils.github_client.GitHubClient.get_pull_requests', return_value=sample_prs), \
         patch('utils.github_client.GitHubClient.get_issues', return_value=sample_issues):
        
        # Test the integrated data collection
        result = perform_integrated_data_collection(
            "ghp_1234567890abcdef1234567890abcdef12345678",
            "test-owner",
            "test-repo",
            mock_update_progress
        )
        
        # Validate results
        assert result == True
        assert hasattr(mock_session, 'integrated_metrics')
        assert hasattr(mock_session, 'repository_info')
        
        # Validate metrics
        metrics = mock_session.integrated_metrics
        assert metrics.commit_metrics.total_commits == 1
        assert metrics.pr_metrics.total_prs == 1
        assert metrics.issue_metrics.total_issues == 1
        
        # Validate repository info
        repo_info = mock_session.repository_info
        assert repo_info['owner'] == 'test-owner'
        assert repo_info['name'] == 'test-repo'
        assert repo_info['data_points']['commits'] == 1
        assert repo_info['data_points']['pull_requests'] == 1
        assert repo_info['data_points']['issues'] == 1
    
    print("✅ Integrated data collection workflow test passed!")


def test_end_to_end_workflow_testing():
    """Test the end-to-end workflow testing function from main.py."""
    
    from main import test_end_to_end_workflow
    
    # Create sample data for mocking
    sample_commits = [
        Commit(
            sha="test123",
            author="test-user",
            timestamp=datetime.now() - timedelta(days=1),
            message="Test commit",
            additions=25,
            deletions=10,
            files_changed=1
        )
    ]
    
    sample_prs = []  # Empty for simplicity
    sample_issues = []  # Empty for simplicity
    
    with patch('utils.github_client.GitHubClient.authenticate', return_value=True), \
         patch('utils.github_client.GitHubClient.validate_repository_access', return_value=True), \
         patch('utils.github_client.GitHubClient.get_commits', return_value=sample_commits), \
         patch('utils.github_client.GitHubClient.get_pull_requests', return_value=sample_prs), \
         patch('utils.github_client.GitHubClient.get_issues', return_value=sample_issues):
        
        # Test the end-to-end workflow
        test_results = test_end_to_end_workflow(
            "ghp_1234567890abcdef1234567890abcdef12345678",
            "test-owner",
            "test-repo"
        )
        
        # Validate test results
        assert test_results['success'] == True
        assert 'GitHub authentication' in test_results['steps_completed']
        assert 'Repository access validation' in test_results['steps_completed']
        assert 'GitHub data collection' in test_results['steps_completed']
        assert 'Metrics calculation' in test_results['steps_completed']
        
        # Validate metrics summary
        assert 'data_points' in test_results['metrics_summary']
        assert test_results['metrics_summary']['data_points']['commits'] == 1
        
        assert 'calculated_metrics' in test_results['metrics_summary']
        assert test_results['metrics_summary']['calculated_metrics']['total_commits'] == 1
    
    print("✅ End-to-end workflow testing test passed!")


def test_performance_optimization():
    """Test performance optimization features."""
    
    from main import create_cache_key, cache_data, get_cached_data
    
    # Mock streamlit session state
    mock_session = MockStreamlitSession()
    
    with patch('main.st.session_state', mock_session):
        # Test that caching reduces API calls
        cache_key = create_cache_key("owner", "repo", "commits")
        
        # First call - cache miss
        result1 = get_cached_data(cache_key, 'github_data')
        assert result1 is None
        
        # Cache some data
        test_data = ["data1", "data2", "data3"]
        cache_data(cache_key, test_data, 'github_data')
        
        # Second call - cache hit
        result2 = get_cached_data(cache_key, 'github_data')
        assert result2 == test_data
        
        # Verify performance metrics
        assert mock_session.performance_metrics['cache_hits'] == 1
        assert mock_session.performance_metrics['cache_misses'] == 1
        
        # Test cache efficiency calculation
        total_requests = mock_session.performance_metrics['cache_hits'] + mock_session.performance_metrics['cache_misses']
        cache_efficiency = (mock_session.performance_metrics['cache_hits'] / total_requests) * 100
        assert cache_efficiency == 50.0  # 1 hit out of 2 total requests
    
    print("✅ Performance optimization test passed!")


def test_data_integrity_validation():
    """Test that data integrity is maintained throughout the workflow."""
    
    # Create test data
    original_commits = [
        Commit(
            sha=f"commit{i}",
            author="test-user",
            timestamp=datetime.now() - timedelta(days=i),
            message=f"Commit {i}",
            additions=10 + i,
            deletions=5 + i,
            files_changed=1 + (i % 3)
        )
        for i in range(5)
    ]
    
    original_prs = [
        PullRequest(
            number=i + 1,
            title=f"PR {i}",
            author="test-user",
            created_at=datetime.now() - timedelta(days=i),
            state=PullRequestState.MERGED,
            merged_at=datetime.now() - timedelta(days=i, hours=-2),
            additions=20 + (i * 10),
            deletions=10 + (i * 5),
            commits=1 + i,
            reviews=[]
        )
        for i in range(3)
    ]
    
    # Store original counts
    original_commit_count = len(original_commits)
    original_pr_count = len(original_prs)
    
    # Process through metrics calculation
    calculator = MetricsCalculator()
    processor = ReviewMetricsProcessor()
    
    commit_metrics = calculator.calculate_commit_metrics(original_commits)
    pr_metrics = calculator.calculate_pr_metrics(original_prs)
    review_metrics = processor.calculate_review_metrics(original_prs)
    
    # Verify original data is unchanged
    assert len(original_commits) == original_commit_count
    assert len(original_prs) == original_pr_count
    
    # Verify calculated metrics match original data
    assert commit_metrics.total_commits == original_commit_count
    assert pr_metrics.total_prs == original_pr_count
    
    # Test that export maintains data integrity
    from utils.export_manager import ExportManager
    export_manager = ExportManager()
    
    # Create integrated metrics
    integrated_metrics = calculator.calculate_productivity_metrics(
        commits=original_commits,
        pull_requests=original_prs,
        issues=[],
        period_start=datetime.now() - timedelta(days=7),
        period_end=datetime.now()
    )
    
    # Export to CSV
    csv_content = export_manager.csv_exporter.export_productivity_metrics(integrated_metrics)
    
    # Verify exported data matches calculated metrics
    assert str(commit_metrics.total_commits) in csv_content
    assert str(pr_metrics.total_prs) in csv_content
    
    # Verify original data is still unchanged after export
    assert len(original_commits) == original_commit_count
    assert len(original_prs) == original_pr_count
    
    print("✅ Data integrity validation test passed!")


def test_error_handling_integration():
    """Test error handling throughout the integrated workflow."""
    
    from main import perform_integrated_data_collection
    
    # Mock progress update function
    def mock_update_progress(progress, message):
        pass
    
    # Mock streamlit session state
    mock_session = MockStreamlitSession()
    
    with patch('main.st.session_state', mock_session):
        # Test authentication failure
        with patch('utils.github_client.GitHubClient.authenticate', return_value=False):
            result = perform_integrated_data_collection(
                "invalid_token",
                "test-owner",
                "test-repo",
                mock_update_progress
            )
            # The function should return False on authentication failure
            assert result == False
        
        # Test repository access failure
        with patch('utils.github_client.GitHubClient.authenticate', return_value=True), \
             patch('utils.github_client.GitHubClient.validate_repository_access', return_value=False):
            result = perform_integrated_data_collection(
                "ghp_1234567890abcdef1234567890abcdef12345678",
                "invalid-owner",
                "invalid-repo",
                mock_update_progress
            )
            # The function should return False on repository access failure
            assert result == False
        
        # Test API error handling
        with patch('utils.github_client.GitHubClient.authenticate', return_value=True), \
             patch('utils.github_client.GitHubClient.validate_repository_access', return_value=True), \
             patch('utils.github_client.GitHubClient.get_commits', side_effect=Exception("API Error")):
            result = perform_integrated_data_collection(
                "ghp_1234567890abcdef1234567890abcdef12345678",
                "test-owner",
                "test-repo",
                mock_update_progress
            )
            # The function should return False on API error
            assert result == False
    
    print("✅ Error handling integration test passed!")


if __name__ == "__main__":
    test_cache_functionality()
    test_integrated_data_collection_workflow()
    test_end_to_end_workflow_testing()
    test_performance_optimization()
    test_data_integrity_validation()
    test_error_handling_integration()
    print("🎉 All dashboard integration tests passed!")