# Deploy to Railway + Vercel - Step by Step

Follow these steps to deploy your Flight Route Anomaly Detection app.

---

## Part 1: Deploy Backend to Railway (10 minutes)

### Step 1: Sign Up for Railway

1. Go to https://railway.app
2. Click "Login" → "Login with GitHub"
3. Authorize Railway to access your GitHub

### Step 2: Create New Project

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose **kvbxss/RouteAnomalyDetection**
4. Railway will start deploying automatically

### Step 3: Add PostgreSQL Database

1. In your project dashboard, click "+ New"
2. Select "Database" → "Add PostgreSQL"
3. Railway automatically creates a database and links it to your app
4. The `DATABASE_URL` environment variable is auto-populated

### Step 4: Configure Environment Variables

1. Click on your backend service
2. Go to "Variables" tab
3. Add these variables (click "+ New Variable"):

```
DEBUG=False
SECRET_KEY=<generate-random-50-char-string>
DJANGO_ENV=production
```

To generate a secure SECRET_KEY, run in terminal:
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### Step 5: Wait for Deployment

1. Go to "Deployments" tab
2. Wait for build to complete (~3-5 minutes)
3. Once deployed, you'll see "Success ✓"
4. Click "Settings" → "Networking" → "Generate Domain"
5. **Copy your Railway URL** (e.g., `https://your-app.up.railway.app`)

### Step 6: Create Admin User

**Option A: Using Railway CLI (Recommended)**

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Login to Railway:
```bash
railway login
```

3. Link to your project:
```bash
cd d:/RouteAnomalyDetection
railway link
```
Select your project from the list

4. Open shell and create admin:
```bash
railway run python backend/manage.py createsuperuser
```

5. Enter username: `admin`
6. Enter password: `admin123` (or your choice)
7. Skip email (press Enter)

**Option B: Using Railway Dashboard**

1. In Railway, click on your backend service
2. Look for the three dots menu (⋮) at the top right
3. Select "Open Shell" or find it in the service menu
4. In the shell, run:
```bash
cd backend
python manage.py createsuperuser
```
5. Enter username: `admin`
6. Enter password: `admin123` (or your choice)

**Option C: Create via Django Admin After First Deploy**

You can also create the admin user later:
1. Visit `https://your-app.railway.app/admin/`
2. Use Railway shell (Options A or B above) to create user
3. Or use the frontend to register first user

---

## Part 2: Deploy Frontend to Vercel (5 minutes)

### Step 1: Sign Up for Vercel

1. Go to https://vercel.com
2. Click "Sign Up" → "Continue with GitHub"
3. Authorize Vercel

### Step 2: Import Project

1. Click "Add New..." → "Project"
2. Find **RouteAnomalyDetection** repository
3. Click "Import"

### Step 3: Configure Build Settings

Vercel should auto-detect, but verify:

- **Framework Preset**: Vite
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`

### Step 4: Add Environment Variables

**IMPORTANT:** Click "Environment Variables" and add:

1. **Variable Name**: `VITE_API_BASE`
   **Value**: `https://your-app.up.railway.app` (your Railway URL from Part 1)

2. **Variable Name**: `VITE_MAPBOX_TOKEN`
   **Value**: Your Mapbox token (get from https://account.mapbox.com/access-tokens/)

   To get Mapbox token:
   - Go to https://account.mapbox.com/access-tokens/
   - Sign up for free (no credit card needed)
   - Copy your "Default public token"

### Step 5: Deploy

1. Click "Deploy"
2. Wait 2-3 minutes for build
3. Once complete, you'll see "Congratulations!"
4. **Copy your Vercel URL** (e.g., `https://your-app.vercel.app`)

### Step 6: Update Railway CORS (IMPORTANT)

1. Go back to Railway
2. Click your backend service → "Variables"
3. Add new variable:
   - **Name**: `CORS_ALLOWED_ORIGINS`
   - **Value**: `https://your-app.vercel.app` (your Vercel URL)
4. Redeploy: Settings → Redeploy

---

## Part 3: Test Your Deployment

### Test Backend

1. Visit: `https://your-app.up.railway.app/api/flights/`
2. You should see JSON response (likely empty array)
3. Visit: `https://your-app.up.railway.app/admin/`
4. Login with admin credentials you created
5. ✅ Backend working!

### Test Frontend

1. Visit: `https://your-app.vercel.app`
2. You should see the login page
3. Login with admin credentials
4. Upload sample flight data (CSV)
5. Run anomaly detection
6. View results on map
7. ✅ Full app working!

---

## Troubleshooting

### Backend Issues

**500 Error / Application Error:**
- Check Railway logs: Click service → "Deployments" → Latest → "View Logs"
- Common issues:
  - Missing SECRET_KEY variable
  - Database connection failed
  - Migration not run

**Fix:**
```bash
# In Railway shell:
cd backend
python manage.py migrate
python manage.py createsuperuser
```

### Frontend Issues

**Map not loading:**
- Check browser console (F12)
- Verify VITE_MAPBOX_TOKEN is set in Vercel
- Redeploy after adding env vars

**API calls failing (CORS errors):**
- Verify CORS_ALLOWED_ORIGINS in Railway includes your Vercel URL
- Check VITE_API_BASE is correct Railway URL
- Redeploy both services

**"Failed to fetch" errors:**
- Check Railway backend is running (green status)
- Verify VITE_API_BASE has no trailing slash
- Test backend URL directly in browser

---

## Post-Deployment Checklist

- [ ] Backend deployed on Railway
- [ ] PostgreSQL database created and linked
- [ ] Admin user created
- [ ] Frontend deployed on Vercel
- [ ] Mapbox token configured
- [ ] CORS configured for Vercel domain
- [ ] Can login to app
- [ ] Can upload CSV data
- [ ] Can run anomaly detection
- [ ] Map displays correctly
- [ ] Flight details modal works

---

## Your URLs

Save these for reference:

- **Frontend**: `https://your-app.vercel.app`
- **Backend API**: `https://your-app.up.railway.app`
- **Admin Panel**: `https://your-app.up.railway.app/admin/`

---

## Updating Your App

**After making code changes:**

1. Push to GitHub:
```bash
git add .
git commit -m "Your changes"
git push origin fix_frontend
```

2. **Railway**: Auto-deploys from GitHub (takes ~3 min)
3. **Vercel**: Auto-deploys from GitHub (takes ~2 min)

Both services have automatic deployments enabled!

---

## Free Tier Limits

**Railway:**
- $5 free credit/month
- Enough for hobby projects
- Sleeps after 30 min inactivity (wakes on request)

**Vercel:**
- 100 deployments/month
- 100GB bandwidth/month
- Perfect for demos and portfolios

---

## Need Help?

Common commands:

**Railway Shell:**
```bash
# View logs
railway logs

# Run migrations
cd backend && python manage.py migrate

# Create superuser
cd backend && python manage.py createsuperuser

# Collect static files
cd backend && python manage.py collectstatic --noinput
```

**Vercel CLI:**
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy from terminal
cd frontend
vercel

# View logs
vercel logs
```

---

## Success! 🎉

Your Flight Route Anomaly Detection app is now live and accessible to anyone with the URL!

Share your Vercel URL with:
- Potential employers
- Friends and colleagues
- In your portfolio
- On LinkedIn
- In your resume

The app will stay online 24/7 (with Railway sleep on inactivity, wakes instantly on request).
