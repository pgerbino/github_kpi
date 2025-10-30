"""
GitHub Productivity Dashboard - Main Streamlit Application

A comprehensive dashboard for analyzing developer productivity using GitHub API data
and AI-powered insights from ChatGPT.
"""

import streamlit as st
import time
from datetime import datetime, timedelta
from typing import Dict, Any
from utils.error_handler import error_handler, with_error_handling, safe_execute
from utils.user_feedback import (
    feedback_manager, loading_context, show_success, show_error, 
    show_warning, show_info, is_loading, set_loading, set_success, set_error
)

# Dashboard sections
DASHBOARD_SECTIONS = {
    "Overview": "📊",
    "Metrics": "📈", 
    "Analytics": "🔍",
    "AI Insights": "🤖",
    "Export": "📥"
}

def initialize_session_state():
    """Initialize session state variables"""
    if 'current_section' not in st.session_state:
        st.session_state.current_section = "Overview"
    if 'github_token' not in st.session_state:
        st.session_state.github_token = ""
    if 'openai_key' not in st.session_state:
        st.session_state.openai_key = ""
    if 'repository_url' not in st.session_state:
        st.session_state.repository_url = ""
    if 'credentials_valid' not in st.session_state:
        st.session_state.credentials_valid = False
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False

def validate_github_token(token: str) -> bool:
    """Validate GitHub token format"""
    if not token:
        return False
    # Basic GitHub token format validation
    import re
    return bool(re.match(r'^gh[a-z]_[A-Za-z0-9_]{36,}$', token))

def validate_openai_key(key: str) -> bool:
    """Validate OpenAI API key format"""
    if not key:
        return False
    return key.startswith('sk-') and len(key) > 20

def validate_repository_url(url: str) -> tuple[bool, str, str]:
    """Validate GitHub repository URL and extract owner/name"""
    if not url:
        return False, "", ""
    
    import re
    # Support both full URLs and owner/repo format
    if url.startswith('https://github.com/'):
        pattern = r'https://github\.com/([^/]+)/([^/]+)/?'
        match = re.match(pattern, url)
        if match:
            owner, name = match.groups()
            if name.endswith('.git'):
                name = name[:-4]
            return True, owner, name
    elif '/' in url and not url.startswith('http'):
        # Handle owner/repo format
        parts = url.split('/')
        if len(parts) == 2:
            owner, name = parts
            return True, owner, name
    
    return False, "", ""

@with_error_handling(context="test_github_connection", fallback=(False, "Connection test failed"))
def test_github_connection(token: str, repo_owner: str, repo_name: str) -> tuple[bool, str]:
    """Test GitHub API connection and repository access with enhanced error handling"""
    try:
        from models.config import GitHubCredentials, RepositoryConfig
        from utils.github_client import GitHubClient
        
        # Validate inputs
        if not token or not token.strip():
            return False, "GitHub token is required"
        
        if not repo_owner or not repo_name:
            return False, "Repository owner and name are required"
        
        # Create credentials and client
        credentials = GitHubCredentials(personal_access_token=token.strip())
        client = GitHubClient(credentials)
        
        # Test authentication
        if not client.authenticate():
            return False, "Authentication failed - invalid token or insufficient permissions"
        
        # Test repository access
        repo_config = RepositoryConfig(owner=repo_owner.strip(), name=repo_name.strip())
        if not client.validate_repository_access(repo_config):
            return False, f"Cannot access repository {repo_owner}/{repo_name} - check permissions"
        
        return True, "Connection successful - GitHub API and repository access verified"
        
    except Exception as e:
        error_info = error_handler.handle_github_api_error(e, "connection_test")
        return False, f"Connection failed: {error_info.get('message', str(e))}"

@with_error_handling(context="test_openai_connection", fallback=(False, "OpenAI connection test failed"))
def test_openai_connection(api_key: str) -> tuple[bool, str]:
    """Test OpenAI API connection with enhanced error handling"""
    try:
        # Validate input
        if not api_key or not api_key.strip():
            return False, "OpenAI API key is required"
        
        if not api_key.startswith('sk-'):
            return False, "Invalid OpenAI API key format - should start with 'sk-'"
        
        from models.config import OpenAICredentials
        from utils.chatgpt_analyzer import ChatGPTAnalyzer
        
        # Create credentials and analyzer
        credentials = OpenAICredentials(api_key=api_key.strip())
        analyzer = ChatGPTAnalyzer(credentials)
        
        # Test credential validation first
        if not analyzer.validate_credentials():
            return False, "OpenAI API key validation failed - check key and account status"
        
        return True, "Connection successful - OpenAI API access verified"
            
    except Exception as e:
        error_info = error_handler.handle_openai_api_error(e, "connection_test")
        return False, f"Connection failed: {error_info.get('message', str(e))}"

