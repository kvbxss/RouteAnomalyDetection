# Mapbox Setup Guide

## Why You Need This

The interactive map component uses Mapbox GL JS to display flight routes and anomaly markers. You need a **free** Mapbox access token to use it.

## Quick Setup (5 minutes)

### Step 1: Get a Free Mapbox Token

1. Go to https://account.mapbox.com/access-tokens/
2. Sign up for a free account (no credit card required)
3. Copy your default public token (or create a new one)

**Free tier includes:**
- 50,000 free map loads per month
- More than enough for development and small projects

### Step 2: Configure Your Token

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Create a `.env.local` file:
   ```bash
   # On Windows:
   copy .env.example .env.local

   # On Mac/Linux:
   cp .env.example .env.local
   ```

3. Edit `.env.local` and add your token:
   ```env
   VITE_MAPBOX_TOKEN=pk.eyJ1IjoieW91ci11c2VybmFtZSIsImEiOiJjbHh4eHh4eHgifQ.your_token_here
   ```

### Step 3: Restart the Dev Server

If the frontend is already running, restart it:

```bash
# Stop the current server (Ctrl+C)
# Then restart:
npm run dev
```

The map should now load correctly!

## Troubleshooting

### Map still shows "Mapbox Token Required"

- Make sure `.env.local` is in the `frontend/` directory
- Check that the file is named exactly `.env.local` (not `.env.local.txt`)
- Verify your token starts with `pk.` (public token)
- Restart the dev server after creating/editing `.env.local`

### Map shows blank/dark area

- Open browser DevTools (F12) → Console tab
- Look for Mapbox-related errors
- Common issues:
  - Invalid token format
  - Token from wrong Mapbox account
  - Network/firewall blocking mapbox.com

### How to verify it's working

1. Open browser DevTools (F12)
2. Go to Network tab
3. Filter by "mapbox"
4. You should see successful requests to `api.mapbox.com`

## What the Map Shows

Once configured, the interactive map displays:

- **Color-coded anomaly markers** (click to view flight details)
  - 🔴 Red: Altitude anomalies
  - 🟠 Orange: Speed anomalies
  - 🟡 Yellow: Route deviations
  - 🔵 Blue: Temporal anomalies
  - 🟣 Purple: Combined anomalies

- **Flight routes** as blue lines
- **Start/end markers** in green/red
- **Interactive popups** with anomaly confidence
- **Map legend** showing anomaly type colors

## Security Notes

- `.env.local` is gitignored (not committed to repository)
- Public Mapbox tokens are safe to use in frontend code
- The token is restricted to your domain in production
- Free tier has rate limits to prevent abuse

## Alternative: Skip Mapbox (Not Recommended)

If you absolutely cannot use Mapbox, the dashboard will still work, but:
- ❌ No interactive map visualization
- ✅ Flight and anomaly data tables still work
- ✅ Statistics and charts still work
- ✅ Flight detail modals still work

However, the map is a key feature for visualizing spatial anomalies, so we strongly recommend setting it up.

## Need Help?

Check the Mapbox documentation:
- Getting started: https://docs.mapbox.com/help/getting-started/
- Access tokens: https://docs.mapbox.com/help/getting-started/access-tokens/
- Troubleshooting: https://docs.mapbox.com/help/troubleshooting/
