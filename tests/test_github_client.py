"""
Unit tests for GitHub API client.

Tests authentication, data fetching, rate limiting, and error handling.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import requests

from models.config import GitHubCredentials, RepositoryConfig
from models.core import Commit, PullRequest, Issue, Review, PullRequestState, IssueState
from utils.github_client import (
    GitHubClient, GitHubAPIError, GitHubAuthenticationError, 
    GitHubRateLimitError, GitHubRepositoryError
)


class TestGitHubClient(unittest.TestCase):
    """Test cases for GitHubClient class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.credentials = GitHubCredentials(
            personal_access_token="ghp_1234567890abcdef1234567890abcdef12345678",
            username="testuser"
        )
        self.client = GitHubClient(self.credentials)
        self.repo_config = RepositoryConfig(
            owner="testowner",
            name="testrepo"
        )
    
    def test_client_initialization(self):
        """Test client initialization with credentials."""
        self.assertEqual(self.client.credentials, self.credentials)
        self.assertIsInstance(self.client.session, requests.Session)
        self.assertIn('Authorization', self.client.session.headers)
        self.assertEqual(
            self.client.session.headers['Authorization'], 
            'token ghp_1234567890abcdef1234567890abcdef12345678'
        )
    
    @patch('utils.github_client.GitHubClient._make_request')
    def test_authenticate_success(self, mock_request):
        """Test successful authentication."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'login': 'testuser', 'id': 12345}
        mock_request.return_value = mock_response
        
        result = self.client.authenticate()
        
        self.assertTrue(result)
        self.assertEqual(self.client.credentials.username, 'testuser')
        mock_request.assert_called_once_with('GET', '/user')
    
    @patch('utils.github_client.GitHubClient._make_request')
    def test_authenticate_invalid_token(self, mock_request):
        """Test authentication with invalid token."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response
        
        with self.assertRaises(GitHubAuthenticationError) as context:
            self.client.authenticate()
        
        self.assertIn("Invalid GitHub token", str(context.exception))
    
    @patch('utils.github_client.GitHubClient._make_request')
    def test_authenticate_network_error(self, mock_request):
        """Test authentication with network error."""
        mock_request.side_effect = requests.exceptions.RequestException("Network error")
        
        with self.assertRaises(GitHubAuthenticationError) as context:
            self.client.authenticate()
        
        self.assertIn("Network error during authentication", str(context.exception))
    
    @patch('utils.github_client.GitHubClient._make_request')
    def test_validate_repository_access_success(self, mock_request):
        """Test successful repository validation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'testrepo',
            'full_name': 'testowner/testrepo',
            'default_branch': 'main'
        }
        mock_request.return_value = mock_response
        
        result = self.client.validate_repository_access(self.repo_config)
        
        self.assertTrue(result)
        self.assertEqual(self.repo_config.default_branch, 'main')
    
    @patch('utils.github_client.GitHubClient._make_request')
    def test_validate_repository_not_found(self, mock_request):
        """Test repository validation with not found error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response
        
        with self.assertRaises(GitHubRepositoryError) as context:
            self.client.validate_repository_access(self.repo_config)
        
        self.assertIn("not found or not accessible", str(context.exception))
    
    @patch('utils.github_client.GitHubClient._make_request')
    def test_validate_repository_insufficient_permissions(self, mock_request):
        """Test repository validation with insufficient permissions."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_request.return_value = mock_response
        
        with self.assertRaises(GitHubRepositoryError) as context:
            self.client.validate_repository_access(self.repo_config)
        
        self.assertIn("Insufficient permissions", str(context.exception))
    
    @patch('utils.github_client.GitHubClient._get_commit_details')
    @patch('utils.github_client.GitHubClient._make_request')
    def test_get_commits_success(self, mock_request, mock_commit_details):
        """Test successful commit retrieval."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'sha': 'abc123', 'commit': {'author': {'name': 'testuser'}}},
            {'sha': 'def456', 'commit': {'author': {'name': 'testuser2'}}}
        ]
        mock_request.return_value = mock_response
        
        # Mock commit details
        test_commit = Commit(
            sha='abc123',
            author='testuser',
            timestamp=datetime.now(),
            message='Test commit',
            additions=10,
            deletions=5,
            files_changed=2
        )
        mock_commit_details.return_value = test_commit
        
        commits = self.client.get_commits(self.repo_config)
        
        self.assertEqual(len(commits), 2)
        self.assertIsInstance(commits[0], Commit)
        mock_request.assert_called()
    
    @patch('utils.github_client.GitHubClient._get_pull_request_details')
    @patch('utils.github_client.GitHubClient._make_request')
    def test_get_pull_requests_success(self, mock_request, mock_pr_details):
        """Test successful pull request retrieval."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'number': 1, 'title': 'Test PR 1'},
            {'number': 2, 'title': 'Test PR 2'}
        ]
        mock_request.return_value = mock_response
        
        # Mock PR details
        test_pr = PullRequest(
            number=1,
            title='Test PR 1',
            author='testuser',
            created_at=datetime.now(),
            state=PullRequestState.OPEN
        )
        mock_pr_details.return_value = test_pr
        
        prs = self.client.get_pull_requests(self.repo_config)
        
        self.assertEqual(len(prs), 2)
        self.assertIsInstance(prs[0], PullRequest)
        mock_request.assert_called()
    
    @patch('utils.github_client.GitHubClient._make_request')
    def test_get_issues_success(self, mock_request):
        """Test successful issue retrieval."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'number': 1,
                'title': 'Test Issue 1',
                'user': {'login': 'testuser'},
                'created_at': '2023-01-01T00:00:00Z',
                'state': 'open',
                'closed_at': None,
                'assignee': None,
                'labels': [],
                'body': 'Test issue body'
            }
        ]
        mock_request.return_value = mock_response
        
        issues = self.client.get_issues(self.repo_config)
        
        self.assertEqual(len(issues), 1)
        self.assertIsInstance(issues[0], Issue)
        self.assertEqual(issues[0].title, 'Test Issue 1')
    
    @patch('utils.github_client.GitHubClient._make_request')
    def test_get_user_activity_success(self, mock_request):
        """Test successful user activity retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'login': 'testuser',
            'public_repos': 10,
            'followers': 5
        }
        mock_request.return_value = mock_response
        
        activity = self.client.get_user_activity('testuser')
        
        self.assertEqual(activity['login'], 'testuser')
        self.assertEqual(activity['public_repos'], 10)
    
    @patch('utils.github_client.time.sleep')
    def test_rate_limit_handling(self, mock_sleep):
        """Test rate limit handling with retry."""
        # First response: rate limit error
        rate_limit_response = Mock()
        rate_limit_response.status_code = 403
        rate_limit_response.text = 'rate limit exceeded'
        rate_limit_response.headers = {
            'X-RateLimit-Reset': str(int((datetime.now() + timedelta(seconds=60)).timestamp()))
        }
        
        # Second response: success
        success_response = Mock()
        success_response.status_code = 200
        success_response.headers = {
            'X-RateLimit-Remaining': '4999',
            'X-RateLimit-Reset': str(int((datetime.now() + timedelta(hours=1)).timestamp()))
        }
        
        with patch.object(self.client.session, 'request', side_effect=[rate_limit_response, success_response]):
            response = self.client._make_request('GET', '/test')
        
        self.assertEqual(response.status_code, 200)
        mock_sleep.assert_called()  # Should have slept due to rate limit
    
    @patch('utils.github_client.time.sleep')
    def test_rate_limit_exceeded_max_retries(self, mock_sleep):
        """Test rate limit error when max retries exceeded."""
        rate_limit_response = Mock()
        rate_limit_response.status_code = 403
        rate_limit_response.text = 'rate limit exceeded'
        rate_limit_response.headers = {
            'X-RateLimit-Reset': str(int((datetime.now() + timedelta(seconds=60)).timestamp()))
        }
        
        with patch.object(self.client.session, 'request', return_value=rate_limit_response):
            with self.assertRaises(GitHubRateLimitError):
                self.client._make_request('GET', '/test')
    
    @patch('utils.github_client.time.sleep')
    def test_server_error_retry(self, mock_sleep):
        """Test server error retry with exponential backoff."""
        # First response: server error
        server_error_response = Mock()
        server_error_response.status_code = 500
        server_error_response.headers = {}
        
        # Second response: success
        success_response = Mock()
        success_response.status_code = 200
        success_response.headers = {
            'X-RateLimit-Remaining': '4999',
            'X-RateLimit-Reset': str(int((datetime.now() + timedelta(hours=1)).timestamp()))
        }
        
        with patch.object(self.client.session, 'request', side_effect=[server_error_response, success_response]):
            response = self.client._make_request('GET', '/test')
        
        self.assertEqual(response.status_code, 200)
        mock_sleep.assert_called()  # Should have slept due to retry
    
    def test_network_error_max_retries(self):
        """Test network error handling with max retries."""
        with patch.object(self.client.session, 'request', side_effect=requests.exceptions.RequestException("Network error")):
            with self.assertRaises(GitHubAPIError) as context:
                self.client._make_request('GET', '/test')
        
        self.assertIn("Request failed after", str(context.exception))
    
    def test_parse_commit_success(self):
        """Test successful commit parsing."""
        commit_data = {
            'sha': 'abc123',
            'commit': {
                'author': {
                    'name': 'testuser',
                    'date': '2023-01-01T00:00:00Z'
                },
                'message': 'Test commit message'
            },
            'stats': {
                'additions': 10,
                'deletions': 5
            },
            'files': [{'filename': 'test.py'}, {'filename': 'test2.py'}]
        }
        
        commit = self.client._parse_commit(commit_data)
        
        self.assertIsInstance(commit, Commit)
        self.assertEqual(commit.sha, 'abc123')
        self.assertEqual(commit.author, 'testuser')
        self.assertEqual(commit.message, 'Test commit message')
        self.assertEqual(commit.additions, 10)
        self.assertEqual(commit.deletions, 5)
        self.assertEqual(commit.files_changed, 2)
    
    def test_parse_pull_request_success(self):
        """Test successful pull request parsing."""
        pr_data = {
            'number': 1,
            'title': 'Test PR',
            'user': {'login': 'testuser'},
            'created_at': '2023-01-01T00:00:00Z',
            'state': 'open',
            'merged_at': None,
            'closed_at': None,
            'additions': 20,
            'deletions': 10,
            'commits': 3
        }
        
        reviews = [
            Review(
                reviewer='reviewer1',
                state='APPROVED',
                submitted_at=datetime.now()
            )
        ]
        
        pr = self.client._parse_pull_request(pr_data, reviews)
        
        self.assertIsInstance(pr, PullRequest)
        self.assertEqual(pr.number, 1)
        self.assertEqual(pr.title, 'Test PR')
        self.assertEqual(pr.author, 'testuser')
        self.assertEqual(pr.state, PullRequestState.OPEN)
        self.assertEqual(len(pr.reviews), 1)
    
    def test_parse_issue_success(self):
        """Test successful issue parsing."""
        issue_data = {
            'number': 1,
            'title': 'Test Issue',
            'user': {'login': 'testuser'},
            'created_at': '2023-01-01T00:00:00Z',
            'state': 'open',
            'closed_at': None,
            'assignee': {'login': 'assignee1'},
            'labels': [{'name': 'bug'}, {'name': 'high-priority'}],
            'body': 'Test issue description'
        }
        
        issue = self.client._parse_issue(issue_data)
        
        self.assertIsInstance(issue, Issue)
        self.assertEqual(issue.number, 1)
        self.assertEqual(issue.title, 'Test Issue')
        self.assertEqual(issue.author, 'testuser')
        self.assertEqual(issue.state, IssueState.OPEN)
        self.assertEqual(issue.assignee, 'assignee1')
        self.assertEqual(len(issue.labels), 2)
    
    def test_calculate_backoff_time(self):
        """Test exponential backoff calculation."""
        # Test without reset time
        backoff_time = self.client._calculate_backoff_time(0)
        self.assertGreaterEqual(backoff_time, 1.0)  # 2^0 + jitter
        
        backoff_time = self.client._calculate_backoff_time(2)
        self.assertGreaterEqual(backoff_time, 4.0)  # 2^2 + jitter
        
        # Test with reset time
        reset_time = datetime.now() + timedelta(seconds=30)
        backoff_time = self.client._calculate_backoff_time(0, reset_time)
        self.assertGreaterEqual(backoff_time, 30.0)
    
    def test_update_rate_limit_info(self):
        """Test rate limit information update."""
        mock_response = Mock()
        mock_response.headers = {
            'X-RateLimit-Remaining': '4500',
            'X-RateLimit-Reset': str(int((datetime.now() + timedelta(hours=1)).timestamp()))
        }
        
        self.client._update_rate_limit_info(mock_response)
        
        self.assertEqual(self.client.rate_limit_remaining, 4500)
        self.assertIsInstance(self.client.rate_limit_reset, datetime)


if __name__ == '__main__':
    unittest.main()