"""UDT-X Behavioral Baseline Snapshot Service for TimescaleDB.

Periodically writes baseline profiles to TimescaleDB for auditability and compliance.
"""

from __future__ import annotations

import logging

from baseline.models import BaselineProfile

logger = logging.getLogger("udtx.baseline.snapshot")


class TimescaleSnapshotter:
    """Writes baseline audit snapshots to TimescaleDB PostgreSQL."""

    def __init__(self, db_url: str | None = None) -> None:
        self.db_url = db_url

    def init_table(self) -> None:
        """Create baseline_snapshots table and hypertable if available."""
        if not self.db_url:
            return
        try:
            import psycopg2  # type: ignore

            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                    CREATE TABLE IF NOT EXISTS baseline_snapshots (
                        time TIMESTAMPTZ NOT NULL,
                        host_ip INET NOT NULL,
                        total_flows INTEGER NOT NULL,
                        byte_mean DOUBLE PRECISION NOT NULL,
                        byte_variance DOUBLE PRECISION NOT NULL,
                        packet_mean DOUBLE PRECISION NOT NULL,
                        known_destinations JSONB NOT NULL,
                        active_hours JSONB NOT NULL,
                        CONSTRAINT pk_baseline_snapshots PRIMARY KEY (time, host_ip)
                    );
                    """)
                    try:
                        cur.execute("""
                        SELECT create_hypertable(
                            'baseline_snapshots',
                            'time',
                            chunk_time_interval => INTERVAL '7 days',
                            if_not_exists => TRUE
                        );
                        """)
                    except Exception:
                        pass
                conn.commit()
                logger.info("TimescaleDB baseline_snapshots table initialized.")
        except Exception as exc:
            logger.warning("Could not initialize TimescaleDB snapshots table: %s", exc)

    def snapshot_profiles(self, profiles: list[BaselineProfile]) -> int:
        """Persist snapshots for all given host profiles."""
        if not self.db_url or not profiles:
            return 0
        try:
            import json

            import psycopg2  # type: ignore

            inserted = 0
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    for p in profiles:
                        cur.execute(
                            """
                            INSERT INTO baseline_snapshots (
                                time, host_ip, total_flows, byte_mean, byte_variance,
                                packet_mean, known_destinations, active_hours
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (time, host_ip) DO UPDATE SET
                                total_flows = EXCLUDED.total_flows,
                                byte_mean = EXCLUDED.byte_mean,
                                byte_variance = EXCLUDED.byte_variance,
                                packet_mean = EXCLUDED.packet_mean,
                                known_destinations = EXCLUDED.known_destinations,
                                active_hours = EXCLUDED.active_hours;
                            """,
                            (
                                p.last_updated,
                                p.host_ip,
                                p.total_flows_observed,
                                p.byte_volume_mean,
                                p.byte_volume_variance,
                                p.packet_volume_mean,
                                json.dumps(p.known_destinations),
                                json.dumps(p.active_hours),
                            ),
                        )
                        inserted += 1
                conn.commit()
            return inserted
        except Exception as exc:
            logger.warning(
                "Failed to snapshot baseline profiles to TimescaleDB: %s",
                exc,
            )
            return 0
