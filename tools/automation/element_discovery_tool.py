"""Element discovery tool for finding and analyzing web page elements."""

import logging
import time
from typing import Any, Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from ..base_tool import BaseTool, ToolResult
from .browser_session import browser_session
from .window_manager import window_manager


class ElementDiscoveryTool(BaseTool):
    """Tool for discovering and analyzing web page elements."""
    
    def __init__(self):
        super().__init__(
            name="element_discovery",
            description=self._get_simple_description()
        )
        
        self.driver = None
        self.wait = None
        self.default_timeout = 5
    
    def _get_detailed_description(self) -> str:
        """Get detailed description with examples for element discovery operations."""
        return """Discover and analyze interactive elements on web pages for automation.

OPERATIONS & SYNTAX:

• find_all_elements - Find all interactive elements on page
  Usage: {"action": "find_all_elements"}
  Usage: {"action": "find_all_elements", "limit": 10}
  Usage: {"action": "find_all_elements", "visible_only": false}

• find_by_type <element_type> - Find elements by specific type
  Usage: {"action": "find_by_type", "element_type": "button"}
  Usage: {"action": "find_by_type", "element_type": "input"}
  Usage: {"action": "find_by_type", "element_type": "link"}
  Usage: {"action": "find_by_type", "element_type": "form"}
  ⚠️  IMPORTANT: Supports button, input, link, form, field, text, checkbox, radio, select

• find_by_text <text_contains> - Find elements containing specific text
  Usage: {"action": "find_by_text", "text_contains": "Sign Up"}
  Usage: {"action": "find_by_text", "text_contains": "login"}
  Usage: {"action": "find_by_text", "text_contains": "Submit"}

• find_form_elements - Find all form-related elements
  Usage: {"action": "find_form_elements"}
  Usage: {"action": "find_form_elements", "limit": 15}

• analyze_element <element_selector> - Get detailed element information
  Usage: {"action": "analyze_element", "element_selector": "#login-form"}
  Usage: {"action": "analyze_element", "element_selector": ".submit-btn"}
  Usage: {"action": "analyze_element", "element_selector": "button[type='submit']"}

• find_by_attributes <attribute_filter> - Find elements by attributes
  Usage: {"action": "find_by_attributes", "attribute_filter": {"placeholder": "email"}}
  Usage: {"action": "find_by_attributes", "attribute_filter": {"type": "password"}}
  Usage: {"action": "find_by_attributes", "attribute_filter": {"class": "btn-primary"}}

RETURN FORMAT:
Returns element information including:
- CSS selectors (id, class, xpath)
- Element type and attributes
- Text content and visibility
- Suggested interaction methods

COMMON PARAMETERS:
- visible_only: Only return visible elements (default: true)
- limit: Maximum number of elements to return (default: 20)

INTEGRATION:
Use the returned element selectors with:
- unified_browser: Click or interact with discovered elements
- click_tool: Click on discovered elements using coordinates
- text_input_tool: Type in discovered input fields

⚠️  IMPORTANT: Requires active browser session. Use unified_browser to open browser first."""

    def _get_simple_description(self) -> str:
        """Get simplified description with only find_by_text action."""
        return """Discover and analyze interactive elements on web pages for automation.

🎯 WHEN TO USE THIS TOOL:
- Finding elements by their visible text content
- Locating buttons, links, or labels with specific text
- Searching for interactive elements containing keywords

✅ KEY BENEFITS:
- Text-based element discovery
- Returns detailed element information including selectors
- Works with visible text content
- Perfect for finding elements by their display text

❌ DON'T USE FOR:
- Actually clicking or interacting with elements (use unified_browser or click_tool)

OPERATIONS & SYNTAX:

• find_by_text <text_contains> - Find elements containing specific text
  Usage: {"action": "find_by_text", "text_contains": "Sign Up"}
  Usage: {"action": "find_by_text", "text_contains": "login"}
  Usage: {"action": "find_by_text", "text_contains": "Submit"}

• find_by_type <element_type> - Find elements by specific type
  Usage: {"action": "find_by_type", "element_type": "button"}
  Usage: {"action": "find_by_type", "element_type": "input"}
  Usage: {"action": "find_by_type", "element_type": "link"}
  Usage: {"action": "find_by_type", "element_type": "form"}
  ⚠️  IMPORTANT: Supports button, input, link, form, field, text, checkbox, radio, select
RETURN FORMAT:
Returns element information including:
- CSS selectors (id, class, xpath)
- Element type and attributes
- Text content and visibility
- Suggested interaction methods

COMMON PARAMETERS:
- visible_only: Only return visible elements (default: true)
- limit: Maximum number of elements to return (default: 20)

INTEGRATION:
Use the returned element selectors with:
- unified_browser: Click or interact with discovered elements
- click_tool: Click on discovered elements using coordinates
- text_input_tool: Type in discovered input fields

⚠️  IMPORTANT: Requires active browser session. Use unified_browser to open browser first."""

    async def execute(self, query: str, **kwargs) -> ToolResult:
        """
        Execute element discovery operations.
        
        Available actions (specify in 'action' parameter):
        - find_all_elements: Find all interactive elements on the page
        - find_by_type: Find elements by specific type (button, input, link, etc.)
        - find_by_text: Find elements containing specific text
        - find_form_elements: Find all form-related elements
        - analyze_element: Get detailed information about a specific element
        - find_by_attributes: Find elements by specific attributes
        
        Args:
            query: Description of elements to find (optional, used for context)
            **kwargs: Action-specific parameters:
                - action: Required - the specific action to perform
                - element_type: for find_by_type - type of element to find
                - text_contains: for find_by_text - text that elements should contain
                - attribute_filter: for find_by_attributes - dict of attributes to filter by
                - element_selector: for analyze_element - selector of element to analyze
                - visible_only: only return visible elements (default: True)
                - limit: maximum number of elements to return (default: 20)
        
        Examples:
            {"action": "find_all_elements", "limit": 10}
            {"action": "find_by_type", "element_type": "button"}
            {"action": "find_by_text", "text_contains": "login"}
            {"action": "find_form_elements"}
            {"action": "analyze_element", "element_selector": "#username"}
            {"action": "find_by_attributes", "attribute_filter": {"placeholder": "email"}}
        """
        # DEBUG: Log what we actually received
        logger = logging.getLogger(__name__)
        logger.info(f"ElementDiscoveryTool.execute() called with:")
        logger.info(f"  query: '{query}'")
        logger.info(f"  kwargs: {kwargs}")
        logger.info(f"  kwargs type: {type(kwargs)}")
        logger.info(f"  kwargs keys: {list(kwargs.keys()) if kwargs else 'No keys'}")
        
        # Handle case where parameters are passed as JSON string in query
        if not kwargs and query.strip().startswith('{') and query.strip().endswith('}'):
            try:
                import json
                parsed_params = json.loads(query)
                if isinstance(parsed_params, dict):
                    kwargs = parsed_params
                    query = kwargs.pop('query', '')  # Extract query if present
                    logger.info(f"🔧 Parsed JSON from query parameter:")
                    logger.info(f"  new query: '{query}'")
                    logger.info(f"  new kwargs: {kwargs}")
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse query as JSON: {e}")
        
        try:
            # CRITICAL: Ensure browser focus before element discovery
            browser_type = kwargs.get('browser_type', 'chrome')# Default to chrome for selenium
            logging.info(f"Ensuring focus on {browser_type} browser before element discovery.")
            focus_success = window_manager.ensure_browser_focus(browser_type)
            if not focus_success:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Failed to focus {browser_type} browser before element discovery. Please ensure browser is open."
                )
            
            # Get or create WebDriver connection
            if not self._ensure_driver():
                return ToolResult(
                    success=False,
                    data=None,
                    error="No active browser session found. Please open a browser first using unified_browser tool."
                )
            
            action = kwargs.get('action', 'find_all_elements')
            logging.info(f"Executing element discovery action: {action} with parameters: {kwargs}")
            if action == 'find_all_elements':
                result = await self._find_all_elements(query, kwargs)
            elif action == 'find_by_type':
                result = await self._find_elements_by_type(query, kwargs)
            elif action == 'find_by_text':
                result = await self._find_elements_by_text(query, kwargs)
            elif action == 'find_form_elements':
                result = await self._find_form_elements(query, kwargs)
            elif action == 'analyze_element':
                result = await self._analyze_element(query, kwargs)
            elif action == 'find_by_attributes':
                result = await self._find_elements_by_attributes(query, kwargs)
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unknown action: {action}. Available actions: find_all_elements, find_by_type, find_by_text, find_form_elements, analyze_element, find_by_attributes"
                )
            
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Element discovery failed: {str(e)}"
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
    

    
    async def _find_all_elements(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Find all interactive elements on the page."""
        try:
            visible_only = kwargs.get('visible_only', True)
            limit = kwargs.get('limit', 20)
            
            # Define interactive element selectors
            interactive_selectors = [
                'button',
                'input',
                'textarea',
                'select',
                'a[href]',
                '[onclick]',
                '[role="button"]',
                '[tabindex]',
                'form'
            ]
            
            all_elements = []
            
            for selector in interactive_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if visible_only and not element.is_displayed():
                            continue
                        
                        element_info = self._extract_element_info(element)
                        if element_info:
                            all_elements.append(element_info)
                            
                        if len(all_elements) >= limit:
                            break
                            
                except Exception:
                    continue
                
                if len(all_elements) >= limit:
                    break
            
            return ToolResult(
                success=True,
                data={
                    "elements": all_elements[:limit],
                    "total_found": len(all_elements),
                    "page_url": self.driver.current_url,
                    "page_title": self.driver.title
                },
                metadata={
                    "action": "find_all_elements",
                    "query": query
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to find elements: {str(e)}"
            )
    
    async def _find_elements_by_type(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Find elements by specific type."""
        try:
            element_type = kwargs.get('element_type', None)
            if not element_type:
                element_type = self._extract_element_type_from_query(query)
            
            visible_only = kwargs.get('visible_only', True)
            limit = kwargs.get('limit', 20)
            
            # Map element types to selectors
            type_selectors = {
                'button': ['button', '[type="button"]', '[role="button"]', 'input[type="submit"]'],
                'input': ['input', 'textarea'],
                'link': ['a[href]'],
                'form': ['form'],
                'field': ['input', 'textarea', 'select'],
                'text': ['input[type="text"]', 'input[type="email"]', 'input[type="password"]', 'textarea'],
                'checkbox': ['input[type="checkbox"]'],
                'radio': ['input[type="radio"]'],
                'select': ['select'],
                'image': ['img'],
                'div': ['div'],
                'span': ['span']
            }
            
            selectors = type_selectors.get(element_type, [element_type])
            elements = []
            
            for selector in selectors:
                try:
                    found_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in found_elements:
                        if visible_only and not element.is_displayed():
                            continue
                        
                        element_info = self._extract_element_info(element)
                        if element_info:
                            elements.append(element_info)
                            
                        if len(elements) >= limit:
                            break
                            
                except Exception:
                    continue
                
                if len(elements) >= limit:
                    break
            
            return ToolResult(
                success=True,
                data={
                    "elements": elements[:limit],
                    "element_type": element_type,
                    "total_found": len(elements),
                    "page_url": self.driver.current_url
                },
                metadata={
                    "action": "find_by_type",
                    "query": query
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to find elements by type: {str(e)}"
            )
    
    async def _find_elements_by_text(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Find elements containing specific text."""
        logger = logging.getLogger(__name__)
        logger.info(f"Starting _find_elements_by_text with query: '{query}', kwargs: {kwargs}")
        
        try:
            text_contains = kwargs.get('text_contains', None)
            if not text_contains:
                text_contains = self._extract_text_from_query(query)
            
            logger.info(f"Extracted text to search for: '{text_contains}'")
            
            if not text_contains:
                logger.warning("No text specified to search for")
                return ToolResult(
                    success=False,
                    data=None,
                    error="No text specified to search for"
                )
            
            visible_only = kwargs.get('visible_only', True)
            limit = kwargs.get('limit', 20)
            
            logger.info(f"Search parameters - visible_only: {visible_only}, limit: {limit}")
            
            # Search strategies
            search_xpaths = [
                f'//*[contains(text(), "{text_contains}")]',
                f'//*[contains(@placeholder, "{text_contains}")]',
                f'//*[contains(@aria-label, "{text_contains}")]',
                f'//*[contains(@title, "{text_contains}")]',
                f'//*[contains(@value, "{text_contains}")]',
                f'//button[contains(text(), "{text_contains}")]',
                f'//a[contains(text(), "{text_contains}")]',
                f'//input[contains(@placeholder, "{text_contains}")]'
            ]
            
            logger.info(f"Using {len(search_xpaths)} search strategies:")
            for i, xpath in enumerate(search_xpaths, 1):
                logger.info(f"  {i}. {xpath}")
            
            elements = []
            found_element_ids = set()  # Avoid duplicates
            
            for i, xpath in enumerate(search_xpaths, 1):
                logger.info(f"Executing search strategy {i}/{len(search_xpaths)}: {xpath}")
                try:
                    found_elements = self.driver.find_elements(By.XPATH, xpath)
                    logger.info(f"  Found {len(found_elements)} raw elements with this XPath")
                    
                    processed_count = 0
                    skipped_invisible = 0
                    skipped_duplicate = 0
                    
                    for element in found_elements:
                        if visible_only and not element.is_displayed():
                            skipped_invisible += 1
                            continue
                        
                        # Create unique identifier to avoid duplicates
                        element_id = f"{element.tag_name}_{element.location}_{element.size}"
                        if element_id in found_element_ids:
                            skipped_duplicate += 1
                            continue
                        found_element_ids.add(element_id)
                        
                        element_info = self._extract_element_info(element)
                        if element_info:
                            elements.append(element_info)
                            processed_count += 1
                            logger.debug(f"    Added element: {element_info.get('tag_name', 'unknown')} - {element_info.get('text', '')[:50]}...")
                            
                        if len(elements) >= limit:
                            logger.info(f"  Reached limit of {limit} elements, stopping search")
                            break
                    
                    logger.info(f"  Strategy {i} results: {processed_count} processed, {skipped_invisible} skipped (invisible), {skipped_duplicate} skipped (duplicate)")
                            
                except Exception as e:
                    logger.warning(f"  Strategy {i} failed with error: {str(e)}")
                    continue
                
                if len(elements) >= limit:
                    logger.info(f"Reached overall limit of {limit} elements, stopping all searches")
                    break
            
            logger.info(f"Search completed. Total elements found: {len(elements)}")
            logger.info(f"Current page URL: {self.driver.current_url}")
            
            # Log summary of found elements
            if elements:
                logger.info("Summary of found elements:")
                for i, elem in enumerate(elements[:5], 1):  # Log first 5 elements
                    logger.info(f"  {i}. {elem.get('tag_name', 'unknown')} - Text: '{elem.get('text', '')[:30]}...' - ID: {elem.get('id', 'N/A')} - Class: {elem.get('class', 'N/A')}")
                if len(elements) > 5:
                    logger.info(f"  ... and {len(elements) - 5} more elements")
            else:
                logger.warning("No elements found matching the search criteria")
            
            return ToolResult(
                success=True,
                data={
                    "elements": elements[:limit],
                    "search_text": text_contains,
                    "total_found": len(elements),
                    "page_url": self.driver.current_url
                },
                metadata={
                    "action": "find_by_text",
                    "query": query
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to find elements by text: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to find elements by text: {str(e)}"
            )
    
    async def _find_form_elements(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Find all form-related elements."""
        try:
            visible_only = kwargs.get('visible_only', True)
            limit = kwargs.get('limit', 20)
            
            form_selectors = [
                'input',
                'textarea',
                'select',
                'button[type="submit"]',
                'input[type="submit"]',
                'form'
            ]
            
            elements = []
            
            for selector in form_selectors:
                try:
                    found_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in found_elements:
                        if visible_only and not element.is_displayed():
                            continue
                        
                        element_info = self._extract_element_info(element)
                        if element_info:
                            # Add form-specific information
                            if element.tag_name in ['input', 'textarea', 'select']:
                                element_info['is_form_field'] = True
                                element_info['required'] = element.get_attribute('required') is not None
                            elements.append(element_info)
                            
                        if len(elements) >= limit:
                            break
                            
                except Exception:
                    continue
                
                if len(elements) >= limit:
                    break
            
            return ToolResult(
                success=True,
                data={
                    "elements": elements[:limit],
                    "total_found": len(elements),
                    "page_url": self.driver.current_url
                },
                metadata={
                    "action": "find_form_elements",
                    "query": query
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to find form elements: {str(e)}"
            )
    
    async def _find_elements_by_attributes(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Find elements by specific attributes."""
        try:
            attribute_filter = kwargs.get('attribute_filter', {})
            if not attribute_filter:
                attribute_filter = self._extract_attributes_from_query(query)
            
            if not attribute_filter:
                return ToolResult(
                    success=False,
                    data=None,
                    error="No attributes specified to search for"
                )
            
            visible_only = kwargs.get('visible_only', True)
            limit = kwargs.get('limit', 20)
            
            elements = []
            
            for attr_name, attr_value in attribute_filter.items():
                try:
                    if attr_value:
                        # Search for specific attribute value
                        css_selector = f'[{attr_name}*="{attr_value}"]'
                    else:
                        # Search for attribute existence
                        css_selector = f'[{attr_name}]'
                    
                    found_elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
                    for element in found_elements:
                        if visible_only and not element.is_displayed():
                            continue
                        
                        element_info = self._extract_element_info(element)
                        if element_info:
                            elements.append(element_info)
                            
                        if len(elements) >= limit:
                            break
                            
                except Exception:
                    continue
                
                if len(elements) >= limit:
                    break
            
            return ToolResult(
                success=True,
                data={
                    "elements": elements[:limit],
                    "attribute_filter": attribute_filter,
                    "total_found": len(elements),
                    "page_url": self.driver.current_url
                },
                metadata={
                    "action": "find_by_attributes",
                    "query": query
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to find elements by attributes: {str(e)}"
            )
    
    async def _analyze_element(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Analyze a specific element in detail."""
        try:
            element_selector = kwargs.get('element_selector', None)
            if not element_selector:
                element_selector = self._extract_selector_from_query(query)
            
            if not element_selector:
                return ToolResult(
                    success=False,
                    data=None,
                    error="No element selector provided"
                )
            
            element = self._find_element_by_selector(element_selector)
            if not element:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Element not found: {element_selector}"
                )
            
            # Get detailed element information
            element_info = self._extract_detailed_element_info(element)
            
            return ToolResult(
                success=True,
                data={
                    "element": element_info,
                    "selector_used": element_selector,
                    "page_url": self.driver.current_url
                },
                metadata={
                    "action": "analyze_element",
                    "query": query
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to analyze element: {str(e)}"
            )
    
    def _extract_element_info(self, element) -> Optional[Dict[str, Any]]:
        """Extract basic information from a web element."""
        try:
            # Generate multiple selector options for the element
            selectors = self._generate_selectors_for_element(element)
            
            info = {
                "tag": element.tag_name,
                "text": element.text[:100] if element.text else "",
                "visible": element.is_displayed(),
                "enabled": element.is_enabled(),
                "selectors": selectors,
                "selector": selectors[0] if selectors else None,  # Primary selector for easy access
                "location": element.location,
                "size": element.size
            }
            
            # Get common attributes
            common_attrs = ['id', 'class', 'name', 'type', 'placeholder', 'value', 'href', 'title', 'aria-label']
            for attr in common_attrs:
                value = element.get_attribute(attr)
                if value:
                    info[attr] = value
            
            return info
            
        except Exception:
            return None
    
    def _extract_detailed_element_info(self, element) -> Dict[str, Any]:
        """Extract detailed information from a web element."""
        try:
            info = self._extract_element_info(element)
            
            # Add more detailed information
            info.update({
                "tag_name": element.tag_name,
                "is_selected": element.is_selected() if element.tag_name in ['input', 'option'] else None,
                "css_classes": element.get_attribute('class').split() if element.get_attribute('class') else [],
                "all_attributes": {}
            })
            
            # Get all attributes
            try:
                # Use JavaScript to get all attributes
                all_attrs = self.driver.execute_script(
                    "var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index) { items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value }; return items;",
                    element
                )
                info["all_attributes"] = all_attrs
            except Exception:
                pass
            
            return info
            
        except Exception as e:
            return {"error": str(e)}
    
    def _generate_selectors_for_element(self, element) -> List[str]:
        """Generate multiple selector options for an element."""
        selectors = []
        
        try:
            # ID selector (most reliable)
            element_id = element.get_attribute('id')
            if element_id:
                selectors.append(f"#{element_id}")
            
            # Name attribute
            name = element.get_attribute('name')
            if name:
                selectors.append(f"[name='{name}']")
            
            # Class selector
            class_name = element.get_attribute('class')
            if class_name:
                classes = class_name.strip().split()
                if classes:
                    selectors.append(f".{'.'.join(classes)}")
            
            # Tag with attributes
            tag = element.tag_name
            
            # Placeholder selector
            placeholder = element.get_attribute('placeholder')
            if placeholder:
                selectors.append(f"{tag}[placeholder='{placeholder}']")
            
            # Type selector for inputs
            input_type = element.get_attribute('type')
            if input_type:
                selectors.append(f"{tag}[type='{input_type}']")
            
            # Text content selector for buttons/links
            if element.text and len(element.text.strip()) > 0 and len(element.text.strip()) < 50:
                text = element.text.strip()
                if tag in ['button', 'a']:
                    selectors.append(f"{tag}:contains('{text}')")
            
            # CSS selector by tag
            selectors.append(tag)
            
        except Exception:
            pass
        
        return selectors[:5]  # Return top 5 selectors
    
    def _find_element_by_selector(self, selector: str):
        """Find element using various selector strategies."""
        try:
            strategies = [
                (By.ID, selector.replace('#', '')),
                (By.CSS_SELECTOR, selector),
                (By.NAME, selector),
                (By.CLASS_NAME, selector),
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
    
    def _extract_element_type_from_query(self, query: str) -> str:
        """Extract element type from query."""
        query_lower = query.lower()
        
        type_mappings = {
            'button': ['button', 'btn'],
            'input': ['input', 'field', 'textbox'],
            'link': ['link', 'hyperlink'],
            'form': ['form'],
            'text': ['text', 'text field'],
            'checkbox': ['checkbox', 'check'],
            'radio': ['radio', 'radio button'],
            'select': ['dropdown', 'select', 'combo'],
            'image': ['image', 'img'],
            'div': ['div'],
            'span': ['span']
        }
        
        for element_type, keywords in type_mappings.items():
            if any(keyword in query_lower for keyword in keywords):
                return element_type
        
        return 'input'  # Default
    
    def _extract_text_from_query(self, query: str) -> Optional[str]:
        """Extract text to search for from query."""
        import re
        
        patterns = [
            r'containing\s+["\']([^"\']+)["\']',
            r'with text\s+["\']([^"\']+)["\']',
            r'text\s+["\']([^"\']+)["\']',
            r'["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_attributes_from_query(self, query: str) -> Dict[str, str]:
        """Extract attribute filters from query."""
        import re
        
        attributes = {}
        
        # Look for placeholder
        placeholder_match = re.search(r'placeholder\s+["\']([^"\']+)["\']', query, re.IGNORECASE)
        if placeholder_match:
            attributes['placeholder'] = placeholder_match.group(1)
        
        # Look for other common attributes
        attr_patterns = {
            'id': r'id\s+["\']([^"\']+)["\']',
            'name': r'name\s+["\']([^"\']+)["\']',
            'class': r'class\s+["\']([^"\']+)["\']',
            'type': r'type\s+["\']([^"\']+)["\']'
        }
        
        for attr_name, pattern in attr_patterns.items():
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                attributes[attr_name] = match.group(1)
        
        return attributes
    
    def _extract_selector_from_query(self, query: str) -> Optional[str]:
        """Extract element selector from query."""
        import re
        
        patterns = [
            r'with id\s+["\']([^"\']+)["\']',
            r'id\s+["\']([^"\']+)["\']',
            r'selector\s+["\']([^"\']+)["\']',
            r'element\s+["\']([^"\']+)["\']',
            r'["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's input schema for LLM agents."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Optional description of what you're looking for"
                },
                "action": {
                    "type": "string",
                    "description": "The specific discovery action to perform",
                    "enum": [
                        "find_all_elements",
                        "find_by_type", 
                        "find_by_text",
                        "find_form_elements",
                        "find_by_attributes",
                        "analyze_element"
                    ]
                },
                "element_type": {
                    "type": "string",
                    "description": "Type of element to find (for find_by_type action)",
                    "enum": ["button", "input", "link", "form", "field", "text", "checkbox", "radio", "select", "image", "div", "span"]
                },
                "text_contains": {
                    "type": "string",
                    "description": "Text content to search for (for find_by_text action)"
                },
                "attribute_filter": {
                    "type": "object",
                    "description": "Attributes to filter by (for find_by_attributes action)",
                    "additionalProperties": {"type": "string"}
                },
                "element_selector": {
                    "type": "string",
                    "description": "CSS selector for specific element (for analyze_element action)"
                },
                "visible_only": {
                    "type": "boolean",
                    "description": "Whether to only return visible elements",
                    "default": True
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of elements to return",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100
                }
            },
            "required": ["action"],
            "additionalProperties": False
        }