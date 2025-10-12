#!/bin/bash

# Simple installation script for debugging
echo "Installing requirements..."
pip install --no-cache-dir -r requirements.txt

echo "Verifying installations..."
python -c "import requests; print('requests:', requests.__version__)"
python -c "import fastapi; print('fastapi:', fastapi.__version__)"
python -c "import uvicorn; print('uvicorn:', uvicorn.__version__)"

echo "Installation complete!"