def render_configuration_panel():
    """Render the configuration and credentials panel"""
    st.header("⚙️ Configuration")
    
    # GitHub Configuration
    st.subheader("🐙 GitHub Configuration")
    
    github_token = st.text_input(
        "GitHub Personal Access Token",
        type="password",
        value=st.session_state.github_token,
        help="Enter your GitHub personal access token with repo access",
        key="github_token_input"
    )
    
    if github_token != st.session_state.github_token:
        st.session_state.github_token = github_token
        st.session_state.credentials_valid = False
    
    # GitHub token validation
    if github_token:
        if validate_github_token(github_token):
            st.success("✅ Valid GitHub token format")
        else:
            st.error("❌ Invalid GitHub token format")
    
    # Repository Configuration
    repository_url = st.text_input(
        "Repository URL or Owner/Name",
        value=st.session_state.repository_url,
        help="Enter GitHub repository URL (https://github.com/owner/repo) or owner/repo format",
        key="repo_url_input"
    )
    
    if repository_url != st.session_state.repository_url:
        st.session_state.repository_url = repository_url
        st.session_state.credentials_valid = False
    
    # Repository validation
    repo_valid = False
    repo_owner = ""
    repo_name = ""
    
    if repository_url:
        repo_valid, repo_owner, repo_name = validate_repository_url(repository_url)
        if repo_valid:
            st.success(f"✅ Valid repository: {repo_owner}/{repo_name}")
        else:
            st.error("❌ Invalid repository URL format")
    
    # Test GitHub connection
    if st.button("🔍 Test GitHub Connection", disabled=not (github_token and repo_valid)):
        with loading_context("github_connection_test", "Testing GitHub connection...") as update_progress:
            try:
                update_progress(0.2, "Validating credentials...")
                success, message = test_github_connection(github_token, repo_owner, repo_name)
                
                update_progress(0.8, "Verifying repository access...")
                
                if success:
                    update_progress(1.0, "Connection verified!")
                    show_success(f"GitHub connection successful: {message}")
                    st.session_state.github_valid = True
                else:
                    show_error(f"GitHub connection failed: {message}")
                    st.session_state.github_valid = False
            except Exception as e:
                show_error(f"Connection test failed: {str(e)}")
                st.session_state.github_valid = False
    
    st.markdown("---")
    
    # OpenAI Configuration
    st.subheader("🤖 OpenAI Configuration")
    
    openai_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=st.session_state.openai_key,
        help="Enter your OpenAI API key for AI-powered insights",
        key="openai_key_input"
    )
    
    if openai_key != st.session_state.openai_key:
        st.session_state.openai_key = openai_key
        st.session_state.credentials_valid = False
    
    # OpenAI key validation
    if openai_key:
        if validate_openai_key(openai_key):
            st.success("✅ Valid OpenAI API key format")
        else:
            st.error("❌ Invalid OpenAI API key format")
    
    # Test OpenAI connection
    if st.button("🔍 Test OpenAI Connection", disabled=not openai_key):
        with loading_context("openai_connection_test", "Testing OpenAI connection...") as update_progress:
            try:
                update_progress(0.3, "Validating API key...")
                success, message = test_openai_connection(openai_key)
                
                update_progress(0.8, "Testing API access...")
                
                if success:
                    update_progress(1.0, "Connection verified!")
                    show_success(f"OpenAI connection successful: {message}")
                    st.session_state.openai_valid = True
                else:
                    show_error(f"OpenAI connection failed: {message}")
                    st.session_state.openai_valid = False
            except Exception as e:
                show_error(f"Connection test failed: {str(e)}")
                st.session_state.openai_valid = False
    
    st.markdown("---")
    
    # Configuration Status
    st.subheader("📋 Configuration Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        github_status = getattr(st.session_state, 'github_valid', False)
        if github_status:
            st.success("✅ GitHub Connected")
        elif github_token and repo_valid:
            st.warning("⚠️ GitHub Not Tested")
        else:
            st.error("❌ GitHub Not Configured")
    
    with col2:
        openai_status = getattr(st.session_state, 'openai_valid', False)
        if openai_status:
            st.success("✅ OpenAI Connected")
        elif openai_key:
            st.warning("⚠️ OpenAI Not Tested")
        else:
            st.info("ℹ️ OpenAI Optional")
    
    # Update overall credentials status
    st.session_state.credentials_valid = (
        github_status and 
        github_token and 
        repo_valid
    )
    
    if st.session_state.credentials_valid:
        st.success("🎉 Configuration Complete! You can now load data and analyze productivity.")
        
        # Load Data button
        if st.button("📊 Load Repository Data", type="primary", disabled=is_loading("data_loading")):
            with loading_context("data_loading", "Loading repository data...") as update_progress:
                try:
                    update_progress(0.1, "Initializing data collection...")
                    
                    # Simulate data loading steps
                    steps = [
                        "Connecting to GitHub API",
                        "Fetching repository information", 
                        "Loading commit history",
                        "Processing pull requests",
                        "Analyzing code reviews",
                        "Calculating metrics"
                    ]
                    
                    for i, step in enumerate(steps):
                        progress = (i + 1) / len(steps)
                        update_progress(progress, step)
                        time.sleep(0.5)  # Simulate processing time
                    
                    # This will be implemented in later tasks
                    show_info("Data loading will be fully implemented in upcoming tasks.")
                    st.session_state.data_loaded = True
                    
                except Exception as e:
                    show_error(f"Data loading failed: {str(e)}")
                    st.session_state.data_loaded = False
    else:
        st.info("Complete the configuration above to start analyzing productivity data.")

def render_sidebar_navigation():
    """Render sidebar navigation and configuration"""
    with st.sidebar:
        st.header("🚀 Navigation")
        
        # Navigation buttons
        for section, icon in DASHBOARD_SECTIONS.items():
            if st.button(f"{icon} {section}", key=f"nav_{section}", use_container_width=True):
                st.session_state.current_section = section
                st.rerun()
        
        st.markdown("---")
        
        # Configuration panel
        render_configuration_panel()

def get_sample_metrics():
    """Generate sample metrics for demonstration"""
    from datetime import datetime, timedelta
    from models.metrics import ProductivityMetrics, CommitMetrics, PRMetrics, ReviewMetrics, IssueMetrics, VelocityPoint
    
    # Create sample data when real data is not available
    if not st.session_state.data_loaded:
        return None
    
    # Sample metrics (in real implementation, this would come from data processing)
    period_start = datetime.now() - timedelta(days=30)
    period_end = datetime.now()
    
    commit_metrics = CommitMetrics(
        total_commits=45,
        commit_frequency={"daily": 1.5, "weekly": 10.5, "monthly": 45},
        average_additions=125.5,
        average_deletions=45.2,
        average_files_changed=3.2,
        most_active_hours=[9, 10, 14, 15, 16],
        commit_message_length_avg=52.3
    )
    
    pr_metrics = PRMetrics(
        total_prs=12,
        merged_prs=10,
        closed_prs=1,
        open_prs=1,
        average_time_to_merge=24.5,
        average_additions=245.8,
        average_deletions=89.3,
        average_commits_per_pr=3.8,
        merge_rate=83.3
    )
    
    review_metrics = ReviewMetrics(
        total_reviews_given=18,
        total_reviews_received=15,
        average_review_time=4.2,
        approval_rate=72.2,
        change_request_rate=22.2,
        review_participation_rate=85.7
    )
    
    issue_metrics = IssueMetrics(
        total_issues=8,
        closed_issues=6,
        open_issues=2,
        average_time_to_close=48.5,
        resolution_rate=75.0,
        issues_created=3,
        issues_assigned=5
    )
    
    # Sample velocity points
    velocity_trends = []
    for i in range(7):
        date = period_end - timedelta(days=i)
        velocity_trends.append(VelocityPoint(
            timestamp=date,
            commits=6 + (i % 3),
            additions=150 + (i * 20),
            deletions=50 + (i * 10),
            pull_requests=1 if i % 2 == 0 else 2,
            issues_closed=1 if i % 3 == 0 else 0
        ))
    
    return ProductivityMetrics(
        period_start=period_start,
        period_end=period_end,
        commit_metrics=commit_metrics,
        pr_metrics=pr_metrics,
        review_metrics=review_metrics,
        issue_metrics=issue_metrics,
        velocity_trends=velocity_trends,
        time_distribution={"coding": 65.5, "reviewing": 20.3, "meetings": 14.2}
    )

def render_metrics_summary(metrics):
    """Render high-level metrics summary"""
    if not metrics:
        st.info("📊 Load repository data to see productivity metrics")
        return
    
    st.subheader("📈 Productivity Summary")
    
    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Commits", 
            metrics.commit_metrics.total_commits,
            delta=f"{metrics.daily_commit_average:.1f}/day",
            help="Total commits in the selected period"
        )
    
    with col2:
        st.metric(
            "Pull Requests", 
            metrics.pr_metrics.total_prs,
            delta=f"{metrics.pr_metrics.merge_rate:.1f}% merged",
            help="Total pull requests created"
        )
    
    with col3:
        st.metric(
            "Code Reviews", 
            metrics.review_metrics.total_reviews_given,
            delta=f"{metrics.review_metrics.review_participation_rate:.1f}% participation",
            help="Code reviews given to others"
        )
    
    with col4:
        st.metric(
            "Issues Resolved", 
            metrics.issue_metrics.closed_issues,
            delta=f"{metrics.issue_metrics.resolution_rate:.1f}% rate",
            help="Issues closed in the period"
        )

