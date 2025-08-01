"""Complete example showing React Agent with automation tools."""

import asyncio
from agent.react_agent import ReactAgent


async def demo_swiggy_automation():
    """Demo: Complete Swiggy automation workflow."""
    print("🍕 Swiggy Automation Demo")
    print("=" * 30)
    
    # Create agent with automation tools
    agent = ReactAgent(verbose=True, include_automation=True)
    
    task = """
    I want to explore Swiggy for food ordering. Please:
    
    1. Open a web browser
    2. Navigate to Swiggy website
    3. Take a screenshot of the homepage
    4. Analyze the screenshot to identify:
       - Login/signup options
       - Search functionality
       - Main navigation elements
       - Any promotional content
    5. Provide a summary of what you found and suggest next steps for ordering food
    
    Please be thorough in your analysis and provide specific details about the UI elements.
    """
    
    try:
        result = await agent.run(task, max_steps=12)
        
        print("\n" + "=" * 50)
        print("🎯 Swiggy Automation Result:")
        print(f"Success: {result.get('success', False)}")
        print(f"Steps taken: {len(result.get('steps', []))}")
        
        if result.get('final_answer'):
            print(f"\n💬 Agent's Analysis:")
            print(result['final_answer'])
        
        return result
        
    except Exception as e:
        print(f"❌ Swiggy automation failed: {e}")
        return None


async def demo_notes_creativity():
    """Demo: Creative writing in Notes app."""
    print("\n📝 Notes Creative Writing Demo")
    print("=" * 35)
    
    agent = ReactAgent(verbose=True, include_automation=True)
    
    task = """
    Please help me write a creative piece in the Notes app:
    
    1. Open the Notes application on macOS
    2. Write a beautiful, inspiring poem about the future of AI and automation
    3. The poem should be at least 4 stanzas long
    4. Include themes of:
       - Technology helping humanity
       - The balance between AI and human creativity
       - Hope for the future
    5. Take a screenshot of the final result
    6. Provide the poem text in your response as well
    
    Make it creative and inspiring!
    """
    
    try:
        result = await agent.run(task, max_steps=10)
        
        print("\n" + "=" * 35)
        print("🎯 Creative Writing Result:")
        print(f"Success: {result.get('success', False)}")
        
        if result.get('final_answer'):
            print(f"\n📜 Agent's Creation:")
            print(result['final_answer'])
        
        return result
        
    except Exception as e:
        print(f"❌ Creative writing failed: {e}")
        return None


async def demo_visual_analysis():
    """Demo: Visual analysis of current screen."""
    print("\n👁️ Visual Analysis Demo")
    print("=" * 25)
    
    agent = ReactAgent(verbose=True, include_automation=True)
    
    task = """
    Please perform a comprehensive visual analysis:
    
    1. Take a screenshot of the current screen
    2. Analyze the screenshot to identify:
       - All visible applications and windows
       - Interactive elements (buttons, menus, text fields)
       - The overall layout and design
       - Any text content that's visible
    3. Suggest 3-5 actions that a user could take based on what's visible
    4. Identify the most important or prominent elements on screen
    
    Provide a detailed analysis as if you're describing the screen to someone who can't see it.
    """
    
    try:
        result = await agent.run(task, max_steps=8)
        
        print("\n" + "=" * 25)
        print("🎯 Visual Analysis Result:")
        print(f"Success: {result.get('success', False)}")
        
        if result.get('final_answer'):
            print(f"\n🔍 Agent's Analysis:")
            print(result['final_answer'])
        
        return result
        
    except Exception as e:
        print(f"❌ Visual analysis failed: {e}")
        return None


async def demo_multi_step_workflow():
    """Demo: Complex multi-step automation workflow."""
    print("\n🔄 Multi-Step Workflow Demo")
    print("=" * 30)
    
    agent = ReactAgent(verbose=True, include_automation=True)
    
    task = """
    Please execute this multi-step automation workflow:
    
    1. Take a screenshot of the current desktop
    2. Open the Calculator app
    3. Take another screenshot showing the Calculator
    4. Open a web browser and go to Google
    5. Take a screenshot of Google homepage
    6. Analyze all three screenshots and compare them
    7. Provide a summary of:
       - What changed between each screenshot
       - The applications that were opened
       - The overall workflow progression
    
    This demonstrates the agent's ability to coordinate multiple automation tools.
    """
    
    try:
        result = await agent.run(task, max_steps=15)
        
        print("\n" + "=" * 30)
        print("🎯 Multi-Step Workflow Result:")
        print(f"Success: {result.get('success', False)}")
        print(f"Steps taken: {len(result.get('steps', []))}")
        
        if result.get('final_answer'):
            print(f"\n🔄 Workflow Summary:")
            print(result['final_answer'])
        
        return result
        
    except Exception as e:
        print(f"❌ Multi-step workflow failed: {e}")
        return None


async def main():
    """Run all automation demos."""
    print("🤖 Complete React Agent Automation Demos")
    print("=" * 60)
    
    print("\nThis demo will showcase the React Agent's automation capabilities:")
    print("- Web browser automation")
    print("- Desktop application control")
    print("- Visual analysis and understanding")
    print("- Multi-step workflow coordination")
    
    # Check if user wants to run all demos
    print("\n" + "=" * 60)
    
    demos = [
        ("Visual Analysis", demo_visual_analysis),
        ("Notes Creative Writing", demo_notes_creativity),
        ("Swiggy Web Automation", demo_swiggy_automation),
        ("Multi-Step Workflow", demo_multi_step_workflow)
    ]
    
    results = {}
    
    for demo_name, demo_func in demos:
        print(f"\n🚀 Starting: {demo_name}")
        print("-" * 40)
        
        try:
            result = await demo_func()
            results[demo_name] = result is not None and result.get('success', False)
        except Exception as e:
            print(f"❌ {demo_name} failed with error: {e}")
            results[demo_name] = False
        
        print(f"✅ Completed: {demo_name}")
        
        # Small delay between demos
        await asyncio.sleep(2)
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 Demo Results Summary:")
    
    for demo_name, success in results.items():
        status = "✅ Success" if success else "❌ Failed"
        print(f"  {demo_name}: {status}")
    
    successful_demos = sum(results.values())
    total_demos = len(results)
    
    print(f"\n🎯 Overall Success Rate: {successful_demos}/{total_demos} ({successful_demos/total_demos*100:.1f}%)")
    
    if successful_demos == total_demos:
        print("\n🎉 All demos completed successfully!")
        print("Your React Agent is fully equipped for automation tasks!")
    elif successful_demos > 0:
        print(f"\n✅ {successful_demos} demos succeeded. Check error messages for failed demos.")
    else:
        print("\n⚠️ All demos failed. Please check your setup and dependencies.")
    
    print("\n💡 What you can do next:")
    print("- Create custom automation workflows")
    print("- Integrate with your specific applications")
    print("- Build complex multi-step automation tasks")
    print("- Use visual analysis for dynamic UI interaction")


if __name__ == "__main__":
    asyncio.run(main())