
DROP TABLE IF EXISTS bear_metrics CASCADE;
DROP TABLE IF EXISTS experiences CASCADE;

-- CREATE SCHEMA default_partition;

-- Metrics Table Definition ----------------------------------------------

CREATE TABLE bear_metrics (
    ts timestamp with time zone NOT NULL,
    mic real,
    n_kids integer,
    attention_avg real,
    page_num integer,
    story text
    );

CREATE TABLE experiences (
    ts timestamp with time zone NOT NULL,
    mic_avg real,
    n_kids integer,
    attention_avg real,
    page_num integer,
    story text,
    action text,
    reward real
    );

-- CREATE INDEX idx_metrics_ts ON bear_metrics(ts timestamp_ops);