def render_detailed_metrics(metrics):
    """Render detailed metrics breakdown"""
    if not metrics:
        return
    
    st.subheader("📊 Detailed Metrics")
    
    # Create tabs for different metric categories
    tab1, tab2, tab3, tab4 = st.tabs(["💻 Commits", "🔄 Pull Requests", "👥 Reviews", "🐛 Issues"])
    
    with tab1:
        st.markdown("**Commit Activity**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Average Additions", f"{metrics.commit_metrics.average_additions:.0f}")
            st.metric("Average Deletions", f"{metrics.commit_metrics.average_deletions:.0f}")
            st.metric("Files per Commit", f"{metrics.commit_metrics.average_files_changed:.1f}")
        
        with col2:
            st.metric("Message Length", f"{metrics.commit_metrics.commit_message_length_avg:.0f} chars")
            if metrics.commit_metrics.most_active_hours:
                active_hours = ", ".join(f"{h}:00" for h in metrics.commit_metrics.most_active_hours[:3])
                st.metric("Most Active Hours", active_hours)
    
    with tab2:
        st.markdown("**Pull Request Performance**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Merged PRs", metrics.pr_metrics.merged_prs)
            st.metric("Open PRs", metrics.pr_metrics.open_prs)
            st.metric("Closed PRs", metrics.pr_metrics.closed_prs)
        
        with col2:
            if metrics.pr_metrics.average_time_to_merge:
                st.metric("Avg Time to Merge", f"{metrics.pr_metrics.average_time_to_merge:.1f} hours")
            st.metric("Avg Commits/PR", f"{metrics.pr_metrics.average_commits_per_pr:.1f}")
            st.metric("Avg Changes/PR", f"{metrics.pr_metrics.average_additions + metrics.pr_metrics.average_deletions:.0f}")
    
    with tab3:
        st.markdown("**Code Review Activity**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Reviews Given", metrics.review_metrics.total_reviews_given)
            st.metric("Reviews Received", metrics.review_metrics.total_reviews_received)
        
        with col2:
            st.metric("Approval Rate", f"{metrics.review_metrics.approval_rate:.1f}%")
            st.metric("Change Request Rate", f"{metrics.review_metrics.change_request_rate:.1f}%")
            if metrics.review_metrics.average_review_time:
                st.metric("Avg Review Time", f"{metrics.review_metrics.average_review_time:.1f} hours")
    
    with tab4:
        st.markdown("**Issue Management**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Issues Created", metrics.issue_metrics.issues_created)
            st.metric("Issues Assigned", metrics.issue_metrics.issues_assigned)
        
        with col2:
            st.metric("Issues Closed", metrics.issue_metrics.closed_issues)
            if metrics.issue_metrics.average_time_to_close:
                st.metric("Avg Time to Close", f"{metrics.issue_metrics.average_time_to_close:.1f} hours")

def render_activity_distribution(metrics):
    """Render time distribution chart"""
    if not metrics or not metrics.time_distribution:
        return
    
    st.subheader("⏰ Time Distribution")
    
    # Create a simple bar chart for time distribution
    import pandas as pd
    
    df = pd.DataFrame(
        list(metrics.time_distribution.items()),
        columns=['Activity', 'Hours']
    )
    
    st.bar_chart(df.set_index('Activity'))

def render_overview_section():
    """Render the overview dashboard section"""
    st.header("📊 Dashboard Overview")
    st.markdown("Welcome to your GitHub Productivity Dashboard")
    
    # Status indicators
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.credentials_valid:
            st.success("✅ Credentials Configured")
        else:
            st.warning("⚠️ Configure Credentials")
    
    with col2:
        if st.session_state.data_loaded:
            st.success("✅ Data Loaded")
        else:
            st.info("📊 No Data Loaded")
    
    with col3:
        if st.session_state.credentials_valid and st.session_state.data_loaded:
            st.success("🔄 Ready for Analysis")
        else:
            st.info("🔄 Configure & Load Data")
    
    st.markdown("---")
    
    # Get metrics data
    metrics = get_sample_metrics()
    
    # Render metrics summary
    render_metrics_summary(metrics)
    
    if metrics:
        st.markdown("---")
        
        # Render detailed metrics
        render_detailed_metrics(metrics)
        
        st.markdown("---")
        
        # Render activity distribution
        render_activity_distribution(metrics)
        
        # Auto-refresh functionality
        if st.session_state.credentials_valid and st.session_state.data_loaded:
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col2:
                if st.button("🔄 Refresh Data", help="Reload data from GitHub"):
                    with st.spinner("Refreshing data..."):
                        # In real implementation, this would reload data
                        st.success("Data refreshed successfully!")
                        st.rerun()

def render_metrics_section():
    """Render the metrics dashboard section"""
    st.header("📈 Productivity Metrics")
    st.markdown("Detailed productivity metrics and KPIs")
    
    # Get metrics data
    metrics = get_sample_metrics()
    
    if not metrics:
        st.info("📊 Configure credentials and load repository data to see detailed metrics")
        return
    
    # Period information
    st.subheader("📅 Analysis Period")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Period Start", metrics.period_start.strftime("%Y-%m-%d"))
    with col2:
        st.metric("Period End", metrics.period_end.strftime("%Y-%m-%d"))
    with col3:
        st.metric("Total Days", metrics.period_days)
    
    st.markdown("---")
    
    # Render all metric components
    render_metrics_summary(metrics)
    
    st.markdown("---")
    
    render_detailed_metrics(metrics)
    
    st.markdown("---")
    
    render_activity_distribution(metrics)
    
    # Velocity trends preview
    if metrics.velocity_trends:
        st.subheader("📈 Recent Velocity Trends")
        st.info("Interactive velocity charts will be available in the Analytics section.")
        
        # Show recent velocity data in a simple table
        import pandas as pd
        
        recent_velocity = metrics.velocity_trends[:5]  # Last 5 days
        df = pd.DataFrame([
            {
                'Date': vp.timestamp.strftime("%Y-%m-%d"),
                'Commits': vp.commits,
                'Additions': vp.additions,
                'Deletions': vp.deletions,
                'PRs': vp.pull_requests,
                'Issues': vp.issues_closed
            }
            for vp in recent_velocity
        ])
        
        st.dataframe(df, use_container_width=True)

def render_analytics_section():
    """Render the analytics dashboard section"""
    st.header("🔍 Detailed Analytics")
    st.markdown("In-depth analysis and visualizations")
    
    # Get metrics data
    metrics = get_sample_metrics()
    
    if not metrics:
        st.info("📊 Configure credentials and load repository data to see detailed analytics")
        return
    
    # Import visualization components
    from components.visualizations import render_time_series_section, render_detailed_analytics_section
    
    # Create tabs for different analytics views
    tab1, tab2 = st.tabs(["📈 Time-Series Analysis", "🔍 Detailed Analytics"])
    
    with tab1:
        # Render time-series analysis section
        render_time_series_section(metrics)
    
    with tab2:
        # Render detailed analytics and drill-down views
        render_detailed_analytics_section(metrics)

def detect_data_changes(metrics):
    """Detect if productivity data has changed since last analysis"""
    if 'last_data_signature' not in st.session_state:
        st.session_state.last_data_signature = None
    
    # Create a signature of the current data
    current_signature = {
        'period_start': metrics.period_start,
        'period_end': metrics.period_end,
        'total_commits': metrics.commit_metrics.total_commits,
        'total_prs': metrics.pr_metrics.total_prs,
        'total_reviews': metrics.review_metrics.total_reviews_given,
        'total_issues': metrics.issue_metrics.total_issues
    }
    
    # Check if data has changed
    if st.session_state.last_data_signature != current_signature:
        st.session_state.last_data_signature = current_signature
        return True
    
    return False

@with_error_handling(context="generate_real_time_analysis")
def generate_real_time_analysis(metrics, analysis_type="summary"):
    """Generate real-time AI analysis with comprehensive error handling and fallbacks"""
    try:
        # Validate inputs
        if not metrics:
            raise ValueError("Metrics data is required for analysis")
        
        if not st.session_state.get('openai_key'):
            raise ValueError("OpenAI API key is required for AI analysis")
        
        from models.config import OpenAICredentials
        from utils.chatgpt_analyzer import ChatGPTAnalyzer, ProductivityInsightGenerator
        
        # Create analyzer with error handling
        credentials = OpenAICredentials(api_key=st.session_state.openai_key.strip())
        analyzer = ChatGPTAnalyzer(credentials)
        
        # Validate credentials first
        if not analyzer.validate_credentials():
            raise ValueError("OpenAI API credentials validation failed - check key and account status")
        
        # Generate analysis based on type with fallbacks
        try:
            if analysis_type == "summary":
                return analyzer.analyze_productivity_trends(metrics)
            elif analysis_type == "detailed":
                insight_generator = ProductivityInsightGenerator(analyzer)
                return insight_generator.generate_comprehensive_insights(metrics)
            elif analysis_type == "trends":
                return analyzer.analyze_trends(metrics)
            elif analysis_type == "anomalies":
                return analyzer.identify_anomalies(metrics)
            else:
                raise ValueError(f"Unknown analysis type: {analysis_type}")
        
        except Exception as analysis_error:
            # Create fallback analysis based on type
            return create_fallback_analysis(metrics, analysis_type, str(analysis_error))
            
    except Exception as e:
        error_handler.handle_openai_api_error(e, f"real_time_analysis_{analysis_type}")
        raise

