"""Simple chatbot interface for the React Agent."""

# Import gRPC configuration first to suppress warnings
import grpc_config

import asyncio
import json
from typing import Dict, Any
from agent import ReactAgent


class ReactChatbot:
    """Simple chatbot interface for the React Agent."""
    
    def __init__(self, verbose: bool = True):
        self.agent = ReactAgent(verbose=verbose)
        self.conversation_history = []
    
    async def chat(self, message: str) -> Dict[str, Any]:
        """Process a chat message and return the response."""
        try:
            # Run the agent
            response = await self.agent.run(message)
            
            # Add to conversation history
            self.conversation_history.append({
                "user": message,
                "assistant": response["output"],
                "success": response["success"],
                "steps": len(response["steps"])
            })
            
            return response
            
        except Exception as e:
            error_response = {
                "input": message,
                "output": f"I apologize, but I encountered an error: {str(e)}",
                "steps": [],
                "success": False,
                "error": str(e),
                "metadata": {}
            }
            
            self.conversation_history.append({
                "user": message,
                "assistant": error_response["output"],
                "success": False,
                "steps": 0
            })
            
            return error_response
    
    def get_stats(self) -> Dict[str, Any]:
        """Get chatbot statistics."""
        total_conversations = len(self.conversation_history)
        successful_conversations = sum(1 for conv in self.conversation_history if conv["success"])
        
        stats = {
            "total_conversations": total_conversations,
            "successful_conversations": successful_conversations,
            "success_rate": successful_conversations / total_conversations if total_conversations > 0 else 0,
            "agent_stats": self.agent.get_memory_stats()
        }
        
        return stats
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history.clear()


async def main():
    """Main function to run the chatbot in console mode."""
    print("🤖 Octopus Prime Chat Bot Reactive Agent")
    print("=" * 50)
    print("Type 'quit', 'exit', or 'bye' to end the conversation")
    print("Type 'stats' to see usage statistics")
    print("Type 'clear' to clear conversation history")
    print("=" * 50)
    
    chatbot = ReactChatbot(verbose=True)
    
    while True:
        try:
            # Get user input
            user_input = input("\n👤 You: ").strip()
            
            # Handle special commands
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'stats':
                stats = chatbot.get_stats()
                print(f"\n📊 Statistics:")
                print(json.dumps(stats, indent=2))
                continue
            elif user_input.lower() == 'clear':
                chatbot.clear_history()
                print("🧹 Conversation history cleared!")
                continue
            elif not user_input:
                print("Please enter a message or command.")
                continue
            
            # Process the message
            print(f"\n🤖 Assistant: Processing your request...")
            response = await chatbot.chat(user_input)
            
            # Display the response
            if response["success"]:
                print(f"\n🤖 Assistant: {response['output']}")
                if response["steps"]:
                    print(f"   (Completed in {len(response['steps'])} reasoning steps)")
            else:
                print(f"\n❌ Error: {response['error']}")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())