#!/bin/bash

# Build script for Render deployment

# Install dependencies
pip install -r requirements.txt

# Run the merge script to ensure curriculum data is available
echo "Setting up curriculum data..."
cd backend/utils
python merge_curriculums.py
cd ../..

# Make sure the data directory exists with curriculum_map.json
if [ ! -f "backend/data/curriculum_map.json" ]; then
    echo "Error: curriculum_map.json not found after merge"
    exit 1
fi

echo "Build completed successfully"