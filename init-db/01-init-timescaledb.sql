-- UDT-X TimescaleDB Initialization Script
-- Initializes TimescaleDB extension and sets up hypertables for network flows and alerts

CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- -----------------------------------------------------------------------------
-- Network Flows Table & Hypertable
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS flows (
    time TIMESTAMPTZ NOT NULL,
    flow_id UUID DEFAULT gen_random_uuid(),
    src_ip INET NOT NULL,
    dst_ip INET NOT NULL,
    src_port INTEGER NOT NULL CHECK (src_port >= 0 AND src_port <= 65535),
    dst_port INTEGER NOT NULL CHECK (dst_port >= 0 AND dst_port <= 65535),
    protocol VARCHAR(16) NOT NULL,
    bytes_in BIGINT DEFAULT 0,
    bytes_out BIGINT DEFAULT 0,
    packets_in BIGINT DEFAULT 0,
    packets_out BIGINT DEFAULT 0,
    duration_ms DOUBLE PRECISION DEFAULT 0.0,
    flags VARCHAR(32),
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT pk_flows PRIMARY KEY (time, flow_id)
);

-- Convert to TimescaleDB Hypertable partitioned by time (7 days chunk interval by default)
SELECT create_hypertable(
    'flows',
    'time',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Optimized query indexes
CREATE INDEX IF NOT EXISTS idx_flows_src_ip_time ON flows (src_ip, time DESC);
CREATE INDEX IF NOT EXISTS idx_flows_dst_ip_time ON flows (dst_ip, time DESC);
CREATE INDEX IF NOT EXISTS idx_flows_dst_port_time ON flows (dst_port, time DESC);
CREATE INDEX IF NOT EXISTS idx_flows_protocol ON flows (protocol, time DESC);

-- -----------------------------------------------------------------------------
-- Security / Anomaly Alerts Table & Hypertable
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alerts (
    time TIMESTAMPTZ NOT NULL,
    alert_id UUID DEFAULT gen_random_uuid(),
    alert_type VARCHAR(128) NOT NULL,
    severity VARCHAR(32) NOT NULL DEFAULT 'medium', -- low, medium, high, critical
    src_ip INET,
    dst_ip INET,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    confidence DOUBLE PRECISION DEFAULT 1.0,
    status VARCHAR(32) DEFAULT 'open',              -- open, investigating, resolved, dismissed
    evidence JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT pk_alerts PRIMARY KEY (time, alert_id)
);

-- Convert to TimescaleDB Hypertable partitioned by time (7 days chunk interval)
SELECT create_hypertable(
    'alerts',
    'time',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Optimized query indexes
CREATE INDEX IF NOT EXISTS idx_alerts_severity_time ON alerts (severity, time DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_type_time ON alerts (alert_type, time DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_src_ip ON alerts (src_ip, time DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_dst_ip ON alerts (dst_ip, time DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts (status, time DESC);
