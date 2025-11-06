#!/bin/bash
# LLMPoker Assistant - Startup Script

echo "🚀 Starting LLMPoker Assistant..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run application
python src/main.py
