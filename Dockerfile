FROM python:3.10-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway provides PORT. On first deploy, load survey_data.csv into Postgres (skipped once loaded),
# then start the web server on 0.0.0.0:$PORT.
CMD ["sh", "-c", "python deploy_db.py --if-empty && gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 app:app"]
