"""
GitHub API client for GitHub Productivity Dashboard.

This module provides a client for interacting with GitHub's REST API,
including authentication, data fetching, rate limiting, and error handling.
"""

import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from urllib.parse import urljoin
import logging

from models.config import GitHubCredentials, RepositoryConfig
from models.core import Commit, PullRequest, Issue, Review, PullRequestState, IssueState
from utils.error_handler import error_handler, with_error_handling, safe_execute


class GitHubAPIError(Exception):
    """Base exception for GitHub API errors."""
    pass


class GitHubAuthenticationError(GitHubAPIError):
    """Exception raised for authentication failures."""
    pass


class GitHubRateLimitError(GitHubAPIError):
    """Exception raised when rate limit is exceeded."""
    def __init__(self, message: str, reset_time: Optional[datetime] = None):
        super().__init__(message)
        self.reset_time = reset_time


class GitHubRepositoryError(GitHubAPIError):
    """Exception raised for repository access issues."""
    pass


class GitHubClient:
    """Client for interacting with GitHub's REST API."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, credentials: GitHubCredentials):
        """
        Initialize GitHub API client.
        
        Args:
            credentials: GitHub API credentials
        """
        self.credentials = credentials
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {credentials.personal_access_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-Productivity-Dashboard/1.0'
        })
        
        # Rate limiting tracking
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = datetime.now()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def authenticate(self) -> bool:
        """
        Validate GitHub API credentials and connection.
        
        Returns:
            bool: True if authentication is successful
            
        Raises:
            GitHubAuthenticationError: If authentication fails
        """
        try:
            response = self._make_request('GET', '/user')
            
            if response.status_code == 200:
                user_data = response.json()
                self.credentials.username = user_data.get('login')
                self.logger.info(f"Successfully authenticated as {self.credentials.username}")
                return True
            elif response.status_code == 401:
                raise GitHubAuthenticationError("Invalid GitHub token or insufficient permissions")
            else:
                raise GitHubAuthenticationError(f"Authentication failed with status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            error_handler.handle_github_api_error(e, "authentication")
            raise GitHubAuthenticationError(f"Network error during authentication: {str(e)}")
        except Exception as e:
            error_handler.handle_github_api_error(e, "authentication")
            raise
    
    def validate_repository_access(self, repo_config: RepositoryConfig) -> bool:
        """
        Validate access to a specific repository.
        
        Args:
            repo_config: Repository configuration
            
        Returns:
            bool: True if repository is accessible
            
        Raises:
            GitHubRepositoryError: If repository access fails
        """
        try:
            endpoint = f'/repos/{repo_config.owner}/{repo_config.name}'
            response = self._make_request('GET', endpoint)
            
            if response.status_code == 200:
                repo_data = response.json()
                # Update repository config with actual default branch
                repo_config.default_branch = repo_data.get('default_branch', 'main')
                return True
            elif response.status_code == 404:
                raise GitHubRepositoryError(f"Repository {repo_config.full_name} not found or not accessible")
            elif response.status_code == 403:
                raise GitHubRepositoryError(f"Insufficient permissions to access {repo_config.full_name}")
            else:
                raise GitHubRepositoryError(f"Repository validation failed with status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            error_handler.handle_github_api_error(e, "repository_validation")
            raise GitHubRepositoryError(f"Network error validating repository: {str(e)}")
        except Exception as e:
            error_handler.handle_github_api_error(e, "repository_validation")
            raise
    
    @with_error_handling(context="GitHubClient.get_commits", fallback=[])
    def get_commits(self, repo_config: RepositoryConfig, since: Optional[datetime] = None, 
                   until: Optional[datetime] = None, author: Optional[str] = None) -> List[Commit]:
        """
        Retrieve commit history for a repository.
        
        Args:
            repo_config: Repository configuration
            since: Start date for commit history
            until: End date for commit history
            author: Filter commits by author
            
        Returns:
            List[Commit]: List of commits
        """
        commits = []
        endpoint = f'/repos/{repo_config.owner}/{repo_config.name}/commits'
        
        params = {
            'per_page': 100,
            'page': 1
        }
        
        if since:
            params['since'] = since.isoformat()
        if until:
            params['until'] = until.isoformat()
        if author:
            params['author'] = author
        
        try:
            while True:
                response = self._make_request('GET', endpoint, params=params)
                
                if response.status_code != 200:
                    error_handler.handle_github_api_error(
                        Exception(f"Failed to fetch commits: HTTP {response.status_code}"),
                        "get_commits"
                    )
                    break
                
                commit_data = response.json()
                if not commit_data:
                    break
                
                for commit_info in commit_data:
                    try:
                        # Get detailed commit information
                        commit_detail = self._get_commit_details(repo_config, commit_info['sha'])
                        if commit_detail:
                            commits.append(commit_detail)
                    except Exception as e:
                        self.logger.warning(f"Failed to process commit {commit_info['sha']}: {str(e)}")
                        continue
                
                # Check if there are more pages
                if len(commit_data) < 100:
                    break
                
                params['page'] += 1
        
        except Exception as e:
            error_handler.handle_github_api_error(e, "get_commits")
            raise
        
        return commits
    
    def get_pull_requests(self, repo_config: RepositoryConfig, state: str = 'all') -> List[PullRequest]:
        """
        Retrieve pull requests for a repository.
        
        Args:
            repo_config: Repository configuration
            state: PR state filter ('open', 'closed', 'all')
            
        Returns:
            List[PullRequest]: List of pull requests
        """
        pull_requests = []
        endpoint = f'/repos/{repo_config.owner}/{repo_config.name}/pulls'
        
        params = {
            'state': state,
            'per_page': 100,
            'page': 1,
            'sort': 'updated',
            'direction': 'desc'
        }
        
        while True:
            response = self._make_request('GET', endpoint, params=params)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch pull requests: {response.status_code}")
                break
            
            pr_data = response.json()
            if not pr_data:
                break
            
            for pr_info in pr_data:
                try:
                    # Get detailed PR information including reviews
                    pr_detail = self._get_pull_request_details(repo_config, pr_info['number'])
                    if pr_detail:
                        pull_requests.append(pr_detail)
                except Exception as e:
                    self.logger.warning(f"Failed to process PR #{pr_info['number']}: {str(e)}")
                    continue
            
            # Check if there are more pages
            if len(pr_data) < 100:
                break
            
            params['page'] += 1
        
        return pull_requests
    
    def get_issues(self, repo_config: RepositoryConfig, state: str = 'all') -> List[Issue]:
        """
        Retrieve issues for a repository.
        
        Args:
            repo_config: Repository configuration
            state: Issue state filter ('open', 'closed', 'all')
            
        Returns:
            List[Issue]: List of issues
        """
        issues = []
        endpoint = f'/repos/{repo_config.owner}/{repo_config.name}/issues'
        
        params = {
            'state': state,
            'per_page': 100,
            'page': 1,
            'sort': 'updated',
            'direction': 'desc'
        }
        
        while True:
            response = self._make_request('GET', endpoint, params=params)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch issues: {response.status_code}")
                break
            
            issue_data = response.json()
            if not issue_data:
                break
            
            for issue_info in issue_data:
                try:
                    # Skip pull requests (GitHub API includes PRs in issues endpoint)
                    if 'pull_request' in issue_info:
                        continue
                    
                    issue = self._parse_issue(issue_info)
                    if issue:
                        issues.append(issue)
                except Exception as e:
                    self.logger.warning(f"Failed to process issue #{issue_info['number']}: {str(e)}")
                    continue
            
            # Check if there are more pages
            if len(issue_data) < 100:
                break
            
            params['page'] += 1
        
        return issues
    
    def get_user_activity(self, username: str) -> Dict[str, Any]:
        """
        Get user activity summary.
        
        Args:
            username: GitHub username
            
        Returns:
            Dict containing user activity data
        """
        try:
            endpoint = f'/users/{username}'
            response = self._make_request('GET', endpoint)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to fetch user activity: {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error fetching user activity: {str(e)}")
            return {}
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None, max_retries: int = 3) -> requests.Response:
        """
        Make HTTP request to GitHub API with rate limiting and retry logic.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            max_retries: Maximum number of retries
            
        Returns:
            requests.Response: API response
            
        Raises:
            GitHubRateLimitError: If rate limit is exceeded
            GitHubAPIError: For other API errors
        """
        url = urljoin(self.BASE_URL, endpoint)
        
        for attempt in range(max_retries + 1):
            try:
                # Check rate limit before making request
                self._check_rate_limit()
                
                response = self.session.request(method, url, params=params, json=data)
                
                # Update rate limit information
                self._update_rate_limit_info(response)
                
                # Handle rate limiting
                if response.status_code == 403 and 'rate limit' in response.text.lower():
                    reset_time = self._get_rate_limit_reset_time(response)
                    if attempt < max_retries:
                        wait_time = self._calculate_backoff_time(attempt, reset_time)
                        self.logger.warning(f"Rate limit hit, waiting {wait_time} seconds")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise GitHubRateLimitError("Rate limit exceeded", reset_time)
                
                # Handle other errors with exponential backoff
                if response.status_code >= 500 and attempt < max_retries:
                    wait_time = self._calculate_backoff_time(attempt)
                    self.logger.warning(f"Server error {response.status_code}, retrying in {wait_time} seconds")
                    time.sleep(wait_time)
                    continue
                
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    wait_time = self._calculate_backoff_time(attempt)
                    self.logger.warning(f"Request failed: {str(e)}, retrying in {wait_time} seconds")
                    time.sleep(wait_time)
                    continue
                else:
                    raise GitHubAPIError(f"Request failed after {max_retries} retries: {str(e)}")
        
        raise GitHubAPIError("Maximum retries exceeded")
    
    def _check_rate_limit(self) -> None:
        """Check if we're approaching rate limits and wait if necessary."""
        if self.rate_limit_remaining < 100:  # Conservative threshold
            now = datetime.now()
            if now < self.rate_limit_reset:
                wait_time = (self.rate_limit_reset - now).total_seconds()
                if wait_time > 0:
                    self.logger.info(f"Approaching rate limit, waiting {wait_time} seconds")
                    time.sleep(wait_time)
    
    def _update_rate_limit_info(self, response: requests.Response) -> None:
        """Update rate limit information from response headers."""
        if 'X-RateLimit-Remaining' in response.headers:
            self.rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
        
        if 'X-RateLimit-Reset' in response.headers:
            reset_timestamp = int(response.headers['X-RateLimit-Reset'])
            self.rate_limit_reset = datetime.fromtimestamp(reset_timestamp)
    
    def _get_rate_limit_reset_time(self, response: requests.Response) -> Optional[datetime]:
        """Extract rate limit reset time from response headers."""
        if 'X-RateLimit-Reset' in response.headers:
            reset_timestamp = int(response.headers['X-RateLimit-Reset'])
            return datetime.fromtimestamp(reset_timestamp)
        return None
    
    def _calculate_backoff_time(self, attempt: int, reset_time: Optional[datetime] = None) -> float:
        """Calculate exponential backoff time."""
        if reset_time:
            # Wait until rate limit resets plus a small buffer
            wait_time = (reset_time - datetime.now()).total_seconds() + 5
            return max(wait_time, 0)
        else:
            # Exponential backoff: 2^attempt seconds with jitter
            base_wait = 2 ** attempt
            jitter = base_wait * 0.1  # 10% jitter
            return base_wait + jitter
    
    def _get_commit_details(self, repo_config: RepositoryConfig, sha: str) -> Optional[Commit]:
        """Get detailed commit information."""
        endpoint = f'/repos/{repo_config.owner}/{repo_config.name}/commits/{sha}'
        response = self._make_request('GET', endpoint)
        
        if response.status_code != 200:
            return None
        
        commit_data = response.json()
        return self._parse_commit(commit_data)
    
    def _get_pull_request_details(self, repo_config: RepositoryConfig, pr_number: int) -> Optional[PullRequest]:
        """Get detailed pull request information including reviews."""
        # Get PR details
        pr_endpoint = f'/repos/{repo_config.owner}/{repo_config.name}/pulls/{pr_number}'
        pr_response = self._make_request('GET', pr_endpoint)
        
        if pr_response.status_code != 200:
            return None
        
        pr_data = pr_response.json()
        
        # Get PR reviews
        reviews_endpoint = f'/repos/{repo_config.owner}/{repo_config.name}/pulls/{pr_number}/reviews'
        reviews_response = self._make_request('GET', reviews_endpoint)
        
        reviews = []
        if reviews_response.status_code == 200:
            reviews_data = reviews_response.json()
            for review_info in reviews_data:
                review = self._parse_review(review_info)
                if review:
                    reviews.append(review)
        
        return self._parse_pull_request(pr_data, reviews)
    
    def _parse_commit(self, commit_data: Dict[str, Any]) -> Optional[Commit]:
        """Parse commit data from GitHub API response."""
        try:
            commit_info = commit_data['commit']
            stats = commit_data.get('stats', {})
            
            return Commit(
                sha=commit_data['sha'],
                author=commit_info['author']['name'],
                timestamp=datetime.fromisoformat(commit_info['author']['date'].replace('Z', '+00:00')),
                message=commit_info['message'],
                additions=stats.get('additions', 0),
                deletions=stats.get('deletions', 0),
                files_changed=len(commit_data.get('files', []))
            )
        except (KeyError, ValueError) as e:
            self.logger.warning(f"Failed to parse commit data: {str(e)}")
            return None
    
    def _parse_pull_request(self, pr_data: Dict[str, Any], reviews: List[Review]) -> Optional[PullRequest]:
        """Parse pull request data from GitHub API response."""
        try:
            # Determine PR state
            if pr_data['merged_at']:
                state = PullRequestState.MERGED
            elif pr_data['state'] == 'closed':
                state = PullRequestState.CLOSED
            else:
                state = PullRequestState.OPEN
            
            return PullRequest(
                number=pr_data['number'],
                title=pr_data['title'],
                author=pr_data['user']['login'],
                created_at=datetime.fromisoformat(pr_data['created_at'].replace('Z', '+00:00')),
                state=state,
                merged_at=datetime.fromisoformat(pr_data['merged_at'].replace('Z', '+00:00')) if pr_data['merged_at'] else None,
                closed_at=datetime.fromisoformat(pr_data['closed_at'].replace('Z', '+00:00')) if pr_data['closed_at'] else None,
                additions=pr_data.get('additions', 0),
                deletions=pr_data.get('deletions', 0),
                commits=pr_data.get('commits', 0),
                reviews=reviews
            )
        except (KeyError, ValueError) as e:
            self.logger.warning(f"Failed to parse pull request data: {str(e)}")
            return None
    
    def _parse_review(self, review_data: Dict[str, Any]) -> Optional[Review]:
        """Parse review data from GitHub API response."""
        try:
            return Review(
                reviewer=review_data['user']['login'],
                state=review_data['state'],
                submitted_at=datetime.fromisoformat(review_data['submitted_at'].replace('Z', '+00:00')),
                body=review_data.get('body')
            )
        except (KeyError, ValueError) as e:
            self.logger.warning(f"Failed to parse review data: {str(e)}")
            return None
    
    def _parse_issue(self, issue_data: Dict[str, Any]) -> Optional[Issue]:
        """Parse issue data from GitHub API response."""
        try:
            state = IssueState.CLOSED if issue_data['state'] == 'closed' else IssueState.OPEN
            
            return Issue(
                number=issue_data['number'],
                title=issue_data['title'],
                author=issue_data['user']['login'],
                created_at=datetime.fromisoformat(issue_data['created_at'].replace('Z', '+00:00')),
                state=state,
                closed_at=datetime.fromisoformat(issue_data['closed_at'].replace('Z', '+00:00')) if issue_data['closed_at'] else None,
                assignee=issue_data['assignee']['login'] if issue_data['assignee'] else None,
                labels=[label['name'] for label in issue_data.get('labels', [])],
                body=issue_data.get('body')
            )
        except (KeyError, ValueError) as e:
            self.logger.warning(f"Failed to parse issue data: {str(e)}")
            return None