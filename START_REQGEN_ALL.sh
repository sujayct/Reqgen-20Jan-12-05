#!/bin/bash
# ReqGen Complete System Start - Linux/Mac Version
# Usage: chmod +x START_REQGEN_ALL.sh && ./START_REQGEN_ALL.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NODE_PORT=5027
PYTHON_PORT=5000
MYSQL_PORT=3306
BROWSER_URL="http://localhost:5173"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════╗"
echo "║       ReqGen System Startup (Linux/Mac)            ║"
echo "║                                                    ║"
echo "║  This script will start all required services      ║"
echo "╚════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check project directory
if [ ! -d "$PROJECT_ROOT" ]; then
    echo -e "${RED}✗ Project directory not found${NC}"
    exit 1
fi

cd "$PROJECT_ROOT"
echo -e "${GREEN}✓ Working directory: $PROJECT_ROOT${NC}"

# Check prerequisites
echo -e "\n${CYAN}Checking prerequisites...${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js not found${NC}"
    exit 1
fi
NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js $NODE_VERSION${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓ $PYTHON_VERSION${NC}"

# Check npm
NPM_VERSION=$(npm --version)
echo -e "${GREEN}✓ npm v$NPM_VERSION${NC}"

# Check MySQL
if nc -z localhost $MYSQL_PORT 2>/dev/null; then
    echo -e "${GREEN}✓ MySQL is running on port $MYSQL_PORT${NC}"
else
    echo -e "${YELLOW}! MySQL not detected on port $MYSQL_PORT${NC}"
    echo -e "${YELLOW}  Please start MySQL separately${NC}"
fi

# Install npm dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "\n${CYAN}Installing Node.js dependencies...${NC}"
    npm install
    echo -e "${GREEN}✓ Node dependencies installed${NC}"
fi

# Check Python venv
VENV_PATH="python-backend/venv"
if [ ! -d "$VENV_PATH" ]; then
    echo -e "\n${CYAN}Creating Python virtual environment...${NC}"
    python3 -m venv "$VENV_PATH"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate venv and install packages
echo -e "\n${CYAN}Checking Python packages...${NC}"
source "$VENV_PATH/bin/activate"
pip install --upgrade pip > /dev/null 2>&1

REQUIRED_PACKAGES=("flask" "flask-cors" "transformers" "torch" "librosa" "requests")
for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! pip show "$package" > /dev/null 2>&1; then
        echo -e "${CYAN}Installing $package...${NC}"
        pip install "$package" > /dev/null 2>&1
    fi
done
echo -e "${GREEN}✓ All Python packages installed${NC}"

# Summary
echo -e "\n${CYAN}"
echo "╔════════════════════════════════════════════════════╗"
echo "║              Pre-Launch Summary                    ║"
echo "╚════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "\n${GREEN}Services to start:
  ✓ Node.js Backend     → http://localhost:$NODE_PORT
  ✓ Python Backend      → http://localhost:$PYTHON_PORT
  ✓ Frontend Browser    → http://localhost:5173
  
  Project Root: $PROJECT_ROOT${NC}"

echo -e "\n${YELLOW}Press Enter to start services...${NC}"
read -r

# Start Node backend
echo -e "\n${CYAN}Starting Node Backend...${NC}"
npm run dev &
NODE_PID=$!
echo -e "${GREEN}✓ Node Backend started (PID: $NODE_PID)${NC}"

sleep 2

# Start Python backend
echo -e "\n${CYAN}Starting Python Backend...${NC}"
cd "$PROJECT_ROOT/python-backend"
source "$VENV_PATH/bin/activate"
python app.py &
PYTHON_PID=$!
echo -e "${GREEN}✓ Python Backend started (PID: $PYTHON_PID)${NC}"

sleep 2

# Open browser
echo -e "\n${CYAN}Opening browser...${NC}"
if command -v xdg-open &> /dev/null; then
    xdg-open "$BROWSER_URL"  # Linux
elif command -v open &> /dev/null; then
    open "$BROWSER_URL"      # macOS
fi

# Show summary
echo -e "\n${GREEN}"
echo "╔════════════════════════════════════════════════════╗"
echo "║        Services Started Successfully!              ║"
echo "╚════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${GREEN}✓ Node Backend:     http://localhost:$NODE_PORT
✓ Python Backend:   http://localhost:$PYTHON_PORT
✓ Frontend:         $BROWSER_URL

Processes Running:
  Node (PID $NODE_PID)
  Python (PID $PYTHON_PID)

To stop all services: Press Ctrl+C${NC}"

# Handle cleanup on exit
trap 'kill $NODE_PID $PYTHON_PID 2>/dev/null' EXIT

# Wait for processes
wait $NODE_PID $PYTHON_PID
