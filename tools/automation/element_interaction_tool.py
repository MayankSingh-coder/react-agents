"""Element interaction tool for precise web element manipulation."""

import time
from typing import Any, Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, StaleElementReferenceException
from ..base_tool import BaseTool, ToolResult
from .browser_session import browser_session
from .window_manager import window_manager


class ElementInteractionTool(BaseTool):
    """Tool for precise interaction with web elements using specific selectors."""
    
    def __init__(self):
        super().__init__(
            name="element_interaction",
            description=self._get_detailed_description()
        )
        
        self.driver = None
        self.wait = None
        self.default_timeout = 10
    
    def _get_detailed_description(self) -> str:
        """Get detailed description with examples for element interaction operations."""
        return """Interact with specific web elements using precise selectors discovered by element_discovery tool.

🎯 WHEN TO USE THIS TOOL:
- Web browsers and web applications
- When you have CSS selectors, IDs, or classes
- Form interactions (input fields, dropdowns, checkboxes)
- Web page automation and testing
- When working with HTML elements

❌ DON'T USE FOR:
- Desktop applications (use ClickTool instead)
- System UI elements (use ClickTool instead)
- When you only have pixel coordinates (use ClickTool instead)
- Non-web applications

OPERATIONS & SYNTAX:

• click - Click on an element
  Usage: {"action": "click", "selector": "#login-button"}
  Usage: {"action": "click", "selector": ".submit-btn"}
  Usage: {"action": "click", "selector": "button[type='submit']"}

• right_click - Right-click on an element
  Usage: {"action": "right_click", "selector": "#menu-item"}
  Usage: {"action": "right_click", "selector": ".context-menu-trigger"}

• double_click - Double-click on an element
  Usage: {"action": "double_click", "selector": ".file-item"}
  Usage: {"action": "double_click", "selector": "#editable-field"}

• type_text - Type text in an element
  Usage: {"action": "type_text", "selector": "#email", "text": "john@email.com"}
  Usage: {"action": "type_text", "selector": "[name='username']", "text": "myuser"}
  Usage: {"action": "type_text", "selector": "#search-input", "text": "pizza"}

• clear_and_type - Clear element and type new text
  Usage: {"action": "clear_and_type", "selector": "#username", "text": "new text"}
  Usage: {"action": "clear_and_type", "selector": "[name='password']", "text": "newpass"}

• append_text - Append text to existing content
  Usage: {"action": "append_text", "selector": "#description", "text": " additional text"}
  Usage: {"action": "append_text", "selector": ".comment-box", "text": " more info"}

• select_dropdown - Select option from dropdown
  Usage: {"action": "select_dropdown", "selector": "#country", "option": "United States"}
  Usage: {"action": "select_dropdown", "selector": ".language-select", "option": "English"}
  ⚠️  IMPORTANT: Option text must match exactly

• check_checkbox - Check a checkbox
  Usage: {"action": "check_checkbox", "selector": "#agree-terms"}
  Usage: {"action": "check_checkbox", "selector": "[name='newsletter']"}

• uncheck_checkbox - Uncheck a checkbox
  Usage: {"action": "uncheck_checkbox", "selector": "#newsletter"}
  Usage: {"action": "uncheck_checkbox", "selector": ".optional-feature"}

• select_radio - Select a radio button
  Usage: {"action": "select_radio", "selector": "#payment-card"}
  Usage: {"action": "select_radio", "selector": "[value='premium']"}

• check_visibility - Check if element is visible
  Usage: {"action": "check_visibility", "selector": "#modal"}
  Usage: {"action": "check_visibility", "selector": ".error-message"}

• check_enabled - Check if element is enabled
  Usage: {"action": "check_enabled", "selector": "#submit-btn"}
  Usage: {"action": "check_enabled", "selector": ".form-button"}

• get_text - Get text content from element
  Usage: {"action": "get_text", "selector": ".status-message"}
  Usage: {"action": "get_text", "selector": "#result-text"}

• get_value - Get value from input element
  Usage: {"action": "get_value", "selector": "#input-field"}
  Usage: {"action": "get_value", "selector": "[name='quantity']"}

• hover - Hover over an element
  Usage: {"action": "hover", "selector": ".menu-item"}
  Usage: {"action": "hover", "selector": "#tooltip-trigger"}

• scroll_to - Scroll element into view
  Usage: {"action": "scroll_to", "selector": "#bottom-section"}
  Usage: {"action": "scroll_to", "selector": ".target-element"}

• wait_for - Wait for element to appear/disappear
  Usage: {"action": "wait_for", "selector": "#loading-spinner"}
  Usage: {"action": "wait_for", "selector": ".success-message", "timeout": 15}

• press_keys - Press specific keys on element
  Usage: {"action": "press_keys", "selector": "#search-input", "keys": "Enter"}
  Usage: {"action": "press_keys", "selector": ".text-field", "keys": "Tab"}
  ⚠️  IMPORTANT: Supports Enter, Tab, Escape, Space, Arrow keys

SELECTOR FORMATS:
- CSS Selectors: '#id', '.class', 'tag[attribute="value"]'
- XPath: '//div[@class="example"]'
- Attribute selectors: '[name="fieldname"]', '[placeholder="Enter email"]'

COMMON PARAMETERS:
- timeout: Custom timeout for operation (default: 10 seconds)
- force: Force interaction even if element seems not ready

ERROR HANDLING:
- Provides detailed error messages when elements are not found
- Suggests alternative selectors when primary selector fails
- Indicates if element exists but is not interactable

INTEGRATION:
Use with element_discovery tool to:
1. First discover elements: {"action": "find_by_type", "element_type": "input"}
2. Then interact with them: {"action": "type_text", "selector": "#discovered-field", "text": "value"}

⚠️  IMPORTANT: Requires active browser session. Use unified_browser to open browser first."""


    async def execute(self, query: str, **kwargs) -> ToolResult:
        """
        Execute element interaction operations.
        
        Available actions (specify in 'action' parameter):
        - click: Click on an element
        - right_click: Right-click on an element
        - double_click: Double-click on an element
        - type_text: Type text in an element
        - clear_and_type: Clear element and type new text
        - append_text: Append text to existing content
        - select_dropdown: Select option from dropdown
        - check_checkbox: Check a checkbox
        - uncheck_checkbox: Uncheck a checkbox
        - select_radio: Select a radio button
        - check_visibility: Check if element is visible
        - check_enabled: Check if element is enabled
        - get_text: Get text content from element
        - get_value: Get value from input element
        - hover: Hover over an element
        - scroll_to: Scroll element into view
        - wait_for: Wait for element to appear/disappear
        - press_keys: Press specific keys on element
        
        Args:
            query: Description of interaction (optional, used for context)
            **kwargs: Action-specific parameters:
                - action: Required - the specific action to perform
                - selector: Required - element selector to interact with
                - text: for type_text/clear_and_type/append_text - text to type
                - option: for select_dropdown - option to select
                - keys: for press_keys - keys to press (e.g., "Enter", "Tab")
                - timeout: custom timeout for operation
                - force: force interaction even if element seems not ready
        
        Examples:
            {"action": "click", "selector": "#login-button"}
            {"action": "type_text", "selector": "#username", "text": "john@email.com"}
            {"action": "clear_and_type", "selector": "[name='password']", "text": "newpassword"}
            {"action": "check_visibility", "selector": ".error-message"}
            {"action": "select_dropdown", "selector": "#country", "option": "United States"}
            {"action": "press_keys", "selector": "#search-input", "keys": "Enter"}
        """
        try:
            # CRITICAL: Ensure browser focus before any element interaction
            browser_type = kwargs.get('browser_type', 'chrome')  # Default to chrome for selenium
            focus_success = window_manager.ensure_browser_focus(browser_type)
            if not focus_success:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Failed to focus {browser_type} browser before element interaction. Please ensure browser is open."
                )
            
            # Get or create WebDriver connection
            if not self._ensure_driver():
                return ToolResult(
                    success=False,
                    data=None,
                    error="No active browser session found. Please open a browser first using unified_browser tool."
                )
            
            # Handle case where parameters are passed as JSON string in query (for LLM agents)
            if not kwargs and query.strip().startswith('{') and query.strip().endswith('}'):
                try:
                    import json
                    parsed_params = json.loads(query)
                    if isinstance(parsed_params, dict):
                        kwargs = parsed_params
                        query = kwargs.pop('query', '')  # Extract query if present
                        print(f"🔧 ElementInteractionTool: Parsed JSON from query parameter")
                        print(f"  new query: '{query}'")
                        print(f"  new kwargs: {kwargs}")
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Failed to parse query as JSON: {e}")
            
            # Parse action from kwargs
            action = kwargs.get('action')
            
            if not action:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Action parameter is required. Available actions: click, type_text, clear_and_type, check_visibility, get_text, hover, scroll_to, press_keys, etc."
                )
            
            if action == 'click':
                result = await self._click_element(query, kwargs)
            elif action == 'right_click':
                result = await self._right_click_element(query, kwargs)
            elif action == 'double_click':
                result = await self._double_click_element(query, kwargs)
            elif action == 'type_text':
                result = await self._type_text(query, kwargs)
            elif action == 'clear_and_type':
                result = await self._clear_and_type(query, kwargs)
            elif action == 'append_text':
                result = await self._append_text(query, kwargs)
            elif action == 'select_dropdown':
                result = await self._select_dropdown(query, kwargs)
            elif action == 'check_checkbox':
                result = await self._check_checkbox(query, kwargs)
            elif action == 'uncheck_checkbox':
                result = await self._uncheck_checkbox(query, kwargs)
            elif action == 'select_radio':
                result = await self._select_radio(query, kwargs)
            elif action == 'check_visibility':
                result = await self._check_visibility(query, kwargs)
            elif action == 'check_enabled':
                result = await self._check_enabled(query, kwargs)
            elif action == 'get_text':
                result = await self._get_text(query, kwargs)
            elif action == 'get_value':
                result = await self._get_value(query, kwargs)
            elif action == 'hover':
                result = await self._hover_element(query, kwargs)
            elif action == 'scroll_to':
                result = await self._scroll_to_element(query, kwargs)
            elif action == 'wait_for':
                result = await self._wait_for_element(query, kwargs)
            elif action == 'press_keys':
                result = await self._press_keys(query, kwargs)
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unknown action: {action}. Available actions: click, right_click, double_click, type_text, clear_and_type, append_text, select_dropdown, check_checkbox, uncheck_checkbox, select_radio, check_visibility, check_enabled, get_text, get_value, hover, scroll_to, wait_for, press_keys"
                )
            
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Element interaction failed: {str(e)}"
            )
    
    def _ensure_driver(self) -> bool:
        """Ensure we have access to a WebDriver instance."""
        try:
            # Check if there's an active browser session
            if browser_session.is_active():
                self.driver = browser_session.driver
                self.wait = browser_session.wait
                return True
            
            return False
            
        except Exception:
            return False
    

    
    async def _click_element(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Click on an element with robust stale element handling."""
        try:
            selector = kwargs.get('selector', None)
            
            if not selector:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Selector parameter is required. Use: {'action': 'click', 'selector': '#element-id'}"
                )
            
            # Find and validate element with retry mechanism
            element, error_msg = self._find_and_validate_element(selector, "click")
            if not element:
                return ToolResult(
                    success=False,
                    data=None,
                    error=error_msg
                )
            
            # Perform click with stale element retry
            max_click_retries = 3
            for attempt in range(max_click_retries):
                try:
                    # Scroll element into view
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(0.3)
                    
                    # Double-check element is still valid before clicking
                    is_valid, validation_error = self._validate_element_for_interaction(element, "click")
                    if not is_valid:
                        if "stale" in validation_error.lower() and attempt < max_click_retries - 1:
                            # Re-find element if it became stale
                            element, error_msg = self._find_and_validate_element(selector, "click")
                            if not element:
                                return ToolResult(
                                    success=False,
                                    data=None,
                                    error=f"Element became stale and could not be re-found: {error_msg}"
                                )
                            continue
                        else:
                            return ToolResult(
                                success=False,
                                data=None,
                                error=validation_error
                            )
                    
                    # Wait for element to be clickable and click
                    clickable_element = self.wait.until(EC.element_to_be_clickable(element))
                    clickable_element.click()
                    
                    # Success - get element info for response
                    element_tag = element.tag_name
                    element_text = element.text[:100] if element.text else ""
                    
                    return ToolResult(
                        success=True,
                        data={
                            "action": "click",
                            "selector": selector,
                            "element_tag": element_tag,
                            "element_text": element_text,
                            "current_url": self.driver.current_url,
                            "attempts": attempt + 1
                        },
                        metadata={"action": "click_element"}
                    )
                    
                except StaleElementReferenceException:
                    if attempt < max_click_retries - 1:
                        # Re-find element and retry
                        element, error_msg = self._find_and_validate_element(selector, "click")
                        if not element:
                            return ToolResult(
                                success=False,
                                data=None,
                                error=f"Element became stale and could not be re-found: {error_msg}"
                            )
                        time.sleep(0.5)
                        continue
                    else:
                        return ToolResult(
                            success=False,
                            data=None,
                            error=f"Element remained stale after {max_click_retries} attempts: {selector}"
                        )
                        
                except ElementNotInteractableException:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Element exists but is not interactable: {selector}. It might be hidden or covered by another element."
                    )
                    
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to click element after {max_click_retries} attempts: {selector}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to click element: {str(e)}"
            )
    
    async def _type_text(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Type text in an element with robust stale element handling."""
        try:
            selector = kwargs.get('selector', None)
            text = kwargs.get('text', None)
            
            if not selector:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Selector parameter is required. Use: {'action': 'type_text', 'selector': '#element-id', 'text': 'your text'}"
                )
            
            if not text:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Text parameter is required. Use: {'action': 'type_text', 'selector': '#element-id', 'text': 'your text'}"
                )
            
            # Find and validate element with retry mechanism
            element, error_msg = self._find_and_validate_element(selector, "type_text")
            if not element:
                return ToolResult(
                    success=False,
                    data=None,
                    error=error_msg
                )
            
            # Perform text input with stale element retry
            max_type_retries = 3
            for attempt in range(max_type_retries):
                try:
                    # Double-check element is still valid before typing
                    is_valid, validation_error = self._validate_element_for_interaction(element, "type_text")
                    if not is_valid:
                        if "stale" in validation_error.lower() and attempt < max_type_retries - 1:
                            # Re-find element if it became stale
                            element, error_msg = self._find_and_validate_element(selector, "type_text")
                            if not element:
                                return ToolResult(
                                    success=False,
                                    data=None,
                                    error=f"Element became stale and could not be re-found: {error_msg}"
                                )
                            continue
                        else:
                            return ToolResult(
                                success=False,
                                data=None,
                                error=validation_error
                            )
                    
                    # Scroll element into view and focus
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(0.3)
                    element.click()  # Focus the element
                    
                    # Type the text
                    element.send_keys(text)
                    
                    # Get current value for response
                    current_value = element.get_attribute('value') if element.tag_name == 'input' else element.text
                    
                    return ToolResult(
                        success=True,
                        data={
                            "action": "type_text",
                            "selector": selector,
                            "text_typed": text,
                            "element_tag": element.tag_name,
                            "current_value": current_value,
                            "current_url": self.driver.current_url,
                            "attempts": attempt + 1
                        },
                        metadata={"action": "type_text"}
                    )
                    
                except StaleElementReferenceException:
                    if attempt < max_type_retries - 1:
                        # Re-find element and retry
                        element, error_msg = self._find_and_validate_element(selector, "type_text")
                        if not element:
                            return ToolResult(
                                success=False,
                                data=None,
                                error=f"Element became stale and could not be re-found: {error_msg}"
                            )
                        time.sleep(0.5)
                        continue
                    else:
                        return ToolResult(
                            success=False,
                            data=None,
                            error=f"Element remained stale after {max_type_retries} attempts: {selector}"
                        )
                        
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to type text after {max_type_retries} attempts: {selector}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to type text: {str(e)}"
            )
    
    async def _clear_and_type(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Clear element and type new text with robust stale element handling."""
        try:
            selector = kwargs.get('selector', None)
            text = kwargs.get('text', None)
            
            if not selector:
                selector = self._extract_selector_from_query(query)
            if not text:
                text = self._extract_text_from_query(query)
            
            if not selector or not text:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Both selector and text are required"
                )
            
            # Find and validate element with retry mechanism
            element, error_msg = self._find_and_validate_element(selector, "clear_and_type")
            if not element:
                return ToolResult(
                    success=False,
                    data=None,
                    error=error_msg
                )
            
            # Perform clear and type with stale element retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Double-check element is still valid
                    is_valid, validation_error = self._validate_element_for_interaction(element, "clear_and_type")
                    if not is_valid:
                        if "stale" in validation_error.lower() and attempt < max_retries - 1:
                            # Re-find element if it became stale
                            element, error_msg = self._find_and_validate_element(selector, "clear_and_type")
                            if not element:
                                return ToolResult(
                                    success=False,
                                    data=None,
                                    error=f"Element became stale and could not be re-found: {error_msg}"
                                )
                            continue
                        else:
                            return ToolResult(
                                success=False,
                                data=None,
                                error=validation_error
                            )
                    
                    # Scroll element into view and focus
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(0.3)
                    element.click()
                    
                    # Clear existing text and type new text
                    element.clear()
                    element.send_keys(text)
                    
                    # Get current value for response
                    current_value = element.get_attribute('value') if element.tag_name == 'input' else element.text
                    
                    return ToolResult(
                        success=True,
                        data={
                            "action": "clear_and_type",
                            "selector": selector,
                            "text_typed": text,
                            "current_value": current_value,
                            "current_url": self.driver.current_url,
                            "attempts": attempt + 1
                        },
                        metadata={"action": "clear_and_type"}
                    )
                    
                except StaleElementReferenceException:
                    if attempt < max_retries - 1:
                        # Re-find element and retry
                        element, error_msg = self._find_and_validate_element(selector, "clear_and_type")
                        if not element:
                            return ToolResult(
                                success=False,
                                data=None,
                                error=f"Element became stale and could not be re-found: {error_msg}"
                            )
                        time.sleep(0.5)
                        continue
                    else:
                        return ToolResult(
                            success=False,
                            data=None,
                            error=f"Element remained stale after {max_retries} attempts: {selector}"
                        )
                        
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to clear and type after {max_retries} attempts: {selector}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to clear and type: {str(e)}"
            )
    
    async def _check_visibility(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Check if an element is visible."""
        try:
            selector = kwargs.get('selector', None)
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
                    success=True,
                    data={
                        "selector": selector,
                        "exists": False,
                        "visible": False,
                        "message": "Element does not exist"
                    },
                    metadata={"action": "check_visibility"}
                )
            
            is_visible = element.is_displayed()
            
            return ToolResult(
                success=True,
                data={
                    "selector": selector,
                    "exists": True,
                    "visible": is_visible,
                    "enabled": element.is_enabled(),
                    "element_tag": element.tag_name,
                    "element_text": element.text[:100] if element.text else "",
                    "current_url": self.driver.current_url
                },
                metadata={"action": "check_visibility"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to check visibility: {str(e)}"
            )
    
    async def _get_text(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Get text content from an element."""
        try:
            selector = kwargs.get('selector', None)
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
                    error=f"Element not found with selector: {selector}"
                )
            
            text_content = element.text
            value_content = element.get_attribute('value')
            
            return ToolResult(
                success=True,
                data={
                    "selector": selector,
                    "text": text_content,
                    "value": value_content,
                    "element_tag": element.tag_name,
                    "visible": element.is_displayed(),
                    "current_url": self.driver.current_url
                },
                metadata={"action": "get_text"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to get text: {str(e)}"
            )
    
    def _find_element_by_selector(self, selector: str):
        """Find element using various selector strategies with detailed error reporting."""
        try:
            # Primary strategies with timeout
            strategies = [
                (By.CSS_SELECTOR, selector),
                (By.ID, selector.replace('#', '')),
                (By.NAME, selector),
                (By.CLASS_NAME, selector.replace('.', '')),
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
    
    def _is_element_stale(self, element) -> bool:
        """Check if an element is stale (no longer attached to DOM)."""
        try:
            # Try to access a property - this will raise StaleElementReferenceException if stale
            _ = element.is_enabled()
            return False
        except StaleElementReferenceException:
            return True
        except Exception:
            # Other exceptions might indicate the element is problematic
            return True
    
    def _validate_element_for_interaction(self, element, interaction_type: str = "click") -> tuple[bool, str]:
        """
        Validate if element is ready for interaction.
        
        Args:
            element: WebElement to validate
            interaction_type: Type of interaction (click, type, etc.)
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # Check if element is stale
            if self._is_element_stale(element):
                return False, "Element is stale (no longer attached to DOM)"
            
            # Check if element is displayed
            if not element.is_displayed():
                return False, "Element is not visible on the page"
            
            # Check if element is enabled
            if not element.is_enabled():
                return False, "Element is not enabled/interactable"
            
            # Additional checks based on interaction type
            if interaction_type in ["click", "right_click", "double_click"]:
                # For click interactions, check if element is clickable
                try:
                    # Try to get element location - this can fail if element is not interactable
                    location = element.location
                    size = element.size
                    if location['x'] < 0 or location['y'] < 0 or size['width'] <= 0 or size['height'] <= 0:
                        return False, "Element has invalid dimensions or position"
                except Exception:
                    return False, "Element location/size cannot be determined"
            
            elif interaction_type in ["type_text", "clear_and_type", "append_text"]:
                # For text input, check if element can receive text
                tag_name = element.tag_name.lower()
                if tag_name not in ['input', 'textarea'] and not element.get_attribute('contenteditable'):
                    return False, f"Element is not a text input field (tag: {tag_name})"
                
                # Check if input is readonly
                if element.get_attribute('readonly'):
                    return False, "Element is readonly and cannot be modified"
            
            return True, ""
            
        except StaleElementReferenceException:
            return False, "Element became stale during validation"
        except Exception as e:
            return False, f"Element validation failed: {str(e)}"
    
    def _find_and_validate_element(self, selector: str, interaction_type: str = "click", max_retries: int = 3):
        """
        Find element and validate it for interaction with retry mechanism for stale elements.
        
        Args:
            selector: Element selector
            interaction_type: Type of interaction to validate for
            max_retries: Maximum number of retries for stale elements
            
        Returns:
            tuple: (element, error_message) - element is None if failed
        """
        for attempt in range(max_retries):
            try:
                # Find the element
                element = self._find_element_by_selector(selector)
                if not element:
                    return None, f"Element not found with selector: {selector}. Use element_discovery tool to find correct selector."
                
                # Validate element for interaction
                is_valid, error_msg = self._validate_element_for_interaction(element, interaction_type)
                if not is_valid:
                    if "stale" in error_msg.lower() and attempt < max_retries - 1:
                        # If element is stale, wait a bit and retry
                        time.sleep(0.5)
                        continue
                    return None, error_msg
                
                return element, ""
                
            except StaleElementReferenceException:
                if attempt < max_retries - 1:
                    # Wait and retry for stale elements
                    time.sleep(0.5)
                    continue
                return None, f"Element became stale after {max_retries} attempts: {selector}"
            except Exception as e:
                return None, f"Failed to find/validate element: {str(e)}"
        
        return None, f"Failed to find stable element after {max_retries} attempts: {selector}"
    
    def _extract_selector_from_query(self, query: str) -> Optional[str]:
        """Extract element selector from query."""
        import re
        
        # Look for various selector patterns
        patterns = [
            r'selector\s+["\']([^"\']+)["\']',
            r'element\s+["\']([^"\']+)["\']',
            r'with\s+selector\s+["\']([^"\']+)["\']',
            r'element\s+with\s+selector\s+["\']([^"\']+)["\']',
            r'in\s+element\s+["\']([^"\']+)["\']',
            r'from\s+element\s+["\']([^"\']+)["\']',
            r'on\s+element\s+["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_text_from_query(self, query: str) -> Optional[str]:
        """Extract text to type from query."""
        import re
        
        patterns = [
            r'type\s+["\']([^"\']+)["\']',
            r'enter\s+["\']([^"\']+)["\']',
            r'input\s+["\']([^"\']+)["\']',
            r'text\s+["\']([^"\']+)["\']',
            r'["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    async def _right_click_element(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Right-click on an element."""
        try:
            selector = kwargs.get('selector', None)
            
            if not selector:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Selector parameter is required. Use: {'action': 'right_click', 'selector': '#element-id'}"
                )
            
            element = self._find_element_by_selector(selector)
            if not element:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Element not found with selector: {selector}"
                )
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            # Right-click using ActionChains
            actions = ActionChains(self.driver)
            actions.context_click(element).perform()
            
            return ToolResult(
                success=True,
                data={
                    "action": "right_click",
                    "selector": selector,
                    "element_tag": element.tag_name,
                    "current_url": self.driver.current_url
                },
                metadata={"action": "right_click_element"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to right-click element: {str(e)}"
            )
    
    async def _double_click_element(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Double-click on an element."""
        try:
            selector = kwargs.get('selector', None)
            
            if not selector:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Selector parameter is required. Use: {'action': 'double_click', 'selector': '#element-id'}"
                )
            
            element = self._find_element_by_selector(selector)
            if not element:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Element not found with selector: {selector}"
                )
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            # Double-click using ActionChains
            actions = ActionChains(self.driver)
            actions.double_click(element).perform()
            
            return ToolResult(
                success=True,
                data={
                    "action": "double_click",
                    "selector": selector,
                    "element_tag": element.tag_name,
                    "current_url": self.driver.current_url
                },
                metadata={"action": "double_click_element"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to double-click element: {str(e)}"
            )
    
    async def _append_text(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Append text to an element."""
        try:
            selector = kwargs.get('selector', None)
            text = kwargs.get('text', None)
            
            if not selector or not text:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Both selector and text parameters are required"
                )
            
            element = self._find_element_by_selector(selector)
            if not element:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Element not found with selector: {selector}"
                )
            
            # Scroll element into view and focus
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            element.click()
            
            # Move cursor to end and append text
            element.send_keys(Keys.END)
            element.send_keys(text)
            
            return ToolResult(
                success=True,
                data={
                    "action": "append_text",
                    "selector": selector,
                    "text_appended": text,
                    "current_value": element.get_attribute('value') if element.tag_name == 'input' else element.text,
                    "current_url": self.driver.current_url
                },
                metadata={"action": "append_text"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to append text: {str(e)}"
            )
    
    async def _select_dropdown(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Select option from dropdown."""
        try:
            from selenium.webdriver.support.ui import Select
            
            selector = kwargs.get('selector', None)
            option = kwargs.get('option', None)
            
            if not selector or not option:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Both selector and option parameters are required"
                )
            
            element = self._find_element_by_selector(selector)
            if not element:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Element not found with selector: {selector}"
                )
            
            if element.tag_name != 'select':
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Element is not a select dropdown: {selector}"
                )
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            # Select option
            select = Select(element)
            try:
                select.select_by_visible_text(option)
            except:
                try:
                    select.select_by_value(option)
                except:
                    select.select_by_index(int(option))
            
            return ToolResult(
                success=True,
                data={
                    "action": "select_dropdown",
                    "selector": selector,
                    "option_selected": option,
                    "current_selection": select.first_selected_option.text,
                    "current_url": self.driver.current_url
                },
                metadata={"action": "select_dropdown"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to select dropdown option: {str(e)}"
            )
    
    async def _check_checkbox(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Check a checkbox."""
        try:
            selector = kwargs.get('selector', None)
            
            if not selector:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Selector parameter is required"
                )
            
            element = self._find_element_by_selector(selector)
            if not element:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Element not found with selector: {selector}"
                )
            
            if element.get_attribute('type') != 'checkbox':
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Element is not a checkbox: {selector}"
                )
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            # Check if already checked
            if not element.is_selected():
                element.click()
            
            return ToolResult(
                success=True,
                data={
                    "action": "check_checkbox",
                    "selector": selector,
                    "checked": element.is_selected(),
                    "current_url": self.driver.current_url
                },
                metadata={"action": "check_checkbox"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to check checkbox: {str(e)}"
            )
    
    async def _uncheck_checkbox(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Uncheck a checkbox."""
        try:
            selector = kwargs.get('selector', None)
            
            if not selector:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Selector parameter is required"
                )
            
            element = self._find_element_by_selector(selector)
            if not element:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Element not found with selector: {selector}"
                )
            
            if element.get_attribute('type') != 'checkbox':
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Element is not a checkbox: {selector}"
                )
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            # Uncheck if checked
            if element.is_selected():
                element.click()
            
            return ToolResult(
                success=True,
                data={
                    "action": "uncheck_checkbox",
                    "selector": selector,
                    "checked": element.is_selected(),
                    "current_url": self.driver.current_url
                },
                metadata={"action": "uncheck_checkbox"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to uncheck checkbox: {str(e)}"
            )
    
    async def _select_radio(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Select a radio button."""
        try:
            selector = kwargs.get('selector', None)
            
            if not selector:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Selector parameter is required"
                )
            
            element = self._find_element_by_selector(selector)
            if not element:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Element not found with selector: {selector}"
                )
            
            if element.get_attribute('type') != 'radio':
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Element is not a radio button: {selector}"
                )
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            # Select radio button
            element.click()
            
            return ToolResult(
                success=True,
                data={
                    "action": "select_radio",
                    "selector": selector,
                    "selected": element.is_selected(),
                    "current_url": self.driver.current_url
                },
                metadata={"action": "select_radio"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to select radio button: {str(e)}"
            )
    
    async def _check_enabled(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Check if an element is enabled."""
        try:
            selector = kwargs.get('selector', None)
            
            if not selector:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Selector parameter is required"
                )
            
            element = self._find_element_by_selector(selector)
            if not element:
                return ToolResult(
                    success=True,
                    data={
                        "selector": selector,
                        "exists": False,
                        "enabled": False,
                        "message": "Element does not exist"
                    },
                    metadata={"action": "check_enabled"}
                )
            
            is_enabled = element.is_enabled()
            
            return ToolResult(
                success=True,
                data={
                    "selector": selector,
                    "exists": True,
                    "enabled": is_enabled,
                    "visible": element.is_displayed(),
                    "element_tag": element.tag_name,
                    "current_url": self.driver.current_url
                },
                metadata={"action": "check_enabled"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to check enabled state: {str(e)}"
            )
    
    async def _get_value(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Get value from an input element."""
        try:
            selector = kwargs.get('selector', None)
            
            if not selector:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Selector parameter is required"
                )
            
            element = self._find_element_by_selector(selector)
            if not element:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Element not found with selector: {selector}"
                )
            
            value_content = element.get_attribute('value')
            text_content = element.text
            
            return ToolResult(
                success=True,
                data={
                    "selector": selector,
                    "value": value_content,
                    "text": text_content,
                    "element_tag": element.tag_name,
                    "current_url": self.driver.current_url
                },
                metadata={"action": "get_value"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to get value: {str(e)}"
            )
    
    async def _hover_element(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Hover over an element."""
        try:
            selector = kwargs.get('selector', None)
            
            if not selector:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Selector parameter is required"
                )
            
            element = self._find_element_by_selector(selector)
            if not element:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Element not found with selector: {selector}"
                )
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            # Hover using ActionChains
            actions = ActionChains(self.driver)
            actions.move_to_element(element).perform()
            
            return ToolResult(
                success=True,
                data={
                    "action": "hover",
                    "selector": selector,
                    "element_tag": element.tag_name,
                    "current_url": self.driver.current_url
                },
                metadata={"action": "hover_element"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to hover over element: {str(e)}"
            )
    
    async def _scroll_to_element(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Scroll element into view."""
        try:
            selector = kwargs.get('selector', None)
            
            if not selector:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Selector parameter is required"
                )
            
            element = self._find_element_by_selector(selector)
            if not element:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Element not found with selector: {selector}"
                )
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(1)
            
            return ToolResult(
                success=True,
                data={
                    "action": "scroll_to",
                    "selector": selector,
                    "element_tag": element.tag_name,
                    "visible": element.is_displayed(),
                    "current_url": self.driver.current_url
                },
                metadata={"action": "scroll_to_element"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to scroll to element: {str(e)}"
            )
    
    async def _wait_for_element(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Wait for element to appear or disappear."""
        try:
            selector = kwargs.get('selector', None)
            timeout = kwargs.get('timeout', 10)
            wait_for = kwargs.get('wait_for', 'appear')  # 'appear' or 'disappear'
            
            if not selector:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Selector parameter is required"
                )
            
            wait = WebDriverWait(self.driver, timeout)
            
            if wait_for == 'disappear':
                # Wait for element to disappear
                wait.until_not(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                return ToolResult(
                    success=True,
                    data={
                        "action": "wait_for",
                        "selector": selector,
                        "wait_for": "disappear",
                        "timeout": timeout,
                        "result": "Element disappeared"
                    },
                    metadata={"action": "wait_for_element"}
                )
            else:
                # Wait for element to appear
                element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                return ToolResult(
                    success=True,
                    data={
                        "action": "wait_for",
                        "selector": selector,
                        "wait_for": "appear",
                        "timeout": timeout,
                        "result": "Element appeared",
                        "element_tag": element.tag_name,
                        "visible": element.is_displayed()
                    },
                    metadata={"action": "wait_for_element"}
                )
            
        except TimeoutException:
            return ToolResult(
                success=False,
                data=None,
                error=f"Timeout waiting for element {selector} to {wait_for}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to wait for element: {str(e)}"
            )
    
    async def _press_keys(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Press specific keys on an element."""
        try:
            selector = kwargs.get('selector', None)
            keys = kwargs.get('keys', None)
            
            if not selector or not keys:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Both selector and keys parameters are required"
                )
            
            element = self._find_element_by_selector(selector)
            if not element:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Element not found with selector: {selector}"
                )
            
            # Scroll element into view and focus
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            element.click()
            
            # Map key names to Selenium Keys
            key_mapping = {
                'Enter': Keys.ENTER,
                'Return': Keys.RETURN,
                'Tab': Keys.TAB,
                'Escape': Keys.ESCAPE,
                'Space': Keys.SPACE,
                'Backspace': Keys.BACKSPACE,
                'Delete': Keys.DELETE,
                'ArrowUp': Keys.ARROW_UP,
                'ArrowDown': Keys.ARROW_DOWN,
                'ArrowLeft': Keys.ARROW_LEFT,
                'ArrowRight': Keys.ARROW_RIGHT,
                'Home': Keys.HOME,
                'End': Keys.END,
                'PageUp': Keys.PAGE_UP,
                'PageDown': Keys.PAGE_DOWN
            }
            
            # Press the key
            key_to_press = key_mapping.get(keys, keys)
            element.send_keys(key_to_press)
            
            return ToolResult(
                success=True,
                data={
                    "action": "press_keys",
                    "selector": selector,
                    "keys_pressed": keys,
                    "element_tag": element.tag_name,
                    "current_url": self.driver.current_url
                },
                metadata={"action": "press_keys"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to press keys: {str(e)}"
            )
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's input schema for LLM agents."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Optional description of the interaction"
                },
                "action": {
                    "type": "string",
                    "description": "The specific interaction action to perform",
                    "enum": [
                        "click", "right_click", "double_click",
                        "type_text", "clear_and_type", "append_text",
                        "select_dropdown", "check_checkbox", "uncheck_checkbox", "select_radio",
                        "check_visibility", "check_enabled", "get_text", "get_value",
                        "hover", "scroll_to", "wait_for", "press_keys"
                    ]
                },
                "selector": {
                    "type": "string",
                    "description": "CSS selector for the target element"
                },
                "text": {
                    "type": "string",
                    "description": "Text to type or append (for text input actions)"
                },
                "option": {
                    "type": "string",
                    "description": "Option to select (for dropdown selection)"
                },
                "keys": {
                    "type": "string",
                    "description": "Keys to press (for press_keys action)",
                    "enum": ["Enter", "Return", "Tab", "Escape", "Space", "Backspace", "Delete", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Home", "End", "PageUp", "PageDown"]
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds for wait operations",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 60
                },
                "wait_for": {
                    "type": "string",
                    "description": "What to wait for (for wait_for action)",
                    "enum": ["appear", "disappear"],
                    "default": "appear"
                }
            },
            "required": ["action", "selector"],
            "additionalProperties": False
        }