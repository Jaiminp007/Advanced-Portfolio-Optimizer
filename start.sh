#!/bin/bash

# Advanced Portfolio Optimizer - Startup Script
# This script sets up and runs the application

echo "🚀 Starting Advanced Portfolio Optimizer..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment found"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ Dependencies installed"

# Check if database exists, if not it will be created on first run
if [ ! -f "portfolio.db" ]; then
    echo "🗄️  Database will be created on first run"
fi

echo ""
echo "======================================"
echo "✨ Setup complete!"
echo "======================================"
echo ""
echo "📊 Available stock tickers:"
echo "   AAPL, MSFT, GOOG, AMZN, TSLA, NVDA, JPM, V"
echo ""
echo "🌐 Server starting at: http://localhost:5000"
echo "📖 Press Ctrl+C to stop the server"
echo ""
echo "======================================"
echo ""

# Start Flask application
python app.py
