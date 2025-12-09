# Deployment Guide - Flight Route Anomaly Detection

This guide covers multiple deployment options for showcasing your app to others.

---

## Quick Demo Options (5-15 minutes)

### Option 1: Vercel (Frontend) + Railway (Backend) ⭐ RECOMMENDED

**Pros:** Free tier, automatic HTTPS, fastest deployment, no server management
**Cons:** Limited to free tier resources

#### Step 1: Deploy Backend to Railway

1. **Sign up at https://railway.app** (free with GitHub)

2. **Create New Project:**
   - Click "New Project" → "Deploy from GitHub repo"
   - Or use Railway CLI:
     ```bash
     npm install -g @railway/cli
     railway login
     railway init
     railway up
     ```

3. **Configure Environment:**
   - Go to your project → Variables
   - Add these variables:
     ```
     DEBUG=False
     SECRET_KEY=generate-random-string-here
     ALLOWED_HOSTS=*.railway.app
     DATABASE_URL=<Railway will auto-provide PostgreSQL>
     ```

4. **Add PostgreSQL Database:**
   - In Railway dashboard: "+ New" → "Database" → "PostgreSQL"
   - Railway automatically links it to your app

5. **Deploy:**
   - Railway auto-detects Django
   - Build: `pip install -r requirements.txt`
   - Start: `python manage.py migrate && gunicorn core.wsgi`
   - Copy your Railway URL (e.g., `https://your-app.railway.app`)

#### Step 2: Deploy Frontend to Vercel

1. **Sign up at https://vercel.com** (free with GitHub)

2. **Deploy:**
   ```bash
   cd frontend
   npm install -g vercel
   vercel login
   vercel
   ```

3. **Configure Environment Variables:**
   - In Vercel dashboard → Your Project → Settings → Environment Variables
   - Add:
     ```
     VITE_API_BASE=https://your-app.railway.app
     VITE_MAPBOX_TOKEN=your_mapbox_token
     ```

4. **Redeploy:**
   ```bash
   vercel --prod
   ```

5. **Done!** Your app is live at `https://your-project.vercel.app`

---

### Option 2: Render.com (Full Stack)

**Pros:** One platform for everything, free tier, auto-deploy from Git
**Cons:** Free tier sleeps after 15 min inactivity (slow cold starts)

1. **Go to https://render.com** → Sign up

2. **Deploy Backend:**
   - "New" → "Web Service"
   - Connect your GitHub repo
   - Settings:
     - Name: `flight-anomaly-backend`
     - Root Directory: `backend`
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn core.wsgi:application --bind 0.0.0.0:$PORT`
   - Environment:
     ```
     PYTHON_VERSION=3.11
     DEBUG=False
     SECRET_KEY=your-secret-key
     ```

3. **Add PostgreSQL:**
   - "New" → "PostgreSQL"
   - Copy the Internal Database URL
   - Add to backend environment: `DATABASE_URL=<internal-url>`

4. **Deploy Frontend:**
   - "New" → "Static Site"
   - Root Directory: `frontend`
   - Build Command: `npm install && npm run build`
   - Publish Directory: `dist`
   - Environment:
     ```
     VITE_API_BASE=https://your-backend.onrender.com
     VITE_MAPBOX_TOKEN=your_mapbox_token
     ```

---

## Production Deployment (1-2 hours)

### Option 3: DigitalOcean/AWS/GCP with Docker

**Pros:** Full control, scalable, production-ready
**Cons:** Requires server management, costs money

#### Prerequisites:
- Docker & Docker Compose installed
- Cloud VM (DigitalOcean Droplet, AWS EC2, GCP Compute Engine)
- Domain name (optional but recommended)

#### Step 1: Prepare Docker Files

1. **Create `backend/Dockerfile`:**
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       postgresql-client \
       && rm -rf /var/lib/apt/lists/*

   # Install Python dependencies
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt gunicorn

   # Copy application
   COPY . .

   # Collect static files
   RUN python manage.py collectstatic --noinput || true

   EXPOSE 8000

   CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
   ```

2. **Create `frontend/Dockerfile`:**
   ```dockerfile
   # Build stage
   FROM node:18-alpine AS builder

   WORKDIR /app
   COPY package*.json ./
   RUN npm ci

   COPY . .
   ARG VITE_API_BASE
   ARG VITE_MAPBOX_TOKEN
   ENV VITE_API_BASE=$VITE_API_BASE
   ENV VITE_MAPBOX_TOKEN=$VITE_MAPBOX_TOKEN

   RUN npm run build

   # Production stage
   FROM nginx:alpine
   COPY --from=builder /app/dist /usr/share/nginx/html
   COPY nginx.conf /etc/nginx/conf.d/default.conf
   EXPOSE 80
   CMD ["nginx", "-g", "daemon off;"]
   ```

