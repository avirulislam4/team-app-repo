# Crew Hiring App Skeleton — Flask + Postgres on Railway

A deployed end-to-end skeleton for the TECH-UB 24 team project (Group 7):

```
browser (templates/index.html, plain JS)  →  Flask (app.py)  →  Postgres on Railway
```

It runs on our own data — the producer survey in `survey_data.csv`, where student-film producers rate the crew they hired (ease of finding, performance, would hire again, flaking) and say where they found them. The content is placeholder: it exists to prove the plumbing works so the real analyses and UI can be plugged in later.

**Team:** Karen, Nicholas, Avirul, Adriana

## What's here

| File | Purpose |
|---|---|
| `survey_data.csv` | Our survey responses: one row per crew position hired on a production |
| `schema.sql` | Relational schema: `productions`, `crew_roles`, `sourcing_channels`, `hires`, plus bridge table `hire_channels` for the 0/1 sourcing-channel columns |
| `deploy_db.py` | Creates the schema and loads the CSV; prints row counts. `--if-empty` skips loading when data already exists |
| `app.py` | Flask backend: `/`, `/api/productions`, `/api/roles`, `/api/role-stats`, `POST /api/recommend`, `/health` |
| `templates/index.html` | Frontend: productions list + **Shuffle**, per-role stats, and a form that sends user input to the backend model |
| `Dockerfile` | `python:3.10-slim`; loads the data on first deploy, then runs `gunicorn --bind 0.0.0.0:$PORT app:app` |
| `.env.example` | Template for your local `.env` (the real `.env` is git-ignored) |

## Endpoints

| Route | What it does | Layer exercised |
|---|---|---|
| `GET /api/productions` | Productions from Postgres with how many positions each rated | backend → database |
| `GET /api/role-stats` | Per crew role: average ease of finding, performance, % rehired, % flaked | model computed in SQL |
| `POST /api/recommend` | Takes a crew role and ranks the sourcing channels by the performance of hires found through them | **user input → model → database** |
| `GET /health` | Confirms the app can reach the database | ops |

To plug in a real model, replace the body of `recommend()` (or add a new route) and call it from the page with `fetch()` — the request/response pattern is already wired.

## Run locally

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # put a Postgres connection string in .env
python deploy_db.py             # create tables + load the CSV
python app.py                   # http://localhost:5001
```

## Deploy (Railway)

1. Railway project with a **Postgres** service.
2. In the same project: **+ New → GitHub Repo →** this repo. Railway builds from the `Dockerfile`.
3. App service **Variables**: `DATABASE_URL` = `${{Postgres.DATABASE_URL}}` (private network).
4. **Settings → Networking → Generate Domain.**

On deploy the container runs `deploy_db.py --if-empty`, so the tables are created and loaded inside Railway's private network — no public database access is needed. To reload after changing the CSV, run `python deploy_db.py` against the database (or empty the `hires` table and redeploy).
