"""Create the schema and load survey_data.csv into Postgres.

Usage:
    python deploy_db.py              # rebuild tables and reload the CSV
    python deploy_db.py --if-empty   # only load when the database has no hires yet (used on deploy)

Reads DATABASE_URL from the environment (or from a local .env file).
"""
import csv
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
CSV_PATH = HERE / "survey_data.csv"
SCHEMA_PATH = HERE / "schema.sql"

# The 0/1 columns in the CSV that say where the hire was found.
CHANNEL_COLUMNS = [
    "Tisch Database", "Instagram ISOs", "Facebook Groups", "Other Social Media", "Backstage", "Apps",
    "Cold Email / Pitching", "WOM / Peer Recommendations", "Classmates", "Already Know", "Already Worked With",
]
FLAKE_COLUMN = "Cancelled/flaked 24-48h (for anyone hired in this position)"


def to_int(value):
    value = (value or "").strip()
    return int(value) if value.isdigit() else None


def to_bool(value):
    value = (value or "").strip().upper()
    return {"Y": True, "YES": True, "N": False, "NO": False}.get(value)


def hires_exist(cur):
    cur.execute("SELECT to_regclass('public.hires')")
    if cur.fetchone()[0] is None:
        return False
    cur.execute("SELECT COUNT(*) FROM hires")
    return cur.fetchone()[0] > 0


def get_or_create(cur, cache, table, id_col, name_col, name):
    if name not in cache:
        cur.execute(f"INSERT INTO {table} ({name_col}) VALUES (%s) RETURNING {id_col}", (name,))
        cache[name] = cur.fetchone()[0]
    return cache[name]


def load(conn):
    with conn.cursor() as cur:
        cur.execute(SCHEMA_PATH.read_text())

        with CSV_PATH.open(newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

        # Channels get ids in CSV column order so the lookup table reads naturally.
        channel_ids, role_ids, production_ids = {}, {}, {}
        for name in CHANNEL_COLUMNS:
            get_or_create(cur, channel_ids, "sourcing_channels", "channel_id", "channel_name", name)

        for row in rows:
            prod_name = row["Production Name"].strip()
            if prod_name not in production_ids:
                cur.execute(
                    """
                    INSERT INTO productions (name, production_type, respondent_code, respondent_role,
                                             shoot_days, hours_per_day, total_shoot_hours)
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING production_id
                    """,
                    (
                        prod_name, row["Production Type"].strip(), row["Respondent #"].strip(),
                        row["Respondent Role"].strip(), to_int(row["Shoot Days"]),
                        to_int(row["Hours Per Day"]), to_int(row["Total Shoot Hours"]),
                    ),
                )
                production_ids[prod_name] = cur.fetchone()[0]

            role_id = get_or_create(cur, role_ids, "crew_roles", "role_id", "role_name", row["Role Hired"].strip())
            cur.execute(
                """
                INSERT INTO hires (production_id, role_id, ease_of_finding, performance,
                                   would_hire_again, flaked_24_48h)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING hire_id
                """,
                (
                    production_ids[prod_name], role_id, to_int(row["Ease of finding (1-10)"]),
                    to_int(row["Performance (1-10)"]), to_bool(row["Would hire again"]),
                    to_bool(row[FLAKE_COLUMN]),
                ),
            )
            hire_id = cur.fetchone()[0]

            for name in CHANNEL_COLUMNS:
                if to_int(row.get(name)) == 1:
                    cur.execute("INSERT INTO hire_channels VALUES (%s, %s)", (hire_id, channel_ids[name]))

        conn.commit()

        for table in ("productions", "crew_roles", "sourcing_channels", "hires", "hire_channels"):
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            print(f"{table:18s} {cur.fetchone()[0]:>4d} rows")


def main():
    load_dotenv()
    url = os.environ.get("DATABASE_URL")
    if not url:
        sys.exit("DATABASE_URL is not set (add it to .env locally, or to Railway's Variables tab).")
    conn = psycopg2.connect(url)
    try:
        if "--if-empty" in sys.argv:
            with conn.cursor() as cur:
                if hires_exist(cur):
                    print("Database already has survey data; skipping load.")
                    return
        load(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
