#!/bin/bash
# Move to the script's directory so relative paths work
cd "$(dirname "$0")"

echo "=================================================="
echo "Starting Camp Belknap Survey Extraction Tool..."
echo "=================================================="
echo ""
echo "Installing requirements (if any updates)..."
python3 -m pip install -r requirements.txt
echo ""
echo "Starting web app in your browser..."
python3 -m streamlit run app.py
echo ""
echo "If the tool stopped or errored, details are shown above."
read -p "Press [Enter] to exit..."
