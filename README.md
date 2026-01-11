# NWAC Forecast Cache Server

A lightweight Flask API that scrapes NWAC avalanche forecasts and caches them. Designed to run on free hosting platforms like Render or PythonAnywhere.

## Deployment Options

### Option 1: Render (Recommended)

1. Create account at https://render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repo (or upload this folder)
4. Configure:
   - **Name**: nwac-cache
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free
5. Click "Create Web Service"
6. Your API will be at: `https://nwac-cache-XXXX.onrender.com`

### Option 2: PythonAnywhere

1. Create account at https://www.pythonanywhere.com
2. Go to "Web" tab → "Add a new web app"
3. Choose "Flask" framework
4. Upload files to `/home/yourusername/mysite/`
5. Install requirements: `pip install -r requirements.txt`
6. Reload web app

## API Endpoints

- `GET /` - API documentation
- `GET /health` - Health check
- `GET /forecast/stevens-pass` - Stevens Pass forecast
- `GET /forecast/snoqualmie-pass` - Snoqualmie Pass forecast  
- `GET /forecast/east-slopes-central` - East Slopes Central forecast
- `GET /forecast/all` - All forecasts

## How It Works

1. First request triggers a scrape of NWAC website
2. Results cached for 6 hours
3. Subsequent requests use cache (fast!)
4. Cache auto-refreshes after 6 hours

## Local Testing

```bash
pip install -r requirements.txt
python app.py
```

Visit http://localhost:5000

## Cache Duration

Default: 6 hours. Modify `CACHE_DURATION` in `app.py` to change.
