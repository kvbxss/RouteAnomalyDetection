# Route Anomaly Detection

A full‑stack system for ingesting ADS‑B flight data, detecting route anomalies with machine learning, and visualizing results on an interactive map.

## Features

- Backend (Django + DRF)
  - Flight, AnomalyDetection, DataSource models
  - CSV ingestion endpoint with validation and normalization
  - ML pipeline (Isolation Forest) with training and detection endpoints
  - OpenAPI/Swagger docs
- Frontend (React + Vite + TypeScript)
  - Modern UI with shadcn/ui and Tailwind CSS v4
  - Mapbox GL JS flight map
  - CSV upload, Train Model, Run Detection quick actions
  - React Query for data fetching/state

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ (Node 20 LTS recommended)
- Mapbox account/token (for map visualization)

### Backend
```bash
# From project root
cd backend
python -m venv venv
# Windows PowerShell (if execution policy blocks activation, run PS as admin):
#   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
#   & .\venv\Scripts\Activate.ps1
# Or cmd:
#   .\venv\Scripts\activate.bat

python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

- API root: `http://127.0.0.1:8000/api/`
- Swagger: `http://127.0.0.1:8000/swagger/`

### Frontend
```bash
# In another terminal, from project root
cd frontend
npm i
# Environment (create a file frontend/.env.local)
# VITE_API_BASE=http://127.0.0.1:8000
# VITE_MAPBOX_TOKEN=pk.your_mapbox_access_token_here
npm run dev
```
- App: `http://localhost:5173`

## Core Endpoints (Backend)

- Flights
  - `GET /api/flights/` (list)
  - `POST /api/flights/upload_csv/` (multipart form) – field name: `file`
- Anomalies
  - `POST /api/anomalies/train_model/`
    - body: `{ "contamination"?: number, "flight_limit"?: number, "save_model"?: boolean }`
  - `POST /api/anomalies/detect_anomalies/`
    - body: `{ "flight_ids"?: string[], "retrain"?: boolean }`
- Data Sources
  - `GET /api/data-sources/`

## Frontend Pages
- Dashboard – quick actions (Upload Flight Data, Train Model, Run Detection)
- Flights – CSV upload & filters (WIP wiring to list)
- Anomalies – filters and model controls (WIP wiring to list)
- Map – Mapbox GL route visualization
- Chatbot – UI scaffold (RAG wiring planned)

## ML Pipeline (Management Commands)

From `backend/`:
```bash
# Train the model
python manage.py train_anomaly_model --contamination 0.15 --save-model

# Detect anomalies (trains if no model loaded)
python manage.py detect_anomalies --min-confidence 0.8
```

## Configuration

- CORS (dev): allows `http://localhost:5173`
- Auth: DRF JWT packages present; dev mode defaults to permissive `AllowAny` for ease of local development
- Logging: file `backend/logs/django.log` and console

## Development Notes

- Tailwind CSS v4
  - PostCSS plugin: `@tailwindcss/postcss`
  - Import order: `@import "tailwindcss";` must be first in `src/index.css`
- shadcn/ui
  - Component tokens map to Tailwind CSS v4 color variables declared in `src/index.css`
- Vite
  - Use Node 18+; if you see crypto/hash errors, align Vite/Node versions (project uses Vite 5)

## Troubleshooting

- PowerShell virtualenv activation blocked
  - Open PowerShell as admin and run:
    ```powershell
    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
    ```
- Vite CSS error `@import must precede all other statements`
  - Ensure `@import "tailwindcss";` is the first line in `frontend/src/index.css`
- Map not rendering
  - Set `VITE_MAPBOX_TOKEN` in `frontend/.env.local`
- CORS/Network errors
  - Confirm backend is running at `http://127.0.0.1:8000` and `VITE_API_BASE` matches

## Project Scripts

- Backend
  - `python manage.py migrate`
  - `python manage.py runserver 8000`
  - `python manage.py train_anomaly_model ...`
  - `python manage.py detect_anomalies ...`
- Frontend
  - `npm run dev`
  - `npm run build`
  - `npm run preview`

## Roadmap
- Wire flights/anomalies lists in UI
- Show anomalies as overlays on Mapbox (points/lines)
- Auth (JWT) enablement and protected routes
- Docker compose for full stack
- RAG chatbot backend and vector DB integration

## License
MIT (see `LICENSE` if present).