3. **Create `frontend/nginx.conf`:**
   ```nginx
   server {
       listen 80;
       server_name _;

       root /usr/share/nginx/html;
       index index.html;

       location / {
           try_files $uri $uri/ /index.html;
       }

       location /api {
           proxy_pass http://backend:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

4. **Create `.env` file in root:**
   ```bash
   # Database
   DB_PASSWORD=your-secure-password

   # Django
   SECRET_KEY=your-secret-key-min-50-chars
   DEBUG=False
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

   # Frontend
   VITE_API_BASE=https://yourdomain.com/api
   VITE_MAPBOX_TOKEN=your_mapbox_token
   ```

#### Step 2: Deploy to Server

1. **SSH into your server:**
   ```bash
   ssh user@your-server-ip
   ```

2. **Install Docker:**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

3. **Clone your repo:**
   ```bash
   git clone https://github.com/yourusername/RouteAnomalyDetection.git
   cd RouteAnomalyDetection
   ```

4. **Create `.env` file** (see step 4 above)

5. **Deploy:**
   ```bash
   docker-compose up -d
   ```

6. **Setup SSL with Let's Encrypt (recommended):**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

---

## Local Network Demo (Immediate)

**For quick local showcases (same WiFi/network):**

1. **Find your local IP:**
   ```bash
   # Windows
   ipconfig | findstr IPv4

   # Mac/Linux
   ifconfig | grep inet
   ```

2. **Update Django allowed hosts:**
   ```python
   # backend/core/settings.py
   ALLOWED_HOSTS = ['localhost', '127.0.0.1', '192.168.1.X']  # Your local IP
   ```

3. **Update frontend API base:**
   ```bash
   # frontend/.env.local
   VITE_API_BASE=http://192.168.1.X:8000
   ```

4. **Run both servers:**
   ```bash
   # Terminal 1 - Backend
   cd backend
   python manage.py runserver 0.0.0.0:8000

   # Terminal 2 - Frontend
   cd frontend
   npm run dev -- --host
   ```

5. **Share the URL:**
   - Send: `http://192.168.1.X:5173` to anyone on your network
   - They can access it from their browser

---

## Tunneling Services (Quick External Access)

**For immediate external access without deployment:**

### ngrok (Recommended for demos)

1. **Install:** https://ngrok.com/download

2. **Run backend:**
   ```bash
   cd backend
   python manage.py runserver
   ```

3. **Expose backend:**
   ```bash
   ngrok http 8000
   ```
   Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

4. **Update frontend:**
   ```bash
   # frontend/.env.local
   VITE_API_BASE=https://abc123.ngrok.io
   ```

5. **Run frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

6. **Expose frontend:**
   ```bash
   ngrok http 5173
   ```

7. **Share the frontend ngrok URL** with your client!

**Note:** Free ngrok URLs change on restart. Paid plan gives permanent URLs.

---

## Pre-Deployment Checklist

Before deploying, ensure:

- [ ] All sensitive data in `.env` files (not hardcoded)
- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` generated
- [ ] CORS configured for your domain
- [ ] Mapbox token configured
- [ ] Database migrations applied
- [ ] Static files collected (`python manage.py collectstatic`)
- [ ] Create superuser for admin access
- [ ] Test locally first
- [ ] `.gitignore` includes `.env`, `*.pyc`, `node_modules/`, `dist/`

---

## Cost Comparison

| Option | Cost | Best For |
|--------|------|----------|
| **Vercel + Railway** | Free tier | Quick demos, portfolios |
| **Render.com** | Free tier | Simple full-stack apps |
| **DigitalOcean** | $5-10/mo | Production, learning DevOps |
| **AWS/GCP** | Pay-as-you-go | Enterprise, scale |
| **ngrok** | Free (temp URLs) | Quick demos, testing |
| **Local Network** | Free | Same-location demos |

---

## Recommended Approach

**For showcasing to someone:**

1. **Quick demo (today):** Use ngrok - 5 minutes setup
2. **Portfolio/interview:** Vercel + Railway - 15 minutes, free, permanent URL
3. **Production app:** DigitalOcean + Docker - Full control, scalable

Choose based on your timeline and requirements!

---

## Troubleshooting

### CORS Errors
Update `backend/core/settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend.vercel.app",
    "http://localhost:5173",
]
```

### Static Files Not Loading
```bash
cd backend
python manage.py collectstatic --noinput
```

### Database Connection Failed
Check `DATABASE_URL` environment variable format:
```
postgresql://user:password@host:port/database
```

### Build Fails
- Check Node.js version (need 18+)
- Check Python version (need 3.11+)
- Clear caches: `npm clean-install` or `pip cache purge`

---

## Need Help?

- **Vercel Docs:** https://vercel.com/docs
- **Railway Docs:** https://docs.railway.app
- **Render Docs:** https://render.com/docs
- **ngrok Docs:** https://ngrok.com/docs
