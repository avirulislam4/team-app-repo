-- schema.sql — relational schema for survey_data.csv (student film crew-hiring survey)
--
-- One CSV row = one crew position a producer hired for on one production.
--
-- Entities
--   productions        one row per production (film), with who answered and shoot length
--   crew_roles         lookup of crew positions (DP, AD, Sound Mixer, ...)
--   sourcing_channels  lookup of where the hire was found (Instagram ISOs, WOM, Classmates, ...)
--   hires              one row per position hired on a production, with the ratings
-- Bridge table (the CSV stores channels as 0/1 columns)
--   hire_channels      many-to-many hires <-> sourcing_channels
--
-- Re-running this file rebuilds the tables from scratch.

DROP TABLE IF EXISTS hire_channels;
DROP TABLE IF EXISTS hires;
DROP TABLE IF EXISTS sourcing_channels;
DROP TABLE IF EXISTS crew_roles;
DROP TABLE IF EXISTS productions;

CREATE TABLE productions (
    production_id     SERIAL PRIMARY KEY,
    name              TEXT NOT NULL UNIQUE,
    production_type   TEXT,
    respondent_code   TEXT,              -- e.g. R1 (anonymous respondent id)
    respondent_role   TEXT,              -- e.g. "Writer, Director, Producer"
    shoot_days        SMALLINT CHECK (shoot_days >= 0),
    hours_per_day     SMALLINT CHECK (hours_per_day BETWEEN 0 AND 24),
    total_shoot_hours SMALLINT CHECK (total_shoot_hours >= 0)
);

CREATE TABLE crew_roles (
    role_id   SERIAL PRIMARY KEY,
    role_name TEXT NOT NULL UNIQUE
);

CREATE TABLE sourcing_channels (
    channel_id   SERIAL PRIMARY KEY,
    channel_name TEXT NOT NULL UNIQUE
);

CREATE TABLE hires (
    hire_id          SERIAL PRIMARY KEY,
    production_id    INTEGER NOT NULL REFERENCES productions(production_id) ON DELETE CASCADE,
    role_id          INTEGER NOT NULL REFERENCES crew_roles(role_id),
    ease_of_finding  SMALLINT CHECK (ease_of_finding BETWEEN 1 AND 10),
    performance      SMALLINT CHECK (performance BETWEEN 1 AND 10),
    would_hire_again BOOLEAN,
    flaked_24_48h    BOOLEAN             -- anyone hired in this position cancelled/flaked 24-48h before
);

CREATE TABLE hire_channels (
    hire_id    INTEGER NOT NULL REFERENCES hires(hire_id) ON DELETE CASCADE,
    channel_id INTEGER NOT NULL REFERENCES sourcing_channels(channel_id) ON DELETE CASCADE,
    PRIMARY KEY (hire_id, channel_id)
);
