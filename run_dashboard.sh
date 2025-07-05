#!/bin/bash

echo "Starting Chaptrix Dashboard..."
echo ""
echo "If this is your first time running Chaptrix, make sure you have installed the requirements:"
echo "pip install -r requirements.txt"
echo ""

# Check if streamlit is installed
if ! pip show streamlit > /dev/null 2>&1; then
    echo "Streamlit not found. Installing requirements..."
    pip install -r requirements.txt
fi

echo ""
echo "Opening Chaptrix Dashboard in your browser..."
streamlit run main.py