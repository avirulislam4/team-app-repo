-- schema.sql — relational schema for class_dataset.csv (student intake responses)
--
-- Entities
--   students            one row per intake response
--   tools               lookup of tools (Python, SQL, Excel, JavaScript, R, ...)
--   availability_slots  lookup of time slots (Weekday mornings, Weekend evenings, ...)
-- Bridge tables (the CSV stores these as "a; b; c" multi-valued columns)
--   student_tools        many-to-many students <-> tools
--   student_availability many-to-many students <-> availability_slots
--
-- Re-running this file rebuilds the tables from scratch.

DROP TABLE IF EXISTS student_availability;
DROP TABLE IF EXISTS student_tools;
DROP TABLE IF EXISTS availability_slots;
DROP TABLE IF EXISTS tools;
DROP TABLE IF EXISTS students;

CREATE TABLE students (
    student_id            SERIAL PRIMARY KEY,
    netid                 TEXT NOT NULL UNIQUE,      -- as submitted (some are N-numbers or emails)
    name                  TEXT NOT NULL,
    school_year           TEXT CHECK (school_year IN ('First-year', 'Sophomore', 'Junior', 'Senior')),
    intro_programming     TEXT CHECK (intro_programming IN ('took_it', 'equivalent', 'neither')),
    skill_programming     SMALLINT CHECK (skill_programming BETWEEN 1 AND 5),
    skill_data_stats      SMALLINT CHECK (skill_data_stats BETWEEN 1 AND 5),
    skill_frontend_design SMALLINT CHECK (skill_frontend_design BETWEEN 1 AND 5),
    skill_business_pitch  SMALLINT CHECK (skill_business_pitch BETWEEN 1 AND 5),
    working_style         TEXT,
    interests             TEXT,
    semester_goal         TEXT,
    submitted_at          TIMESTAMPTZ
);

CREATE TABLE tools (
    tool_id   SERIAL PRIMARY KEY,
    tool_name TEXT NOT NULL UNIQUE
);

CREATE TABLE availability_slots (
    slot_id    SERIAL PRIMARY KEY,
    slot_label TEXT NOT NULL UNIQUE
);

CREATE TABLE student_tools (
    student_id INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    tool_id    INTEGER NOT NULL REFERENCES tools(tool_id) ON DELETE CASCADE,
    PRIMARY KEY (student_id, tool_id)
);

CREATE TABLE student_availability (
    student_id INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    slot_id    INTEGER NOT NULL REFERENCES availability_slots(slot_id) ON DELETE CASCADE,
    PRIMARY KEY (student_id, slot_id)
);
