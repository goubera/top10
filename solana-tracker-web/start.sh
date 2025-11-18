#!/bin/bash

# Solana Token Tracker - Start Script

echo "🚀 Starting Solana Token Tracker..."

# Check if in correct directory
if [ ! -d "backend" ]; then
    echo "❌ Error: Please run this script from the solana-tracker-web directory"
    exit 1
fi

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    cd backend && pip install -r requirements.txt && cd ..
fi

# Initialize database if it doesn't exist
if [ ! -f "data/tracker.db" ]; then
    echo "🗄️  Initializing database..."
    cd backend && python -c "from database import init_db; init_db()" && cd ..
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Starting FastAPI server..."
echo "Dashboard will be available at: http://localhost:8000/static/index.html"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
cd backend && python main.py
