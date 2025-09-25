#!/bin/bash

# Memory DC Redis API Server Startup Script
# Starts the FastAPI development server with auto-reload

set -e  # Exit on any error

echo "🚀 Starting Memory DC Redis API Server..."
echo "📍 API will be available at: http://localhost:8000"
echo "📚 API Documentation at: http://localhost:8000/docs"
echo "🔄 Auto-reload enabled for development"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Please copy .env.example to .env and configure your settings"
    echo ""
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: 'uv' is not installed or not in PATH"
    echo "   Please install uv: https://github.com/astral-sh/uv"
    exit 1
fi

# Start the FastAPI development server
echo "▶️  Starting server..."
uv run fastapi dev app/api.py

# This line will only be reached if the server exits
echo ""
echo "🛑 API server stopped"