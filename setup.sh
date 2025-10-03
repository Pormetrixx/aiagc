#!/bin/bash
# Setup script for AIAGC

set -e

echo "======================================"
echo "AIAGC Setup Script"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p logs
mkdir -p recordings
mkdir -p config/asterisk

# Copy environment template
echo ""
echo "Setting up environment file..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env file from template"
    echo "⚠️  Please edit .env with your API keys and configuration"
else
    echo ".env file already exists"
fi

# Check Docker
echo ""
echo "Checking Docker..."
if command -v docker &> /dev/null; then
    echo "Docker is installed: $(docker --version)"
    
    if command -v docker-compose &> /dev/null; then
        echo "Docker Compose is installed: $(docker-compose --version)"
    else
        echo "⚠️  Docker Compose is not installed"
    fi
else
    echo "⚠️  Docker is not installed"
    echo "   Visit https://docs.docker.com/get-docker/ to install Docker"
fi

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials:"
echo "   - DEEPGRAM_API_KEY"
echo "   - OPENAI_API_KEY"
echo "   - ASTERISK configuration"
echo ""
echo "2. Configure Asterisk (config/asterisk/*.conf)"
echo "   - Update SIP trunk credentials in pjsip.conf"
echo ""
echo "3. Start services:"
echo "   docker-compose up -d"
echo ""
echo "4. Run example:"
echo "   python examples/make_calls.py"
echo ""
echo "For more information, see README.md"
echo ""
