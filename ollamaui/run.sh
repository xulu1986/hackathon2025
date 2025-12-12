#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Starting Ollama UI..."

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed."
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "⚠️ Warning: pip3 is not found. Installing dependencies might fail."
fi

# Install dependencies
echo "📦 Checking dependencies..."
python3 -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Error installing dependencies."
    exit 1
fi

# Run the application
echo "✨ Launching Streamlit app..."
python3 -m streamlit run app.py

