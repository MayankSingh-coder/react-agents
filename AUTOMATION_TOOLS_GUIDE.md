# Automation Tools Guide

This guide covers the automation tools that enable your React Agent to interact with browsers, desktop applications, and perform visual analysis.

## 🛠️ Available Tools

### 1. **ScreenshotTool**
Captures screenshots for visual analysis.

**Capabilities:**
- Full screen screenshots
- Region-specific screenshots
- Automatic file management
- Screenshot metadata extraction

**Usage Examples:**
```python
screenshot_tool = ScreenshotTool()
result = await screenshot_tool.execute("take a full screen screenshot")
result = await screenshot_tool.execute("capture browser window", region=(0, 0, 1200, 800))
```

### 2. **AppLauncherTool**
Launches and manages macOS applications.

**Supported Apps:**
- Notes, TextEdit, Safari, Chrome, Chromium
- Calculator, Calendar, Mail, Music, Photos
- Terminal, Finder, System Preferences
- And many more...

**Usage Examples:**
```python
app_launcher = AppLauncherTool()
result = await app_launcher.execute("open notes")
result = await app_launcher.execute("launch safari")
```

### 3. **TextInputTool**
Types text and performs keyboard interactions.

**Capabilities:**
- Type text with realistic timing
- Execute keyboard shortcuts (copy, paste, save, etc.)
- Press special keys (Enter, Tab, Escape)
- Clear existing text before typing

**Usage Examples:**
```python
text_input = TextInputTool()
result = await text_input.execute("type 'Hello World!'")
result = await text_input.execute("press enter")
result = await text_input.execute("copy shortcut")
```

### 4. **ClickTool**
Performs mouse clicks and interactions.

**Capabilities:**
- Left, right, double, middle clicks
- Scroll operations
- Drag and drop
- Coordinate-based clicking

**Usage Examples:**
```python
click_tool = ClickTool()
result = await click_tool.execute("click at 100,200")
result = await click_tool.execute("right click at coordinates 300,400")
result = await click_tool.execute("scroll down at 500,300")
```

### 5. **BrowserAutomationTool**
Automates web browser interactions using Selenium.

**Capabilities:**
- Open/close browser instances
- Navigate to websites
- Find and interact with web elements
- Take browser screenshots
- Handle forms and buttons

**Usage Examples:**
```python
browser_tool = BrowserAutomationTool()
result = await browser_tool.execute("open browser")
result = await browser_tool.execute("go to swiggy")
result = await browser_tool.execute("click login button")
result = await browser_tool.execute("type username in email field")
```

### 6. **VisualAnalysisTool**
Analyzes screenshots using Gemini Vision API.

**Analysis Types:**
- **General**: Overall UI analysis
- **Login/Signup**: Authentication forms
- **E-commerce**: Shopping sites (Swiggy, Amazon, etc.)
- **Form Filling**: Form fields and validation

**Usage Examples:**
```python
visual_tool = VisualAnalysisTool()
result = await visual_tool.execute("analyze this screenshot for login elements")
result = await visual_tool.execute("find all clickable buttons", analysis_type="general")
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install selenium webdriver-manager pillow pyautogui pynput
```

### 2. Basic Usage
```python
import asyncio
from tools.automation.screenshot_tool import ScreenshotTool
from tools.automation.visual_analysis_tool import VisualAnalysisTool

async def basic_example():
    # Take a screenshot
    screenshot_tool = ScreenshotTool()
    screenshot_result = await screenshot_tool.execute("take screenshot")
    
    # Analyze it
    visual_tool = VisualAnalysisTool()
    analysis_result = await visual_tool.execute("analyze this screenshot")
    
    print(f"Screenshot: {screenshot_result.data['filepath']}")
    print(f"Analysis: {analysis_result.data['raw_response']}")

asyncio.run(basic_example())
```

### 3. Integration with React Agent
```python
from agent.react_agent import ReactAgent
from tools.automation import *

# Create agent with automation tools
agent = ReactAgent()

# Add automation tools
automation_tools = [
    ScreenshotTool(),
    AppLauncherTool(),
    BrowserAutomationTool(),
    VisualAnalysisTool()
]

for tool in automation_tools:
    agent.tool_manager.add_tool(tool.name, tool)

# Use the agent
result = await agent.run("Open Swiggy and take a screenshot")
```

## 🎯 Use Case Examples

### Swiggy Food Ordering
```python
async def order_food():
    browser_tool = BrowserAutomationTool()
    visual_tool = VisualAnalysisTool()
    
    # Open Swiggy
    await browser_tool.execute("open browser")
    await browser_tool.execute("go to swiggy")
    
    # Take screenshot and analyze
    screenshot_result = await browser_tool.execute("take screenshot")
    analysis = await visual_tool.execute(
        "analyze for food ordering elements",
        analysis_type="ecommerce"
    )
    
    # Based on analysis, interact with elements
    if "login" in analysis.data['raw_response'].lower():
        await browser_tool.execute("click login button")
```

