"""
Configuration data models for GitHub Productivity Dashboard.

This module contains data structures for managing API credentials,
application settings, and user preferences.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import re


class AnalysisPeriod(Enum):
    """Enumeration for analysis time periods."""
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    LAST_6_MONTHS = "last_6_months"
    LAST_YEAR = "last_year"
    CUSTOM = "custom"


class ChartType(Enum):
    """Enumeration for chart visualization types."""
    LINE = "line"
    BAR = "bar"
    AREA = "area"
    SCATTER = "scatter"
    HEATMAP = "heatmap"


@dataclass
class GitHubCredentials:
    """GitHub API credentials and configuration."""
    personal_access_token: str
    username: Optional[str] = None
    
    def __post_init__(self):
        """Validate GitHub credentials."""
        if not self.personal_access_token:
            raise ValueError("GitHub personal access token is required")
        
        # Basic token format validation (GitHub tokens start with 'ghp_', 'gho_', etc.)
        if not re.match(r'^gh[a-z]_[A-Za-z0-9_]{36,}$', self.personal_access_token):
            raise ValueError("Invalid GitHub token format")
    
    def is_valid(self) -> bool:
        """Check if credentials are properly formatted."""
        try:
            self.__post_init__()
            return True
        except ValueError:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert credentials to dictionary (excluding sensitive data)."""
        return {
            'username': self.username,
            'token_present': bool(self.personal_access_token)
        }


@dataclass
class OpenAICredentials:
    """OpenAI API credentials and configuration."""
    api_key: str
    organization_id: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 2000
    temperature: float = 0.7
    
    def __post_init__(self):
        """Validate OpenAI credentials."""
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # Basic API key format validation
        if not self.api_key.startswith('sk-'):
            raise ValueError("Invalid OpenAI API key format")
        
        if not 0 <= self.temperature <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        
        if self.max_tokens <= 0:
            raise ValueError("Max tokens must be positive")
        
        valid_models = [
            "gpt-3.5-turbo", "gpt-3.5-turbo-16k", 
            "gpt-4", "gpt-4-32k", "gpt-4-turbo-preview"
        ]
        if self.model not in valid_models:
            raise ValueError(f"Model must be one of: {valid_models}")
    
    def is_valid(self) -> bool:
        """Check if credentials are properly formatted."""
        try:
            self.__post_init__()
            return True
        except ValueError:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert credentials to dictionary (excluding sensitive data)."""
        return {
            'organization_id': self.organization_id,
            'model': self.model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'api_key_present': bool(self.api_key)
        }


@dataclass
class RepositoryConfig:
    """Configuration for a GitHub repository."""
    owner: str
    name: str
    url: Optional[str] = None
    default_branch: str = "main"
    include_forks: bool = False
    include_private: bool = True
    
    def __post_init__(self):
        """Validate repository configuration."""
        if not self.owner:
            raise ValueError("Repository owner is required")
        if not self.name:
            raise ValueError("Repository name is required")
        
        # Validate repository name format
        if not re.match(r'^[a-zA-Z0-9._-]+$', self.name):
            raise ValueError("Invalid repository name format")
        
        # Generate URL if not provided
        if not self.url:
            self.url = f"https://github.com/{self.owner}/{self.name}"
    
    @property
    def full_name(self) -> str:
        """Get full repository name (owner/name)."""
        return f"{self.owner}/{self.name}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert repository config to dictionary."""
        return {
            'owner': self.owner,
            'name': self.name,
            'url': self.url,
            'default_branch': self.default_branch,
            'include_forks': self.include_forks,
            'include_private': self.include_private
        }
    
    @classmethod
    def from_url(cls, url: str) -> 'RepositoryConfig':
        """Create repository config from GitHub URL."""
        # Parse GitHub URL
        pattern = r'https://github\.com/([^/]+)/([^/]+)/?'
        match = re.match(pattern, url)
        
        if not match:
            raise ValueError("Invalid GitHub repository URL")
        
        owner, name = match.groups()
        # Remove .git suffix if present
        if name.endswith('.git'):
            name = name[:-4]
        
        return cls(owner=owner, name=name, url=url)


