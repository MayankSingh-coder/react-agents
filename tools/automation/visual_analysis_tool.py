"""Visual analysis tool using Gemini Vision API for screenshot analysis."""

import base64
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import google.generativeai as genai
from PIL import Image
import pyautogui
from ..base_tool import BaseTool, ToolResult
from .window_manager import window_manager


class VisualAnalysisTool(BaseTool):
    """Tool for analyzing screenshots and images using Gemini Vision API."""
    
    def __init__(self):
        super().__init__(
            name="visual_analysis",
            description=self._get_simple_description()
        )
        
        # Configure Gemini API
        from config import Config
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Create screenshots directory if it doesn't exist
        self.screenshots_dir = "/Users/mayank/Desktop/concepts/react-agents/screenshots"
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # Disable pyautogui failsafe for automation
        pyautogui.FAILSAFE = False
        
        # Analysis templates for different use cases
        self.analysis_prompts = {
            'general': """
            Analyze this screenshot and provide:
            1. What type of page/application this is
            2. Main UI elements visible (buttons, forms, links, etc.)
            3. Clickable elements and their approximate locations
            4. Any text input fields
            5. Suggested next actions a user might take
            
            Format your response as JSON with these keys:
            - page_type: string
            - ui_elements: list of objects with {type, text, location_description}
            - clickable_elements: list of objects with {text, type, location_description, action_suggestion}
            - input_fields: list of objects with {type, placeholder, location_description}
            - suggested_actions: list of strings
            """,
            
            'login_signup': """
            Analyze this screenshot for login/signup elements:
            1. Identify login or signup forms
            2. Find username/email and password fields
            3. Locate login/signup buttons
            4. Find any "Create Account", "Sign Up", or "Register" links
            5. Identify social login options (Google, Facebook, etc.)
            
            Format response as JSON with:
            - form_type: "login" or "signup" or "both" or "none"
            - username_field: {type, placeholder, location_description}
            - password_field: {type, placeholder, location_description}
            - submit_button: {text, location_description}
            - signup_link: {text, location_description} if found
            - social_logins: list of {provider, location_description}
            """,
            
            'ecommerce': """
            Analyze this e-commerce page screenshot:
            1. Identify product listings, search bars, categories
            2. Find add to cart buttons, buy now buttons
            3. Locate user account/login areas
            4. Identify navigation menus and filters
            5. Find shopping cart icon
            
            Format response as JSON with:
            - page_section: string (homepage, product_list, product_detail, cart, etc.)
            - search_elements: {search_bar, search_button, location_description}
            - products: list of {name, price, add_to_cart_button_location}
            - navigation: list of {text, type, location_description}
            - user_actions: list of {action, element_location}
            """,
            
            'form_filling': """
            Analyze this form screenshot:
            1. Identify all form fields and their types
            2. Find required vs optional fields
            3. Locate submit/save buttons
            4. Identify any validation messages or errors
            5. Find form sections or steps
            
            Format response as JSON with:
            - form_fields: list of {name, type, required, placeholder, location_description}
            - submit_buttons: list of {text, type, location_description}
            - validation_messages: list of {message, type, location_description}
            - form_progress: {current_step, total_steps} if applicable
            """
        }
    
    def _get_detailed_description(self) -> str:
        """Get detailed description with examples for visual analysis operations."""
        return """🔍 INTEGRATED SCREENSHOT + VISUAL ANALYSIS TOOL
Automatically takes fresh screenshots and analyzes them using Gemini Vision API to identify page state, UI elements, buttons, forms, and provide actionable insights.

🎯 WHEN TO USE THIS TOOL:
- Understanding current page state and available actions (takes fresh screenshot automatically)
- Identifying clickable elements and their locations
- Analyzing forms and input fields
- Extracting text content from images (OCR)
- Comparing screenshots to detect changes
- Finding specific elements by description
- Starting any automation workflow (e.g., "analyze Swiggy page to order food")

✅ KEY BENEFITS:
- ALWAYS uses fresh screenshots (no stale data)
- Automatically focuses correct browser/app before screenshot
- One-step process: screenshot + analysis combined
- Perfect for automation workflows

❌ DON'T USE FOR:
- Actually clicking or interacting with elements (use ClickTool/ElementInteractionTool)
- Modifying page content
- Real-time dynamic content analysis

OPERATIONS & SYNTAX:

• analyze_page - General page analysis and UI element identification
  Usage: {"action": "analyze_page", "analysis_type": "general"}
  Usage: {"action": "analyze_page", "analysis_type": "login_signup"}
  Usage: {"action": "analyze_page", "analysis_type": "ecommerce"}
  Usage: {"action": "analyze_page", "analysis_type": "form_filling"}
  ⚠️  IMPORTANT: Analysis types: general, login_signup, ecommerce, form_filling

• find_element - Locate specific element and get coordinates
  Usage: {"action": "find_element", "element_description": "login button"}
  Usage: {"action": "find_element", "element_description": "search bar"}
  Usage: {"action": "find_element", "element_description": "add to cart button"}
  Usage: {"action": "find_element", "element_description": "username field"}
  ⚠️  IMPORTANT: Returns approximate coordinates for use with click tools

• extract_text - OCR text extraction from image
  Usage: {"action": "extract_text", "region": "full"}
  Usage: {"action": "extract_text", "region": "top_half"}
  Usage: {"action": "extract_text", "focus": "error_messages"}
  Usage: {"action": "extract_text", "focus": "form_labels"}
  ⚠️  IMPORTANT: Regions: full, top_half, bottom_half, center, left_side, right_side

• compare_screenshots - Compare two screenshots to detect changes
  Usage: {"action": "compare_screenshots", "image1_path": "/path/to/before.png", "image2_path": "/path/to/after.png"}
  Usage: {"action": "compare_screenshots", "image1_path": "auto", "image2_path": "auto"}
  ⚠️  IMPORTANT: Use "auto" to compare with previous screenshot

• analyze_form - Specialized form analysis
  Usage: {"action": "analyze_form", "form_type": "login"}
  Usage: {"action": "analyze_form", "form_type": "signup"}
  Usage: {"action": "analyze_form", "form_type": "checkout"}
  Usage: {"action": "analyze_form", "form_type": "contact"}
  ⚠️  IMPORTANT: Returns detailed field information and validation states

• detect_state - Detect current page state and required actions
  Usage: {"action": "detect_state", "context": "navigation"}
  Usage: {"action": "detect_state", "context": "authentication"}
  Usage: {"action": "detect_state", "context": "checkout_flow"}
  Usage: {"action": "detect_state", "context": "error_handling"}
  ⚠️  IMPORTANT: Identifies what user needs to do next

• analyze_ecommerce - E-commerce specific analysis
  Usage: {"action": "analyze_ecommerce", "focus": "products"}
  Usage: {"action": "analyze_ecommerce", "focus": "cart"}
  Usage: {"action": "analyze_ecommerce", "focus": "checkout"}
  Usage: {"action": "analyze_ecommerce", "focus": "search_results"}
  ⚠️  IMPORTANT: Focus areas: products, cart, checkout, search_results, categories

ANALYSIS TYPES:
- general: Basic UI element identification and page structure
- login_signup: Authentication forms, social logins, registration
- ecommerce: Products, cart, checkout, search, categories
- form_filling: Form fields, validation, required fields

COMMON PARAMETERS:
- image_path: Path to specific image (takes fresh screenshot if not provided)
- custom_prompt: Override default analysis prompt
- return_coordinates: Include approximate element coordinates
- confidence_threshold: Minimum confidence for element detection (0.0-1.0)
- take_fresh_screenshot: Force new screenshot even if image_path provided (default: true)
- app_name: Focus specific application before screenshot (e.g., 'Safari', 'Chrome')
- browser_type: Focus specific browser before screenshot (e.g., 'safari', 'chrome')
- region: Screenshot specific region (x, y, width, height)

OUTPUT FORMAT:
Returns structured JSON with:
- page_type: Current page classification
- ui_elements: List of identified elements with locations
- clickable_elements: Buttons/links with action suggestions
- input_fields: Form fields with types and placeholders
- text_content: Extracted text and OCR results
- coordinates: Element positions for automation tools
- suggested_actions: Recommended next steps
- confidence_scores: Reliability of analysis results

LIMITATIONS:
- Analysis only (cannot interact with elements)
- Coordinate extraction is approximate, not pixel-perfect
- Cannot handle dynamic content or JavaScript interactions
- Requires clear, high-quality screenshots for best results
- OCR accuracy depends on image quality and text clarity

WORKFLOW INTEGRATION:
Perfect starting point for automation workflows:
1. Use visual_analysis to automatically screenshot and understand current page state
2. Extract element locations and required actions from analysis
3. Use click/text_input tools to interact with identified elements
4. Repeat cycle for multi-step processes

✅ AUTOMATIC FRESH SCREENSHOTS: This tool automatically takes fresh screenshots, ensuring you always analyze current page state."""

    def _get_simple_description(self) -> str:
        """Get simplified description with only analyze_page action."""
        return """🔍 INTEGRATED SCREENSHOT + VISUAL ANALYSIS TOOL
Automatically takes fresh screenshots and analyzes them using Gemini Vision API to identify page state, UI elements, buttons, forms, and provide actionable insights.

🎯 WHEN TO USE THIS TOOL:
- Understanding current page state and available actions (takes fresh screenshot automatically)
- Identifying clickable elements and their locations
- Analyzing forms and input fields
- Starting any automation workflow (e.g., "analyze Swiggy page to order food")

✅ KEY BENEFITS:
- ALWAYS uses fresh screenshots (no stale data)
- Automatically focuses correct browser/app before screenshot
- One-step process: screenshot + analysis combined
- Perfect for automation workflows

❌ DON'T USE FOR:
- Actually clicking or interacting with elements (use ClickTool/ElementInteractionTool)
- Modifying page content
- Real-time dynamic content analysis

OPERATIONS & SYNTAX:

• analyze_page - General page analysis and UI element identification
  Usage: {"action": "analyze_page", "analysis_type": "general"}
  ⚠️  IMPORTANT: Analysis types: general

ANALYSIS TYPES:
- general: Basic UI element identification and page structure

OUTPUT FORMAT:
Returns structured JSON with:
- page_type: Current page classification
- ui_elements: List of identified elements with locations
- clickable_elements: Buttons/links with action suggestions
- input_fields: Form fields with types and placeholders
- suggested_actions: Recommended next steps

✅ AUTOMATIC FRESH SCREENSHOTS: This tool automatically takes fresh screenshots, ensuring you always analyze current page state."""

    async def execute(self, query: str, **kwargs) -> ToolResult:
        """
        Perform visual analysis based on structured action.
        
        Args:
            query: JSON string or description of analysis to perform
            **kwargs: Additional parameters:
                - action: specific action to perform (analyze_page, find_element, extract_text, etc.)
                - image_path: path to image file
                - analysis_type: type of analysis (general, login_signup, ecommerce, form_filling)
                - element_description: description of element to find
                - region: region for text extraction
                - focus: focus area for analysis
                - form_type: type of form to analyze
                - context: context for state detection
                - custom_prompt: custom analysis prompt
                - return_coordinates: whether to try to extract coordinates
                - confidence_threshold: minimum confidence for detection
        """
        try:
            # Handle case where parameters are passed as JSON string in query (for LLM agents)
            if not kwargs and query.strip().startswith('{') and query.strip().endswith('}'):
                try:
                    import json
                    parsed_params = json.loads(query)
                    if isinstance(parsed_params, dict):
                        kwargs = parsed_params
                        query = kwargs.pop('query', '')  # Extract query if present
                        print(f"🔧 VisualAnalysisTool: Parsed JSON from query parameter")
                        print(f"  new query: '{query}'")
                        print(f"  new kwargs: {kwargs}")
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Failed to parse query as JSON: {e}")
            
          # Parse action from kwargs or query
            action = kwargs.get('action')
            if not action:
                  # Fallback to legacy parsing for backward compatibility
                action = 'analyze_page'
            
            # Get image path - prioritize fresh screenshots
            image_path = kwargs.get('image_path', None)
            take_fresh_screenshot = kwargs.get('take_fresh_screenshot', True)  # Default to fresh screenshot
            
            # Take fresh screenshot unless explicitly disabled and image_path provided
            if take_fresh_screenshot or not image_path:
                fresh_screenshot_path = await self._take_fresh_screenshot(query=query, **kwargs)
                if fresh_screenshot_path:
                    image_path = fresh_screenshot_path
                elif not image_path:
                    # Fallback to latest screenshot if fresh screenshot fails
                    image_path = self._get_latest_screenshot()
            
            if not image_path or not os.path.exists(image_path):
                return ToolResult(
                    success=False,
                    data=None,
                    error="No image file found. Failed to take screenshot and no existing screenshots available."
                )
            
            # Route to appropriate action handler
            if action == 'analyze_page':
                result = await self._analyze_page(query, kwargs, image_path)
            elif action == 'find_element':
                result = await self._find_element(query, kwargs, image_path)
            elif action == 'extract_text':
                result = await self._extract_text(query, kwargs, image_path)
            elif action == 'compare_screenshots':
                result = await self._compare_screenshots(query, kwargs)
            elif action == 'analyze_form':
                result = await self._analyze_form(query, kwargs, image_path)
            elif action == 'detect_state':
                result = await self._detect_state(query, kwargs, image_path)
            elif action == 'analyze_ecommerce':
                result = await self._analyze_ecommerce(query, kwargs, image_path)
            else:
                # Fallback to legacy method for backward compatibility
                analysis_type = kwargs.get('analysis_type', None)
                if not analysis_type:
                    analysis_type = self._determine_analysis_type(query)
                
                custom_prompt = kwargs.get('custom_prompt', None)
                if custom_prompt:
                    prompt = custom_prompt
                else:
                    prompt = self.analysis_prompts.get(analysis_type, self.analysis_prompts['general'])
                
                result = await self._analyze_image(image_path, prompt, query)
            
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Visual analysis failed: {str(e)}"
            )
    
    async def _analyze_image(self, image_path: str, prompt: str, original_query: str) -> ToolResult:
        """Analyze image using Gemini Vision API."""
        try:
            # Load and prepare image
            image = Image.open(image_path)
            
            # Add context to prompt
            full_prompt = f"""
            User Query: {original_query}
            
            {prompt}
            
            Please be specific about locations (top-left, center, bottom-right, etc.) and provide actionable information.
            If you can identify specific coordinates or regions, include them.
            """
            
            # Generate analysis
            response = self.model.generate_content([full_prompt, image])
            
            # Parse response
            analysis_text = response.text
            
            # Try to extract JSON if present
            analysis_data = self._parse_analysis_response(analysis_text)
            
            # Get image metadata
            image_info = {
                "width": image.width,
                "height": image.height,
                "format": image.format,
                "mode": image.mode,
                "file_size": os.path.getsize(image_path)
            }
            
            return ToolResult(
                success=True,
                data={
                    "analysis": analysis_data,
                    "raw_response": analysis_text,
                    "image_info": image_info,
                    "image_path": image_path
                },
                metadata={
                    "query": original_query,
                    "analysis_type": self._determine_analysis_type(original_query),
                    "model": "gemini-2.0-flash-lite"
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to analyze image: {str(e)}"
            )
    
    def _determine_analysis_type(self, query: str) -> str:
        """Determine the type of analysis based on query."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['login', 'signup', 'sign up', 'register', 'authentication']):
            return 'login_signup'
        elif any(word in query_lower for word in ['shop', 'buy', 'cart', 'product', 'ecommerce', 'swiggy', 'zomato', 'amazon']):
            return 'ecommerce'
        elif any(word in query_lower for word in ['form', 'fill', 'input', 'field', 'submit']):
            return 'form_filling'
        else:
            return 'general'
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the analysis response, extracting JSON if present."""
        import json
        import re
        
        try:
            # Try to find JSON in the response
            json_pattern = r'```json\s*(.*?)\s*```'
            json_match = re.search(json_pattern, response_text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            
            # Try to find JSON without code blocks
            json_pattern2 = r'\{.*\}'
            json_match2 = re.search(json_pattern2, response_text, re.DOTALL)
            
            if json_match2:
                json_str = json_match2.group(0)
                return json.loads(json_str)
            
            # If no JSON found, structure the text response
            return {
                "analysis_text": response_text,
                "structured_data": self._extract_structured_info(response_text)
            }
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return structured text analysis
            return {
                "analysis_text": response_text,
                "structured_data": self._extract_structured_info(response_text)
            }
    
    def _extract_structured_info(self, text: str) -> Dict[str, Any]:
        """Extract structured information from text response."""
        structured = {
            "ui_elements": [],
            "clickable_elements": [],
            "suggestions": []
        }
        
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Identify sections
            if 'ui elements' in line.lower() or 'elements' in line.lower():
                current_section = 'ui_elements'
            elif 'clickable' in line.lower() or 'buttons' in line.lower():
                current_section = 'clickable_elements'
            elif 'suggest' in line.lower() or 'action' in line.lower():
                current_section = 'suggestions'
            elif line.startswith('-') or line.startswith('*') or line.startswith('•'):
                # This is a list item
                item = line[1:].strip()
                if current_section and item:
                    structured[current_section].append(item)
        
        return structured
    
    def _get_latest_screenshot(self) -> Optional[str]:
        """Get the path to the most recent screenshot."""
        if not os.path.exists(self.screenshots_dir):
            return None
        
        try:
            screenshots = [f for f in os.listdir(self.screenshots_dir) if f.endswith('.png')]
            if not screenshots:
                return None
            
            # Sort by modification time
            screenshots.sort(key=lambda x: os.path.getmtime(os.path.join(self.screenshots_dir, x)), reverse=True)
            return os.path.join(self.screenshots_dir, screenshots[0])
        except Exception:
            return None
    
    async def _take_fresh_screenshot(self, **kwargs) -> Optional[str]:
        """Take a fresh screenshot with optional app/browser focusing."""
        try:
            # Extract screenshot parameters
            app_name = kwargs.get('app_name', None)
            browser_type = kwargs.get('browser_type', None)
            region = kwargs.get('region', None)
            
            # Detect application from query if not explicitly provided
            if not app_name and not browser_type:
                query = kwargs.get('query', '')
                query_lower = query.lower()
                
                # Check for browser mentions
                if 'safari' in query_lower:
                    browser_type = 'safari'
                elif 'chrome' in query_lower and 'chromium' not in query_lower:
                    browser_type = 'chrome'
                elif 'chromium' in query_lower:
                    browser_type = 'chromium'
                elif 'firefox' in query_lower:
                    browser_type = 'firefox'
                elif 'edge' in query_lower:
                    browser_type = 'edge'
                # Check for other common applications
                elif 'finder' in query_lower:
                    app_name = 'Finder'
                elif 'terminal' in query_lower:
                    app_name = 'Terminal'
                elif any(word in query_lower for word in ['swiggy', 'zomato', 'amazon', 'flipkart', 'shop', 'order']):
                    # For e-commerce sites, default to Safari if no browser specified
                    browser_type = 'safari'
            
            # Focus the correct application before taking screenshot
            focus_success = True
            if browser_type:
                focus_success = window_manager.ensure_browser_focus(browser_type)
                if not focus_success:
                    print(f"Warning: Failed to focus {browser_type} browser before screenshot")
            elif app_name:
                focus_success = window_manager.ensure_app_focus(app_name)
                if not focus_success:
                    print(f"Warning: Failed to focus {app_name} before screenshot")
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if browser_type:
                filename = f"visual_analysis_{browser_type}_{timestamp}.png"
            elif app_name:
                filename = f"visual_analysis_{app_name.lower().replace(' ', '_')}_{timestamp}.png"
            else:
                filename = f"visual_analysis_{timestamp}.png"
            
            filepath = os.path.join(self.screenshots_dir, filename)
            
            # Take screenshot
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            # Save screenshot
            screenshot.save(filepath)
            
            return filepath
            
        except Exception as e:
            print(f"Error taking fresh screenshot: {e}")
            return None
    
    async def analyze_for_coordinates(self, image_path: str, element_description: str) -> ToolResult:
        """Analyze image to find coordinates of specific elements."""
        try:
            image = Image.open(image_path)
            
            prompt = f"""
            Look at this screenshot and find the element described as: "{element_description}"
            
            Provide the approximate coordinates or region where this element is located.
            Consider the image dimensions are {image.width}x{image.height}.
            
            Return your response as JSON with:
            - found: boolean (whether element was found)
            - element_description: string (what you found)
            - approximate_coordinates: object with x, y (center point)
            - region: object with x, y, width, height (bounding box if possible)
            - confidence: number (0-1, how confident you are)
            - instructions: string (how to interact with this element)
            """
            
            response = self.model.generate_content([prompt, image])
            analysis_data = self._parse_analysis_response(response.text)
            
            return ToolResult(
                success=True,
                data=analysis_data,
                metadata={
                    "element_description": element_description,
                    "image_path": image_path
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to analyze for coordinates: {str(e)}"
            )
    
    async def compare_screenshots(self, image1_path: str, image2_path: str) -> ToolResult:
        """Compare two screenshots to identify changes."""
        try:
            image1 = Image.open(image1_path)
            image2 = Image.open(image2_path)
            
            prompt = """
            Compare these two screenshots and identify:
            1. What has changed between them
            2. New elements that appeared
            3. Elements that disappeared
            4. Any state changes (loading, errors, success messages)
            5. Navigation or page changes
            
            Format as JSON with:
            - changes_detected: boolean
            - change_summary: string
            - new_elements: list of strings
            - removed_elements: list of strings
            - state_changes: list of strings
            - suggested_next_action: string
            """
            
            response = self.model.generate_content([prompt, image1, image2])
            analysis_data = self._parse_analysis_response(response.text)
            
            return ToolResult(
                success=True,
                data=analysis_data,
                metadata={
                    "image1_path": image1_path,
                    "image2_path": image2_path
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to compare screenshots: {str(e)}"
            )
    
    async def _analyze_page(self, query: str, kwargs: Dict[str, Any], image_path: str) -> ToolResult:
        """Perform general page analysis."""
        try:
            analysis_type = kwargs.get('analysis_type', 'general')
            custom_prompt = kwargs.get('custom_prompt', None)
            
            if custom_prompt:
                prompt = custom_prompt
            else:
                prompt = self.analysis_prompts.get(analysis_type, self.analysis_prompts['general'])
            
            return await self._analyze_image(image_path, prompt, query)
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to analyze page: {str(e)}"
            )
    
    async def _find_element(self, query: str, kwargs: Dict[str, Any], image_path: str) -> ToolResult:
        """Find specific element and return coordinates."""
        try:
            element_description = kwargs.get('element_description', '')
            if not element_description:
                # Extract from query
                element_description = query.replace('find', '').replace('locate', '').strip()
            
            return await self.analyze_for_coordinates(image_path, element_description)
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to find element: {str(e)}"
            )
    
    async def _extract_text(self, query: str, kwargs: Dict[str, Any], image_path: str) -> ToolResult:
        """Extract text content from image (OCR)."""
        try:
            image = Image.open(image_path)
            region = kwargs.get('region', 'full')
            focus = kwargs.get('focus', 'all_text')
            
            prompt = f"""
            Extract all readable text from this screenshot. Focus on: {focus}
            
            Region to analyze: {region}
            
            Provide the extracted text in a structured format as JSON with:
            - extracted_text: string (all text found)
            - text_elements: list of objects with {{text, location_description, type}}
            - headings: list of heading texts
            - buttons: list of button texts
            - links: list of link texts
            - form_labels: list of form field labels
            - error_messages: list of error/warning messages
            - confidence: number (0-1, OCR confidence)
            
            Be thorough and include all visible text, maintaining structure and hierarchy.
            """
            
            response = self.model.generate_content([prompt, image])
            analysis_data = self._parse_analysis_response(response.text)
            
            return ToolResult(
                success=True,
                data=analysis_data,
                metadata={
                    "query": query,
                    "action": "extract_text",
                    "region": region,
                    "focus": focus,
                    "image_path": image_path
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to extract text: {str(e)}"
            )
    
    async def _compare_screenshots(self, query: str, kwargs: Dict[str, Any]) -> ToolResult:
        """Compare two screenshots to detect changes."""
        try:
            image1_path = kwargs.get('image1_path', 'auto')
            image2_path = kwargs.get('image2_path', 'auto')
            
            # Handle auto paths
            if image1_path == 'auto' or image2_path == 'auto':
                screenshots_dir = "/Users/mayank/Desktop/concepts/react-agents/screenshots"
                if os.path.exists(screenshots_dir):
                    screenshots = [f for f in os.listdir(screenshots_dir) if f.endswith('.png')]
                    screenshots.sort(key=lambda x: os.path.getmtime(os.path.join(screenshots_dir, x)), reverse=True)
                    
                    if len(screenshots) >= 2:
                        if image2_path == 'auto':
                            image2_path = os.path.join(screenshots_dir, screenshots[0])  # Latest
                        if image1_path == 'auto':
                            image1_path = os.path.join(screenshots_dir, screenshots[1])  # Previous
                    else:
                        return ToolResult(
                            success=False,
                            data=None,
                            error="Need at least 2 screenshots for comparison"
                        )
            
            return await self.compare_screenshots(image1_path, image2_path)
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to compare screenshots: {str(e)}"
            )
    
    async def _analyze_form(self, query: str, kwargs: Dict[str, Any], image_path: str) -> ToolResult:
        """Analyze form elements in detail."""
        try:
            image = Image.open(image_path)
            form_type = kwargs.get('form_type', 'general')
            
            prompt = f"""
            Analyze this {form_type} form in detail. Identify:
            
            1. All form fields with their types, labels, and placeholders
            2. Required vs optional fields (look for asterisks, "required" text)
            3. Field validation states (errors, warnings, success indicators)
            4. Submit/action buttons and their states (enabled/disabled)
            5. Form sections or steps if it's a multi-step form
            6. Any help text, tooltips, or instructions
            7. Auto-fill suggestions or dropdown options
            
            Return as JSON with:
            - form_type: string
            - form_fields: list of {{name, type, label, placeholder, required, validation_state, location_description}}
            - action_buttons: list of {{text, type, enabled, location_description}}
            - validation_messages: list of {{message, type, field, location_description}}
            - form_sections: list of {{title, fields, step_number}}
            - help_text: list of strings
            - completion_status: {{filled_fields, total_fields, completion_percentage}}
            - suggested_next_action: string
            """
            
            response = self.model.generate_content([prompt, image])
            analysis_data = self._parse_analysis_response(response.text)
            
            return ToolResult(
                success=True,
                data=analysis_data,
                metadata={
                    "query": query,
                    "action": "analyze_form",
                    "form_type": form_type,
                    "image_path": image_path
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to analyze form: {str(e)}"
            )
    
    async def _detect_state(self, query: str, kwargs: Dict[str, Any], image_path: str) -> ToolResult:
        """Detect current page state and required actions."""
        try:
            image = Image.open(image_path)
            context = kwargs.get('context', 'general')
            
            prompt = f"""
            Analyze this screenshot to detect the current page state in the context of: {context}
            
            Determine:
            1. What page/screen is currently displayed
            2. What state the application is in (loading, error, success, waiting for input)
            3. What actions are required from the user
            4. Any blocking elements (popups, modals, error messages)
            5. Progress indicators or step completions
            6. Authentication state (logged in/out, permissions)
            7. Data loading states (empty, loading, loaded, error)
            
            Return as JSON with:
            - current_page: string
            - page_state: string (loading, ready, error, success, waiting_input, blocked)
            - required_actions: list of strings
            - blocking_elements: list of {{type, message, action_needed}}
            - progress_indicators: {{current_step, total_steps, percentage}}
            - authentication_state: string (logged_in, logged_out, unknown)
            - data_state: string (empty, loading, loaded, error)
            - next_recommended_action: string
            - urgency_level: string (low, medium, high, critical)
            """
            
            response = self.model.generate_content([prompt, image])
            analysis_data = self._parse_analysis_response(response.text)
            
            return ToolResult(
                success=True,
                data=analysis_data,
                metadata={
                    "query": query,
                    "action": "detect_state",
                    "context": context,
                    "image_path": image_path
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to detect state: {str(e)}"
            )
    
    async def _analyze_ecommerce(self, query: str, kwargs: Dict[str, Any], image_path: str) -> ToolResult:
        """Analyze e-commerce specific elements."""
        try:
            image = Image.open(image_path)
            focus = kwargs.get('focus', 'general')
            
            if focus == 'products':
                prompt = """
                Analyze this e-commerce page focusing on products. Identify:
                1. Product listings with names, prices, ratings
                2. Product images and thumbnails
                3. Add to cart/buy buttons for each product
                4. Product filters and sorting options
                5. Pagination or load more options
                6. Product comparison features
                7. Wishlist/save for later options
                
                Return as JSON with:
                - products: list of {name, price, rating, image_location, add_to_cart_location, availability}
                - filters: list of {type, options, location_description}
                - sorting_options: list of strings
                - pagination: {current_page, total_pages, next_button_location}
                - view_options: list of strings (grid, list, etc.)
                """
            elif focus == 'cart':
                prompt = """
                Analyze this shopping cart page. Identify:
                1. Cart items with quantities, prices, and remove options
                2. Subtotal, taxes, shipping costs, and total
                3. Quantity adjustment controls
                4. Promo code/coupon fields
                5. Checkout button and its state
                6. Continue shopping options
                7. Save for later or wishlist options
                
                Return as JSON with:
                - cart_items: list of {name, quantity, price, remove_button_location, quantity_controls}
                - pricing: {subtotal, tax, shipping, total, currency}
                - promo_code: {field_location, apply_button_location}
                - checkout_button: {text, enabled, location_description}
                - cart_actions: list of {action, location_description}
                """
            elif focus == 'checkout':
                prompt = """
                Analyze this checkout page. Identify:
                1. Shipping address form fields
                2. Payment method options and forms
                3. Order summary with items and pricing
                4. Delivery options and dates
                5. Place order button and its state
                6. Security indicators and trust badges
                7. Terms and conditions checkboxes
                
                Return as JSON with:
                - shipping_form: list of {field_name, field_type, required, filled}
                - payment_methods: list of {type, selected, form_fields}
                - order_summary: {items, subtotal, tax, shipping, total}
                - delivery_options: list of {method, cost, estimated_date}
                - place_order_button: {text, enabled, location_description}
                - security_indicators: list of strings
                """
            else:
                prompt = self.analysis_prompts['ecommerce']
            
            response = self.model.generate_content([prompt, image])
            analysis_data = self._parse_analysis_response(response.text)
            
            return ToolResult(
                success=True,
                data=analysis_data,
                metadata={
                    "query": query,
                    "action": "analyze_ecommerce",
                    "focus": focus,
                    "image_path": image_path
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to analyze e-commerce elements: {str(e)}"
            )
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's input schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "JSON string or description of analysis to perform"
                },
                "action": {
                    "type": "string",
                    "enum": ["analyze_page", "find_element", "extract_text", "compare_screenshots", "analyze_form", "detect_state", "analyze_ecommerce"],
                    "description": "Optional: specific action to perform"
                },
                "image_path": {
                    "type": "string",
                    "description": "Optional: path to specific image file (takes fresh screenshot if not provided)"
                },
                "take_fresh_screenshot": {
                    "type": "boolean",
                    "description": "Optional: force new screenshot even if image_path provided (default: true)"
                },
                "app_name": {
                    "type": "string",
                    "description": "Optional: focus specific application before screenshot (e.g., 'Safari', 'Chrome')"
                },
                "browser_type": {
                    "type": "string",
                    "enum": ["safari", "chrome", "chromium", "firefox", "edge"],
                    "description": "Optional: focus specific browser before screenshot"
                },
                "analysis_type": {
                    "type": "string",
                    "enum": ["general", "login_signup", "ecommerce", "form_filling"],
                    "description": "Optional: type of analysis for analyze_page action"
                },
                "element_description": {
                    "type": "string",
                    "description": "Optional: description of element to find for find_element action"
                },
                "region": {
                    "type": "string",
                    "enum": ["full", "top_half", "bottom_half", "center", "left_side", "right_side"],
                    "description": "Optional: region for text extraction"
                },
                "focus": {
                    "type": "string",
                    "description": "Optional: focus area for analysis (e.g., 'products', 'cart', 'error_messages')"
                },
                "form_type": {
                    "type": "string",
                    "enum": ["login", "signup", "checkout", "contact", "general"],
                    "description": "Optional: type of form for analyze_form action"
                },
                "context": {
                    "type": "string",
                    "enum": ["navigation", "authentication", "checkout_flow", "error_handling", "general"],
                    "description": "Optional: context for state detection"
                },
                "image1_path": {
                    "type": "string",
                    "description": "Optional: first image path for comparison (use 'auto' for previous screenshot)"
                },
                "image2_path": {
                    "type": "string",
                    "description": "Optional: second image path for comparison (use 'auto' for latest screenshot)"
                },
                "custom_prompt": {
                    "type": "string",
                    "description": "Optional: custom analysis prompt"
                },
                "return_coordinates": {
                    "type": "boolean",
                    "description": "Optional: whether to try to extract element coordinates"
                },
                "confidence_threshold": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Optional: minimum confidence for element detection"
                }
            },
            "required": ["query"]
        }