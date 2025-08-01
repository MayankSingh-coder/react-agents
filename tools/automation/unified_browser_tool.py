"""Unified browser tool that handles both opening browsers and web automation."""

import subprocess
import time
import os
from typing import Any, Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from ..base_tool import BaseTool, ToolResult
from .browser_session import browser_session
from .window_manager import window_manager


class UnifiedBrowserTool(BaseTool):
    """Unified tool for browser operations - opening browsers and web automation."""
    
    def __init__(self):
        super().__init__(
            name="unified_browser",
            description=self._get_detailed_description()
        )
        
        self.driver = None
        self.wait = None
        self.default_timeout = 10
        self.current_browser = None
        
        # Browser configurations
        self.browser_configs = {
            'safari': {
                'app_name': 'Safari',
                'selenium_support': False,
                'open_command': ['open', '-a', 'Safari']
            },
            'chrome': {
                'app_name': 'Google Chrome',
                'selenium_support': True,
                'open_command': ['open', '-a', 'Google Chrome']
            },
            'chromium': {
                'app_name': 'Chromium',
                'selenium_support': True,
                'open_command': ['open', '-a', 'Chromium']
            }
        }
        
        # Common website mappings
        self.website_mappings = {
            'swiggy': 'https://www.swiggy.com',
            'zomato': 'https://www.zomato.com',
            'amazon': 'https://www.amazon.in',
            'flipkart': 'https://www.flipkart.com',
            'google': 'https://www.google.com',
            'youtube': 'https://www.youtube.com',
            'facebook': 'https://www.facebook.com',
            'twitter': 'https://www.twitter.com',
            'instagram': 'https://www.instagram.com',
            'linkedin': 'https://www.linkedin.com',
            'github': 'https://www.github.com'
        }
    
    def _get_detailed_description(self) -> str:
        """Get detailed description with examples for browser operations."""
        return """Perform browser operations including opening browsers and navigation.

OPERATIONS & SYNTAX:
• open <browser> - Open browser (or new tab if browser already open)
  Usage: open safari
  Usage: open chrome
  Usage: open chromium
  ⚠️  IMPORTANT: If browser is already open, opens new tab instead

• navigate <url> - Navigate to URL
  Usage: navigate https://example.com
  Usage: navigate swiggy.com
  ⚠️  IMPORTANT: URL can be with or without https://

• open_and_navigate <browser> <url> - Open browser and navigate (RECOMMENDED)
  Usage: open_and_navigate chrome https://swiggy.com
  Usage: open_and_navigate safari google.com

• new_tab [url] - Open new tab
  Usage: new_tab
  Usage: new_tab https://youtube.com

• close_tab - Close current tab
  Usage: close_tab

• help - Show detailed usage information
  Usage: help

SUPPORTED BROWSERS:
- safari: AppleScript-based navigation
- chrome: Selenium-based navigation
- chromium: Selenium-based navigation

COMMON ERRORS:
- Browser not available → Check if browser is installed
- Invalid URL → Ensure URL format is correct

WORKFLOW RECOMMENDATIONS:
For browsing tasks:
1. Use: open_and_navigate chrome https://example.com
2. Use: new_tab https://another-site.com for additional tabs
3. Use: close_tab to close current tab when done"""

    async def execute(self, query: str, **kwargs) -> ToolResult:
        """Execute browser operations based on command syntax."""
        try:
            # Parse the query to determine operation
            parts = query.strip().split()
            if not parts:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Empty query provided"
                )
            
            operation = parts[0].lower()
            
            if operation == "open":
                return await self._open_operation(parts[1:], kwargs)
            elif operation == "navigate":
                return await self._navigate_operation(parts[1:], kwargs)
            elif operation == "open_and_navigate":
                return await self._open_and_navigate_operation(parts[1:], kwargs)
            elif operation == "new_tab":
                return await self._new_tab_operation(parts[1:], kwargs)
            elif operation == "close_tab":
                return await self._close_tab_operation(kwargs)
            elif operation == "help":
                return await self._help_operation()
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unknown operation: {operation}. Supported: open, navigate, open_and_navigate, new_tab, close_tab, help. Use 'help' for detailed usage information."
                )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Browser operation failed: {str(e)}"
            )
    
    async def _open_operation(self, args: List[str], kwargs: Dict[str, Any]) -> ToolResult:
        """Handle open browser operations. If browser is already open, opens new tab instead."""
        if not args:
            return ToolResult(
                success=False,
                data=None,
                error="Open operation requires browser name (safari, chrome, chromium)"
            )
        
        browser = args[0].lower()
        if browser not in ['safari', 'chrome', 'chromium']:
            return ToolResult(
                success=False,
                data=None,
                error=f"Unsupported browser: {browser}. Supported: safari, chrome, chromium"
            )
        
        # Check if browser is already open
        if self.current_browser == browser and (self.driver or self.current_browser):
            # Browser is already open, open new tab instead
            return await self._new_tab_operation([], kwargs)
        
        # Use existing _open_browser method with modified kwargs
        kwargs['browser'] = browser
        return await self._open_browser("", kwargs)
    
    async def _navigate_operation(self, args: List[str], kwargs: Dict[str, Any]) -> ToolResult:
        """Handle navigate operations."""
        if not args:
            return ToolResult(
                success=False,
                data=None,
                error="Navigate operation requires URL"
            )
        
        url = args[0]
        # Use existing _navigate_to_url method
        kwargs['url'] = url
        return await self._navigate_to_url("", kwargs)
    
    async def _open_and_navigate_operation(self, args: List[str], kwargs: Dict[str, Any]) -> ToolResult:
        """Handle open and navigate operations."""
        if len(args) < 2:
            return ToolResult(
                success=False,
                data=None,
                error="Open and navigate operation requires browser and URL"
            )
        
        browser = args[0].lower()
        url = args[1]
        
        if browser not in ['safari', 'chrome', 'chromium']:
            return ToolResult(
                success=False,
                data=None,
                error=f"Unsupported browser: {browser}. Supported: safari, chrome, chromium"
            )
        
        # Use existing _open_and_navigate method
        kwargs['browser'] = browser
        kwargs['url'] = url
        return await self._open_and_navigate("", kwargs)
    
    async def _new_tab_operation(self, args: List[str], kwargs: Dict[str, Any]) -> ToolResult:
        """Handle new tab operations."""
        url = args[0] if args else None
        if url:
            kwargs['url'] = url
        # Use existing _new_tab method
        return await self._new_tab("", kwargs)
    
    async def _close_tab_operation(self, kwargs: Dict[str, Any]) -> ToolResult:
        """Handle close tab operations."""
        # Use existing _close_tab method
        return await self._close_tab("", kwargs)
    
    async def _help_operation(self) -> ToolResult:
        """Handle help operations."""
        return ToolResult(
            success=True,
            data={"help": self._get_detailed_description()},
            metadata={"operation": "help"}
        )
    
    def _extract_browser_type(self, query: str, kwargs: Dict[str, Any]) -> str:
        """Extract which browser to use from query."""
        browser = kwargs.get('browser', None)
        if browser:
            return browser.lower()
        
        query_lower = query.lower()
        
        if 'safari' in query_lower:
            return 'safari'
        elif 'chrome' in query_lower and 'chromium' not in query_lower:
            return 'chrome'
        elif 'chromium' in query_lower:
            return 'chromium'
        else:
            # Default preference: Chrome > Chromium > Safari
            for browser_type in ['chrome', 'chromium', 'safari']:
                if self._is_browser_available(browser_type):
                    return browser_type
            return 'safari'  # Fallback
    
    def _is_browser_available(self, browser_type: str) -> bool:
        """Check if a browser is available on the system."""
        try:
            config = self.browser_configs.get(browser_type, {})
            app_name = config.get('app_name', '')
            
            # Check if app exists
            result = subprocess.run(
                ['mdfind', f'kMDItemDisplayName == "{app_name}"'],
                capture_output=True, text=True, timeout=5
            )
            return len(result.stdout.strip()) > 0
        except Exception:
            return False
    
    def _ensure_browser_focus(self, browser_type: str = None) -> bool:
        """
        Ensure the correct browser is focused before performing operations.
        This is called before any browser operation to prevent operating on wrong window.
        
        Args:
            browser_type: Type of browser to focus (uses current_browser if not specified)
            
        Returns:
            True if browser is focused successfully, False otherwise
        """
        target_browser = browser_type or self.current_browser
        
        if not target_browser:
            # No browser specified, try to detect running browser
            running_browsers = window_manager.get_running_browsers()
            if running_browsers:
                target_browser = running_browsers[0]  # Use first running browser
            else:
                return False
        
        # Always ensure browser focus before operations
        success = window_manager.ensure_browser_focus(target_browser)
        
        if success:
            # Update current browser if focus was successful
            self.current_browser = target_browser
        
        return success
    
    async def _open_browser(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Open a browser."""
        try:
            browser_type = self._extract_browser_type(query, kwargs)
            config = self.browser_configs.get(browser_type, {})
            
            if not config:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unsupported browser type: {browser_type}"
                )
            
            # Open the browser application
            result = subprocess.run(config['open_command'], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.current_browser = browser_type
                time.sleep(2)  # Wait for browser to open
                
                # Initialize Selenium for Chrome/Chromium browsers
                selenium_initialized = False
                if config['selenium_support'] and browser_type in ['chrome', 'chromium']:
                    try:
                        await self._init_selenium(kwargs)
                        selenium_initialized = True
                    except Exception as e:
                        print(f"Warning: Failed to initialize Selenium: {e}")
                
                return ToolResult(
                    success=True,
                    data={
                        "browser": browser_type,
                        "app_name": config['app_name'],
                        "selenium_support": config['selenium_support'],
                        "selenium_initialized": selenium_initialized
                    },
                    metadata={"action": "open_browser"}
                )
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Failed to open {browser_type}: {result.stderr}"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to open browser: {str(e)}"
            )
    
    async def _navigate_to_url(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Navigate to a URL using the appropriate method."""
        try:
            url = kwargs.get('url', None)
            if not url:
                url = self._extract_url_from_query(query)
            
            if not url:
                return ToolResult(
                    success=False,
                    data=None,
                    error="No URL provided or could be extracted from query"
                )
            
            # CRITICAL: Ensure browser focus before navigation
            if not self._ensure_browser_focus():
                return ToolResult(
                    success=False,
                    data=None,
                    error="Failed to focus browser before navigation. Please ensure browser is open."
                )
            
            # If we have a Selenium-supported browser and it's already open, use Selenium
            if (self.current_browser in ['chrome', 'chromium'] and 
                self.browser_configs[self.current_browser]['selenium_support']):
                
                return await self._navigate_with_selenium(url, kwargs)
            else:
                # Use AppleScript or open command for Safari or when Selenium isn't available
                return await self._navigate_with_applescript(url, kwargs)
                
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to navigate: {str(e)}"
            )
    
    async def _open_and_navigate(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Open browser and navigate to URL in one action."""
        try:
            # First open the browser
            browser_result = await self._open_browser(query, kwargs)
            
            if not browser_result.success:
                return browser_result
            
            # Wait for browser to fully open
            time.sleep(3)
            
            # Then navigate
            navigate_result = await self._navigate_to_url(query, kwargs)
            
            if navigate_result.success:
                return ToolResult(
                    success=True,
                    data={
                        **browser_result.data,
                        **navigate_result.data,
                        "action": "open_and_navigate"
                    },
                    metadata={"query": query}
                )
            else:
                return navigate_result
                
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to open and navigate: {str(e)}"
            )
    
    async def _navigate_with_selenium(self, url: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Navigate using Selenium WebDriver."""
        try:
            # Initialize Selenium if not already done
            if not self.driver:
                await self._init_selenium(kwargs)
            
            # Normalize URL - ensure it has proper protocol
            normalized_url = self._normalize_url(url)
            
            # Navigate to URL
            self.driver.get(normalized_url)
            time.sleep(2)  # Wait for page to load
            
            return ToolResult(
                success=True,
                data={
                    "url": normalized_url,
                    "original_url": url,
                    "current_url": self.driver.current_url,
                    "title": self.driver.title,
                    "method": "selenium"
                },
                metadata={"action": "navigate"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Selenium navigation failed: {str(e)}"
            )
    
    async def _navigate_with_applescript(self, url: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Navigate using AppleScript (works with Safari and other browsers)."""
        try:
            browser_name = self.browser_configs.get(self.current_browser, {}).get('app_name', 'Safari')
            
            applescript = f'''
            tell application "{browser_name}"
                activate
                if (count of windows) = 0 then
                    make new document
                end if
                set URL of front document to "{url}"
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                return ToolResult(
                    success=True,
                    data={
                        "url": url,
                        "browser": self.current_browser,
                        "method": "applescript"
                    },
                    metadata={"action": "navigate"}
                )
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"AppleScript navigation failed: {result.stderr}"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"AppleScript navigation failed: {str(e)}"
            )
    
    async def _init_selenium(self, kwargs: Dict[str, Any]):
        """Initialize Selenium WebDriver."""
        try:
            chrome_options = Options()
            
            # Check if headless mode requested
            headless = kwargs.get('headless', False)
            if headless:
                chrome_options.add_argument('--headless')
            
            # Additional Chrome options
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Try to use the appropriate browser
            if self.current_browser == 'chromium':
                chromium_path = "/Applications/Chromium.app/Contents/MacOS/Chromium"
                if os.path.exists(chromium_path):
                    chrome_options.binary_location = chromium_path
            
            # Initialize WebDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, self.default_timeout)
            
            # Register with session manager
            browser_session.set_driver(self.driver, self.default_timeout)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
        except Exception as e:
            raise Exception(f"Failed to initialize Selenium: {str(e)}")
    
    async def _click_element(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Click on a web element (requires Selenium)."""
        try:
            # CRITICAL: Ensure browser focus before clicking
            if not self._ensure_browser_focus():
                return ToolResult(
                    success=False,
                    data=None,
                    error="Failed to focus browser before clicking. Please ensure browser is open."
                )
            
            if not self.driver:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Selenium not initialized. Use Chrome/Chromium for element interaction."
                )
            
            selector = kwargs.get('element_selector', None)
            if not selector:
                selector = self._extract_selector_from_query(query)
            
            if not selector:
                return ToolResult(
                    success=False,
                    data=None,
                    error="No element selector provided"
                )
            
            element = self._find_element_by_selector(selector)
            if not element:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Element not found: {selector}"
                )
            
            # Scroll element into view and click
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            element.click()
            
            return ToolResult(
                success=True,
                data={
                    "element_clicked": selector,
                    "element_text": element.text[:100] if element.text else "",
                    "current_url": self.driver.current_url
                },
                metadata={"action": "click_element"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to click element: {str(e)}"
            )
    
    async def _type_in_element(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Type text in a web element (requires Selenium)."""
        try:
            # CRITICAL: Ensure browser focus before typing
            if not self._ensure_browser_focus():
                return ToolResult(
                    success=False,
                    data=None,
                    error="Failed to focus browser before typing. Please ensure browser is open."
                )
            
            if not self.driver:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Selenium not initialized. Use Chrome/Chromium for form interaction."
                )
            
            selector = kwargs.get('element_selector', None)
            text = kwargs.get('text', None)
            
            if not selector:
                selector = self._extract_selector_from_query(query)
            if not text:
                text = self._extract_text_from_query(query)
            
            if not selector or not text:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Element selector or text not provided"
                )
            
            element = self._find_element_by_selector(selector)
            if not element:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Element not found: {selector}"
                )
            
            element.clear()
            element.send_keys(text)
            
            return ToolResult(
                success=True,
                data={
                    "element": selector,
                    "text_typed": text,
                    "current_url": self.driver.current_url
                },
                metadata={"action": "type_text"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to type in element: {str(e)}"
            )
    
    async def _find_element(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Find elements on the page (requires Selenium)."""
        try:
            if not self.driver:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Selenium not initialized. Use Chrome/Chromium for element finding."
                )
            
            selector = kwargs.get('element_selector', None)
            if not selector:
                selector = self._extract_selector_from_query(query)
            
            if not selector:
                return ToolResult(
                    success=False,
                    data=None,
                    error="No element selector provided"
                )
            
            elements = self._find_elements_by_selector(selector)
            
            element_info = []
            for i, element in enumerate(elements[:5]):  # Limit to first 5 elements
                try:
                    info = {
                        "index": i,
                        "tag": element.tag_name,
                        "text": element.text[:100] if element.text else "",
                        "visible": element.is_displayed(),
                        "enabled": element.is_enabled()
                    }
                    
                    # Try to get common attributes
                    for attr in ['id', 'class', 'name', 'type', 'href']:
                        value = element.get_attribute(attr)
                        if value:
                            info[attr] = value
                    
                    element_info.append(info)
                except Exception:
                    continue
            
            return ToolResult(
                success=True,
                data={
                    "selector": selector,
                    "elements_found": len(elements),
                    "elements_info": element_info
                },
                metadata={"action": "find_element"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to find elements: {str(e)}"
            )
    
    async def _take_screenshot(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Take a screenshot of the browser."""
        try:
            # CRITICAL: Ensure browser focus before taking screenshot
            if not self._ensure_browser_focus():
                return ToolResult(
                    success=False,
                    data=None,
                    error="Failed to focus browser before taking screenshot. Please ensure browser is open."
                )
            
            if self.driver:
                # Use Selenium screenshot
                screenshots_dir = "/Users/mayank/Desktop/concepts/react-agents/screenshots"
                os.makedirs(screenshots_dir, exist_ok=True)
                
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"browser_screenshot_{timestamp}.png"
                filepath = os.path.join(screenshots_dir, filename)
                
                self.driver.save_screenshot(filepath)
                
                return ToolResult(
                    success=True,
                    data={
                        "screenshot_path": filepath,
                        "filename": filename,
                        "url": self.driver.current_url,
                        "title": self.driver.title,
                        "method": "selenium"
                    },
                    metadata={"action": "take_screenshot"}
                )
            else:
                # Use system screenshot as fallback, but ensure browser is focused
                from .screenshot_tool import ScreenshotTool
                screenshot_tool = ScreenshotTool()
                return await screenshot_tool.execute("browser screenshot")
                
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to take screenshot: {str(e)}"
            )
    
    async def _new_tab(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Open a new tab."""
        try:
            # CRITICAL: Ensure browser focus before opening new tab
            if not self._ensure_browser_focus():
                return ToolResult(
                    success=False,
                    data=None,
                    error="Failed to focus browser before opening new tab. Please ensure browser is open."
                )
            
            url = kwargs.get('url', None)
            if not url:
                url = self._extract_url_from_query(query)
            
            if self.driver:
                # For Selenium, open new tab
                self.driver.execute_script("window.open('');")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                
                if url:
                    self.driver.get(url)
                    time.sleep(2)
                    
                    return ToolResult(
                        success=True,
                        data={
                            "message": "New tab opened and navigated",
                            "url": url,
                            "current_url": self.driver.current_url,
                            "title": self.driver.title,
                            "method": "selenium"
                        },
                        metadata={"action": "new_tab"}
                    )
                else:
                    return ToolResult(
                        success=True,
                        data={
                            "message": "New tab opened",
                            "method": "selenium"
                        },
                        metadata={"action": "new_tab"}
                    )
            else:
                # For non-Selenium browsers (Safari), use AppleScript
                if self.current_browser:
                    config = self.browser_configs.get(self.current_browser, {})
                    app_name = config.get('app_name', '')
                    
                    if app_name:
                        if url:
                            # AppleScript to open new tab with URL
                            applescript = f'''
                            tell application "{app_name}"
                                activate
                                if (count of windows) = 0 then
                                    make new document
                                end if
                                tell front window
                                    set current tab to (make new tab with properties {{URL:"{url}"}})
                                end tell
                            end tell
                            '''
                        else:
                            # AppleScript to open new empty tab
                            applescript = f'''
                            tell application "{app_name}"
                                activate
                                if (count of windows) = 0 then
                                    make new document
                                else
                                    tell front window
                                        make new tab
                                    end tell
                                end if
                            end tell
                            '''
                        
                        result = subprocess.run(
                            ['osascript', '-e', applescript],
                            capture_output=True, text=True, timeout=10
                        )
                        
                        if result.returncode == 0:
                            return ToolResult(
                                success=True,
                                data={
                                    "message": "New tab opened" + (f" with URL: {url}" if url else ""),
                                    "url": url,
                                    "method": "applescript"
                                },
                                metadata={"action": "new_tab"}
                            )
                        else:
                            return ToolResult(
                                success=False,
                                data=None,
                                error=f"Failed to open new tab: {result.stderr}"
                            )
                
                return ToolResult(
                    success=False,
                    data=None,
                    error="No browser available to open new tab"
                )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to open new tab: {str(e)}"
            )

    async def _close_tab(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Close the current tab (not the entire browser)."""
        try:
            if self.driver:
                # For Selenium, close current tab
                if len(self.driver.window_handles) > 1:
                    # Close current tab if there are multiple tabs
                    self.driver.close()
                    # Switch to the remaining tab
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    
                    return ToolResult(
                        success=True,
                        data={"message": "Tab closed successfully", "method": "selenium"},
                        metadata={"action": "close_tab"}
                    )
                else:
                    # If only one tab, close the entire browser
                    return await self._close_browser(query, kwargs)
            else:
                # For non-Selenium browsers (Safari), use AppleScript to close tab
                if self.current_browser:
                    config = self.browser_configs.get(self.current_browser, {})
                    app_name = config.get('app_name', '')
                    
                    if app_name:
                        # AppleScript to close current tab
                        applescript = f'''
                        tell application "{app_name}"
                            if (count of windows) > 0 then
                                if (count of tabs of front window) > 1 then
                                    close current tab of front window
                                else
                                    close front window
                                end if
                            end if
                        end tell
                        '''
                        
                        result = subprocess.run(
                            ['osascript', '-e', applescript],
                            capture_output=True, text=True, timeout=5
                        )
                        
                        return ToolResult(
                            success=True,
                            data={"message": "Tab closed successfully", "method": "applescript"},
                            metadata={"action": "close_tab"}
                        )
                
                return ToolResult(
                    success=False,
                    data=None,
                    error="No browser or tab to close"
                )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to close tab: {str(e)}"
            )

    async def _close_browser(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Close the entire browser application."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
                # Clear from session manager
                browser_session.clear_driver()
            
            # Also try to close the browser application
            if self.current_browser:
                config = self.browser_configs.get(self.current_browser, {})
                app_name = config.get('app_name', '')
                
                if app_name:
                    applescript = f'tell application "{app_name}" to quit'
                    subprocess.run(['osascript', '-e', applescript], timeout=5)
            
            self.current_browser = None
            
            return ToolResult(
                success=True,
                data={"message": "Browser closed successfully"},
                metadata={"action": "close_browser"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to close browser: {str(e)}"
            )
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL to ensure it has proper protocol."""
        if not url:
            return url
            
        # If URL already has protocol, return as is
        if url.startswith(('http://', 'https://')):
            return url
            
        # Check if it's a known website mapping
        url_lower = url.lower()
        for name, mapped_url in self.website_mappings.items():
            if name == url_lower or url_lower.endswith(f'.{name}') or url_lower.startswith(f'{name}.'):
                return mapped_url
        
        # For gmail.com specifically, use https
        if 'gmail.com' in url_lower:
            return 'https://gmail.com'
            
        # Default to https for any domain
        return f"https://{url}"
    
    def _extract_url_from_query(self, query: str) -> Optional[str]:
        """Extract URL from query."""
        import re
        
        # Check for direct URLs
        url_pattern = r'https?://[^\s]+'
        match = re.search(url_pattern, query)
        if match:
            return match.group(0)
        
        # Check for website names
        query_lower = query.lower()
        for name, url in self.website_mappings.items():
            if name in query_lower:
                return url
        
        # Look for "go to" or "open" patterns
        patterns = [
            r'(?:go to|open|visit)\s+([^\s]+)',
            r'navigate to\s+([^\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                site = match.group(1)
                if site in self.website_mappings:
                    return self.website_mappings[site]
                elif not site.startswith('http'):
                    return f"https://{site}"
                return site
        
        return None
    
    def _extract_selector_from_query(self, query: str) -> Optional[str]:
        """Extract element selector from query."""
        import re
        
        # Look for quoted selectors
        patterns = [
            r'"([^"]*)"',
            r"'([^']*)'",
            r'selector\s*[:\s]\s*([^\s]+)',
            r'element\s*[:\s]\s*([^\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1)
        
        # Common element patterns
        if 'button' in query.lower():
            return 'button'
        elif 'input' in query.lower():
            return 'input'
        elif 'link' in query.lower():
            return 'a'
        
        return None
    
    def _extract_text_from_query(self, query: str) -> Optional[str]:
        """Extract text to type from query."""
        import re
        
        # Look for quoted text
        patterns = [
            r'"([^"]*)"',
            r"'([^']*)'",
            r'type\s+(.+)',
            r'enter\s+(.+)',
            r'input\s+(.+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _find_element_by_selector(self, selector: str):
        """Find a single element by selector."""
        try:
            strategies = [
                (By.ID, selector),
                (By.NAME, selector),
                (By.CLASS_NAME, selector),
                (By.CSS_SELECTOR, selector),
                (By.XPATH, selector),
                (By.TAG_NAME, selector),
                (By.LINK_TEXT, selector),
                (By.PARTIAL_LINK_TEXT, selector)
            ]
            
            for by, value in strategies:
                try:
                    element = self.wait.until(EC.presence_of_element_located((by, value)))
                    return element
                except TimeoutException:
                    continue
            
            return None
            
        except Exception:
            return None
    
    def _find_elements_by_selector(self, selector: str):
        """Find multiple elements by selector."""
        try:
            strategies = [
                (By.ID, selector),
                (By.NAME, selector),
                (By.CLASS_NAME, selector),
                (By.CSS_SELECTOR, selector),
                (By.XPATH, selector),
                (By.TAG_NAME, selector),
                (By.LINK_TEXT, selector),
                (By.PARTIAL_LINK_TEXT, selector)
            ]
            
            for by, value in strategies:
                try:
                    elements = self.driver.find_elements(by, value)
                    if elements:
                        return elements
                except Exception:
                    continue
            
            return []
            
        except Exception:
            return []
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's input schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Description of browser action (e.g., 'open safari and go to swiggy', 'open chrome', 'navigate to google')"
                },
                "browser": {
                    "type": "string",
                    "enum": ["safari", "chrome", "chromium"],
                    "description": "Optional: specific browser to use"
                },
                "url": {
                    "type": "string",
                    "description": "Optional: specific URL to navigate to"
                },
                "headless": {
                    "type": "boolean",
                    "description": "Optional: run browser in headless mode (Chrome/Chromium only)"
                },
                "element_selector": {
                    "type": "string",
                    "description": "Optional: CSS selector, XPath, or element identifier"
                },
                "text": {
                    "type": "string",
                    "description": "Optional: text to type in form fields"
                }
            },
            "required": ["query"]
        }
    
    def __del__(self):
        """Cleanup browser on object destruction."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass