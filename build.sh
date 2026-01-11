#!/bin/bash
# Install Python dependencies
pip install -r requirements.txt

# Set playwright browsers path to project directory (persists across build/runtime)
export PLAYWRIGHT_BROWSERS_PATH="${RENDER_PROJECT_ROOT}/browsers"
mkdir -p "${PLAYWRIGHT_BROWSERS_PATH}"

# Install Playwright browsers
playwright install chromium

# Install required system dependencies for Playwright on Render
playwright install-deps chromium
