# Crew Hiring App Skeleton — Flask + Postgres on Railway

TECH-UB 24 · Group 7: Karen, Nicholas, Avirul, Adriana

A deployed 3-tier skeleton: **Browser (templates/index.html) → Flask (app.py) → Postgres on Railway**, built on our own dataset, `survey_data.csv` (student-film producers rating the crew they hired and where they found them). The content is placeholder: it proves the plumbing works so the real analyses and UI can be plugged in later.

## Files

| File | Purpose |
|---|---|
| `survey_data.csv` | Our raw dataset: one row per crew position hired on a production |
| `schema.sql` | Normalized schema: `productions`, `crew_roles`, `sourcing_channels`, `hires`, and bridge table `hire_channels` (the 11 multi-valued 0/1 sourcing-channel columns) |
| `deploy_db.py` | psycopg2 + python-dotenv loader: connects to `DATABASE_URL`, runs `schema.sql`, parses the CSV, populates the tables, prints row counts |
| `app.py` | Flask backend (reads `DATABASE_URL` via python-dotenv) |
| `templates/index.html` | Plain-JS frontend: fetches data on page load, **Shuffle Names** button reorders the list in the browser |
| `requirements.txt` | flask, psycopg2-binary, python-dotenv, gunicorn |
| `Dockerfile` | python:3.10-slim, installs requirements, runs gunicorn on `0.0.0.0:$PORT` |
| `.env.example` | Template for your local `.env` (the real `.env` is git-ignored and never committed) |

## Endpoints

| Route | What it does | Layer |
|---|---|---|
| `GET /` | Serves `templates/index.html` | frontend |
| `GET /api/productions` | Production names (and details) from Postgres as JSON | backend → database |
| `GET /api/role-stats` | Per crew role: avg ease of finding, performance, % rehired, % flaked | model in SQL |
| `POST /api/recommend` | Takes a crew role, ranks sourcing channels by the performance of hires found through them | user input → model → database |
| `GET /health` | Confirms the app can reach the database | ops |

## Step 0 — Workspace setup & Git protection

```bash
git init
python3 -m venv venv
source venv/bin/activate
echo ".env" >> .gitignore
echo "venv/" >> .gitignore
touch .env
git status          # .env must NOT be listed
```

## Step 1 — Database provisioning & schema

1. Railway → **+ New Project → Deploy PostgreSQL**.
2. Postgres card → **Add Public Access** → copy `DATABASE_PUBLIC_URL`.
3. In `.env`: `DATABASE_URL=<the DATABASE_PUBLIC_URL>`
4. `schema.sql` holds the CREATE TABLE statements (multi-valued columns split into bridge tables).

## Step 2 — Seed the database & run locally

```bash
source venv/bin/activate
pip install -r requirements.txt
python deploy_db.py     # creates tables, loads survey_data.csv, prints row counts
python app.py           # http://localhost:5000  → click "Shuffle Names"
```

(On a Mac, if port 5000 is taken by AirPlay Receiver, run `PORT=5001 python app.py`.)

## Step 3 — Docker & deploy to Railway

```bash
git status              # DOUBLE CHECK .env is NOT listed
git add .
git commit -m "Complete web application skeleton and dockerfile"
git push
```

1. In the **same Railway project** as Postgres: **+ New → GitHub Repo →** this repo.
2. Web service → **Variables**: `DATABASE_URL` = `${{Postgres.DATABASE_URL}}` (Railway's private network).
3. **Settings → Networking → Generate Domain.**

## Verification & submission checklist

- [x] Local security: `.env` was never committed to GitHub
- [x] Live database connection: the app loads records directly from Railway Postgres
- [x] Interactive UI: **Shuffle Names** reorders the list in the browser via JavaScript
- [x] Deployed public URL: https://team-app-repo-production.up.railway.app
- [x] Team repo: https://github.com/karenqhhan/group7_project
