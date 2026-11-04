"""Team app skeleton: browser (HTML/JS) -> Flask (this file) -> Postgres.

Data: our crew-hiring survey (survey_data.csv) — producers rating the crew they hired.

Routes
  GET  /                   the page (templates/index.html)
  GET  /api/productions    productions in the database
  GET  /api/roles          crew roles (fills the dropdown on the page)
  GET  /api/role-stats     "model" #1: per-role averages computed in SQL
  POST /api/recommend      "model" #2: takes user input (a crew role) and returns which
                           sourcing channels found the best hires for it — placeholder logic
  GET  /health             liveness check (also confirms the database answers)
"""
import os

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()  # local development only; on Railway the variable comes from the Variables tab

app = Flask(__name__)


def get_conn():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)


def query(sql, params=None):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def numeric(rows):
    """Postgres ROUND() returns Decimal; make every row JSON-friendly."""
    return [{k: (float(v) if hasattr(v, "as_tuple") else v) for k, v in r.items()} for r in rows]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/productions")
def productions():
    rows = query(
        """
        SELECT p.name, p.production_type, p.respondent_role, p.shoot_days, p.total_shoot_hours,
               COUNT(h.hire_id) AS positions_rated
        FROM productions p
        LEFT JOIN hires h ON h.production_id = p.production_id
        GROUP BY p.production_id
        ORDER BY p.name
        """
    )
    return jsonify(rows)


@app.route("/api/roles")
def roles():
    return jsonify([r["role_name"] for r in query("SELECT role_name FROM crew_roles ORDER BY role_name")])


@app.route("/api/role-stats")
def role_stats():
    rows = query(
        """
        SELECT r.role_name,
               COUNT(*)                                                     AS hires,
               ROUND(AVG(h.ease_of_finding)::numeric, 1)                    AS avg_ease,
               ROUND(AVG(h.performance)::numeric, 1)                        AS avg_performance,
               ROUND(100.0 * AVG(CASE WHEN h.would_hire_again THEN 1 ELSE 0 END), 0) AS rehire_pct,
               ROUND(100.0 * AVG(CASE WHEN h.flaked_24_48h   THEN 1 ELSE 0 END), 0) AS flake_pct
        FROM hires h
        JOIN crew_roles r ON r.role_id = h.role_id
        GROUP BY r.role_name
        ORDER BY avg_ease, r.role_name          -- hardest-to-find roles first
        """
    )
    return jsonify(numeric(rows))


@app.route("/api/recommend", methods=["POST"])
def recommend():
    """Placeholder model: for the chosen role, rank sourcing channels by the hires they produced.

    score = average performance of hires found through the channel (ties -> more hires first)
    Swap this function out for the real analysis later; the request/response shape stays the same.
    """
    data = request.get_json(silent=True) or {}
    role = (data.get("role") or "").strip()
    found = query("SELECT role_id FROM crew_roles WHERE role_name = %s", (role,))
    if not found:
        return jsonify({"error": "unknown role — pick one from the list"}), 400
    role_id = found[0]["role_id"]

    summary = numeric(query(
        """
        SELECT COUNT(*) AS hires,
               ROUND(AVG(ease_of_finding)::numeric, 1) AS avg_ease,
               ROUND(AVG(performance)::numeric, 1)     AS avg_performance
        FROM hires WHERE role_id = %s
        """,
        (role_id,),
    ))[0]
    channels = numeric(query(
        """
        SELECT c.channel_name,
               COUNT(*)                                  AS hires,
               ROUND(AVG(h.performance)::numeric, 1)     AS avg_performance,
               ROUND(AVG(h.ease_of_finding)::numeric, 1) AS avg_ease,
               BOOL_AND(h.would_hire_again)              AS always_rehired
        FROM hires h
        JOIN hire_channels hc ON hc.hire_id = h.hire_id
        JOIN sourcing_channels c ON c.channel_id = hc.channel_id
        WHERE h.role_id = %s
        GROUP BY c.channel_name
        ORDER BY avg_performance DESC, hires DESC, c.channel_name
        """,
        (role_id,),
    ))
    return jsonify({"role": role, "summary": summary, "channels": channels})


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
