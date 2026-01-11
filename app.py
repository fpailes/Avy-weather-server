"""
NWAC Forecast Cache Server
A simple Flask API that scrapes NWAC forecasts and caches them.
Designed to run on PythonAnywhere or Render.
"""
from flask import Flask, jsonify
from datetime import datetime, timedelta
import requests
import re
import os
import threading

app = Flask(__name__)

# In-memory cache
cache = {
    "last_update": None,
    "forecasts": {},
    "is_updating": False
}

# Cache duration: 6 hours
CACHE_DURATION = timedelta(hours=6)

ZONES = {
    "stevens-pass": "stevens-pass",
    "snoqualmie-pass": "snoqualmie-pass",
    "east-slopes-central": "east-slopes-central"
}


def scrape_forecast_playwright(zone_slug):
    """Scrape forecast using Playwright for JavaScript rendering."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not installed")
        return None
    
    url = f"https://nwac.us/avalanche-forecast/#{zone_slug}"
    
    try:
        print(f"Rendering {url} with Playwright...", flush=True)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_default_timeout(120000)  # 2 minutes
            page.goto(url, wait_until="networkidle", timeout=120000)
            
            # Wait for danger labels
            try:
                page.wait_for_selector("text=Upper Elevations", timeout=120000)
            except:
                page.wait_for_timeout(5000)
            
            html = page.content()
            text = page.inner_text("body")
            browser.close()
            
            print(f"Successfully rendered {zone_slug}", flush=True)
            
            # Parse the content
            danger_pattern = r'(Low|Moderate|Considerable|High|Extreme)'
            
            def find_danger(label):
                patterns = [
                    rf"{label}.*?(?:[1-5]\s*-\s*)?{danger_pattern}",
                    rf"{label.replace(' ','')}.*?(?:[1-5]\s*-\s*)?{danger_pattern}",
                ]
                for pat in patterns:
                    m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
                    if m:
                        return m.group(1).capitalize()
                return "Unknown"
            
            upper = find_danger("Upper Elevations")
            middle = find_danger("Middle Elevations")
            lower = find_danger("Lower Elevations")
            
            if upper == "Unknown" and middle == "Unknown" and lower == "Unknown":
                print(f"Could not parse danger levels for {zone_slug}", flush=True)
                return None
            
            # Extract publish date
            issued_match = re.search(r'ISSUED[^<]*?<[^>]*>([^<]+)', html, re.IGNORECASE)
            publish_date = issued_match.group(1).strip() if issued_match else datetime.now().strftime("%Y-%m-%d %H:%M")
            
            return {
                "zone_name": zone_slug.replace("-", " ").title(),
                "publish_date": publish_date,
                "danger_above_treeline": upper,
                "danger_near_treeline": middle,
                "danger_below_treeline": lower,
                "bottom_line": "",
                "detailed_forecast": "",
                "avalanche_problems": [],
                "cached_at": datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Error scraping {zone_slug}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return None


def update_cache():
    """Update the cache with fresh forecast data."""
    cache["is_updating"] = True
    print("Updating forecast cache...", flush=True)
    forecasts = {}
    
    for zone_key, zone_slug in ZONES.items():
        print(f"Starting scrape for {zone_key}...", flush=True)
        forecast = scrape_forecast_playwright(zone_slug)
        if forecast:
            forecasts[zone_key] = forecast
            print(f"✓ Cached {zone_key}", flush=True)
        else:
            print(f"✗ Failed to cache {zone_key}", flush=True)
    
    cache["last_update"] = datetime.now()
    cache["forecasts"] = forecasts
    cache["is_updating"] = False
    print(f"Cache updated at {cache['last_update']} with {len(forecasts)} zones", flush=True)


def update_cache_background():
    """Trigger cache update in background thread."""
    if cache["is_updating"]:
        print("Cache update already in progress, skipping", flush=True)
        return
    
    thread = threading.Thread(target=update_cache)
    thread.daemon = True
    thread.start()
    print(f"Background cache update started (thread: {thread.name})", flush=True)


def is_cache_stale():
    """Check if cache needs updating."""
    if cache["last_update"] is None:
        return True
    
    age = datetime.now() - cache["last_update"]
    return age > CACHE_DURATION


@app.route('/')
def index():
    """API documentation."""
    return jsonify({
        "name": "NWAC Forecast Cache API",
        "version": "1.0",
        "endpoints": {
            "/forecast/<zone>": "Get forecast for a specific zone",
            "/forecast/all": "Get all forecasts",
            "/health": "Health check"
        },
        "zones": list(ZONES.keys()),
        "cache_info": {
            "last_update": cache["last_update"].isoformat() if cache["last_update"] else None,
            "cache_duration_hours": CACHE_DURATION.total_seconds() / 3600
        }
    })


@app.route('/health')
def health():
    """Health check endpoint."""
    cache_age = None
    if cache["last_update"]:
        cache_age = (datetime.now() - cache["last_update"]).total_seconds()
    
    return jsonify({
        "status": "ok",
        "cache_age_seconds": cache_age,
        "is_updating": cache["is_updating"]
    })


@app.route('/forecast/<zone>')
def get_forecast(zone):
    """Get forecast for a specific zone."""
    if zone not in ZONES:
        return jsonify({"error": f"Unknown zone: {zone}"}), 404
    
    # Trigger update in background if stale
    if is_cache_stale():
        update_cache_background()
    
    forecast = cache["forecasts"].get(zone)
    if not forecast:
        if cache["is_updating"]:
            return jsonify({"error": "Cache is being updated, please try again in a moment"}), 503
        return jsonify({"error": f"No forecast available for {zone}"}), 404
    
    return jsonify(forecast)


@app.route('/forecast/all')
def get_all_forecasts():
    """Get all forecasts."""
    # Trigger update in background if stale
    if is_cache_stale():
        update_cache_background()
    
    return jsonify({
        "forecasts": cache["forecasts"],
        "cached_at": cache["last_update"].isoformat() if cache["last_update"] else None,
        "is_updating": cache["is_updating"]
    })


if __name__ == '__main__':
    # Initialize cache on startup (background)
    update_cache_background()
    
    # Run server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
