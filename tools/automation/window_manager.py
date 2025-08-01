"""Window management utility for ensuring correct application focus before operations."""

import subprocess
import time
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class WindowManager:
    """Manages application windows and ensures correct focus for automation operations."""
    
    def __init__(self):
        self.browser_apps = {
            'safari': 'Safari',
            'chrome': 'Google Chrome', 
            'chromium': 'Chromium',
            'firefox': 'Firefox',
            'edge': 'Microsoft Edge'
        }
        
        self.common_apps = {
            'finder': 'Finder',
            'terminal': 'Terminal',
            'notes': 'Notes',
            'calculator': 'Calculator',
            'textedit': 'TextEdit',
            'preview': 'Preview',
            'mail': 'Mail',
            'calendar': 'Calendar',
            'contacts': 'Contacts',
            'messages': 'Messages',
            'facetime': 'FaceTime',
            'music': 'Music',
            'photos': 'Photos',
            'maps': 'Maps',
            'weather': 'Weather',
            'stocks': 'Stocks',
            'news': 'News',
            'podcasts': 'Podcasts',
            'tv': 'TV',
            'books': 'Books',
            'app_store': 'App Store',
            'system_preferences': 'System Preferences',
            'activity_monitor': 'Activity Monitor',
            'disk_utility': 'Disk Utility',
            'keychain_access': 'Keychain Access'
        }
        
        # Track current focused application
        self._current_app = None
        self._last_focus_time = 0
    
    def get_frontmost_application(self) -> Optional[str]:
        """Get the currently frontmost (focused) application."""
        try:
            applescript = '''
            tell application "System Events"
                return name of first application process whose frontmost is true
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get frontmost application: {e}")
            return None
    
    def is_application_running(self, app_name: str) -> bool:
        """Check if an application is currently running."""
        try:
            applescript = f'''
            tell application "System Events"
                return exists (processes where name is "{app_name}")
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True, text=True, timeout=5
            )
            
            return result.returncode == 0 and result.stdout.strip().lower() == 'true'
            
        except Exception as e:
            logger.error(f"Failed to check if {app_name} is running: {e}")
            return False
    
    def focus_application(self, app_name: str, force: bool = False) -> bool:
        """
        Focus (bring to front) the specified application.
        
        Args:
            app_name: Name of the application to focus
            force: Force focus even if already focused recently
            
        Returns:
            True if successful, False otherwise
        """
        try:
            current_time = time.time()
            
            # Skip if we just focused this app recently (unless forced)
            if (not force and 
                self._current_app == app_name and 
                current_time - self._last_focus_time < 2):
                return True
            
            # Check if app is running first
            if not self.is_application_running(app_name):
                logger.warning(f"Application {app_name} is not running")
                return False
            
            # Focus the application
            applescript = f'''
            tell application "{app_name}"
                activate
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                self._current_app = app_name
                self._last_focus_time = current_time
                time.sleep(0.5)  # Brief pause for focus to take effect
                return True
            else:
                logger.error(f"Failed to focus {app_name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to focus application {app_name}: {e}")
            return False
    
    def focus_browser(self, browser_type: str, force: bool = False) -> bool:
        """
        Focus a specific browser application.
        
        Args:
            browser_type: Type of browser (safari, chrome, chromium, etc.)
            force: Force focus even if already focused recently
            
        Returns:
            True if successful, False otherwise
        """
        app_name = self.browser_apps.get(browser_type.lower())
        if not app_name:
            logger.error(f"Unknown browser type: {browser_type}")
            return False
        
        return self.focus_application(app_name, force)
    
    def ensure_browser_focus(self, browser_type: str) -> bool:
        """
        Ensure browser is focused before performing operations.
        This is the main method that should be called before browser operations.
        
        Args:
            browser_type: Type of browser to focus
            
        Returns:
            True if browser is focused, False otherwise
        """
        if not browser_type:
            logger.warning("No browser type specified for focus")
            return False
        
        # Always focus the browser before operations
        success = self.focus_browser(browser_type, force=True)
        
        if success:
            logger.info(f"Successfully focused {browser_type} browser")
        else:
            logger.error(f"Failed to focus {browser_type} browser")
        
        return success
    
    def ensure_app_focus(self, app_name: str) -> bool:
        """
        Ensure application is focused before performing operations.
        
        Args:
            app_name: Name of the application to focus
            
        Returns:
            True if application is focused, False otherwise
        """
        if not app_name:
            logger.warning("No application name specified for focus")
            return False
        
        # Always focus the application before operations
        success = self.focus_application(app_name, force=True)
        
        if success:
            logger.info(f"Successfully focused {app_name}")
        else:
            logger.error(f"Failed to focus {app_name}")
        
        return success
    
    def get_running_browsers(self) -> List[str]:
        """Get list of currently running browsers."""
        running_browsers = []
        
        for browser_type, app_name in self.browser_apps.items():
            if self.is_application_running(app_name):
                running_browsers.append(browser_type)
        
        return running_browsers
    
    def get_browser_windows_count(self, browser_type: str) -> int:
        """Get number of windows for a specific browser."""
        try:
            app_name = self.browser_apps.get(browser_type.lower())
            if not app_name:
                return 0
            
            applescript = f'''
            tell application "{app_name}"
                return count of windows
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                return int(result.stdout.strip())
            return 0
            
        except Exception as e:
            logger.error(f"Failed to get window count for {browser_type}: {e}")
            return 0
    
    def bring_browser_to_front_and_wait(self, browser_type: str, wait_time: float = 1.0) -> bool:
        """
        Bring browser to front and wait for it to be ready.
        
        Args:
            browser_type: Type of browser to bring to front
            wait_time: Time to wait after bringing to front
            
        Returns:
            True if successful, False otherwise
        """
        if self.ensure_browser_focus(browser_type):
            time.sleep(wait_time)
            
            # Verify the browser is now frontmost
            frontmost = self.get_frontmost_application()
            expected_app = self.browser_apps.get(browser_type.lower())
            
            if frontmost == expected_app:
                logger.info(f"Successfully brought {browser_type} to front")
                return True
            else:
                logger.warning(f"Expected {expected_app} to be frontmost, but got {frontmost}")
                return False
        
        return False


# Global instance for use across tools
window_manager = WindowManager()