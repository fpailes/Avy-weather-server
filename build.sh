#!/bin/bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install chromium

# Install required system dependencies for Playwright on Render
python -m playwright install-deps chromium
