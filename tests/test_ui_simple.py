"""
Simple UI tests for GitHub Productivity Dashboard using Streamlit testing utilities.

This module contains UI tests that validate the dashboard components
without requiring a full browser setup.
"""

import pytest
import streamlit as st
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

# Import main components
from main import (
    initialize_session_state, validate_github_token, validate_openai_key,
    validate_repository_url, render_configuration_panel, get_sample_metrics
)


class TestStreamlitComponents:
    """Test Streamlit components and functions."""
    
    def test_initialize_session_state(self):
        """Test session state initialization."""
        # Mock streamlit session state
        mock_session_state = {}
        
        with patch('main.st.session_state', mock_session_state):
            initialize_session_state()
            
            # Check all required keys are initialized
            expected_keys = [
                'current_section', 'github_token', 'openai_key', 'repository_url',
                'credentials_valid', 'data_loaded', 'github_data_cache',
                'metrics_cache', 'cache_timestamps', 'performance_metrics'
            ]
            
            for key in expected_keys:
                assert key in mock_session_state
            
            # Check default values
            assert mock_session_state['current_section'] == "Overview"
            assert mock_session_state['credentials_valid'] == False
            assert mock_session_state['data_loaded'] == False
            assert isinstance(mock_session_state['github_data_cache'], dict)
            assert isinstance(mock_session_state['performance_metrics'], dict)
    
    def test_validate_github_token(self):
        """Test GitHub token validation."""
        # Test empty token
        assert validate_github_token("") == False
        assert validate_github_token(None) == False
        
        # Test invalid format
        assert validate_github_token("invalid_token") == False
        assert validate_github_token("github_pat_123") == False
        
        # Test valid format
        assert validate_github_token("ghp_1234567890abcdef1234567890abcdef12345678") == True
        assert validate_github_token("gho_1234567890abcdef1234567890abcdef12345678") == True
    
    def test_validate_openai_key(self):
        """Test OpenAI API key validation."""
        # Test empty key
        assert validate_openai_key("") == False
        assert validate_openai_key(None) == False
        
        # Test invalid format
        assert validate_openai_key("invalid_key") == False
        assert validate_openai_key("api_key_123") == False
        
        # Test valid format
        assert validate_openai_key("sk-1234567890abcdef1234567890abcdef") == True
        assert validate_openai_key("sk-proj-1234567890abcdef1234567890abcdef") == True
    
    def test_validate_repository_url(self):
        """Test repository URL validation."""
        # Test empty URL
        valid, owner, name = validate_repository_url("")
        assert valid == False
        assert owner == ""
        assert name == ""
        
        # Test invalid URL
        valid, owner, name = validate_repository_url("invalid-url")
        assert valid == False
        
        # Test valid GitHub URL
        valid, owner, name = validate_repository_url("https://github.com/microsoft/vscode")
        assert valid == True
        assert owner == "microsoft"
        assert name == "vscode"
        
        # Test valid GitHub URL with .git
        valid, owner, name = validate_repository_url("https://github.com/facebook/react.git")
        assert valid == True
        assert owner == "facebook"
        assert name == "react"
        
        # Test owner/repo format
        valid, owner, name = validate_repository_url("google/tensorflow")
        assert valid == True
        assert owner == "google"
        assert name == "tensorflow"
    
    def test_get_sample_metrics_without_data(self):
        """Test get_sample_metrics when no data is loaded."""
        mock_session_state = {'data_loaded': False}
        
        with patch('main.st.session_state', mock_session_state):
            metrics = get_sample_metrics()
            assert metrics is None
    
    def test_get_sample_metrics_with_integrated_data(self):
        """Test get_sample_metrics with integrated data."""
        from models.metrics import ProductivityMetrics, CommitMetrics, PRMetrics, ReviewMetrics, IssueMetrics
        from datetime import datetime, timedelta
        
        # Create mock integrated metrics
        mock_metrics = ProductivityMetrics(
            period_start=datetime.now() - timedelta(days=30),
            period_end=datetime.now(),
            commit_metrics=CommitMetrics(
                total_commits=10,
                commit_frequency={},
                average_additions=50.0,
                average_deletions=20.0,
                average_files_changed=2.0,
                most_active_hours=[9, 10, 14],
                commit_message_length_avg=45.0
            ),
            pr_metrics=PRMetrics(
                total_prs=5,
                merged_prs=4,
                closed_prs=0,
                open_prs=1,
                average_time_to_merge=24.0,
                average_additions=100.0,
                average_deletions=30.0,
                average_commits_per_pr=2.0,
                merge_rate=80.0
            ),
            review_metrics=ReviewMetrics(
                total_reviews_given=8,
                total_reviews_received=6,
                average_review_time=4.0,
                approval_rate=75.0,
                change_request_rate=20.0,
                review_participation_rate=85.0
            ),
            issue_metrics=IssueMetrics(
                total_issues=3,
                closed_issues=2,
                open_issues=1,
                average_time_to_close=48.0,
                resolution_rate=66.7,
                issues_created=1,
                issues_assigned=2
            ),
            velocity_trends=[],
            time_distribution={"coding": 70.0, "reviewing": 20.0, "meetings": 10.0}
        )
        
        mock_session_state = {
            'data_loaded': True,
            'integrated_metrics': mock_metrics
        }
        
        with patch('main.st.session_state', mock_session_state):
            metrics = get_sample_metrics()
            assert metrics is not None
            assert metrics == mock_metrics
            assert metrics.commit_metrics.total_commits == 10
            assert metrics.pr_metrics.total_prs == 5


