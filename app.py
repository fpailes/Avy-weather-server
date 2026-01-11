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

app = Flask(__name__)

# In-memory cache
cache = {
    "last_update": None,
    "forecasts": {}
}

# Cache duration: 6 hours
CACHE_DURATION = timedelta(hours=6)

ZONES = {
    "stevens-pass": "stevens-pass",
    "snoqualmie-pass": "snoqualmie-pass",
    "east-slopes-central": "east-slopes-central"
}


def scrape_forecast_simple(zone_slug):
    """Scrape forecast using simple HTTP request and regex parsing."""
    url = f"https://nwac.us/avalanche-forecast/#{zone_slug}"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            return None
        
        html = response.text
        
        # Look for danger ratings in format like "2 - Moderate"
        danger_pattern = r'(\d)\s*-\s*(Low|Moderate|Considerable|High|Extreme)'
        
        # Try to find the three elevation bands
        upper = middle = lower = "Unknown"
        
        # Look for patterns like "Upper Elevations...2 - Moderate"
        upper_match = re.search(
            r'Upper Elevations[^<]*?(\d)\s*-\s*(Low|Moderate|Considerable|High|Extreme)',
            html,
            re.IGNORECASE | re.DOTALL
        )
        if upper_match:
            upper = upper_match.group(2)
        
        middle_match = re.search(
            r'Middle Elevations[^<]*?(\d)\s*-\s*(Low|Moderate|Considerable|High|Extreme)',
            html,
            re.IGNORECASE | re.DOTALL
        )
        if middle_match:
            middle = middle_match.group(2)
        
        lower_match = re.search(
            r'Lower Elevations[^<]*?(\d)\s*-\s*(Low|Moderate|Considerable|High|Extreme)',
            html,
            re.IGNORECASE | re.DOTALL
        )
        if lower_match:
            lower = lower_match.group(2)
        
        # Extract publish date
        issued_match = re.search(
            r'ISSUED[^<]*?<[^>]*>([^<]+)',
            html,
            re.IGNORECASE
        )
        publish_date = issued_match.group(1).strip() if issued_match else datetime.now().strftime("%Y-%m-%d")
        
        if upper == "Unknown" and middle == "Unknown" and lower == "Unknown":
            return None
        
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
        print(f"Error scraping {zone_slug}: {e}")
        return None


def update_cache():
    """Update the cache with fresh forecast data."""
    print("Updating forecast cache...")
    forecasts = {}
    
    for zone_key, zone_slug in ZONES.items():
        forecast = scrape_forecast_simple(zone_slug)
        if forecast:
            forecasts[zone_key] = forecast
            print(f"✓ Cached {zone_key}")
        else:
            print(f"✗ Failed to cache {zone_key}")
    
    cache["last_update"] = datetime.now()
    cache["forecasts"] = forecasts
    print(f"Cache updated at {cache['last_update']}")


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
    return jsonify({
        "status": "ok",
        "cache_age_seconds": (datetime.now() - cache["last_update"]).total_seconds() if cache["last_update"] else None
    })


@app.route('/forecast/<zone>')
def get_forecast(zone):
    """Get forecast for a specific zone."""
    if zone not in ZONES:
        return jsonify({"error": f"Unknown zone: {zone}"}), 404
    
    # Update cache if stale
    if is_cache_stale():
        update_cache()
    
    forecast = cache["forecasts"].get(zone)
    if not forecast:
        return jsonify({"error": f"No forecast available for {zone}"}), 404
    
    return jsonify(forecast)


@app.route('/forecast/all')
def get_all_forecasts():
    """Get all forecasts."""
    # Update cache if stale
    if is_cache_stale():
        update_cache()
    
    return jsonify({
        "forecasts": cache["forecasts"],
        "cached_at": cache["last_update"].isoformat() if cache["last_update"] else None
    })


if __name__ == '__main__':
    # Initialize cache on startup
    update_cache()
    
    # Run server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
