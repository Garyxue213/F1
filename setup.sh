#!/bin/bash

# Project Apex - Setup Script
# Initializes the F1 race analysis system

echo "================================================"
echo "Project Apex - F1 Analysis System Setup"
echo "================================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi
echo "✅ Python found: $(python3 --version)"
echo ""

# Create directories
echo "📁 Creating directories..."
mkdir -p config
mkdir -p data
mkdir -p analysis
mkdir -p audio
mkdir -p Assets/Scripts
mkdir -p Logs
echo "✅ Directories created"
echo ""

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo ""

# Check for .env file
echo "🔐 Checking configuration..."
if [ -f config/.env ]; then
    echo "✅ config/.env already exists"
    read -p "Do you want to reconfigure API keys? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm config/.env
    else
        echo "Using existing configuration"
    fi
else
    echo "⚠️  config/.env not found. Creating template..."
    cat > config/.env << 'EOF'
# Project Apex - F1 Analysis Agent System Configuration

# Gemini API Key - Get from https://ai.google.dev
GEMINI_API_KEY=your_gemini_api_key_here

# ElevenLabs API Key - Get from https://elevenlabs.io
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# F1 Race Configuration
F1_YEAR=2023
F1_GRAND_PRIX=Australian
F1_SESSION=R
F1_DRIVERS=["VER", "ALO"]

# Output Directories
DATA_DIR=./data
ANALYSIS_DIR=./analysis
AUDIO_DIR=./audio

# Replay Configuration
REPLAY_FRAME_RATE=30
REPLAY_DEFAULT_SPEED=1.0
EOF
    echo "✅ Template created. Please edit config/.env and add your API keys"
fi
echo ""

# Create .gitignore if needed
if [ ! -f .gitignore ]; then
    echo "📝 Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Environment
config/.env
.env
.venv/
venv/

# Data files
data/
analysis/
audio/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
Logs/
*.log
EOF
    echo "✅ .gitignore created"
fi
echo ""

echo "================================================"
echo "✅ Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Edit config/.env and add your API keys"
echo "2. Run: python orchestrator.py --skip-audio"
echo "3. Then: python data_server.py"
echo "4. Open Unity and run the replay scene"
echo ""
echo "For help: python orchestrator.py --help"
echo ""
