#!/bin/bash

# Start Bus System - Frontend and Backend

echo "🚀 Starting Bus System..."

# Function to kill background processes on exit
cleanup() {
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

# Set up cleanup on script exit
trap cleanup EXIT INT TERM

# Start Django backend
echo "🐍 Starting Django backend on port 8000..."
cd bus_system_backend
source ../venv/bin/activate
python manage.py runserver 8000 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start React frontend
echo "⚛️  Starting React frontend..."
cd ../Users/nivas/Desktop/Projects/TBD
npm run dev &
FRONTEND_PID=$!

echo "✅ Both servers are starting..."
echo "🌐 Backend: http://localhost:8000"
echo "🌐 Frontend: http://localhost:5173 (or next available port)"
echo "📊 API Status: http://localhost:8000/api/status/"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for processes
wait