### Write Poem in Notes
```python
async def write_poem():
    app_launcher = AppLauncherTool()
    text_input = TextInputTool()
    
    # Open Notes
    await app_launcher.execute("open notes")
    
    # Write poem
    poem = """
    Automation flows like a gentle stream,
    Making tasks easier than they seem.
    With code and logic, we build the way,
    For a more efficient, brighter day.
    """
    
    await text_input.execute(f"type '{poem}'")
```

### Visual UI Analysis
```python
async def analyze_ui():
    screenshot_tool = ScreenshotTool()
    visual_tool = VisualAnalysisTool()
    
    # Capture current screen
    screenshot = await screenshot_tool.execute("take screenshot")
    
    # Analyze for interactive elements
    analysis = await visual_tool.execute(
        "find all buttons, links, and input fields with their locations"
    )
    
    # Extract actionable information
    if analysis.success:
        elements = analysis.data.get('analysis', {})
        print(f"Found {len(elements.get('clickable_elements', []))} clickable elements")
```

## ⚙️ Configuration

### Browser Settings
```python
# Headless mode
browser_tool = BrowserAutomationTool()
await browser_tool.execute("open browser", headless=True)

# Custom browser path
# Modify browser_automation_tool.py to set custom Chrome/Chromium path
```

### Screenshot Settings
```python
# Custom screenshot directory
screenshot_tool = ScreenshotTool()
screenshot_tool.screenshots_dir = "/custom/path/screenshots"

# Region screenshot
await screenshot_tool.execute("take screenshot", region=(0, 0, 800, 600))
```

### Visual Analysis Prompts
```python
# Custom analysis prompt
visual_tool = VisualAnalysisTool()
custom_prompt = "Find all food items and their prices on this page"
await visual_tool.execute("analyze", custom_prompt=custom_prompt)
```

## 🔧 Troubleshooting

### Common Issues

1. **Browser not opening**
   - Install ChromeDriver: `webdriver-manager` handles this automatically
   - Check if Chrome/Chromium is installed
   - Try headless mode if GUI issues occur

2. **Screenshot permissions on macOS**
   - Grant screen recording permissions to Terminal/PyCharm
   - System Preferences → Security & Privacy → Privacy → Screen Recording

3. **Automation permissions**
   - Grant accessibility permissions for automation
   - System Preferences → Security & Privacy → Privacy → Accessibility

4. **Visual analysis not working**
   - Check your `GOOGLE_API_KEY` in config.py
   - Ensure Gemini API is enabled
   - Verify image file exists and is readable

### Performance Tips

1. **Optimize screenshot frequency**
   - Only take screenshots when needed
   - Use cleanup methods to manage disk space

2. **Browser resource management**
   - Always close browsers when done
   - Use headless mode for background tasks

3. **Visual analysis efficiency**
   - Use specific analysis types for better results
   - Cache analysis results when possible

## 🔮 Advanced Features

### Custom Workflows
```python
async def custom_workflow():
    """Example: Multi-step automation workflow"""
    
    # Step 1: Setup
    browser_tool = BrowserAutomationTool()
    visual_tool = VisualAnalysisTool()
    
    # Step 2: Navigate and analyze
    await browser_tool.execute("open swiggy")
    screenshot = await browser_tool.execute("take screenshot")
    
    # Step 3: Visual analysis
    analysis = await visual_tool.execute("find signup button")
    
    # Step 4: Action based on analysis
    if "signup" in analysis.data['raw_response'].lower():
        await browser_tool.execute("click signup button")
        
    # Step 5: Continue workflow...
```

### Error Handling
```python
async def robust_automation():
    try:
        result = await browser_tool.execute("click button")
        if not result.success:
            # Fallback: try visual analysis to find button
            analysis = await visual_tool.execute("find the submit button")
            # Extract coordinates and use click tool
            
    except Exception as e:
        print(f"Automation failed: {e}")
        # Cleanup and retry logic
```

## 📚 API Reference

Each tool follows the same interface:

```python
class BaseTool:
    async def execute(self, query: str, **kwargs) -> ToolResult
    def get_schema(self) -> Dict[str, Any]
```

**ToolResult Structure:**
```python
{
    "success": bool,
    "data": Any,           # Tool-specific result data
    "error": str,          # Error message if failed
    "metadata": dict       # Additional information
}
```

## 🤝 Contributing

To add new automation tools:

1. Inherit from `BaseTool`
2. Implement `execute()` and `get_schema()` methods
3. Add to `tools/automation/__init__.py`
4. Update main `tools/__init__.py`
5. Add tests and documentation

## 📄 License

These automation tools are part of the React Agent project and follow the same license terms.

---

**Happy Automating! 🤖✨**