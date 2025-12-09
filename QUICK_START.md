# Quick Start Commands

## Local Development

### First Time Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser  # Create admin user

# Frontend
cd ../frontend
npm install
```

### Create .env.local for Frontend

```bash
cd frontend
```

Create `frontend/.env.local` file:
```env
VITE_MAPBOX_TOKEN=your_mapbox_token_here
VITE_API_BASE=http://127.0.0.1:8000
```

Get Mapbox token: https://account.mapbox.com/access-tokens/

### Run Development Servers

**Terminal 1 - Backend:**
```bash
cd backend
python manage.py runserver
```
Backend runs on: http://127.0.0.1:8000

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```
Frontend runs on: http://localhost:5173

**Terminal 3 - Optional: Run Tests**
```bash
cd backend
python manage.py test
```

---

## Deploy to Production

### Option 1: Railway + Vercel (Recommended)

**See `DEPLOY_NOW.md` for full walkthrough.**

Quick steps:
1. Push code to GitHub ✓ (already done)
2. Railway: New Project → Deploy from GitHub
3. Railway: Add PostgreSQL database
4. Railway: Set environment variables (DEBUG=False, SECRET_KEY)
5. Vercel: Import project from GitHub
6. Vercel: Set env vars (VITE_API_BASE, VITE_MAPBOX_TOKEN)
7. Done! Your app is live

---

## Common Commands

### Backend (Django)

```bash
# Database migrations
python manage.py makemigrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Run tests
python manage.py test

# Check for issues
python manage.py check

# Django shell
python manage.py shell

# Collect static files (production)
python manage.py collectstatic

# View all routes
python manage.py show_urls  # if django-extensions installed
```

### Frontend (React + Vite)

```bash
# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint

# Type check
npm run tsc
```

### Git

```bash
# Check status
git status

# Stage changes
git add .

# Commit
git commit -m "Your message"

# Push to GitHub
git push origin fix_frontend

# Pull latest changes
git pull origin fix_frontend

# Create new branch
git checkout -b feature-name
```

---

## Testing the App

### 1. Start Servers

Start both backend and frontend as described above.

### 2. Login

- Visit http://localhost:5173
- Login with admin credentials

### 3. Upload Flight Data

- Go to "Flights" page
- Click "Choose File" and select a CSV file
- Click "Upload and Process"

CSV format example:
```csv
flight_id,icao24,departure_airport,arrival_airport,first_seen,last_seen,latitude,longitude,altitude,speed
FLIGHT_1,abc123,KJFK,KLAX,2024-01-01T10:00:00,2024-01-01T14:00:00,40.6413,-73.7781,35000,500
```

### 4. Train ML Model

- Go to "Anomaly Detection" page
- Select contamination level (10% balanced)
- Click "Train Model"
- Wait for success message

### 5. Run Detection

- Click "Run Detection"
- View detected anomalies in the table
- See statistics dashboard
- Click "View" to see flight details

### 6. View on Map

- Go to "Dashboard"
- See anomalies plotted on map
- Click markers to open flight details
- Interactive legend shows anomaly types

---

## Troubleshooting

### Backend Issues

**Port already in use:**
```bash
# Find process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <process_id> /F

# Mac/Linux:
lsof -ti:8000 | xargs kill -9
```

**Database locked:**
```bash
# Delete database and recreate
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

**Module not found:**
```bash
pip install -r requirements.txt
```

### Frontend Issues

**Port already in use:**
- Vite will automatically use next available port (5174, 5175, etc.)

**Dependencies error:**
```bash
rm -rf node_modules package-lock.json
npm install
```

**Build errors:**
```bash
npm run build
# Check error messages and fix
```

**Map not loading:**
- Check `frontend/.env.local` exists
- Verify VITE_MAPBOX_TOKEN is set
- Restart dev server after adding .env.local

---

## Environment Variables

### Backend (Production - Railway)

```env
DEBUG=False
SECRET_KEY=<generate-random-50-char-string>
DATABASE_URL=<auto-provided-by-railway>
ALLOWED_HOSTS=.railway.app
CORS_ALLOWED_ORIGINS=https://your-app.vercel.app
```

### Frontend (Production - Vercel)

```env
VITE_API_BASE=https://your-app.up.railway.app
VITE_MAPBOX_TOKEN=<your-mapbox-token>
```

---

## Project Structure

```
RouteAnomalyDetection/
├── backend/                 # Django REST API
│   ├── core/               # Django settings
│   ├── flights/            # Main app
│   │   ├── models.py       # Database models
│   │   ├── views.py        # API endpoints
│   │   ├── ml_pipeline.py  # ML anomaly detection
│   │   └── tests/          # 112 tests
│   ├── manage.py
│   └── requirements.txt
├── frontend/               # React + Vite
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Dashboard, Flights, Anomalies
│   │   ├── lib/            # API client, utilities
│   │   └── App.tsx
│   ├── package.json
│   └── .env.local          # Create this file!
├── DEPLOY_NOW.md           # Deployment walkthrough
├── DEPLOYMENT_GUIDE.md     # Alternative deployments
└── README.md
```

---

## Quick Links

- **Mapbox Tokens**: https://account.mapbox.com/access-tokens/
- **Railway**: https://railway.app
- **Vercel**: https://vercel.com
- **Django Docs**: https://docs.djangoproject.com/
- **React Docs**: https://react.dev
- **Vite Docs**: https://vitejs.dev

---

## Next Steps

1. ✅ Run locally and test
2. ✅ Follow DEPLOY_NOW.md to deploy
3. ✅ Share your live URL
4. 📝 Add to your portfolio
5. 💼 Include in resume/LinkedIn

Good luck! 🚀
