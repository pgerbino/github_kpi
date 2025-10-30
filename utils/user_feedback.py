"""
User feedback and loading states management for GitHub Productivity Dashboard.

This module provides utilities for displaying progress indicators, success/error notifications,
and managing loading states throughout the application.
"""

import streamlit as st
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from contextlib import contextmanager
from enum import Enum


class NotificationType(Enum):
    """Types of notifications for user feedback."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class LoadingState(Enum):
    """Loading states for different operations."""
    IDLE = "idle"
    LOADING = "loading"
    SUCCESS = "success"
    ERROR = "error"


class FeedbackManager:
    """Manages user feedback, notifications, and loading states."""
    
    def __init__(self):
        """Initialize the feedback manager."""
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state variables for feedback management."""
        if 'notifications' not in st.session_state:
            st.session_state.notifications = []
        
        if 'loading_states' not in st.session_state:
            st.session_state.loading_states = {}
        
        if 'progress_tracking' not in st.session_state:
            st.session_state.progress_tracking = {}
    
    def show_notification(self, message: str, notification_type: NotificationType = NotificationType.INFO,
                         duration: Optional[int] = None, dismissible: bool = True):
        """
        Show a notification to the user.
        
        Args:
            message: The notification message
            notification_type: Type of notification (success, error, warning, info)
            duration: Auto-dismiss duration in seconds (None for persistent)
            dismissible: Whether the notification can be manually dismissed
        """
        notification = {
            'id': f"notification_{len(st.session_state.notifications)}_{int(time.time())}",
            'message': message,
            'type': notification_type.value,
            'timestamp': datetime.now(),
            'duration': duration,
            'dismissible': dismissible,
            'dismissed': False
        }
        
        st.session_state.notifications.append(notification)
        
        # Display the notification immediately
        self._display_notification(notification)
    
    def _display_notification(self, notification: Dict[str, Any]):
        """Display a single notification in the UI."""
        if notification['dismissed']:
            return
        
        message = notification['message']
        notification_type = notification['type']
        
        # Display based on type
        if notification_type == NotificationType.SUCCESS.value:
            st.success(f"✅ {message}")
        elif notification_type == NotificationType.ERROR.value:
            st.error(f"❌ {message}")
        elif notification_type == NotificationType.WARNING.value:
            st.warning(f"⚠️ {message}")
        else:
            st.info(f"ℹ️ {message}")
    
    def clear_notifications(self):
        """Clear all notifications."""
        st.session_state.notifications = []
    
    def set_loading_state(self, operation: str, state: LoadingState, 
                         message: Optional[str] = None, progress: Optional[float] = None):
        """
        Set the loading state for an operation.
        
        Args:
            operation: Name of the operation
            state: Loading state
            message: Optional status message
            progress: Optional progress value (0.0 to 1.0)
        """
        st.session_state.loading_states[operation] = {
            'state': state.value,
            'message': message,
            'progress': progress,
            'timestamp': datetime.now()
        }
    
    def get_loading_state(self, operation: str) -> Dict[str, Any]:
        """Get the current loading state for an operation."""
        return st.session_state.loading_states.get(operation, {
            'state': LoadingState.IDLE.value,
            'message': None,
            'progress': None,
            'timestamp': None
        })
    
    def is_loading(self, operation: str) -> bool:
        """Check if an operation is currently loading."""
        state = self.get_loading_state(operation)
        return state['state'] == LoadingState.LOADING.value
    
    @contextmanager
    def loading_context(self, operation: str, message: str = "Loading...", 
                       show_progress: bool = True):
        """
        Context manager for handling loading states.
        
        Args:
            operation: Name of the operation
            message: Loading message to display
            show_progress: Whether to show a progress bar
        """
        try:
            # Set loading state
            self.set_loading_state(operation, LoadingState.LOADING, message)
            
            # Create UI elements
            if show_progress:
                progress_bar = st.progress(0)
                status_text = st.empty()
                status_text.text(message)
            else:
                progress_bar = None
                status_text = st.empty()
                status_text.text(f"🔄 {message}")
            
            # Yield control with progress updater
            def update_progress(progress: float, status: str = None):
                if progress_bar:
                    progress_bar.progress(progress)
                if status and status_text:
                    status_text.text(status)
                self.set_loading_state(operation, LoadingState.LOADING, status, progress)
            
            yield update_progress
            
            # Success state
            self.set_loading_state(operation, LoadingState.SUCCESS, "Completed successfully")
            if status_text:
                status_text.text("✅ Completed successfully!")
            if progress_bar:
                progress_bar.progress(1.0)
            
            # Clean up UI elements after a brief delay
            time.sleep(0.5)
            if progress_bar:
                progress_bar.empty()
            if status_text:
                status_text.empty()
        
        except Exception as e:
            # Error state
            self.set_loading_state(operation, LoadingState.ERROR, f"Failed: {str(e)}")
            if status_text:
                status_text.text(f"❌ Failed: {str(e)}")
            if progress_bar:
                progress_bar.empty()
            raise
    
    def show_progress_steps(self, operation: str, steps: List[Dict[str, Any]], 
                           auto_advance: bool = False):
        """
        Show a multi-step progress indicator.
        
        Args:
            operation: Name of the operation
            steps: List of step dictionaries with 'name', 'description', and optional 'duration'
            auto_advance: Whether to automatically advance steps
        """
        total_steps = len(steps)
        
        # Create progress UI
        st.subheader(f"🔄 {operation}")
        progress_bar = st.progress(0)
        current_step_text = st.empty()
        step_details = st.empty()
        
        # Initialize progress tracking
        st.session_state.progress_tracking[operation] = {
            'current_step': 0,
            'total_steps': total_steps,
            'steps': steps,
            'start_time': datetime.now()
        }
        
        def advance_step(step_index: int, status: str = "completed", details: str = None):
            """Advance to the next step."""
            if step_index < total_steps:
                progress = (step_index + 1) / total_steps
                progress_bar.progress(progress)
                
                step = steps[step_index]
                current_step_text.text(f"Step {step_index + 1}/{total_steps}: {step['name']} - {status}")
                
                if details:
                    step_details.text(details)
                elif 'description' in step:
                    step_details.text(step['description'])
                
                st.session_state.progress_tracking[operation]['current_step'] = step_index + 1
        
        return advance_step
    
    def show_operation_status(self, operation: str, show_details: bool = True):
        """Show the current status of an operation."""
        state = self.get_loading_state(operation)
        
        if state['state'] == LoadingState.IDLE.value:
            return
        
        # Status indicator
        status_icons = {
            LoadingState.LOADING.value: "🔄",
            LoadingState.SUCCESS.value: "✅",
            LoadingState.ERROR.value: "❌"
        }
        
        icon = status_icons.get(state['state'], "ℹ️")
        message = state.get('message', operation)
        
        st.write(f"{icon} **{operation}**: {message}")
        
        if show_details and state.get('progress') is not None:
            st.progress(state['progress'])
        
        if show_details and state.get('timestamp'):
            st.caption(f"Last updated: {state['timestamp'].strftime('%H:%M:%S')}")
    
    def create_status_dashboard(self, operations: List[str]):
        """Create a status dashboard for multiple operations."""
        st.subheader("📊 Operation Status")
        
        cols = st.columns(min(len(operations), 3))
        
        for i, operation in enumerate(operations):
            col = cols[i % len(cols)]
            
            with col:
                state = self.get_loading_state(operation)
                
                # Status card
                if state['state'] == LoadingState.LOADING.value:
                    st.info(f"🔄 {operation}")
                elif state['state'] == LoadingState.SUCCESS.value:
                    st.success(f"✅ {operation}")
                elif state['state'] == LoadingState.ERROR.value:
                    st.error(f"❌ {operation}")
                else:
                    st.write(f"⏸️ {operation}")
                
                if state.get('message'):
                    st.caption(state['message'])
    
    def show_loading_spinner(self, message: str = "Loading...", key: Optional[str] = None):
        """Show a loading spinner with message."""
        with st.spinner(message):
            # This will be used in context managers
            yield
    
    def create_progress_tracker(self, operation: str, total_items: int, 
                              item_name: str = "items") -> Callable[[int], None]:
        """
        Create a progress tracker for batch operations.
        
        Args:
            operation: Name of the operation
            total_items: Total number of items to process
            item_name: Name of the items being processed
            
        Returns:
            Function to update progress
        """
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(completed_items: int, current_item: str = None):
            progress = completed_items / total_items
            progress_bar.progress(progress)
            
            status_message = f"Processing {item_name}: {completed_items}/{total_items}"
            if current_item:
                status_message += f" (Current: {current_item})"
            
            status_text.text(status_message)
            
            # Update loading state
            self.set_loading_state(operation, LoadingState.LOADING, status_message, progress)
        
        return update_progress
    
    def show_success_message(self, title: str, details: List[str] = None, 
                           actions: List[Dict[str, Any]] = None):
        """
        Show a comprehensive success message.
        
        Args:
            title: Success message title
            details: List of detail messages
            actions: List of action buttons with 'label' and 'callback'
        """
        st.success(f"🎉 {title}")
        
        if details:
            with st.expander("📋 Details"):
                for detail in details:
                    st.write(f"• {detail}")
        
        if actions:
            cols = st.columns(len(actions))
            for i, action in enumerate(actions):
                with cols[i]:
                    if st.button(action['label'], key=f"success_action_{i}"):
                        action['callback']()
    
    def show_error_message(self, title: str, error: Exception = None, 
                          suggestions: List[str] = None, 
                          retry_callback: Optional[Callable] = None):
        """
        Show a comprehensive error message.
        
        Args:
            title: Error message title
            error: The exception that occurred
            suggestions: List of troubleshooting suggestions
            retry_callback: Function to call for retry
        """
        st.error(f"❌ {title}")
        
        if error:
            with st.expander("🔧 Error Details"):
                st.code(str(error))
        
        if suggestions:
            with st.expander("💡 Troubleshooting Suggestions"):
                for i, suggestion in enumerate(suggestions, 1):
                    st.write(f"{i}. {suggestion}")
        
        if retry_callback:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🔄 Retry", type="primary"):
                    retry_callback()
    
    def create_confirmation_dialog(self, title: str, message: str, 
                                 confirm_label: str = "Confirm",
                                 cancel_label: str = "Cancel") -> Optional[bool]:
        """
        Create a confirmation dialog.
        
        Args:
            title: Dialog title
            message: Confirmation message
            confirm_label: Label for confirm button
            cancel_label: Label for cancel button
            
        Returns:
            True if confirmed, False if cancelled, None if no action
        """
        st.subheader(f"⚠️ {title}")
        st.write(message)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button(cancel_label, key="confirm_cancel"):
                return False
        
        with col3:
            if st.button(confirm_label, key="confirm_ok", type="primary"):
                return True
        
        return None
    
    def show_data_loading_status(self, data_sources: Dict[str, Any]):
        """
        Show loading status for multiple data sources.
        
        Args:
            data_sources: Dictionary of data source names and their status
        """
        st.subheader("📊 Data Loading Status")
        
        for source_name, status in data_sources.items():
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**{source_name}**")
            
            with col2:
                if status.get('loading', False):
                    st.write("🔄 Loading...")
                elif status.get('loaded', False):
                    st.write("✅ Loaded")
                elif status.get('error', False):
                    st.write("❌ Error")
                else:
                    st.write("⏸️ Pending")
            
            with col3:
                if status.get('count'):
                    st.write(f"{status['count']} items")
                elif status.get('error_message'):
                    st.write("⚠️ Failed")


