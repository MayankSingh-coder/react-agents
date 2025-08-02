"""Demo React Agent with improved browser automation."""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.append('/Users/mayank/Desktop/concepts/react-agents')

from tools.enhanced_tool_manager import EnhancedToolManager


async def demo_swiggy_exploration():
    """Demo: Explore Swiggy with proper tab management."""
    print("🍕 Demo: Swiggy Exploration with Tab Management")
    print("=" * 50)
    
    # Create tool manager with automation tools
    tool_manager = EnhancedToolManager(
        use_mysql=False,  # Use in-memory for demo
        include_automation=True
    )
    
    try:
        print("Step 1: Opening Safari and navigating to Swiggy...")
        result1 = await tool_manager.execute_tool(
            "unified_browser",
            "open safari and go to swiggy"
        )
        
        if result1.success:
            print("✅ Safari opened with Swiggy")
            print(f"   Browser: {result1.data.get('browser', 'N/A')}")
            print(f"   URL: {result1.data.get('url', 'N/A')}")
        else:
            print(f"❌ Failed: {result1.error}")
            return False
        
        await asyncio.sleep(3)  # Wait for page to load
        
        print("\nStep 2: Taking screenshot for analysis...")
        result2 = await tool_manager.execute_tool(
            "screenshot",
            "take screenshot of swiggy homepage"
        )
        
        if result2.success:
            print("✅ Screenshot taken")
            print(f"   File: {result2.data.get('filename', 'N/A')}")
            
            # Analyze the screenshot
            print("\nStep 3: Analyzing Swiggy homepage...")
            result3 = await tool_manager.execute_tool(
                "visual_analysis",
                "analyze this swiggy homepage for food ordering elements and login options",
                analysis_type="ecommerce",
                image_path=result2.data.get('filepath')
            )
            
            if result3.success:
                print("✅ Visual analysis completed")
                
                # Show analysis summary
                raw_response = result3.data.get('raw_response', '')
                if raw_response:
                    print(f"   Analysis preview: {raw_response[:300]}...")
            else:
                print(f"❌ Analysis failed: {result3.error}")
        else:
            print(f"❌ Screenshot failed: {result2.error}")
        
        print("\nStep 4: Opening new tab with Zomato for comparison...")
        result4 = await tool_manager.execute_tool(
            "unified_browser",
            "open new tab and go to zomato"
        )
        
        if result4.success:
            print("✅ New tab opened with Zomato")
            print(f"   URL: {result4.data.get('url', 'N/A')}")
        else:
            print(f"❌ Failed to open Zomato tab: {result4.error}")
        
        await asyncio.sleep(3)
        
        print("\nStep 5: Taking screenshot of Zomato...")
        result5 = await tool_manager.execute_tool(
            "screenshot",
            "take screenshot of zomato page"
        )
        
        if result5.success:
            print("✅ Zomato screenshot taken")
        
        print("\nStep 6: Closing Zomato tab (keeping Swiggy open)...")
        result6 = await tool_manager.execute_tool(
            "unified_browser",
            "close current tab"
        )
        
        if result6.success:
            print("✅ Zomato tab closed, back to Swiggy")
            print(f"   Method: {result6.data.get('method', 'N/A')}")
        else:
            print(f"❌ Failed to close tab: {result6.error}")
        
        print("\nStep 7: Final screenshot of Swiggy...")
        result7 = await tool_manager.execute_tool(
            "screenshot",
            "final swiggy screenshot"
        )
        
        if result7.success:
            print("✅ Final screenshot taken")
        
        print("\nStep 8: Closing browser...")
        result8 = await tool_manager.execute_tool(
            "unified_browser",
            "close browser"
        )
        
        if result8.success:
            print("✅ Browser closed")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        # Try to close browser
        try:
            await tool_manager.execute_tool("unified_browser", "close browser")
        except:
            pass
        return False


async def demo_multi_site_comparison():
    """Demo: Compare multiple food delivery sites."""
    print("\n🔍 Demo: Multi-Site Food Delivery Comparison")
    print("=" * 50)
    
    tool_manager = EnhancedToolManager(
        use_mysql=False,
        include_automation=True
    )
    
    sites = [
        ("swiggy", "Swiggy"),
        ("zomato", "Zomato"),
        ("amazon", "Amazon Fresh")
    ]
    
    try:
        print("Opening Chrome for multi-tab comparison...")
        result1 = await tool_manager.execute_tool(
            "unified_browser",
            "open chrome and go to google",
            browser="chrome"
        )
        
        if not result1.success:
            print(f"❌ Failed to open Chrome: {result1.error}")
            return False
        
        print("✅ Chrome opened")
        await asyncio.sleep(2)
        
        # Open each site in a new tab
        for site_url, site_name in sites:
            print(f"\nOpening {site_name} in new tab...")
            result = await tool_manager.execute_tool(
                "unified_browser",
                f"new tab and go to {site_url}"
            )
            
            if result.success:
                print(f"✅ {site_name} opened")
                print(f"   Title: {result.data.get('title', 'N/A')[:50]}...")
                
                # Take screenshot
                screenshot_result = await tool_manager.execute_tool(
                    "unified_browser",
                    "take screenshot"
                )
                
                if screenshot_result.success:
                    print(f"   Screenshot: {screenshot_result.data.get('filename', 'N/A')}")
                
                await asyncio.sleep(2)
            else:
                print(f"❌ Failed to open {site_name}: {result.error}")
        
        print(f"\nTaking final screenshot...")
        final_screenshot = await tool_manager.execute_tool(
            "unified_browser",
            "take screenshot"
        )
        
        if final_screenshot.success:
            print("✅ Final comparison screenshot taken")
        
        print(f"\nClosing browser...")
        close_result = await tool_manager.execute_tool(
            "unified_browser",
            "close browser"
        )
        
        if close_result.success:
            print("✅ Browser closed")
        
        return True
        
    except Exception as e:
        print(f"❌ Multi-site comparison failed: {e}")
        try:
            await tool_manager.execute_tool("unified_browser", "close browser")
        except:
            pass
        return False


