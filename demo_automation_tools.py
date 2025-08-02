"""Demo script to test the automation tools."""

import asyncio
import time
from tools.automation.screenshot_tool import ScreenshotTool
from tools.automation.app_launcher_tool import AppLauncherTool
from tools.automation.text_input_tool import TextInputTool
from tools.automation.click_tool import ClickTool
from tools.automation.browser_automation_tool import BrowserAutomationTool
from tools.automation.visual_analysis_tool import VisualAnalysisTool


async def demo_screenshot_tool():
    """Demo the screenshot tool."""
    print("\n=== Screenshot Tool Demo ===")
    
    screenshot_tool = ScreenshotTool()
    
    # Take a screenshot
    result = await screenshot_tool.execute("take a full screen screenshot")
    
    if result.success:
        print(f"✅ Screenshot taken successfully!")
        print(f"   File: {result.data['filename']}")
        print(f"   Size: {result.data['width']}x{result.data['height']}")
        print(f"   Path: {result.data['filepath']}")
    else:
        print(f"❌ Screenshot failed: {result.error}")
    
    return result


async def demo_app_launcher():
    """Demo the app launcher tool."""
    print("\n=== App Launcher Tool Demo ===")
    
    app_launcher = AppLauncherTool()
    
    # Launch Notes app
    result = await app_launcher.execute("open notes")
    
    if result.success:
        print(f"✅ App launched successfully!")
        print(f"   App: {result.data['app_name']}")
        print(f"   Launched: {result.data['launched']}")
    else:
        print(f"❌ App launch failed: {result.error}")
    
    # Wait a bit for the app to open
    time.sleep(2)
    
    return result


async def demo_text_input():
    """Demo the text input tool."""
    print("\n=== Text Input Tool Demo ===")
    
    text_input_tool = TextInputTool()
    
    # Type some text (assuming Notes is open)
    poem_text = """Here's a beautiful poem:

Roses are red,
Violets are blue,
Automation is awesome,
And so are you!

Written by AI Assistant 🤖"""
    
    result = await text_input_tool.execute(f"type this text: {poem_text}")
    
    if result.success:
        print(f"✅ Text typed successfully!")
        print(f"   Characters typed: {result.data['character_count']}")
    else:
        print(f"❌ Text input failed: {result.error}")
    
    return result


async def demo_browser_automation():
    """Demo the browser automation tool."""
    print("\n=== Browser Automation Tool Demo ===")
    
    browser_tool = BrowserAutomationTool()
    
    try:
        # Open browser
        result1 = await browser_tool.execute("open browser")
        if result1.success:
            print("✅ Browser opened successfully!")
        else:
            print(f"❌ Browser open failed: {result1.error}")
            return
        
        # Navigate to Swiggy
        result2 = await browser_tool.execute("go to swiggy")
        if result2.success:
            print(f"✅ Navigated to Swiggy!")
            print(f"   URL: {result2.data['current_url']}")
            print(f"   Title: {result2.data['title']}")
        else:
            print(f"❌ Navigation failed: {result2.error}")
        
        # Take a screenshot of the browser
        result3 = await browser_tool.execute("take screenshot")
        if result3.success:
            print(f"✅ Browser screenshot taken!")
            print(f"   File: {result3.data['filename']}")
        else:
            print(f"❌ Screenshot failed: {result3.error}")
        
        # Wait a bit to see the page
        time.sleep(3)
        
        # Get page info
        result4 = await browser_tool.execute("get page info")
        if result4.success:
            print(f"✅ Page info retrieved!")
            print(f"   Title: {result4.data['title']}")
            print(f"   URL: {result4.data['url']}")
        
        # Close browser
        await browser_tool.execute("close browser")
        print("✅ Browser closed!")
        
    except Exception as e:
        print(f"❌ Browser demo failed: {e}")
        # Try to close browser if it's open
        try:
            await browser_tool.execute("close browser")
        except:
            pass


