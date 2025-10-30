"""
Centralized error handling for GitHub Productivity Dashboard.

This module provides comprehensive error handling utilities, custom exceptions,
and user-friendly error messages for all components of the application.
"""

import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, Union
from enum import Enum
import streamlit as st


class ErrorSeverity(Enum):
    """Error severity levels for categorizing different types of errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors for better organization and handling."""
    AUTHENTICATION = "authentication"
    API_RATE_LIMIT = "api_rate_limit"
    NETWORK = "network"
    DATA_PROCESSING = "data_processing"
    CONFIGURATION = "configuration"
    AI_SERVICE = "ai_service"
    EXPORT = "export"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


class DashboardError(Exception):
    """Base exception class for dashboard-specific errors."""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, 
                 details: Optional[Dict[str, Any]] = None,
                 suggestions: Optional[list] = None):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.suggestions = suggestions or []
        self.timestamp = datetime.now()


class GitHubAPIError(DashboardError):
    """Specific error for GitHub API issues."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 rate_limit_reset: Optional[datetime] = None, **kwargs):
        super().__init__(message, category=ErrorCategory.AUTHENTICATION, **kwargs)
        self.status_code = status_code
        self.rate_limit_reset = rate_limit_reset


class OpenAIAPIError(DashboardError):
    """Specific error for OpenAI API issues."""
    
    def __init__(self, message: str, error_type: Optional[str] = None, **kwargs):
        super().__init__(message, category=ErrorCategory.AI_SERVICE, **kwargs)
        self.error_type = error_type


class ConfigurationError(DashboardError):
    """Error for configuration and credential issues."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.CONFIGURATION, **kwargs)


