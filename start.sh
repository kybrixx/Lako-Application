#!/bin/bash

# Lako Application Startup Script
# This script starts both the backend API and frontend server

echo "=========================================="
echo "🍜 LAKO APPLICATION STARTUP"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install/update dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"
pip install -q -r PublicWebApp/Backendpwa/requirements.txt

# Start backend in background
echo -e "${GREEN}Starting backend API on port 5000...${NC}"
cd PublicWebApp/Backendpwa
python3 app.py > /tmp/lako_backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}Backend started (PID: $BACKEND_PID)${NC}"
echo -e "${YELLOW}API endpoint: http://localhost:5000/api/test${NC}"

# Wait for backend to start
sleep 2

# Check if backend is running
if curl -s http://localhost:5000/api/test > /dev/null; then
    echo -e "${GREEN}✓ Backend API is running!${NC}"
else
    echo -e "${RED}✗ Backend API failed to start${NC}"
    cat /tmp/lako_backend.log
    exit 1
fi

# Navigate to frontend directory
cd ../../PublicWebApp/Frontendpwa

# Start frontend HTTP server
echo -e "${GREEN}Starting frontend HTTP server on port 8000...${NC}"
python3 -m http.server 8000 > /tmp/lako_frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}Frontend started (PID: $FRONTEND_PID)${NC}"

echo ""
echo "=========================================="
echo -e "${GREEN}✓ LAKO APPLICATION IS READY!${NC}"
echo "=========================================="
echo ""
echo -e "${YELLOW}📱 FRONTEND:${NC}"
echo "   URL: http://localhost:8000/index.html"
echo ""
echo -e "${YELLOW}🔌 BACKEND API:${NC}"
echo "   URL: http://localhost:5000"
echo "   Test: http://localhost:5000/api/test"
echo ""
echo -e "${YELLOW}📝 LOGS:${NC}"
echo "   Backend: tail -f /tmp/lako_backend.log"
echo "   Frontend: tail -f /tmp/lako_frontend.log"
echo ""
echo -e "${YELLOW}🛑 TO STOP THE APPLICATION:${NC}"
echo "   Press Ctrl+C or run: kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "=========================================="
echo ""

# Trap Ctrl+C to stop both processes
trap "kill $BACKEND_PID $FRONTEND_PID; echo -e '${GREEN}Application stopped${NC}'; exit 0" INT

# Keep script running
wait
