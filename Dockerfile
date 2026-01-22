FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app


COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

RUN python manage.py collectstatic --noinput || true

ENV PORT=8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py create_default_admin && gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120"]