def create_fallback_analysis(metrics, analysis_type: str, error_message: str):
    """Create fallback analysis when AI analysis fails"""
    fallback_data = {
        'status': 'fallback',
        'error_message': error_message,
        'generated_at': datetime.now().isoformat(),
        'analysis_type': analysis_type
    }
    
    if analysis_type == "summary":
        from models.metrics import AnalysisReport
        return AnalysisReport(
            generated_at=datetime.now(),
            summary=f"Basic analysis for {metrics.period_days} day period with {metrics.commit_metrics.total_commits} commits.",
            key_insights=[
                f"Total commits: {metrics.commit_metrics.total_commits}",
                f"Pull requests: {metrics.pr_metrics.total_prs} ({metrics.pr_metrics.merge_rate:.1f}% merge rate)",
                f"Code reviews: {metrics.review_metrics.total_reviews_given} given"
            ],
            recommendations=[
                "AI analysis temporarily unavailable - basic metrics shown",
                "Try refreshing the analysis in a few minutes"
            ],
            anomalies=[],
            confidence_score=0.5
        )
    
    elif analysis_type == "detailed":
        fallback_data.update({
            'performance_score': 75.0,
            'overview': {
                'summary': f"Fallback analysis for {metrics.period_days} day period",
                'key_insights': [f"Processed {metrics.commit_metrics.total_commits} commits"],
                'confidence_score': 0.5
            },
            'trends': {
                'trend_direction': 'stable',
                'key_patterns': ['AI analysis temporarily unavailable'],
                'confidence_score': 0.5
            }
        })
        return fallback_data
    
    elif analysis_type == "trends":
        return {
            'trend_direction': 'stable',
            'key_patterns': ['Trend analysis temporarily unavailable'],
            'confidence_score': 0.0,
            'fallback': True
        }
    
    elif analysis_type == "anomalies":
        return []
    
    return fallback_data

def auto_generate_analysis_if_needed(metrics):
    """Automatically generate analysis if data has changed and auto-refresh is enabled"""
    # Check if auto-refresh is enabled for any analysis type
    auto_refresh_enabled = (
        st.session_state.get('auto_refresh_summary', False) or
        st.session_state.get('auto_refresh_detailed', False)
    )
    
    if not auto_refresh_enabled:
        return
    
    # Check if data has changed
    if not detect_data_changes(metrics):
        return
    
    # Check if OpenAI is configured
    if not st.session_state.openai_key:
        return
    
    # Show notification about auto-refresh
    st.info("🔄 Data changes detected - auto-generating analysis...")
    
    try:
        # Auto-generate summary analysis if enabled
        if st.session_state.get('auto_refresh_summary', False):
            cache_key = f"analysis_{metrics.period_start}_{metrics.period_end}_{hash(str(metrics.commit_metrics.total_commits))}"
            
            with st.spinner("Updating AI analysis..."):
                analysis_report = generate_real_time_analysis(metrics, "summary")
                st.session_state.ai_analysis_cache[cache_key] = analysis_report
            
            st.success("✅ Analysis updated automatically")
        
        # Auto-generate detailed insights if enabled
        if st.session_state.get('auto_refresh_detailed', False):
            cache_key = f"detailed_{metrics.period_start}_{metrics.period_end}_{hash(str(metrics.commit_metrics.total_commits))}"
            
            with st.spinner("Updating detailed insights..."):
                detailed_insights = generate_real_time_analysis(metrics, "detailed")
                st.session_state.detailed_insights_cache[cache_key] = detailed_insights
            
            st.success("✅ Detailed insights updated automatically")
    
    except Exception as e:
        st.warning(f"⚠️ Auto-refresh failed: {str(e)}")
        st.info("You can still generate analysis manually using the buttons below.")

def render_ai_analysis_summary(metrics):
    """Render AI-generated analysis summary with real-time generation"""
    st.subheader("📋 AI Analysis Summary")
    st.markdown("Comprehensive productivity analysis powered by ChatGPT")
    
    # Initialize session state for analysis cache and loading states
    if 'ai_analysis_cache' not in st.session_state:
        st.session_state.ai_analysis_cache = {}
    if 'analysis_loading' not in st.session_state:
        st.session_state.analysis_loading = False
    
    # Create cache key based on metrics
    cache_key = f"analysis_{metrics.period_start}_{metrics.period_end}_{hash(str(metrics.commit_metrics.total_commits))}"
    
    # Auto-generate analysis if not cached and not currently loading
    analysis_report = None
    if cache_key in st.session_state.ai_analysis_cache:
        analysis_report = st.session_state.ai_analysis_cache[cache_key]
        
        # Show cache status
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.success("✅ Analysis ready (cached)")
    
    # Control buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🔄 Generate Analysis", type="primary", use_container_width=True, 
                    disabled=st.session_state.analysis_loading):
            st.session_state.analysis_loading = True
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear Cache", use_container_width=True, 
                    disabled=st.session_state.analysis_loading):
            if cache_key in st.session_state.ai_analysis_cache:
                del st.session_state.ai_analysis_cache[cache_key]
            st.success("Cache cleared")
            st.rerun()
    
    with col3:
        auto_refresh = st.checkbox("🔄 Auto-refresh", 
                                  key="auto_refresh_summary",
                                  help="Automatically refresh analysis when data changes")
    
    # Handle loading state and analysis generation
    if st.session_state.analysis_loading:
        with loading_context("ai_analysis", "Analyzing your productivity data...") as update_progress:
            try:
                # Update progress with detailed steps
                update_progress(0.1, "Initializing AI analysis...")
                
                update_progress(0.3, "Connecting to AI service...")
                
                # Generate analysis
                update_progress(0.5, "Processing productivity metrics...")
                analysis_report = generate_real_time_analysis(metrics, "summary")
                
                update_progress(0.8, "Generating insights and recommendations...")
                
                # Cache the result
                st.session_state.ai_analysis_cache[cache_key] = analysis_report
                
                update_progress(1.0, "Analysis complete!")
                
                # Reset loading state
                st.session_state.analysis_loading = False
                
                # Show success and rerun to display results
                show_success("AI analysis generated successfully!")
                st.rerun()
                
            except Exception as e:
                # Reset loading state
                st.session_state.analysis_loading = False
                
                # Show comprehensive error message
                feedback_manager.show_error_message(
                    "AI Analysis Generation Failed",
                    error=e,
                    suggestions=[
                        "Check your OpenAI API key is valid and has sufficient credits",
                        "Ensure you have a stable internet connection", 
                        "Try again in a few moments if the service is temporarily unavailable",
                        "Consider using the dashboard without AI features for now"
                    ],
                    retry_callback=lambda: st.session_state.update({'analysis_loading': True}) or st.rerun()
                )
                
                return
    
    # Display analysis if available
    if analysis_report:
        st.markdown("---")
        
        # Summary section
        st.subheader("📊 Summary")
        st.write(analysis_report.summary)
        
        # Key insights
        if analysis_report.key_insights:
            st.subheader("💡 Key Insights")
            for i, insight in enumerate(analysis_report.key_insights, 1):
                st.write(f"**{i}.** {insight}")
        
        # Recommendations
        if analysis_report.recommendations:
            st.subheader("🎯 Recommendations")
            for i, recommendation in enumerate(analysis_report.recommendations, 1):
                st.write(f"**{i}.** {recommendation}")
        
        # Anomalies
        if analysis_report.anomalies:
            st.subheader("⚠️ Anomalies Detected")
            for anomaly in analysis_report.anomalies:
                severity_color = {
                    'LOW': 'info',
                    'MEDIUM': 'warning', 
                    'HIGH': 'error'
                }.get(anomaly.severity, 'info')
                
                if severity_color == 'error':
                    st.error(f"**{anomaly.metric_name}**: {anomaly.description}")
                elif severity_color == 'warning':
                    st.warning(f"**{anomaly.metric_name}**: {anomaly.description}")
                else:
                    st.info(f"**{anomaly.metric_name}**: {anomaly.description}")
        
        # Confidence score
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            confidence_percentage = int(analysis_report.confidence_score * 100)
            st.metric("Analysis Confidence", f"{confidence_percentage}%")
        
        # Analysis metadata
        st.caption(f"Analysis generated at: {analysis_report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")

