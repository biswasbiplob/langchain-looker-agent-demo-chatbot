#!/bin/bash
# Looker Chatbot Startup Script

echo "🚀 Starting Looker Data Analyst Chatbot..."

# Check if PostgreSQL container is running
if ! docker ps | grep -q looker_chatbot_db; then
    echo "📊 Starting PostgreSQL database..."
    docker-compose up -d
    echo "⏳ Waiting for database to be ready..."
    sleep 5
fi

# Load environment variables and start the app
echo "🔧 Loading configuration..."
export $(cat .env | grep -v '^#' | xargs)

echo "🌐 Starting Flask server..."
echo "📍 Server will be available at: http://localhost:5001"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

uv run python main.py