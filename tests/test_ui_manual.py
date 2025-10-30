"""
Manual UI test for GitHub Productivity Dashboard.

This script starts the Streamlit app and provides instructions for manual testing.
Run this to verify the UI works correctly in a real browser environment.
"""

import subprocess
import time
import webbrowser
import sys
import os
import signal
import requests
from typing import Optional


class StreamlitTestRunner:
    """Helper class to run Streamlit app for manual testing."""
    
    def __init__(self, port: int = 8501):
        self.port = port
        self.url = f"http://localhost:{port}"
        self.process: Optional[subprocess.Popen] = None
    
    def start_app(self):
        """Start the Streamlit app."""
        print("🚀 Starting GitHub Productivity Dashboard...")
        
        # Kill any existing process on the port
        try:
            subprocess.run(["pkill", "-f", "streamlit"], check=False)
            time.sleep(2)
        except:
            pass
        
        # Set environment
        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        
        # Start Streamlit
        self.process = subprocess.Popen(
            ["streamlit", "run", "main.py", "--server.port", str(self.port)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for app to start
        print("⏳ Waiting for app to start...")
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get(self.url, timeout=1)
                if response.status_code == 200:
                    print(f"✅ App started successfully at {self.url}")
                    return True
            except:
                pass
            time.sleep(1)
            print(f"   Attempt {attempt + 1}/{max_attempts}...")
        
        print("❌ Failed to start app")
        return False
    
    def open_browser(self):
        """Open the app in the default browser."""
        print(f"🌐 Opening browser at {self.url}")
        webbrowser.open(self.url)
    
    def stop_app(self):
        """Stop the Streamlit app."""
        if self.process:
            print("🛑 Stopping app...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
        
        # Additional cleanup
        try:
            subprocess.run(["pkill", "-f", "streamlit"], check=False)
        except:
            pass
        
        print("✅ App stopped")
    
    def run_manual_test(self):
        """Run the manual test session."""
        print("\n" + "="*60)
        print("🧪 GITHUB PRODUCTIVITY DASHBOARD - MANUAL UI TEST")
        print("="*60)
        
        if not self.start_app():
            print("❌ Could not start the app. Please check for errors.")
            return False
        
        self.open_browser()
        
        print("\n📋 MANUAL TEST CHECKLIST:")
        print("="*40)
        
        test_items = [
            "✅ Page loads without errors",
            "✅ Title shows 'GitHub Productivity Dashboard'",
            "✅ Navigation sidebar is visible with all sections",
            "✅ Configuration panel is visible",
            "✅ GitHub token input field is present",
            "✅ Repository URL input field is present", 
            "✅ OpenAI API key input field is present",
            "✅ Test invalid GitHub token (should show error)",
            "✅ Test valid GitHub token format (should show success)",
            "✅ Test invalid repository URL (should show error)",
            "✅ Test valid repository URL (should show success)",
            "✅ Test invalid OpenAI key (should show error)",
            "✅ Test valid OpenAI key format (should show success)",
            "✅ Navigate to Metrics section",
            "✅ Navigate to Analytics section",
            "✅ Navigate to AI Insights section",
            "✅ Navigate to Export section",
            "✅ Return to Overview section",
            "✅ Check Performance & Caching section",
            "✅ Test cache management buttons",
            "✅ Check responsive design on different screen sizes",
            "✅ Verify footer is displayed",
        ]
        
        for i, item in enumerate(test_items, 1):
            print(f"{i:2d}. {item}")
        
        print("\n🔧 TEST SCENARIOS:")
        print("="*40)
        
        scenarios = [
            "1. BASIC VALIDATION:",
            "   • Enter invalid GitHub token: 'invalid_token'",
            "   • Should show: ❌ Invalid GitHub token format",
            "   • Enter valid GitHub token: 'ghp_1234567890abcdef1234567890abcdef12345678'",
            "   • Should show: ✅ Valid GitHub token format",
            "",
            "2. REPOSITORY VALIDATION:",
            "   • Enter invalid repo: 'invalid-repo'",
            "   • Should show: ❌ Invalid repository URL format",
            "   • Enter valid repo: 'microsoft/vscode'",
            "   • Should show: ✅ Valid repository: microsoft/vscode",
            "",
            "3. OPENAI VALIDATION:",
            "   • Enter invalid key: 'invalid_key'",
            "   • Should show: ❌ Invalid OpenAI API key format",
            "   • Enter valid key: 'sk-1234567890abcdef1234567890abcdef'",
            "   • Should show: ✅ Valid OpenAI API key format",
            "",
            "4. NAVIGATION TEST:",
            "   • Click each navigation button in sidebar",
            "   • Verify content changes for each section",
            "   • Check for loading indicators on Analytics/AI sections",
            "",
            "5. CONFIGURATION STATUS:",
            "   • Initially should show: ⚠️ Configure Credentials",
            "   • After valid inputs: ⚠️ GitHub Not Tested",
            "   • Check configuration status updates",
            "",
            "6. PERFORMANCE SECTION:",
            "   • Check cache metrics display",
            "   • Click 'Clear Cache' button",
            "   • Click 'Clear Expired' button", 
            "   • Click 'Reset Performance' button",
            "",
            "7. RESPONSIVE DESIGN:",
            "   • Resize browser window",
            "   • Check mobile view (narrow width)",
            "   • Verify sidebar collapses appropriately",
            "   • Check column layouts adapt",
        ]
        
        for scenario in scenarios:
            print(scenario)
        
        print("\n⌨️  KEYBOARD TESTING:")
        print("="*40)
        print("• Tab through form elements")
        print("• Use Enter to submit forms")
        print("• Use Escape to close modals/dialogs")
        print("• Test keyboard navigation")
        
        print("\n🎨 VISUAL TESTING:")
        print("="*40)
        print("• Check color contrast")
        print("• Verify error messages are clearly visible")
        print("• Check success messages are prominent")
        print("• Verify loading indicators work")
        print("• Check icons and emojis display correctly")
        
        print("\n" + "="*60)
        print("⏳ App is running. Perform manual tests in your browser.")
        print(f"🌐 URL: {self.url}")
        print("Press Ctrl+C when finished testing...")
        print("="*60)
        
        try:
            # Keep the app running until user interrupts
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🏁 Manual testing session ended.")
            return True
        finally:
            self.stop_app()


def main():
    """Main function to run manual UI tests."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Manual UI Test for GitHub Productivity Dashboard")
        print("Usage: python tests/test_ui_manual.py [--port PORT]")
        print("Options:")
        print("  --port PORT    Port to run Streamlit on (default: 8501)")
        print("  --help         Show this help message")
        return
    
    port = 8501
    if len(sys.argv) > 2 and sys.argv[1] == "--port":
        try:
            port = int(sys.argv[2])
        except ValueError:
            print("❌ Invalid port number")
            return
    
    runner = StreamlitTestRunner(port)
    
    def signal_handler(sig, frame):
        print("\n\n🛑 Interrupted by user")
        runner.stop_app()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        success = runner.run_manual_test()
        if success:
            print("\n✅ Manual testing completed successfully!")
        else:
            print("\n❌ Manual testing failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during manual testing: {e}")
        runner.stop_app()
        sys.exit(1)


if __name__ == "__main__":
    main()