async def demo_visual_analysis():
    """Demo the visual analysis tool."""
    print("\n=== Visual Analysis Tool Demo ===")
    
    visual_tool = VisualAnalysisTool()
    
    # Analyze the latest screenshot
    result = await visual_tool.execute("analyze this screenshot for UI elements and suggest actions")
    
    if result.success:
        print("✅ Visual analysis completed!")
        print(f"   Analysis type: {result.metadata.get('analysis_type', 'general')}")
        
        # Print structured analysis if available
        if 'analysis' in result.data and isinstance(result.data['analysis'], dict):
            analysis = result.data['analysis']
            
            if 'page_type' in analysis:
                print(f"   Page type: {analysis['page_type']}")
            
            if 'ui_elements' in analysis:
                print(f"   UI elements found: {len(analysis['ui_elements'])}")
            
            if 'suggested_actions' in analysis:
                print("   Suggested actions:")
                for action in analysis['suggested_actions'][:3]:  # Show first 3
                    print(f"     - {action}")
        
        # Show raw response (truncated)
        raw_response = result.data.get('raw_response', '')
        if raw_response:
            print(f"   Raw analysis (first 200 chars): {raw_response[:200]}...")
            
    else:
        print(f"❌ Visual analysis failed: {result.error}")
    
    return result


async def demo_complete_workflow():
    """Demo a complete workflow: Open Swiggy, take screenshot, analyze it."""
    print("\n=== Complete Workflow Demo ===")
    print("This will: Open browser → Go to Swiggy → Screenshot → Analyze → Close")
    
    browser_tool = BrowserAutomationTool()
    screenshot_tool = ScreenshotTool()
    visual_tool = VisualAnalysisTool()
    
    try:
        # Step 1: Open browser and go to Swiggy
        print("Step 1: Opening browser and navigating to Swiggy...")
        await browser_tool.execute("open browser")
        await browser_tool.execute("go to swiggy")
        time.sleep(3)  # Wait for page to load
        
        # Step 2: Take screenshot
        print("Step 2: Taking screenshot...")
        screenshot_result = await screenshot_tool.execute("take screenshot of swiggy page")
        
        if not screenshot_result.success:
            print(f"❌ Screenshot failed: {screenshot_result.error}")
            return
        
        # Step 3: Analyze the screenshot
        print("Step 3: Analyzing screenshot for e-commerce elements...")
        analysis_result = await visual_tool.execute(
            "analyze this swiggy page for food ordering elements",
            analysis_type="ecommerce",
            image_path=screenshot_result.data['filepath']
        )
        
        if analysis_result.success:
            print("✅ Complete workflow successful!")
            print("   Analysis summary:")
            
            # Show analysis results
            if 'analysis' in analysis_result.data:
                analysis = analysis_result.data['analysis']
                if isinstance(analysis, dict):
                    if 'page_section' in analysis:
                        print(f"     Page section: {analysis['page_section']}")
                    if 'products' in analysis:
                        print(f"     Products found: {len(analysis['products'])}")
                    if 'user_actions' in analysis:
                        print(f"     Possible actions: {len(analysis['user_actions'])}")
        else:
            print(f"❌ Analysis failed: {analysis_result.error}")
        
        # Step 4: Close browser
        print("Step 4: Closing browser...")
        await browser_tool.execute("close browser")
        
    except Exception as e:
        print(f"❌ Complete workflow failed: {e}")
        try:
            await browser_tool.execute("close browser")
        except:
            pass


async def main():
    """Run all demos."""
    print("🚀 Starting Automation Tools Demo")
    print("=" * 50)
    
    # Demo individual tools
    await demo_screenshot_tool()
    await demo_app_launcher()
    await demo_text_input()
    await demo_visual_analysis()
    await demo_browser_automation()
    
    # Demo complete workflow
    await demo_complete_workflow()
    
    print("\n" + "=" * 50)
    print("🎉 All demos completed!")
    print("\nYour automation tools are ready to use!")
    print("\nNext steps:")
    print("1. Integrate these tools with your React Agent")
    print("2. Create custom workflows for specific tasks")
    print("3. Add error handling and retry logic")
    print("4. Customize the visual analysis prompts for your use cases")


if __name__ == "__main__":
    asyncio.run(main())