class DataProcessingError(DashboardError):
    """Error for data processing and calculation issues."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.DATA_PROCESSING, **kwargs)


class ErrorHandler:
    """Centralized error handler for the dashboard application."""
    
    def __init__(self):
        """Initialize the error handler with logging configuration."""
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # Error message templates
        self.error_messages = {
            ErrorCategory.AUTHENTICATION: {
                "github_invalid_token": {
                    "message": "Invalid GitHub personal access token",
                    "suggestions": [
                        "Verify your token is correct and hasn't expired",
                        "Ensure the token has 'repo' scope permissions",
                        "Generate a new token if needed at https://github.com/settings/tokens"
                    ]
                },
                "github_insufficient_permissions": {
                    "message": "Insufficient permissions to access repository",
                    "suggestions": [
                        "Ensure your token has access to the repository",
                        "Check if the repository is private and you have access",
                        "Verify the repository owner and name are correct"
                    ]
                },
                "openai_invalid_key": {
                    "message": "Invalid OpenAI API key",
                    "suggestions": [
                        "Verify your API key is correct",
                        "Check if your API key has sufficient credits",
                        "Ensure the key hasn't been revoked or expired"
                    ]
                }
            },
            ErrorCategory.API_RATE_LIMIT: {
                "github_rate_limit": {
                    "message": "GitHub API rate limit exceeded",
                    "suggestions": [
                        "Wait for the rate limit to reset",
                        "Use a personal access token for higher limits",
                        "Consider reducing the frequency of API calls"
                    ]
                },
                "openai_rate_limit": {
                    "message": "OpenAI API rate limit exceeded",
                    "suggestions": [
                        "Wait a moment before trying again",
                        "Consider upgrading your OpenAI plan for higher limits",
                        "Reduce the frequency of AI analysis requests"
                    ]
                }
            },
            ErrorCategory.NETWORK: {
                "connection_failed": {
                    "message": "Network connection failed",
                    "suggestions": [
                        "Check your internet connection",
                        "Verify firewall settings allow the connection",
                        "Try again in a few moments"
                    ]
                },
                "timeout": {
                    "message": "Request timed out",
                    "suggestions": [
                        "Check your internet connection stability",
                        "Try again with a smaller data range",
                        "Contact support if the issue persists"
                    ]
                }
            },
            ErrorCategory.DATA_PROCESSING: {
                "invalid_data": {
                    "message": "Invalid or corrupted data received",
                    "suggestions": [
                        "Try refreshing the data",
                        "Check if the repository has valid commit history",
                        "Contact support if the issue persists"
                    ]
                },
                "calculation_error": {
                    "message": "Error calculating productivity metrics",
                    "suggestions": [
                        "Ensure the repository has sufficient data",
                        "Try with a different date range",
                        "Check if all required data is available"
                    ]
                }
            },
            ErrorCategory.CONFIGURATION: {
                "missing_credentials": {
                    "message": "Required credentials are missing",
                    "suggestions": [
                        "Configure your GitHub personal access token",
                        "Add your OpenAI API key for AI features",
                        "Ensure all required fields are filled"
                    ]
                },
                "invalid_repository": {
                    "message": "Invalid repository configuration",
                    "suggestions": [
                        "Check the repository URL format",
                        "Ensure the repository exists and is accessible",
                        "Use the format: owner/repository or full GitHub URL"
                    ]
                }
            },
            ErrorCategory.AI_SERVICE: {
                "analysis_failed": {
                    "message": "AI analysis generation failed",
                    "suggestions": [
                        "Check your OpenAI API key and credits",
                        "Try again in a few moments",
                        "Reduce the amount of data being analyzed"
                    ]
                },
                "service_unavailable": {
                    "message": "AI service temporarily unavailable",
                    "suggestions": [
                        "Try again in a few minutes",
                        "Check OpenAI service status",
                        "Use the dashboard without AI features for now"
                    ]
                }
            },
            ErrorCategory.EXPORT: {
                "export_failed": {
                    "message": "Data export failed",
                    "suggestions": [
                        "Ensure you have sufficient data to export",
                        "Try a different export format",
                        "Check your browser's download settings"
                    ]
                }
            }
        }
    
    def _setup_logging(self):
        """Setup logging configuration for error tracking."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )
    
    def handle_error(self, error: Union[Exception, DashboardError], 
                    context: Optional[str] = None,
                    show_in_ui: bool = True) -> Dict[str, Any]:
        """
        Handle an error with appropriate logging and user feedback.
        
        Args:
            error: The exception or error to handle
            context: Additional context about where the error occurred
            show_in_ui: Whether to display the error in the Streamlit UI
            
        Returns:
            Dict containing error information and handling results
        """
        # Convert regular exceptions to DashboardError if needed
        if not isinstance(error, DashboardError):
            dashboard_error = self._convert_to_dashboard_error(error)
        else:
            dashboard_error = error
        
        # Log the error
        self._log_error(dashboard_error, context)
        
        # Show in UI if requested
        if show_in_ui:
            self._display_error_in_ui(dashboard_error)
        
        # Return error information
        return {
            'error_id': id(dashboard_error),
            'category': dashboard_error.category.value,
            'severity': dashboard_error.severity.value,
            'message': dashboard_error.message,
            'suggestions': dashboard_error.suggestions,
            'timestamp': dashboard_error.timestamp,
            'handled': True
        }
    
    def _convert_to_dashboard_error(self, error: Exception) -> DashboardError:
        """Convert a regular exception to a DashboardError."""
        error_str = str(error).lower()
        
        # GitHub API errors
        if 'github' in error_str or 'api' in error_str:
            if 'rate limit' in error_str:
                return GitHubAPIError(
                    "GitHub API rate limit exceeded",
                    severity=ErrorSeverity.MEDIUM,
                    suggestions=self.error_messages[ErrorCategory.API_RATE_LIMIT]["github_rate_limit"]["suggestions"]
                )
            elif 'authentication' in error_str or 'unauthorized' in error_str:
                return GitHubAPIError(
                    "GitHub authentication failed",
                    severity=ErrorSeverity.HIGH,
                    suggestions=self.error_messages[ErrorCategory.AUTHENTICATION]["github_invalid_token"]["suggestions"]
                )
            elif 'not found' in error_str or '404' in error_str:
                return GitHubAPIError(
                    "Repository not found or not accessible",
                    severity=ErrorSeverity.HIGH,
                    suggestions=self.error_messages[ErrorCategory.AUTHENTICATION]["github_insufficient_permissions"]["suggestions"]
                )
        
        # OpenAI API errors
        elif 'openai' in error_str or 'chatgpt' in error_str:
            if 'rate limit' in error_str:
                return OpenAIAPIError(
                    "OpenAI API rate limit exceeded",
                    severity=ErrorSeverity.MEDIUM,
                    suggestions=self.error_messages[ErrorCategory.API_RATE_LIMIT]["openai_rate_limit"]["suggestions"]
                )
            elif 'api key' in error_str or 'authentication' in error_str:
                return OpenAIAPIError(
                    "OpenAI API authentication failed",
                    severity=ErrorSeverity.HIGH,
                    suggestions=self.error_messages[ErrorCategory.AUTHENTICATION]["openai_invalid_key"]["suggestions"]
                )
        
        # Network errors
        elif any(term in error_str for term in ['connection', 'network', 'timeout', 'unreachable']):
            return DashboardError(
                "Network connection issue",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                suggestions=self.error_messages[ErrorCategory.NETWORK]["connection_failed"]["suggestions"]
            )
        
        # Data processing errors
        elif any(term in error_str for term in ['json', 'parse', 'decode', 'invalid data']):
            return DataProcessingError(
                "Data processing error",
                severity=ErrorSeverity.MEDIUM,
                suggestions=self.error_messages[ErrorCategory.DATA_PROCESSING]["invalid_data"]["suggestions"]
            )
        
        # Generic error
        return DashboardError(
            f"An unexpected error occurred: {str(error)}",
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.MEDIUM,
            suggestions=[
                "Try refreshing the page",
                "Check your internet connection",
                "Contact support if the issue persists"
            ]
        )
    
    def _log_error(self, error: DashboardError, context: Optional[str] = None):
        """Log the error with appropriate level based on severity."""
        log_message = f"[{error.category.value.upper()}] {error.message}"
        if context:
            log_message = f"{context}: {log_message}"
        
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, exc_info=True)
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message, exc_info=True)
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def _display_error_in_ui(self, error: DashboardError):
        """Display the error in the Streamlit UI with appropriate styling."""
        # Choose the appropriate Streamlit function based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            st.error(f"🚨 Critical Error: {error.message}")
        elif error.severity == ErrorSeverity.HIGH:
            st.error(f"❌ Error: {error.message}")
        elif error.severity == ErrorSeverity.MEDIUM:
            st.warning(f"⚠️ Warning: {error.message}")
        else:
            st.info(f"ℹ️ Notice: {error.message}")
        
        # Show suggestions if available
        if error.suggestions:
            with st.expander("💡 Troubleshooting Suggestions"):
                for i, suggestion in enumerate(error.suggestions, 1):
                    st.write(f"{i}. {suggestion}")
        
        # Show technical details for debugging (in expander)
        if error.details:
            with st.expander("🔧 Technical Details"):
                st.json(error.details)
    
    def create_error_context(self, component: str, operation: str, 
                           additional_info: Optional[Dict[str, Any]] = None) -> str:
        """Create a standardized error context string."""
        context = f"{component}.{operation}"
        if additional_info:
            context += f" ({', '.join(f'{k}={v}' for k, v in additional_info.items())})"
        return context
    
    def handle_github_api_error(self, error: Exception, operation: str = "API call") -> Dict[str, Any]:
        """Specialized handler for GitHub API errors."""
        context = self.create_error_context("GitHubClient", operation)
        
        # Extract specific GitHub API error information
        error_str = str(error).lower()
        status_code = None
        
        # Try to extract status code from error message
        import re
        status_match = re.search(r'(\d{3})', str(error))
        if status_match:
            status_code = int(status_match.group(1))
        
        if status_code == 401:
            github_error = GitHubAPIError(
                "GitHub authentication failed - invalid or expired token",
                status_code=status_code,
                severity=ErrorSeverity.HIGH,
                suggestions=[
                    "Check that your personal access token is correct",
                    "Ensure the token hasn't expired",
                    "Verify the token has 'repo' scope permissions",
                    "Generate a new token at https://github.com/settings/tokens"
                ]
            )
        elif status_code == 403:
            if 'rate limit' in error_str:
                github_error = GitHubAPIError(
                    "GitHub API rate limit exceeded",
                    status_code=status_code,
                    severity=ErrorSeverity.MEDIUM,
                    suggestions=[
                        "Wait for the rate limit to reset (usually within an hour)",
                        "Use a personal access token for higher rate limits",
                        "Reduce the frequency of data requests"
                    ]
                )
            else:
                github_error = GitHubAPIError(
                    "Access forbidden - insufficient permissions",
                    status_code=status_code,
                    severity=ErrorSeverity.HIGH,
                    suggestions=[
                        "Ensure your token has access to the repository",
                        "Check if the repository is private",
                        "Verify the repository owner and name are correct"
                    ]
                )
        elif status_code == 404:
            github_error = GitHubAPIError(
                "Repository not found or not accessible",
                status_code=status_code,
                severity=ErrorSeverity.HIGH,
                suggestions=[
                    "Verify the repository URL is correct",
                    "Check if the repository exists",
                    "Ensure you have access to private repositories"
                ]
            )
        else:
            github_error = GitHubAPIError(
                f"GitHub API error: {str(error)}",
                status_code=status_code,
                severity=ErrorSeverity.MEDIUM,
                suggestions=[
                    "Check your internet connection",
                    "Try again in a few moments",
                    "Verify your GitHub credentials"
                ]
            )
        
        return self.handle_error(github_error, context)
    
    def handle_openai_api_error(self, error: Exception, operation: str = "AI analysis") -> Dict[str, Any]:
        """Specialized handler for OpenAI API errors."""
        context = self.create_error_context("ChatGPTAnalyzer", operation)
        
        error_str = str(error).lower()
        
        if 'rate limit' in error_str:
            openai_error = OpenAIAPIError(
                "OpenAI API rate limit exceeded",
                error_type="rate_limit",
                severity=ErrorSeverity.MEDIUM,
                suggestions=[
                    "Wait a moment before trying again",
                    "Consider upgrading your OpenAI plan",
                    "Reduce the frequency of AI analysis requests"
                ]
            )
        elif 'api key' in error_str or 'authentication' in error_str:
            openai_error = OpenAIAPIError(
                "OpenAI API authentication failed",
                error_type="authentication",
                severity=ErrorSeverity.HIGH,
                suggestions=[
                    "Verify your OpenAI API key is correct",
                    "Check if your API key has sufficient credits",
                    "Ensure the key hasn't been revoked"
                ]
            )
        elif 'quota' in error_str or 'billing' in error_str:
            openai_error = OpenAIAPIError(
                "OpenAI API quota exceeded or billing issue",
                error_type="quota",
                severity=ErrorSeverity.HIGH,
                suggestions=[
                    "Check your OpenAI account billing status",
                    "Add credits to your OpenAI account",
                    "Upgrade your OpenAI plan if needed"
                ]
            )
        else:
            openai_error = OpenAIAPIError(
                f"OpenAI API error: {str(error)}",
                error_type="unknown",
                severity=ErrorSeverity.MEDIUM,
                suggestions=[
                    "Check your internet connection",
                    "Verify your OpenAI API key",
                    "Try again in a few moments"
                ]
            )
        
        return self.handle_error(openai_error, context)
    
    def handle_data_processing_error(self, error: Exception, operation: str = "data processing") -> Dict[str, Any]:
        """Specialized handler for data processing errors."""
        context = self.create_error_context("DataProcessor", operation)
        
        processing_error = DataProcessingError(
            f"Data processing failed: {str(error)}",
            severity=ErrorSeverity.MEDIUM,
            suggestions=[
                "Ensure the repository has valid data",
                "Try with a different date range",
                "Check if all required data is available",
                "Refresh the data and try again"
            ]
        )
        
        return self.handle_error(processing_error, context)
    
    def handle_configuration_error(self, error: Exception, component: str = "Configuration") -> Dict[str, Any]:
        """Specialized handler for configuration errors."""
        context = self.create_error_context(component, "configuration")
        
        config_error = ConfigurationError(
            f"Configuration error: {str(error)}",
            severity=ErrorSeverity.HIGH,
            suggestions=[
                "Check all required credentials are provided",
                "Verify the configuration format is correct",
                "Ensure all required fields are filled",
                "Review the configuration documentation"
            ]
        )
        
        return self.handle_error(config_error, context)
    
    def create_graceful_fallback(self, operation: str, fallback_data: Any = None) -> Dict[str, Any]:
        """Create a graceful fallback when services are unavailable."""
        return {
            'status': 'fallback',
            'operation': operation,
            'message': f"Service temporarily unavailable for {operation}",
            'fallback_data': fallback_data,
            'suggestions': [
                "Try again in a few minutes",
                "Check service status",
                "Use alternative features if available"
            ]
        }


# Global error handler instance
error_handler = ErrorHandler()


def handle_error(error: Exception, context: Optional[str] = None, show_in_ui: bool = True) -> Dict[str, Any]:
    """Convenience function to handle errors using the global error handler."""
    return error_handler.handle_error(error, context, show_in_ui)


def safe_execute(func, *args, fallback=None, context: Optional[str] = None, **kwargs):
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Positional arguments for the function
        fallback: Fallback value to return on error
        context: Context information for error logging
        **kwargs: Keyword arguments for the function
        
    Returns:
        Function result or fallback value on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler.handle_error(e, context)
        return fallback


def with_error_handling(context: Optional[str] = None, fallback=None, show_in_ui: bool = True):
    """
    Decorator for adding error handling to functions.
    
    Args:
        context: Context information for error logging
        fallback: Fallback value to return on error
        show_in_ui: Whether to show errors in the UI
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_context = context or f"{func.__module__}.{func.__name__}"
                error_handler.handle_error(e, error_context, show_in_ui)
                return fallback
        return wrapper
    return decorator