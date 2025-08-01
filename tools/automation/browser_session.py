"""Shared browser session manager for automation tools."""

from typing import Optional
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait


class BrowserSession:
    """Singleton class to manage shared browser session across tools."""
    
    _instance = None
    _driver = None
    _wait = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BrowserSession, cls).__new__(cls)
        return cls._instance
    
    @property
    def driver(self) -> Optional[webdriver.Chrome]:
        """Get the current WebDriver instance."""
        return self._driver
    
    @property
    def wait(self) -> Optional[WebDriverWait]:
        """Get the current WebDriverWait instance."""
        return self._wait
    
    def set_driver(self, driver: webdriver.Chrome, timeout: int = 10):
        """Set the WebDriver instance."""
        self._driver = driver
        self._wait = WebDriverWait(driver, timeout) if driver else None
    
    def clear_driver(self):
        """Clear the WebDriver instance."""
        self._driver = None
        self._wait = None
    
    def is_active(self) -> bool:
        """Check if there's an active browser session."""
        try:
            if self._driver is None:
                return False
            # Try to access the current URL to check if driver is still active
            _ = self._driver.current_url
            return True
        except Exception:
            # Driver is no longer active, clear it
            self.clear_driver()
            return False


# Global instance
browser_session = BrowserSession()