def render_ai_question_interface(metrics):
    """Render AI question answering interface"""
    st.subheader("❓ Ask Questions About Your Data")
    st.markdown("Ask specific questions about your productivity metrics and get AI-powered answers")
    
    # Initialize session state for Q&A history
    if 'qa_history' not in st.session_state:
        st.session_state.qa_history = []
    
    # Question input
    user_question = st.text_area(
        "What would you like to know about your productivity?",
        placeholder="Examples:\n- What are my strongest productivity patterns?\n- How can I improve my code review participation?\n- What trends do you see in my commit activity?",
        height=100,
        key="ai_question_input"
    )
    
    # Initialize loading state for questions
    if 'question_loading' not in st.session_state:
        st.session_state.question_loading = False
    
    # Submit question button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🤖 Ask AI", type="primary", use_container_width=True, 
                    disabled=not user_question.strip() or st.session_state.question_loading):
            if user_question.strip():
                st.session_state.question_loading = True
                st.rerun()
    
    # Handle question processing
    if st.session_state.question_loading and user_question.strip():
        with st.spinner("🤖 Analyzing your question..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                progress_bar.progress(25)
                status_text.text("Processing question...")
                
                from models.config import OpenAICredentials
                from utils.chatgpt_analyzer import ChatGPTAnalyzer
                
                # Create analyzer
                credentials = OpenAICredentials(api_key=st.session_state.openai_key)
                analyzer = ChatGPTAnalyzer(credentials)
                
                progress_bar.progress(50)
                status_text.text("Generating AI response...")
                
                # Get answer
                answer = analyzer.answer_user_question(user_question, metrics)
                
                progress_bar.progress(90)
                status_text.text("Finalizing response...")
                
                # Add to history
                st.session_state.qa_history.append({
                    'question': user_question,
                    'answer': answer,
                    'timestamp': datetime.now()
                })
                
                progress_bar.progress(100)
                status_text.text("Complete!")
                
                # Reset states
                st.session_state.question_loading = False
                st.session_state.ai_question_input = ""
                
                st.success("✅ Question answered!")
                st.rerun()
                
            except Exception as e:
                # Handle errors gracefully
                progress_bar.empty()
                status_text.empty()
                st.session_state.question_loading = False
                
                st.error("❌ Failed to process question")
                
                with st.expander("Error Details"):
                    st.code(str(e))
                    st.markdown("**Troubleshooting:**")
                    st.markdown("• Verify your OpenAI API key is valid")
                    st.markdown("• Check your internet connection")
                    st.markdown("• Try rephrasing your question")
    
    # Display Q&A history
    if st.session_state.qa_history:
        st.markdown("---")
        st.subheader("💬 Q&A History")
        
        # Show most recent questions first
        for i, qa in enumerate(reversed(st.session_state.qa_history[-5:])):  # Show last 5
            with st.expander(f"Q: {qa['question'][:100]}{'...' if len(qa['question']) > 100 else ''}", expanded=(i == 0)):
                st.markdown(f"**Question:** {qa['question']}")
                st.markdown(f"**Answer:** {qa['answer']}")
                st.caption(f"Asked at: {qa['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Clear history button
        if st.button("🗑️ Clear Q&A History"):
            st.session_state.qa_history = []
            st.rerun()
    
    # Suggested questions
    st.markdown("---")
    st.subheader("💡 Suggested Questions")
    
    suggested_questions = [
        "What are my most productive days and times?",
        "How does my code review participation compare to best practices?",
        "What patterns do you see in my pull request activity?",
        "Are there any concerning trends in my productivity?",
        "How can I improve my development workflow?",
        "What's my strongest area of contribution?"
    ]
    
    cols = st.columns(2)
    for i, question in enumerate(suggested_questions):
        col = cols[i % 2]
        with col:
            if st.button(f"💭 {question}", key=f"suggested_q_{i}", use_container_width=True):
                st.session_state.ai_question_input = question
                st.rerun()

def render_ai_detailed_insights(metrics):
    """Render detailed AI insights and analysis"""
    st.subheader("🔍 Detailed AI Insights")
    st.markdown("Comprehensive analysis across all productivity dimensions")
    
    # Initialize session state for detailed insights cache
    if 'detailed_insights_cache' not in st.session_state:
        st.session_state.detailed_insights_cache = {}
    
    # Create cache key
    cache_key = f"detailed_{metrics.period_start}_{metrics.period_end}_{hash(str(metrics.commit_metrics.total_commits))}"
    
    # Initialize loading state for detailed insights
    if 'detailed_loading' not in st.session_state:
        st.session_state.detailed_loading = False
    
    # Control buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🔍 Generate Insights", type="primary", use_container_width=True,
                    disabled=st.session_state.detailed_loading):
            st.session_state.detailed_loading = True
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear Insights", use_container_width=True,
                    disabled=st.session_state.detailed_loading):
            if cache_key in st.session_state.detailed_insights_cache:
                del st.session_state.detailed_insights_cache[cache_key]
            st.success("Insights cache cleared")
            st.rerun()
    
    with col3:
        real_time_mode = st.checkbox("⚡ Real-time", 
                                   key="auto_refresh_detailed",
                                   help="Generate insights automatically when data changes")
    
    # Handle detailed insights generation
    if st.session_state.detailed_loading:
        with st.spinner("🤖 Generating comprehensive analysis..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                progress_bar.progress(20)
                status_text.text("Initializing AI analysis...")
                
                # Generate detailed insights using real-time function
                detailed_insights = generate_real_time_analysis(metrics, "detailed")
                
                progress_bar.progress(60)
                status_text.text("Processing comprehensive insights...")
                
                # Cache the result
                st.session_state.detailed_insights_cache[cache_key] = detailed_insights
                
                progress_bar.progress(90)
                status_text.text("Finalizing insights...")
                
                progress_bar.progress(100)
                status_text.text("Insights ready!")
                
                # Reset loading state
                st.session_state.detailed_loading = False
                
                st.success("✅ Detailed insights generated successfully!")
                st.rerun()
                
            except Exception as e:
                # Handle errors gracefully
                progress_bar.empty()
                status_text.empty()
                st.session_state.detailed_loading = False
                
                st.error("❌ Failed to generate detailed insights")
                
                with st.expander("Error Details"):
                    st.code(str(e))
                    st.markdown("**Troubleshooting:**")
                    st.markdown("• Ensure OpenAI API key has sufficient credits")
                    st.markdown("• Check network connectivity")
                    st.markdown("• Try reducing the analysis scope")
                
                return
    
    # Display detailed insights if available
    if cache_key in st.session_state.detailed_insights_cache:
        insights = st.session_state.detailed_insights_cache[cache_key]
        
        st.markdown("---")
        
        # Performance score
        if 'performance_score' in insights:
            st.subheader("🎯 Overall Performance Score")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                score = insights['performance_score']
                score_color = 'success' if score >= 80 else 'warning' if score >= 60 else 'error'
                st.metric("Performance Score", f"{score}/100")
                
                if score >= 80:
                    st.success("🎉 Excellent performance!")
                elif score >= 60:
                    st.warning("⚠️ Good performance with room for improvement")
                else:
                    st.error("📈 Performance needs attention")
        
        # Trend analysis
        if 'trends' in insights and insights['trends']:
            st.subheader("📈 Trend Analysis")
            trend_data = insights['trends']
            
            if 'trend_direction' in trend_data:
                direction = trend_data['trend_direction']
                direction_emoji = {
                    'increasing': '📈',
                    'decreasing': '📉',
                    'stable': '➡️',
                    'volatile': '📊'
                }.get(direction, '📊')
                
                st.write(f"{direction_emoji} **Overall Trend:** {direction.title()}")
            
            if 'key_patterns' in trend_data:
                st.write("**Key Patterns:**")
                for pattern in trend_data['key_patterns']:
                    st.write(f"• {pattern}")
        
        # Specific insights by category
        categories = [
            ('commit_insights', '💻 Commit Patterns'),
            ('pr_insights', '🔄 Pull Request Patterns'),
            ('review_insights', '👥 Review Patterns'),
            ('issue_insights', '🐛 Issue Patterns')
        ]
        
        for key, title in categories:
            if key in insights and insights[key]:
                st.subheader(title)
                category_insights = insights[key]
                
                # Display insights in a structured way
                cols = st.columns(2)
                col_idx = 0
                
                for insight_key, insight_value in category_insights.items():
                    if insight_key != 'recommendations':
                        col = cols[col_idx % 2]
                        with col:
                            # Format the insight key for display
                            display_key = insight_key.replace('_', ' ').title()
                            
                            if isinstance(insight_value, str):
                                # Color code based on value
                                if 'high' in insight_value.lower() or 'excellent' in insight_value.lower():
                                    st.success(f"**{display_key}:** {insight_value}")
                                elif 'low' in insight_value.lower() or 'needs' in insight_value.lower():
                                    st.warning(f"**{display_key}:** {insight_value}")
                                else:
                                    st.info(f"**{display_key}:** {insight_value}")
                            else:
                                st.write(f"**{display_key}:** {insight_value}")
                        
                        col_idx += 1
                
                # Show recommendations for this category
                if 'recommendations' in category_insights and category_insights['recommendations']:
                    st.write("**Recommendations:**")
                    for rec in category_insights['recommendations']:
                        st.write(f"• {rec}")
        
        # Anomalies section
        if 'anomalies' in insights and insights['anomalies']:
            st.subheader("⚠️ Anomalies and Alerts")
            for anomaly in insights['anomalies']:
                severity = anomaly.get('severity', 'LOW')
                description = anomaly.get('description', 'No description available')
                
                if severity == 'HIGH':
                    st.error(f"🚨 **High Priority:** {description}")
                elif severity == 'MEDIUM':
                    st.warning(f"⚠️ **Medium Priority:** {description}")
                else:
                    st.info(f"ℹ️ **Low Priority:** {description}")
        
        # Generation timestamp
        if 'generated_at' in insights:
            st.caption(f"Insights generated at: {insights['generated_at']}")

def render_ai_insights_section():
    """Render the AI insights dashboard section"""
    st.header("🤖 AI Insights")
    st.markdown("ChatGPT-powered analysis and recommendations")
    
    # Check if OpenAI is configured
    if not st.session_state.openai_key:
        st.warning("⚠️ OpenAI API key required for AI insights")
        st.info("Configure your OpenAI API key in the sidebar to enable AI-powered analysis.")
        return
    
    # Check if data is loaded
    metrics = get_sample_metrics()
    if not metrics:
        st.info("📊 Load repository data to generate AI insights")
        return
    
    # Auto-generate analysis if needed (real-time feature)
    auto_generate_analysis_if_needed(metrics)
    
    # Real-time analysis status
    if detect_data_changes(metrics):
        st.info("🔄 New data detected - consider refreshing your analysis")
    
    # Create tabs for different AI analysis types
    tab1, tab2, tab3 = st.tabs(["📋 Analysis Summary", "❓ Ask Questions", "🔍 Detailed Insights"])
    
    with tab1:
        render_ai_analysis_summary(metrics)
    
    with tab2:
        render_ai_question_interface(metrics)
    
    with tab3:
        render_ai_detailed_insights(metrics)

def render_metrics_export_section(metrics):
    """Render metrics export section with CSV download options"""
    st.subheader("📊 Productivity Metrics Export")
    st.markdown("Export your productivity metrics in CSV format for further analysis")
    
    from utils.export_manager import ExportManager
    export_manager = ExportManager()
    
    # Export options
    st.markdown("**Export Options**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        include_config = st.checkbox(
            "Include Configuration Details",
            value=True,
            help="Include timestamp, period information, and metadata in the export"
        )
        
        include_velocity = st.checkbox(
            "Include Velocity Trends",
            value=True,
            help="Include time-series velocity data in the export"
        )
    
    with col2:
        export_format = st.selectbox(
            "Export Format",
            options=["Complete Metrics", "Velocity Trends Only", "Summary Only"],
            help="Choose what data to include in the export"
        )
        
        date_format = st.selectbox(
            "Date Format",
            options=["YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY"],
            help="Choose date format for the export"
        )
    
    st.markdown("---")
    
    # Export preview
    st.markdown("**Export Preview**")
    
    try:
        if export_format == "Complete Metrics":
            csv_content = export_manager.csv_exporter.export_productivity_metrics(
                metrics, include_config=include_config
            )
        elif export_format == "Velocity Trends Only":
            csv_content = export_manager.csv_exporter.export_velocity_trends_only(metrics)
        else:  # Summary Only
            csv_content = export_manager.csv_exporter.export_productivity_metrics(
                metrics, include_config=include_config
            )
            # Truncate to summary only (first part before velocity trends)
            if "\n\n## Velocity Trends\n" in csv_content:
                csv_content = csv_content.split("\n\n## Velocity Trends\n")[0]
        
        # Show preview (first 20 lines)
        preview_lines = csv_content.split('\n')[:20]
        preview_text = '\n'.join(preview_lines)
        if len(csv_content.split('\n')) > 20:
            remaining_lines = len(csv_content.split('\n')) - 20
            preview_text += f"\n... ({remaining_lines} more lines)"
        
        st.code(preview_text, language="csv")
        
        # Export statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Lines", len(csv_content.split('\n')))
        with col2:
            st.metric("File Size", f"{len(csv_content.encode('utf-8')) / 1024:.1f} KB")
        with col3:
            st.metric("Data Points", len(metrics.velocity_trends) if metrics.velocity_trends else 0)
        
        st.markdown("---")
        
        # Download buttons
        st.markdown("**Download Export**")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            filename = export_manager.create_export_filename("metrics", metrics, "csv")
            st.download_button(
                label="📥 Download CSV",
                data=csv_content,
                file_name=filename,
                mime="text/csv",
                type="primary",
                use_container_width=True
            )
        
        with col2:
            # Create JSON export as well
            import json
            from dataclasses import asdict
            
            json_data = {
                'metadata': export_manager.get_export_metadata(metrics),
                'metrics': asdict(metrics)
            }
            json_content = json.dumps(json_data, indent=2, default=str)
            json_filename = export_manager.create_export_filename("metrics", metrics, "json")
            
            st.download_button(
                label="📄 Download JSON",
                data=json_content,
                file_name=json_filename,
                mime="application/json",
                use_container_width=True
            )
        
        with col3:
            # Create Excel-compatible CSV
            excel_csv = csv_content.replace('\n', '\r\n')  # Windows line endings
            excel_filename = export_manager.create_export_filename("metrics", metrics, "csv")
            
            st.download_button(
                label="📊 Excel CSV",
                data=excel_csv,
                file_name=excel_filename,
                mime="text/csv",
                help="CSV formatted for Excel compatibility",
                use_container_width=True
            )
        
        # Export success message
        st.success("✅ Export ready for download!")
        
        # Additional export options
        with st.expander("🔧 Advanced Export Options"):
            st.markdown("**Custom Date Range Export**")
            
            col1, col2 = st.columns(2)
            with col1:
                custom_start = st.date_input(
                    "Custom Start Date",
                    value=metrics.period_start.date(),
                    min_value=metrics.period_start.date(),
                    max_value=metrics.period_end.date()
                )
            
            with col2:
                custom_end = st.date_input(
                    "Custom End Date", 
                    value=metrics.period_end.date(),
                    min_value=metrics.period_start.date(),
                    max_value=metrics.period_end.date()
                )
            
            if custom_start != metrics.period_start.date() or custom_end != metrics.period_end.date():
                st.info("Custom date range export will filter the data to the selected period")
                
                if st.button("📥 Export Custom Range", use_container_width=True):
                    # Filter metrics for custom range (simplified implementation)
                    st.info("Custom date range filtering will be implemented in a future update")
    
    except Exception as e:
        feedback_manager.show_error_message(
            "Export Generation Failed",
            error=e,
            suggestions=[
                "Ensure all required data is loaded",
                "Try a different export format",
                "Check your browser's download settings",
                "Refresh the page and try again"
            ],
            retry_callback=lambda: st.rerun()
        )

def render_ai_reports_export_section(metrics):
    """Render AI reports export section"""
    st.subheader("🤖 AI Analysis Reports")
    st.markdown("Export AI-generated insights and analysis reports")
    
    # Check if OpenAI is configured
    if not st.session_state.openai_key:
        st.warning("⚠️ OpenAI API key required for AI report exports")
        st.info("Configure your OpenAI API key in the sidebar to enable AI report exports.")
        return
    
    from utils.export_manager import ExportManager
    export_manager = ExportManager()
    
    # Report type selection
    st.markdown("**Report Types**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        report_types = st.multiselect(
            "Select Reports to Export",
            options=[
                "Analysis Summary",
                "Detailed Insights", 
                "Executive Summary",
                "Trend Analysis",
                "Anomaly Report"
            ],
            default=["Analysis Summary"],
            help="Choose which AI reports to include in the export"
        )
    
    with col2:
        export_format = st.selectbox(
            "Export Format",
            options=["Text Report", "Markdown", "JSON Data"],
            help="Choose the format for the exported reports"
        )
        
        include_metadata = st.checkbox(
            "Include Metadata",
            value=True,
            help="Include generation timestamps and configuration details"
        )
    
    if not report_types:
        st.info("Select at least one report type to export")
        return
    
    st.markdown("---")
    
    # Generate and export reports
    st.markdown("**Generate Reports**")
    
    if st.button("🤖 Generate AI Reports", type="primary", use_container_width=True):
        with st.spinner("Generating AI reports..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                reports_content = []
                total_reports = len(report_types)
                
                from models.config import OpenAICredentials
                from utils.chatgpt_analyzer import ChatGPTAnalyzer, ProductivityInsightGenerator
                
                # Initialize AI components
                credentials = OpenAICredentials(api_key=st.session_state.openai_key)
                analyzer = ChatGPTAnalyzer(credentials)
                insight_generator = ProductivityInsightGenerator(analyzer)
                
                for i, report_type in enumerate(report_types):
                    progress = (i + 1) / total_reports
                    progress_bar.progress(progress)
                    status_text.text(f"Generating {report_type}...")
                    
                    if report_type == "Analysis Summary":
                        analysis_report = analyzer.analyze_productivity_trends(metrics)
                        content = export_manager.report_exporter.export_ai_analysis_report(
                            analysis_report, metrics, include_metadata
                        )
                        reports_content.append(("Analysis Summary", content))
                    
                    elif report_type == "Detailed Insights":
                        insights = insight_generator.generate_comprehensive_insights(metrics)
                        content = export_manager.report_exporter.export_comprehensive_insights(
                            insights, metrics
                        )
                        reports_content.append(("Detailed Insights", content))
                    
                    elif report_type == "Executive Summary":
                        executive_summary = insight_generator.generate_executive_summary(metrics)
                        content = export_manager.report_exporter.export_executive_summary(
                            executive_summary, metrics
                        )
                        reports_content.append(("Executive Summary", content))
                    
                    elif report_type == "Trend Analysis":
                        trend_analysis = analyzer.analyze_trends(metrics)
                        content = f"""
TREND ANALYSIS REPORT
====================

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Period: {metrics.period_start.strftime('%Y-%m-%d')} to {metrics.period_end.strftime('%Y-%m-%d')}

Overall Trend Direction: {trend_analysis.get('trend_direction', 'Unknown')}

Key Patterns:
{chr(10).join(f"• {pattern}" for pattern in trend_analysis.get('key_patterns', []))}

Confidence Score: {trend_analysis.get('confidence_score', 0) * 100:.1f}%
"""
                        reports_content.append(("Trend Analysis", content))
                    
                    elif report_type == "Anomaly Report":
                        anomalies = analyzer.identify_anomalies(metrics)
                        content = f"""
ANOMALY DETECTION REPORT
========================

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Period: {metrics.period_start.strftime('%Y-%m-%d')} to {metrics.period_end.strftime('%Y-%m-%d')}

Anomalies Detected: {len(anomalies)}

"""
                        if anomalies:
                            for anomaly in anomalies:
                                content += f"""
[{anomaly.severity}] {anomaly.metric_name}
Description: {anomaly.description}
Detected: {anomaly.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Expected: {anomaly.expected_value}, Actual: {anomaly.actual_value}

"""
                        else:
                            content += "No anomalies detected in the current period.\n"
                        
                        reports_content.append(("Anomaly Report", content))
                
                progress_bar.progress(1.0)
                status_text.text("Reports generated successfully!")
                
                # Combine all reports
                if export_format == "Text Report":
                    report_sections = []
                    for title, content in reports_content:
                        separator = '=' * len(title)
                        section = f"{title}\n{separator}\n\n{content}"
                        report_sections.append(section)
                    combined_content = "\n\n" + "="*80 + "\n\n".join(report_sections)
                elif export_format == "Markdown":
                    report_sections = []
                    for title, content in reports_content:
                        section = f"# {title}\n\n{content}"
                        report_sections.append(section)
                    combined_content = "\n\n---\n\n".join(report_sections)
                else:  # JSON
                    json_data = {
                        'metadata': export_manager.get_export_metadata(metrics, {
                            'report_types': report_types,
                            'ai_model': credentials.model
                        }),
                        'reports': {title: content for title, content in reports_content}
                    }
                    combined_content = json.dumps(json_data, indent=2, default=str)
                
                # Show preview
                st.markdown("**Report Preview**")
                preview_lines = combined_content.split('\n')[:30]
                preview_text = '\n'.join(preview_lines)
                if len(combined_content.split('\n')) > 30:
                    remaining_lines = len(combined_content.split('\n')) - 30
                    preview_text += f"\n... ({remaining_lines} more lines)"
                
                st.code(preview_text, language="markdown" if export_format == "Markdown" else "text")
                
                # Export statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Reports Generated", len(reports_content))
                with col2:
                    st.metric("Total Lines", len(combined_content.split('\n')))
                with col3:
                    st.metric("File Size", f"{len(combined_content.encode('utf-8')) / 1024:.1f} KB")
                
                st.markdown("---")
                
                # Download buttons
                st.markdown("**Download Reports**")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    file_ext = "txt" if export_format == "Text Report" else "md" if export_format == "Markdown" else "json"
                    filename = export_manager.create_export_filename("ai_reports", metrics, file_ext)
                    mime_type = "text/plain" if export_format == "Text Report" else "text/markdown" if export_format == "Markdown" else "application/json"
                    
                    st.download_button(
                        label=f"📥 Download {export_format}",
                        data=combined_content,
                        file_name=filename,
                        mime=mime_type,
                        type="primary",
                        use_container_width=True
                    )
                
                with col2:
                    # Create PDF-ready version (plain text)
                    pdf_content = combined_content.replace('*', '').replace('#', '')  # Remove markdown
                    pdf_filename = export_manager.create_export_filename("ai_reports", metrics, "txt")
                    
                    st.download_button(
                        label="📄 PDF-Ready Text",
                        data=pdf_content,
                        file_name=pdf_filename,
                        mime="text/plain",
                        help="Plain text version suitable for PDF conversion",
                        use_container_width=True
                    )
                
                with col3:
                    # Create individual reports zip (simplified as combined file)
                    archive_sections = []
                    for title, content in reports_content:
                        filename = title.replace(' ', '_').lower()
                        section = f"FILE: {filename}.txt\n\n{content}"
                        archive_sections.append(section)
                    separator = "="*50 + " ARCHIVE SEPARATOR " + "="*50
                    archive_content = f"\n\n{separator}\n\n".join(archive_sections)
                    archive_filename = export_manager.create_export_filename("ai_reports_archive", metrics, "txt")
                    
                    st.download_button(
                        label="📦 Archive Format",
                        data=archive_content,
                        file_name=archive_filename,
                        mime="text/plain",
                        help="All reports in a single archive-style file",
                        use_container_width=True
                    )
                
                # Additional export formats
                st.markdown("**Dashboard Visualizations**")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Dashboard HTML export
                    dashboard_html = export_manager.export_dashboard_html(metrics)
                    dashboard_filename = export_manager.create_export_filename("dashboard", metrics, "html")
                    
                    st.download_button(
                        label="🌐 Dashboard HTML",
                        data=dashboard_html,
                        file_name=dashboard_filename,
                        mime="text/html",
                        help="Complete dashboard as HTML for screenshots or PDF conversion",
                        use_container_width=True
                    )
                
                with col2:
                    # Charts collection HTML
                    charts_data = [
                        {"title": "Commit Frequency Trends", "description": "Daily commit activity over time"},
                        {"title": "Code Volume Analysis", "description": "Lines added and deleted trends"},
                        {"title": "Pull Request Metrics", "description": "PR creation and merge statistics"},
                        {"title": "Review Participation", "description": "Code review activity and quality"}
                    ]
                    charts_html = export_manager.export_charts_html(charts_data, metrics)
                    charts_filename = export_manager.create_export_filename("charts", metrics, "html")
                    
                    st.download_button(
                        label="📊 Charts HTML",
                        data=charts_html,
                        file_name=charts_filename,
                        mime="text/html",
                        help="Interactive charts collection for presentations",
                        use_container_width=True
                    )
                
                with col3:
                    # PDF export (if available)
                    if export_manager.is_pdf_export_available():
                        if st.button("📄 Generate PDF", use_container_width=True):
                            try:
                                pdf_content = export_manager.pdf_exporter.create_pdf_report(metrics)
                                pdf_filename = export_manager.create_export_filename("dashboard", metrics, "pdf")
                                
                                st.download_button(
                                    label="📥 Download PDF",
                                    data=pdf_content,
                                    file_name=pdf_filename,
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                            except Exception as e:
                                st.error(f"PDF generation failed: {str(e)}")
                    else:
                        pdf_info_text = "📄 PDF Export\n\nInstall weasyprint or similar library to enable PDF export"
                        st.info(pdf_info_text)
                
                # Screenshot instructions
                st.markdown("---")
                st.markdown("**📸 Screenshot Instructions**")
                
                with st.expander("How to create screenshots and PDFs"):
                    st.markdown("""
                    **For Screenshots:**
                    1. Download the "Dashboard HTML" file above
                    2. Open it in your web browser
                    3. Use your browser's screenshot tools or extensions
                    4. For full-page screenshots, try browser extensions like "Full Page Screen Capture"
                    
                    **For PDF Conversion:**
                    1. Download the "Dashboard HTML" file
                    2. Open it in your web browser
                    3. Use Print → Save as PDF (Ctrl+P / Cmd+P)
                    4. Or use online HTML-to-PDF converters
                    
                    **For Presentations:**
                    1. Download the "Charts HTML" file for interactive charts
                    2. Open in browser and screenshot individual charts
                    3. Use the dashboard HTML for overview slides
                    
                    **Professional PDF Reports:**
                    - Install `weasyprint` library for automated PDF generation
                    - Use `pip install weasyprint` in your environment
                    - Restart the dashboard to enable PDF export button
                    """)
                
                # Export summary
                st.markdown("---")
                st.info(f"""
                **Export Summary:**
                - {len(reports_content)} AI reports generated
                - {len(combined_content.split())} words total
                - Multiple formats available (Text, Markdown, JSON, HTML)
                - Dashboard visualization exports included
                """)
                
                st.success("✅ All export formats ready for download!")
                
                st.success("✅ AI reports generated and ready for download!")
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ Report generation failed: {str(e)}")
                
                with st.expander("Error Details"):
                    st.code(str(e))
                    st.markdown("**Troubleshooting:**")
                    st.markdown("• Verify your OpenAI API key is valid and has sufficient credits")
                    st.markdown("• Check your internet connection")
                    st.markdown("• Try generating fewer reports at once")
                    st.markdown("• Ensure the productivity data is properly loaded")
    
    # Additional export options
    with st.expander("🔧 Advanced Report Options"):
        st.markdown("**Report Customization**")
        
        custom_prompt = st.text_area(
            "Custom Analysis Prompt",
            placeholder="Enter a custom prompt for AI analysis (optional)",
            help="Provide specific questions or focus areas for the AI analysis"
        )
        
        if custom_prompt:
            st.info("Custom prompts will be included in the analysis generation")
        
        st.markdown("**Batch Export Options**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Export All Data + Reports", use_container_width=True):
                st.info("Combined metrics and AI reports export will be available in a future update")
        
        with col2:
            if st.button("📧 Email Reports", use_container_width=True):
                st.info("Email delivery feature will be available in a future update")

def render_export_section():
    """Render the export dashboard section"""
    st.header("📥 Export & Reports")
    st.markdown("Download reports and export data in various formats")
    
    # Check if data is loaded
    metrics = get_sample_metrics()
    if not metrics:
        st.info("📊 Load repository data to enable export functionality")
        return
    
    # Create tabs for different export types
    tab1, tab2 = st.tabs(["📊 Metrics Export", "🤖 AI Reports"])
    
    with tab1:
        render_metrics_export_section(metrics)
    
    with tab2:
        render_ai_reports_export_section(metrics)

def render_main_content():
    """Render main content area based on selected section"""
    current_section = st.session_state.current_section
    
    if current_section == "Overview":
        render_overview_section()
    elif current_section == "Metrics":
        render_metrics_section()
    elif current_section == "Analytics":
        render_analytics_section()
    elif current_section == "AI Insights":
        render_ai_insights_section()
    elif current_section == "Export":
        render_export_section()

def main():
    """Main application entry point"""
    
    # Configure Streamlit page
    st.set_page_config(
        page_title="GitHub Productivity Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Main title
    st.title("📊 GitHub Productivity Dashboard")
    st.markdown("Analyze developer productivity with GitHub data and AI insights")
    
    # Render sidebar navigation
    render_sidebar_navigation()
    
    # Render main content
    render_main_content()
    
    # Footer
    st.markdown("---")
    st.markdown("*GitHub Productivity Dashboard - Powered by Streamlit and OpenAI*")

if __name__ == "__main__":
    main()