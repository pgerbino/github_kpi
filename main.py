"""
GitHub Productivity Dashboard - Main Streamlit Application

A comprehensive dashboard for analyzing developer productivity using GitHub API data
and AI-powered insights from ChatGPT.
"""

import streamlit as st
from datetime import datetime, timedelta

def main():
    """Main application entry point"""
    
    # Configure Streamlit page
    st.set_page_config(
        page_title="GitHub Productivity Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Main title
    st.title("📊 GitHub Productivity Dashboard")
    st.markdown("Analyze developer productivity with GitHub data and AI insights")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        st.info("Configure your API credentials and repository settings to get started.")
        
        # Placeholder for future configuration components
        st.text_input("GitHub Token", type="password", help="Enter your GitHub personal access token")
        st.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API key")
        st.text_input("Repository URL", help="Enter GitHub repository URL (e.g., owner/repo)")
    
    # Main content area
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Productivity Metrics")
        st.info("Productivity metrics will be displayed here once data is loaded.")
    
    with col2:
        st.subheader("🤖 AI Insights")
        st.info("AI-generated insights and recommendations will appear here.")
    
    # Footer
    st.markdown("---")
    st.markdown("*GitHub Productivity Dashboard - Powered by Streamlit and OpenAI*")

if __name__ == "__main__":
    main()