# Global feedback manager instance
feedback_manager = FeedbackManager()


# Convenience functions
def show_success(message: str, duration: Optional[int] = None):
    """Show a success notification."""
    feedback_manager.show_notification(message, NotificationType.SUCCESS, duration)


def show_error(message: str, duration: Optional[int] = None):
    """Show an error notification."""
    feedback_manager.show_notification(message, NotificationType.ERROR, duration)


def show_warning(message: str, duration: Optional[int] = None):
    """Show a warning notification."""
    feedback_manager.show_notification(message, NotificationType.WARNING, duration)


def show_info(message: str, duration: Optional[int] = None):
    """Show an info notification."""
    feedback_manager.show_notification(message, NotificationType.INFO, duration)


def loading_context(operation: str, message: str = "Loading..."):
    """Context manager for loading operations."""
    return feedback_manager.loading_context(operation, message)


def is_loading(operation: str) -> bool:
    """Check if an operation is currently loading."""
    return feedback_manager.is_loading(operation)


def set_loading(operation: str, message: str = "Loading..."):
    """Set an operation to loading state."""
    feedback_manager.set_loading_state(operation, LoadingState.LOADING, message)


def set_success(operation: str, message: str = "Completed successfully"):
    """Set an operation to success state."""
    feedback_manager.set_loading_state(operation, LoadingState.SUCCESS, message)


def set_error(operation: str, message: str = "Operation failed"):
    """Set an operation to error state."""
    feedback_manager.set_loading_state(operation, LoadingState.ERROR, message)