@dataclass
class AnalysisConfig:
    """Configuration for productivity analysis."""
    period: AnalysisPeriod
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_weekends: bool = True
    timezone: str = "UTC"
    developers: List[str] = field(default_factory=list)  # Filter by specific developers
    
    def __post_init__(self):
        """Validate analysis configuration."""
        if self.period == AnalysisPeriod.CUSTOM:
            if not self.start_date or not self.end_date:
                raise ValueError("Custom period requires start_date and end_date")
            if self.end_date <= self.start_date:
                raise ValueError("End date must be after start date")
        else:
            # Set dates based on predefined period
            self.end_date = datetime.now()
            
            period_days = {
                AnalysisPeriod.LAST_7_DAYS: 7,
                AnalysisPeriod.LAST_30_DAYS: 30,
                AnalysisPeriod.LAST_90_DAYS: 90,
                AnalysisPeriod.LAST_6_MONTHS: 180,
                AnalysisPeriod.LAST_YEAR: 365
            }
            
            days = period_days.get(self.period, 30)
            self.start_date = self.end_date - timedelta(days=days)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis config to dictionary."""
        return {
            'period': self.period.value,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'include_weekends': self.include_weekends,
            'timezone': self.timezone,
            'developers': self.developers
        }


@dataclass
class DashboardConfig:
    """Configuration for dashboard display and behavior."""
    theme: str = "light"  # light, dark, auto
    default_chart_type: ChartType = ChartType.LINE
    show_ai_insights: bool = True
    auto_refresh_interval: int = 300  # seconds
    max_data_points: int = 1000
    enable_caching: bool = True
    cache_duration: int = 3600  # seconds
    
    def __post_init__(self):
        """Validate dashboard configuration."""
        if self.theme not in ["light", "dark", "auto"]:
            raise ValueError("Theme must be 'light', 'dark', or 'auto'")
        
        if self.auto_refresh_interval < 60:
            raise ValueError("Auto refresh interval must be at least 60 seconds")
        
        if self.max_data_points <= 0:
            raise ValueError("Max data points must be positive")
        
        if self.cache_duration < 0:
            raise ValueError("Cache duration must be non-negative")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert dashboard config to dictionary."""
        return {
            'theme': self.theme,
            'default_chart_type': self.default_chart_type.value,
            'show_ai_insights': self.show_ai_insights,
            'auto_refresh_interval': self.auto_refresh_interval,
            'max_data_points': self.max_data_points,
            'enable_caching': self.enable_caching,
            'cache_duration': self.cache_duration
        }


@dataclass
class ApplicationConfig:
    """Main application configuration containing all settings."""
    github_credentials: Optional[GitHubCredentials] = None
    openai_credentials: Optional[OpenAICredentials] = None
    repositories: List[RepositoryConfig] = field(default_factory=list)
    analysis_config: AnalysisConfig = field(default_factory=lambda: AnalysisConfig(AnalysisPeriod.LAST_30_DAYS))
    dashboard_config: DashboardConfig = field(default_factory=DashboardConfig)
    
    def is_configured(self) -> bool:
        """Check if application is properly configured."""
        return (
            self.github_credentials is not None and 
            self.github_credentials.is_valid() and
            len(self.repositories) > 0
        )
    
    def has_ai_enabled(self) -> bool:
        """Check if AI analysis is enabled and configured."""
        return (
            self.openai_credentials is not None and 
            self.openai_credentials.is_valid() and
            self.dashboard_config.show_ai_insights
        )
    
    def add_repository(self, repo: RepositoryConfig) -> None:
        """Add a repository to the configuration."""
        # Check if repository already exists
        for existing_repo in self.repositories:
            if existing_repo.full_name == repo.full_name:
                raise ValueError(f"Repository {repo.full_name} already exists")
        
        self.repositories.append(repo)
    
    def remove_repository(self, full_name: str) -> bool:
        """Remove a repository from the configuration."""
        for i, repo in enumerate(self.repositories):
            if repo.full_name == full_name:
                del self.repositories[i]
                return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert application config to dictionary."""
        return {
            'github_credentials': self.github_credentials.to_dict() if self.github_credentials else None,
            'openai_credentials': self.openai_credentials.to_dict() if self.openai_credentials else None,
            'repositories': [repo.to_dict() for repo in self.repositories],
            'analysis_config': self.analysis_config.to_dict(),
            'dashboard_config': self.dashboard_config.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApplicationConfig':
        """Create application config from dictionary."""
        config = cls()
        
        if data.get('github_credentials'):
            # Note: Sensitive data not included in to_dict, so we can't fully restore
            pass
        
        if data.get('openai_credentials'):
            # Note: Sensitive data not included in to_dict, so we can't fully restore
            pass
        
        config.repositories = [
            RepositoryConfig(**repo_data) 
            for repo_data in data.get('repositories', [])
        ]
        
        if data.get('analysis_config'):
            analysis_data = data['analysis_config']
            config.analysis_config = AnalysisConfig(
                period=AnalysisPeriod(analysis_data['period']),
                start_date=datetime.fromisoformat(analysis_data['start_date']) if analysis_data.get('start_date') else None,
                end_date=datetime.fromisoformat(analysis_data['end_date']) if analysis_data.get('end_date') else None,
                include_weekends=analysis_data.get('include_weekends', True),
                timezone=analysis_data.get('timezone', 'UTC'),
                developers=analysis_data.get('developers', [])
            )
        
        if data.get('dashboard_config'):
            dashboard_data = data['dashboard_config']
            config.dashboard_config = DashboardConfig(
                theme=dashboard_data.get('theme', 'light'),
                default_chart_type=ChartType(dashboard_data.get('default_chart_type', 'line')),
                show_ai_insights=dashboard_data.get('show_ai_insights', True),
                auto_refresh_interval=dashboard_data.get('auto_refresh_interval', 300),
                max_data_points=dashboard_data.get('max_data_points', 1000),
                enable_caching=dashboard_data.get('enable_caching', True),
                cache_duration=dashboard_data.get('cache_duration', 3600)
            )
        
        return config