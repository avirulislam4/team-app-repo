"""Team app skeleton: browser (HTML/JS) -> Flask (this file) -> Postgres.

Routes
  GET  /                    the page (templates/index.html)
  GET  /api/students        student names from Postgres
  GET  /api/skill-averages  "model" #1: average of the four skill ratings (computed in SQL)
  POST /api/match           "model" #2: takes user input (your four skill ratings) and returns
                            the classmates who best complement you — placeholder model logic
  GET  /health              liveness check (also confirms the database answers)
"""
import os

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()  # local development only; on Railway the variable comes from the Variables tab

app = Flask(__name__)
SKILLS = ["skill_programming", "skill_data_stats", "skill_frontend_design", "skill_business_pitch"]


def get_conn():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)


def query(sql, params=None):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/students")
def students():
    rows = query("SELECT name FROM students ORDER BY name")
    return jsonify([r["name"] for r in rows])


@app.route("/api/skill-averages")
def skill_averages():
    row = query(
        """
        SELECT ROUND(AVG(skill_programming)::numeric, 2)     AS programming,
               ROUND(AVG(skill_data_stats)::numeric, 2)      AS data_stats,
               ROUND(AVG(skill_frontend_design)::numeric, 2) AS frontend_design,
               ROUND(AVG(skill_business_pitch)::numeric, 2)  AS business_pitch,
               COUNT(*)                                      AS n
        FROM students
        """
    )[0]
    return jsonify({k: float(v) if k != "n" else int(v) for k, v in row.items()})


@app.route("/api/match", methods=["POST"])
def match():
    """Placeholder model: score each classmate by how much they add where you are weaker.

    complement score = sum over skills of max(0, their_rating - your_rating)
    Swap this function out for the real analysis later; the request/response shape stays the same.
    """
    data = request.get_json(silent=True) or {}
    try:
        mine = [int(data.get(k, 3)) for k in ("programming", "data_stats", "frontend_design", "business_pitch")]
    except (TypeError, ValueError):
        return jsonify({"error": "ratings must be whole numbers 1-5"}), 400
    if not all(1 <= v <= 5 for v in mine):
        return jsonify({"error": "ratings must be between 1 and 5"}), 400

    rows = query(
        f"""
        SELECT s.name, {", ".join("s." + k for k in SKILLS)},
               GREATEST(s.skill_programming     - %s, 0)
             + GREATEST(s.skill_data_stats      - %s, 0)
             + GREATEST(s.skill_frontend_design - %s, 0)
             + GREATEST(s.skill_business_pitch  - %s, 0) AS complement_score,
               COALESCE(STRING_AGG(DISTINCT t.tool_name, ', '), '') AS tools
        FROM students s
        LEFT JOIN student_tools st ON st.student_id = s.student_id
        LEFT JOIN tools t ON t.tool_id = st.tool_id
        GROUP BY s.student_id
        ORDER BY complement_score DESC, s.name
        LIMIT 3
        """,
        mine,
    )
    return jsonify(rows)


@app.route("/health")
def health():
    try:
        query("SELECT 1 AS ok")
        return jsonify({"status": "ok", "database": "connected"})
    except Exception as exc:  # noqa: BLE001 - surface the reason in the health check
        return jsonify({"status": "error", "database": str(exc)}), 500


if __name__ == "__main__":
    # Local run: python app.py  ->  http://localhost:5001
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)), debug=True)
