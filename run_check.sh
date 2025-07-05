#!/bin/bash

echo "Running Chaptrix Check for new chapters..."
echo ""
echo "If this is your first time running Chaptrix, make sure you have installed the requirements:"
echo "pip install -r requirements.txt"
echo ""

# Check if required packages are installed
if ! pip show requests > /dev/null 2>&1; then
    echo "Requirements not found. Installing..."
    pip install -r requirements.txt
fi

echo ""
python main.py --check
echo ""
echo "Check completed."