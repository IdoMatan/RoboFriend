
DROP TABLE IF EXISTS bear_metrics CASCADE;


-- CREATE SCHEMA default_partition;

-- Metrics Table Definition ----------------------------------------------

CREATE TABLE bear_metrics (
    ts timestamp with time zone NOT NULL,
    story text,
    page integer,
    session_id real,
    mic_volume real,
    mic_diff real,
    n_kids integer,
    attention_avg real,
    excitement real,
    prev_action1 integer,
    prev_action2 integer,
    prev_action3 integer
    );