class TestUIComponentRendering:
    """Test UI component rendering with mocked Streamlit."""
    
    def setup_method(self):
        """Set up mocks for each test."""
        self.mock_st = MagicMock()
        self.mock_session_state = {
            'current_section': 'Overview',
            'github_token': '',
            'openai_key': '',
            'repository_url': '',
            'credentials_valid': False,
            'data_loaded': False,
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
    
    def test_configuration_panel_structure(self):
        """Test configuration panel renders with correct structure."""
        with patch('main.st', self.mock_st), \
             patch('main.st.session_state', self.mock_session_state):
            
            # Mock the required streamlit functions
            self.mock_st.header = MagicMock()
            self.mock_st.subheader = MagicMock()
            self.mock_st.text_input = MagicMock(return_value="")
            self.mock_st.button = MagicMock(return_value=False)
            self.mock_st.success = MagicMock()
            self.mock_st.error = MagicMock()
            self.mock_st.columns = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock()])
            self.mock_st.metric = MagicMock()
            self.mock_st.markdown = MagicMock()
            self.mock_st.info = MagicMock()
            
            # Test that configuration panel can be called without errors
            try:
                render_configuration_panel()
                success = True
            except Exception as e:
                success = False
                print(f"Configuration panel rendering failed: {e}")
            
            assert success == True
            
            # Verify key components were called
            self.mock_st.header.assert_called()
            self.mock_st.subheader.assert_called()
            self.mock_st.text_input.assert_called()
    
    def test_navigation_sections(self):
        """Test navigation between different sections."""
        from main import DASHBOARD_SECTIONS
        
        # Test all sections are defined
        expected_sections = ["Overview", "Metrics", "Analytics", "AI Insights", "Export"]
        for section in expected_sections:
            assert section in DASHBOARD_SECTIONS
            assert DASHBOARD_SECTIONS[section]  # Has an icon
    
    def test_error_handling_in_ui_functions(self):
        """Test error handling in UI functions."""
        # Test with invalid inputs
        assert validate_github_token("invalid") == False
        assert validate_openai_key("invalid") == False
        
        valid, owner, name = validate_repository_url("invalid")
        assert valid == False
        assert owner == ""
        assert name == ""
    
    def test_session_state_updates(self):
        """Test session state updates correctly."""
        mock_session_state = {
            'github_token': '',
            'repository_url': '',
            'credentials_valid': False
        }
        
        with patch('main.st.session_state', mock_session_state):
            # Simulate token input
            mock_session_state['github_token'] = 'ghp_1234567890abcdef1234567890abcdef12345678'
            assert validate_github_token(mock_session_state['github_token']) == True
            
            # Simulate repository input
            mock_session_state['repository_url'] = 'microsoft/vscode'
            valid, owner, name = validate_repository_url(mock_session_state['repository_url'])
            assert valid == True
            assert owner == 'microsoft'
            assert name == 'vscode'


