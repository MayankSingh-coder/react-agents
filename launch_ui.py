#!/usr/bin/env python3
"""Launcher script for the AI Agent web interfaces."""

import subprocess
import sys
import os


def main():
    """Main launcher function."""
    print("🤖 AI Agent Web Interface Launcher")
    print("=" * 50)
    print("Choose which interface to launch:")
    print("1. 🧠 Real-time Thinking Interface (Recommended)")
    print("2. 📋 Standard Interface with Steps")
    print("3. ❌ Exit")
    print("=" * 50)
    
    while True:
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "1":
                print("\n🚀 Launching Real-time Thinking Interface...")
                print("📍 URL: http://localhost:8501")
                print("🔄 Starting Streamlit server...")
                subprocess.run([
                    sys.executable, "-m", "streamlit", "run", 
                    "web_interface_streaming.py",
                    "--server.port=8501",
                    "--server.headless=false"
                ])
                break
                
            elif choice == "2":
                print("\n🚀 Launching Standard Interface...")
                print("📍 URL: http://localhost:8502")
                print("🔄 Starting Streamlit server...")
                subprocess.run([
                    sys.executable, "-m", "streamlit", "run", 
                    "web_interface.py",
                    "--server.port=8502",
                    "--server.headless=false"
                ])
                break
                
            elif choice == "3":
                print("\n👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            break


if __name__ == "__main__":
    # Change to the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    main()