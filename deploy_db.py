"""Create the schema and load class_dataset.csv into Postgres.

Usage:
    python deploy_db.py              # rebuild tables and reload the CSV
    python deploy_db.py --if-empty   # only load when the database has no students yet

Reads DATABASE_URL from the environment (or from a local .env file).
"""
import csv
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
CSV_PATH = HERE / "class_dataset.csv"
SCHEMA_PATH = HERE / "schema.sql"


def split_multi(value):
    """'Python; SQL; Excel' -> ['Python', 'SQL', 'Excel'] (trimmed, de-duplicated, order kept)."""
    seen = []
    for part in (value or "").split(";"):
        part = part.strip()
        if part and part not in seen:
            seen.append(part)
    return seen


def to_int(value):
    value = (value or "").strip()
    return int(value) if value.isdigit() else None


def students_exist(cur):
    cur.execute("SELECT to_regclass('public.students')")
    if cur.fetchone()[0] is None:
        return False
    cur.execute("SELECT COUNT(*) FROM students")
    return cur.fetchone()[0] > 0


def load(conn):
    with conn.cursor() as cur:
        cur.execute(SCHEMA_PATH.read_text())

        with CSV_PATH.open(newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

        tool_ids, slot_ids = {}, {}
        for row in rows:
            cur.execute(
                """
                INSERT INTO students (netid, name, school_year, intro_programming,
                    skill_programming, skill_data_stats, skill_frontend_design, skill_business_pitch,
                    working_style, interests, semester_goal, submitted_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULLIF(%s, '')::timestamptz)
                RETURNING student_id
                """,
                (
                    row["netid"].strip(), row["name"].strip(), row["school_year"].strip() or None,
                    row["intro_programming"].strip() or None,
                    to_int(row["skill_programming"]), to_int(row["skill_data_stats"]),
                    to_int(row["skill_frontend_design"]), to_int(row["skill_business_pitch"]),
                    row["working_style"], row["interests"], row["semester_goal"], row["submitted_at"].strip(),
                ),
            )
            student_id = cur.fetchone()[0]

            for tool in split_multi(row["tools"]):
                if tool not in tool_ids:
                    cur.execute("INSERT INTO tools (tool_name) VALUES (%s) RETURNING tool_id", (tool,))
                    tool_ids[tool] = cur.fetchone()[0]
                cur.execute("INSERT INTO student_tools VALUES (%s, %s)", (student_id, tool_ids[tool]))

            for slot in split_multi(row["availability"]):
                if slot not in slot_ids:
                    cur.execute("INSERT INTO availability_slots (slot_label) VALUES (%s) RETURNING slot_id", (slot,))
                    slot_ids[slot] = cur.fetchone()[0]
                cur.execute("INSERT INTO student_availability VALUES (%s, %s)", (student_id, slot_ids[slot]))

        conn.commit()

        for table in ("students", "tools", "availability_slots", "student_tools", "student_availability"):
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            print(f"{table:22s} {cur.fetchone()[0]:>4d} rows")


def main():
    load_dotenv()
    url = os.environ.get("DATABASE_URL")
    if not url:
        sys.exit("DATABASE_URL is not set (add it to .env locally, or to Railway's Variables tab).")
    conn = psycopg2.connect(url)
    try:
        if "--if-empty" in sys.argv:
            with conn.cursor() as cur:
                if students_exist(cur):
                    print("Database already has students; skipping load.")
                    return
        load(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
