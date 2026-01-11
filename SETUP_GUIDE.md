# Cache API Setup Guide

## What is this?

The cache server solves the slow Playwright scraping problem on Raspberry Pi. Instead of scraping NWAC directly (10+ minutes), the Pi fetches pre-scraped data from your cache API (<5 seconds).

## Step-by-Step Deployment on Render (Free)

### 1. Create Render Account
- Go to https://render.com
- Sign up with GitHub or email

### 2. Deploy the Cache Server

**Option A: GitHub (Recommended)**
1. Create a new GitHub repo for the cache server
2. Upload the contents of `cache_server/` folder
3. In Render dashboard: "New+" → "Web Service"
4. Connect your GitHub repo
5. Configure:
   - **Name**: `nwac-cache`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: `Free`
6. Click "Create Web Service"
7. Wait for deployment (~2 minutes)
8. Note your URL: `https://nwac-cache-XXXX.onrender.com`

**Option B: Direct Upload**
1. In Render dashboard: "New+" → "Web Service"
2. Choose "Public Git repository"
3. Paste a GitHub repo URL or upload files
4. Follow same config as Option A

### 3. Test Your Cache API

Visit these URLs in your browser:
```
https://your-app.onrender.com/
https://your-app.onrender.com/forecast/stevens-pass
https://your-app.onrender.com/forecast/all
```

You should see JSON responses with forecast data.

### 4. Configure Raspberry Pi to Use Cache API

**Method 1: Environment Variable**
```bash
export NWAC_CACHE_API="https://your-app.onrender.com"
python main.py --once
```

**Method 2: Command Line Argument**
```bash
python main.py --once --cache-api "https://your-app.onrender.com"
```

**Method 3: Add to systemd service**
Edit your systemd service file:
```ini
[Service]
Environment="NWAC_CACHE_API=https://your-app.onrender.com"
```

## How It Works

1. **First request**: Cache server scrapes NWAC (takes 30 sec on Render's servers)
2. **Cached for 6 hours**: Subsequent requests are instant (uses cached data)
3. **Auto-refresh**: After 6 hours, next request triggers new scrape

## Expected Performance

- **Without cache**: 10+ minutes (Playwright on Pi)
- **With cache (warm)**: < 5 seconds (JSON fetch)
- **With cache (cold)**: ~30-60 seconds (server wakes up + scrapes)

## Free Tier Limitations

Render free tier:
- App "spins down" after 15 min of inactivity
- Takes ~30 sec to wake up on first request
- 750 hours/month (enough for hobby use)

If you update 2x daily:
- Cold start: ~1 minute (server wakes + scrapes)
- Still **10x faster** than Playwright on Pi!

## Troubleshooting

**API returns 404**:
- Server might be sleeping, try again in 30 seconds
- Check URL is correct (no trailing slash)

**Forecast data is stale**:
- Cache updates every 6 hours automatically
- To force update, restart the Render service

**Server not responding**:
- Free tier has monthly limits
- Check Render dashboard for errors
- Logs available in Render dashboard

## Cost Estimate

**Free tier**: $0/month (perfect for this use case)

If you upgrade later:
- **Starter**: $7/month (always-on, no cold starts)
- Still cheaper than running a VPS!

## Next Steps

1. Deploy cache server on Render
2. Copy updated `main.py` and `nwac_client.py` to Pi
3. Test with: `python main.py --once --cache-api "YOUR_URL"`
4. Once working, add to cron/systemd with env variable
