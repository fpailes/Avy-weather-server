#!/bin/bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Install required system dependencies for Playwright on Render
playwright install-deps chromium
