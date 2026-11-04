# Team App Skeleton — Flask + Postgres on Railway

A deployed end-to-end skeleton for the TECH-UB 24 team project:

```
browser (templates/index.html, plain JS)  →  Flask (app.py)  →  Postgres on Railway
```

It exists to prove the plumbing works so real analyses and UI can be plugged in later.

**Team:** Karen, Nicholas, Avirul, Adriana

## What's here

| File | Purpose |
|---|---|
| `class_dataset.csv` | Student intake responses — **kept out of the repo** (classmates' personal info). Each teammate keeps their own copy locally |
| `schema.sql` | Relational schema: `students`, `tools`, `availability_slots`, plus bridge tables `student_tools` and `student_availability` for the multi-valued `tools` / `availability` columns |
| `deploy_db.py` | Creates the schema and loads the CSV; prints row counts. `--if-empty` skips loading when data already exists |
| `app.py` | Flask backend: `/`, `/api/students`, `/api/skill-averages`, `POST /api/match`, `/health` |
| `templates/index.html` | Frontend: name list + **Shuffle Names**, skill averages, and a form that sends user input to the backend model |
| `Dockerfile` | `python:3.10-slim`; runs `gunicorn --bind 0.0.0.0:$PORT app:app` |
| `hello.py` | Earlier Git/GitHub workflow exercise (each member added their name via a pull request) |
| `.env.example` | Template for your local `.env` (the real `.env` is git-ignored) |

## Endpoints

| Route | What it does | Layer exercised |
|---|---|---|
| `GET /api/students` | Names from Postgres | backend → database |
| `GET /api/skill-averages` | `AVG()` of the four skill ratings across all students | model computed in SQL |
| `POST /api/match` | Takes your 4 self-ratings and returns the 3 classmates who complement you most (`Σ max(0, theirs − yours)`) | **user input → model → database** |
| `GET /health` | Confirms the app can reach the database | ops |

To plug in a real model, replace the body of `match()` (or add a new route) and call it from the page with `fetch()` — the request/response pattern is already wired.

## Run locally

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # paste Railway's DATABASE_PUBLIC_URL into .env
# put class_dataset.csv in this folder (not committed)
python deploy_db.py             # create tables + load the CSV into Railway Postgres
python app.py                   # http://localhost:5001
```

## Deploy (Railway)

1. Railway project with a **Postgres** service.
2. In the same project: **+ New → GitHub Repo →** this repo. Railway builds from the `Dockerfile`.
3. App service **Variables**: `DATABASE_URL` = `${{Postgres.DATABASE_URL}}` (private network).
4. **Settings → Networking → Generate Domain.**

The database is loaded once from a laptop with `python deploy_db.py` (using the public URL in `.env`); the deployed app only reads from it.