class TestUIDataFlow:
    """Test data flow through UI components."""
    
    def test_credentials_to_data_loading_flow(self):
        """Test the flow from credentials input to data loading."""
        # Start with empty state
        mock_session_state = {
            'github_token': '',
            'repository_url': '',
            'credentials_valid': False,
            'data_loaded': False
        }
        
        # Step 1: Add valid credentials
        mock_session_state['github_token'] = 'ghp_1234567890abcdef1234567890abcdef12345678'
        mock_session_state['repository_url'] = 'microsoft/vscode'
        
        # Validate credentials
        token_valid = validate_github_token(mock_session_state['github_token'])
        repo_valid, owner, name = validate_repository_url(mock_session_state['repository_url'])
        
        assert token_valid == True
        assert repo_valid == True
        assert owner == 'microsoft'
        assert name == 'vscode'
        
        # Step 2: Credentials should be considered valid
        mock_session_state['credentials_valid'] = token_valid and repo_valid
        assert mock_session_state['credentials_valid'] == True
        
        # Step 3: Data loading would be enabled
        # (In real app, this would trigger data collection)
        assert mock_session_state['credentials_valid'] == True
    
    def test_cache_functionality_flow(self):
        """Test cache functionality flow."""
        from main import create_cache_key, cache_data, get_cached_data, is_cache_valid
        from datetime import datetime
        
        mock_session_state = {
            'github_data_cache': {},
            'cache_timestamps': {},
            'performance_metrics': {
                'cache_hits': 0,
                'cache_misses': 0
            }
        }
        
        with patch('main.st.session_state', mock_session_state):
            # Create cache key
            cache_key = create_cache_key("owner", "repo", "commits", datetime.now())
            assert isinstance(cache_key, str)
            assert len(cache_key) == 32  # MD5 hash
            
            # Initially no cache
            assert not is_cache_valid(cache_key)
            assert get_cached_data(cache_key, 'github_data') is None
            
            # Cache some data
            test_data = ["commit1", "commit2"]
            cache_data(cache_key, test_data, 'github_data')
            
            # Should now be cached
            assert is_cache_valid(cache_key)
            cached_result = get_cached_data(cache_key, 'github_data')
            assert cached_result == test_data
            assert mock_session_state['performance_metrics']['cache_hits'] == 1


class TestUIAccessibility:
    """Test UI accessibility features."""
    
    def test_form_labels_and_help_text(self):
        """Test that forms have proper labels and help text."""
        # This would be tested in a real browser environment
        # Here we test that the validation functions provide clear feedback
        
        # Test clear validation messages
        assert validate_github_token("invalid") == False
        assert validate_openai_key("invalid") == False
        
        valid, owner, name = validate_repository_url("invalid")
        assert valid == False
        
        # Test successful validation
        assert validate_github_token("ghp_1234567890abcdef1234567890abcdef12345678") == True
        assert validate_openai_key("sk-1234567890abcdef1234567890abcdef") == True
        
        valid, owner, name = validate_repository_url("microsoft/vscode")
        assert valid == True
    
    def test_error_message_clarity(self):
        """Test that error messages are clear and helpful."""
        # Test validation functions return boolean values that can be used
        # to show clear error messages in the UI
        
        token_tests = [
            ("", False),
            ("invalid", False),
            ("ghp_short", False),
            ("ghp_1234567890abcdef1234567890abcdef12345678", True)
        ]
        
        for token, expected in token_tests:
            result = validate_github_token(token)
            assert result == expected, f"Token '{token}' validation failed"
        
        repo_tests = [
            ("", (False, "", "")),
            ("invalid", (False, "", "")),
            ("microsoft/vscode", (True, "microsoft", "vscode")),
            ("https://github.com/facebook/react", (True, "facebook", "react"))
        ]
        
        for repo, expected in repo_tests:
            result = validate_repository_url(repo)
            assert result == expected, f"Repository '{repo}' validation failed"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])