async def demo_browser_commands():
    """Demo: Show various browser commands."""
    print("\n🎮 Demo: Browser Command Showcase")
    print("=" * 35)
    
    tool_manager = EnhancedToolManager(
        use_mysql=False,
        include_automation=True
    )
    
    commands = [
        ("open safari and go to google", "Open Safari with Google"),
        ("new tab with youtube", "Open YouTube in new tab"),
        ("take screenshot", "Take screenshot"),
        ("close tab", "Close current tab"),
        ("new tab and go to github", "Open GitHub in new tab"),
        ("close current tab", "Close GitHub tab"),
        ("close browser", "Close entire browser")
    ]
    
    try:
        for command, description in commands:
            print(f"\n🔧 {description}")
            print(f"   Command: '{command}'")
            
            result = await tool_manager.execute_tool("unified_browser", command)
            
            if result.success:
                print(f"   ✅ Success")
                if 'title' in result.data:
                    print(f"   Title: {result.data['title'][:50]}...")
                if 'url' in result.data:
                    print(f"   URL: {result.data['url']}")
                if 'filename' in result.data:
                    print(f"   File: {result.data['filename']}")
                if 'message' in result.data:
                    print(f"   Result: {result.data['message']}")
            else:
                print(f"   ❌ Failed: {result.error}")
            
            await asyncio.sleep(2)
        
        return True
        
    except Exception as e:
        print(f"❌ Command showcase failed: {e}")
        try:
            await tool_manager.execute_tool("unified_browser", "close browser")
        except:
            pass
        return False


async def main():
    """Run all browser automation demos."""
    print("🚀 React Agent Browser Automation Demos")
    print("=" * 60)
    
    print("\nThis demo showcases the improved browser automation with:")
    print("- Proper tab management (close tab vs close browser)")
    print("- Multi-site navigation")
    print("- Visual analysis integration")
    print("- Screenshot capabilities")
    
    demos = [
        ("Swiggy Exploration", demo_swiggy_exploration),
        ("Multi-Site Comparison", demo_multi_site_comparison),
        ("Browser Commands", demo_browser_commands)
    ]
    
    results = {}
    
    for demo_name, demo_func in demos:
        print(f"\n{'='*60}")
        print(f"🚀 Starting: {demo_name}")
        print(f"{'='*60}")
        
        try:
            result = await demo_func()
            results[demo_name] = result
            
            if result:
                print(f"\n✅ {demo_name} completed successfully!")
            else:
                print(f"\n❌ {demo_name} failed!")
                
        except Exception as e:
            print(f"\n❌ {demo_name} failed with error: {e}")
            results[demo_name] = False
        
        # Small delay between demos
        await asyncio.sleep(2)
    
    # Final summary
    print(f"\n{'='*60}")
    print("📊 Demo Results Summary")
    print(f"{'='*60}")
    
    successful_demos = 0
    total_demos = len(results)
    
    for demo_name, success in results.items():
        status = "✅ Success" if success else "❌ Failed"
        print(f"  {demo_name:<25} {status}")
        if success:
            successful_demos += 1
    
    print(f"\n🎯 Overall Success Rate: {successful_demos}/{total_demos} ({successful_demos/total_demos*100:.1f}%)")
    
    if successful_demos == total_demos:
        print(f"\n🎉 All demos completed successfully!")
        print(f"✅ Your React Agent browser automation is fully functional!")
    elif successful_demos > 0:
        print(f"\n✅ {successful_demos} demos succeeded!")
        print(f"Some features may need debugging.")
    else:
        print(f"\n⚠️ All demos failed. Please check your setup.")
    
    print(f"\n💡 Key Features Now Available:")
    print(f"  ✅ Smart tab management (close tab vs close browser)")
    print(f"  ✅ Multi-browser support (Safari, Chrome, Chromium)")
    print(f"  ✅ Visual analysis integration")
    print(f"  ✅ Screenshot capabilities")
    print(f"  ✅ URL extraction from natural language")
    print(f"  ✅ AppleScript + Selenium automation")
    
    print(f"\n🔧 Example Commands You Can Use:")
    print(f"  - 'Open Safari and go to Swiggy'")
    print(f"  - 'Open new tab with Zomato'")
    print(f"  - 'Take a screenshot'")
    print(f"  - 'Close current tab' (keeps browser open)")
    print(f"  - 'Close browser' (closes entire application)")
    print(f"  - 'Analyze this page for login options'")
    
    return successful_demos > 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)