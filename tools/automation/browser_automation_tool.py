"""Browser automation tool using Selenium WebDriver."""

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
from .window_manager import window_manager


class BrowserAutomationTool(BaseTool):
    """Tool for automating browser interactions using Selenium."""
    
    def __init__(self):
        super().__init__(
            name="browser_automation",
            description="Automate browser interactions like opening websites, clicking elements, filling forms"
        )
        
        self.driver = None
        self.wait = None
        self.default_timeout = 10
        
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
    
    async def execute(self, query: str, **kwargs) -> ToolResult:
        """
        Execute browser automation based on the query.
        
        Args:
            query: Description of browser action to perform
            **kwargs: Additional parameters:
                - url: specific URL to navigate to
                - action: specific action (open, click, type, etc.)
                - element_selector: CSS selector or XPath for element
                - text: text to type
                - headless: run browser in headless mode
        """
        try:
            action = self._determine_action(query, kwargs)
            
            # CRITICAL: Ensure browser focus before any browser operation (except open_browser)
            if action != 'open_browser':
                browser_type = kwargs.get('browser_type', 'chrome')  # Default to chrome for selenium
                focus_success = window_manager.ensure_browser_focus(browser_type)
                if not focus_success:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Failed to focus {browser_type} browser before {action}. Please ensure browser is open."
                    )
            
            if action == 'open_browser':
                result = await self._open_browser(query, kwargs)
            elif action == 'navigate':
                result = await self._navigate_to_url(query, kwargs)
            elif action == 'click_element':
                result = await self._click_element(query, kwargs)
            elif action == 'type_text':
                result = await self._type_in_element(query, kwargs)
            elif action == 'find_element':
                result = await self._find_element(query, kwargs)
            elif action == 'get_page_info':
                result = await self._get_page_info(query, kwargs)
            elif action == 'close_browser':
                result = await self._close_browser(query, kwargs)
            elif action == 'take_screenshot':
                result = await self._take_screenshot(query, kwargs)
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unknown browser action: {action}"
                )
            
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Browser automation failed: {str(e)}"
            )
    
    def _determine_action(self, query: str, kwargs: Dict[str, Any]) -> str:
        """Determine the browser action to perform."""
        query_lower = query.lower()
        
        # Check kwargs first
        if 'action' in kwargs:
            return kwargs['action']
        
        # Determine action from query
        if any(word in query_lower for word in ['open', 'launch', 'start']):
            if 'browser' in query_lower or not self.driver:
                return 'open_browser'
            else:
                return 'navigate'
        elif any(word in query_lower for word in ['navigate', 'go to', 'visit']):
            return 'navigate'
        elif any(word in query_lower for word in ['click', 'press', 'tap']):
            return 'click_element'
        elif any(word in query_lower for word in ['type', 'enter', 'input', 'fill']):
            return 'type_text'
        elif any(word in query_lower for word in ['find', 'locate', 'search for']):
            return 'find_element'
        elif any(word in query_lower for word in ['screenshot', 'capture', 'image']):
            return 'take_screenshot'
        elif any(word in query_lower for word in ['close', 'quit', 'exit']):
            return 'close_browser'
        elif any(word in query_lower for word in ['page', 'title', 'url', 'info']):
            return 'get_page_info'
        else:
            return 'navigate'  # Default action
    
    async def _open_browser(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Open a new browser instance."""
        try:
            if self.driver:
                # Browser already open
                return ToolResult(
                    success=True,
                    data={"message": "Browser already open", "current_url": self.driver.current_url},
                    metadata={"action": "open_browser"}
                )
            
            # Configure Chrome options
            chrome_options = Options()
            
            # Check if headless mode requested
            headless = kwargs.get('headless', False)
            if headless:
                chrome_options.add_argument('--headless')
            
            # Additional Chrome options for better automation
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Try to use Chromium if available, otherwise Chrome
            try:
                # First try to find Chromium
                chromium_path = "/Applications/Chromium.app/Contents/MacOS/Chromium"
                if os.path.exists(chromium_path):
                    chrome_options.binary_location = chromium_path
            except Exception:
                pass  # Fall back to default Chrome
            
            # Initialize WebDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, self.default_timeout)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return ToolResult(
                success=True,
                data={
                    "message": "Browser opened successfully",
                    "browser": "Chrome/Chromium",
                    "headless": headless
                },
                metadata={"action": "open_browser"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to open browser: {str(e)}"
            )
    
    async def _navigate_to_url(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Navigate to a specific URL."""
        try:
            # Ensure browser is open
            if not self.driver:
                await self._open_browser(query, kwargs)
            
            # Get URL
            url = kwargs.get('url', None)
            if not url:
                url = self._extract_url_from_query(query)
            
            if not url:
                return ToolResult(
                    success=False,
                    data=None,
                    error="No URL provided or could be extracted from query"
                )
            
            # Navigate to URL
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(2)
            
            return ToolResult(
                success=True,
                data={
                    "url": url,
                    "current_url": self.driver.current_url,
                    "title": self.driver.title
                },
                metadata={"action": "navigate", "query": query}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to navigate to URL: {str(e)}"
            )
    
    async def _click_element(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Click on a web element."""
        try:
            if not self.driver:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Browser not open. Please open browser first."
                )
            
            # Get element selector
            selector = kwargs.get('element_selector', None)
            if not selector:
                selector = self._extract_selector_from_query(query)
            
            if not selector:
                return ToolResult(
                    success=False,
                    data=None,
                    error="No element selector provided"
                )
            
            # Find and click element
            element = self._find_element_by_selector(selector)
            if not element:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Element not found: {selector}"
                )
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            # Click element
            element.click()
            
            return ToolResult(
                success=True,
                data={
                    "element_clicked": selector,
                    "element_text": element.text[:100] if element.text else "",
                    "current_url": self.driver.current_url
                },
                metadata={"action": "click_element", "query": query}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to click element: {str(e)}"
            )
    
    async def _type_in_element(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Type text in a web element."""
        try:
            if not self.driver:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Browser not open. Please open browser first."
                )
            
            # Get element selector and text
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
            
            # Find element
            element = self._find_element_by_selector(selector)
            if not element:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Element not found: {selector}"
                )
            
            # Clear and type text
            element.clear()
            element.send_keys(text)
            
            return ToolResult(
                success=True,
                data={
                    "element": selector,
                    "text_typed": text,
                    "current_url": self.driver.current_url
                },
                metadata={"action": "type_text", "query": query}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to type in element: {str(e)}"
            )
    
    async def _find_element(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Find elements on the page."""
        try:
            if not self.driver:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Browser not open. Please open browser first."
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
                metadata={"action": "find_element", "query": query}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to find elements: {str(e)}"
            )
    
    async def _get_page_info(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Get information about the current page."""
        try:
            if not self.driver:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Browser not open. Please open browser first."
                )
            
            page_info = {
                "title": self.driver.title,
                "url": self.driver.current_url,
                "page_source_length": len(self.driver.page_source)
            }
            
            return ToolResult(
                success=True,
                data=page_info,
                metadata={"action": "get_page_info", "query": query}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to get page info: {str(e)}"
            )
    
    async def _take_screenshot(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Take a screenshot of the current page."""
        try:
            if not self.driver:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Browser not open. Please open browser first."
                )
            
            # Create screenshots directory
            screenshots_dir = "/Users/mayank/Desktop/concepts/react-agents/screenshots"
            os.makedirs(screenshots_dir, exist_ok=True)
            
            # Generate filename
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"browser_screenshot_{timestamp}.png"
            filepath = os.path.join(screenshots_dir, filename)
            
            # Take screenshot
            self.driver.save_screenshot(filepath)
            
            return ToolResult(
                success=True,
                data={
                    "screenshot_path": filepath,
                    "filename": filename,
                    "url": self.driver.current_url,
                    "title": self.driver.title
                },
                metadata={"action": "take_screenshot", "query": query}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to take screenshot: {str(e)}"
            )
    
    async def _close_browser(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Close the browser."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
                
                return ToolResult(
                    success=True,
                    data={"message": "Browser closed successfully"},
                    metadata={"action": "close_browser"}
                )
            else:
                return ToolResult(
                    success=True,
                    data={"message": "Browser was not open"},
                    metadata={"action": "close_browser"}
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to close browser: {str(e)}"
            )
    
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
        # This is a simplified version - in production you'd want more sophisticated parsing
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
            # Try different selector strategies
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
                    "description": "Description of browser action (e.g., 'open swiggy', 'click login button', 'type username')"
                },
                "url": {
                    "type": "string",
                    "description": "Optional: specific URL to navigate to"
                },
                "action": {
                    "type": "string",
                    "enum": ["open_browser", "navigate", "click_element", "type_text", "find_element", "get_page_info", "close_browser", "take_screenshot"],
                    "description": "Optional: specific action to perform"
                },
                "element_selector": {
                    "type": "string",
                    "description": "Optional: CSS selector, XPath, or element identifier"
                },
                "text": {
                    "type": "string",
                    "description": "Optional: text to type in form fields"
                },
                "headless": {
                    "type": "boolean",
                    "description": "Optional: run browser in headless mode (default: false)"
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