#!/bin/bash

# Setup and run script for the AI Agent with Real-time Thinking

echo "🤖 AI Agent with Real-time Thinking - Setup & Run"
echo "=================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "🔑 IMPORTANT: Please edit .env file and add your API keys:"
    echo "   - GOOGLE_API_KEY=your_gemini_api_key"
    echo "   - SERPER_API_KEY=your_serper_api_key (optional)"
    echo ""
    read -p "Press Enter after you've configured your API keys..."
fi

echo ""
echo "🚀 Starting the Real-time Thinking Interface..."
echo "📍 URL: http://localhost:8503"
echo "💡 Watch the AI think in real-time!"
echo ""

# Run the streaming interface
streamlit run web_interface_streaming.py --server.port=8503