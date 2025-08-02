"""Example of integrating automation tools with React Agent."""

import asyncio
from agent.react_agent import ReactAgent
from tools.automation.screenshot_tool import ScreenshotTool
from tools.automation.app_launcher_tool import AppLauncherTool
from tools.automation.text_input_tool import TextInputTool
from tools.automation.click_tool import ClickTool
from tools.automation.browser_automation_tool import BrowserAutomationTool
from tools.automation.visual_analysis_tool import VisualAnalysisTool


class AutomationReactAgent(ReactAgent):
    """Extended React Agent with automation capabilities."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Add automation tools
        self._add_automation_tools()
    
    def _add_automation_tools(self):
        """Add automation tools to the agent."""
        automation_tools = [
            ScreenshotTool(),
            AppLauncherTool(),
            TextInputTool(),
            ClickTool(),
            BrowserAutomationTool(),
            VisualAnalysisTool()
        ]
        
        # Add tools to the tool manager
        for tool in automation_tools:
            self.tool_manager.add_tool(tool.name, tool)
        
        print(f"✅ Added {len(automation_tools)} automation tools to the agent")


async def demo_swiggy_ordering():
    """Demo: Automated Swiggy food ordering workflow."""
    print("\n🍕 Demo: Swiggy Food Ordering Automation")
    print("=" * 50)
    
    # Create automation-enabled agent
    agent = AutomationReactAgent(verbose=True)
    
    # Define the task
    task = """
    I want to order food from Swiggy. Please:
    1. Open a browser and go to Swiggy website
    2. Take a screenshot to see what's on the page
    3. Analyze the screenshot to understand the UI
    4. Look for login/signup options
    5. Take another screenshot after any interactions
    6. Provide a summary of what you found and next steps
    """
    
    try:
        result = await agent.run(task, max_steps=10)
        
        print("\n" + "=" * 50)
        print("🎯 Task Result:")
        print(f"Success: {result.get('success', False)}")
        print(f"Final Answer: {result.get('final_answer', 'No final answer')}")
        
        if 'steps' in result:
            print(f"Steps taken: {len(result['steps'])}")
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")


async def demo_notes_poem():
    """Demo: Write a poem in Notes app."""
    print("\n📝 Demo: Write Poem in Notes")
    print("=" * 30)
    
    agent = AutomationReactAgent(verbose=True)
    
    task = """
    Please write a beautiful poem about automation in the Notes app:
    1. Open the Notes application
    2. Write a creative poem about the future of automation
    3. Take a screenshot to show the result
    """
    
    try:
        result = await agent.run(task, max_steps=8)
        
        print("\n" + "=" * 30)
        print("🎯 Task Result:")
        print(f"Success: {result.get('success', False)}")
        print(f"Final Answer: {result.get('final_answer', 'No final answer')}")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")


async def demo_visual_ui_analysis():
    """Demo: Take screenshot and analyze UI elements."""
    print("\n👁️ Demo: Visual UI Analysis")
    print("=" * 35)
    
    agent = AutomationReactAgent(verbose=True)
    
    task = """
    Please analyze the current screen:
    1. Take a screenshot of the current screen
    2. Analyze the screenshot to identify all UI elements
    3. List all clickable buttons, input fields, and interactive elements
    4. Suggest what actions a user could take
    5. Provide coordinates for the most important elements
    """
    
    try:
        result = await agent.run(task, max_steps=6)
        
        print("\n" + "=" * 35)
        print("🎯 Task Result:")
        print(f"Success: {result.get('success', False)}")
        print(f"Final Answer: {result.get('final_answer', 'No final answer')}")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")


async def main():
    """Run automation demos with React Agent."""
    print("🤖 Automation React Agent Demo")
    print("=" * 60)
    
    print("\nAvailable demos:")
    print("1. Swiggy food ordering workflow")
    print("2. Write poem in Notes app")
    print("3. Visual UI analysis")
    
    # You can uncomment the demos you want to run:
    
    # Demo 1: Swiggy ordering (most complex)
    # await demo_swiggy_ordering()
    
    # Demo 2: Notes poem (simpler)
    await demo_notes_poem()
    
    # Demo 3: Visual analysis (screenshot analysis)
    # await demo_visual_ui_analysis()
    
    print("\n" + "=" * 60)
    print("🎉 Automation demos completed!")
    
    print("\n💡 Usage Tips:")
    print("- The agent can now handle visual tasks through screenshots")
    print("- It can interact with both web browsers and desktop applications")
    print("- Visual analysis helps the agent understand what's on screen")
    print("- You can chain multiple automation actions together")
    
    print("\n🔧 Customization Options:")
    print("- Modify visual analysis prompts for specific use cases")
    print("- Add custom application mappings in AppLauncherTool")
    print("- Extend browser automation for specific websites")
    print("- Create custom workflows for repetitive tasks")


if __name__ == "__main__":
    asyncio.run(main())