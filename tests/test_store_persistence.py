"""Integration test for AlertManagerStore database persistence across service restarts.

Validates that saving alerts and incidents writes to the underlying database
and that a newly created store object (simulating a service restart) successfully
reloads the persisted entities.
"""

import sqlite3
from datetime import UTC, datetime

import pytest

from alert_manager.store import AlertManagerStore
from correlation.models import AttackChainProgression, Incident, IncidentStatus
from schema.models import Alert, SeverityLevel


@pytest.fixture
def test_db():
    """Create in-memory database with alerts and incidents schema."""
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE alerts (
            time TEXT NOT NULL,
            alert_id TEXT PRIMARY KEY,
            alert_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            src_ip TEXT,
            dst_ip TEXT,
            title TEXT NOT NULL,
            description TEXT,
            confidence REAL,
            status TEXT,
            evidence TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE incidents (
            time TEXT NOT NULL,
            incident_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            attack_chain TEXT,
            severity TEXT NOT NULL,
            risk_score REAL,
            status TEXT,
            alert_ids TEXT,
            created_at TEXT NOT NULL,
            last_updated TEXT NOT NULL
        )
    """)
    conn.commit()
    yield conn
    conn.close()


def test_alert_persistence_across_service_restart(test_db):
    """Test saving an alert, restarting store, and confirming retrieval."""
    # 1. Start initial store service instance
    initial_store = AlertManagerStore(db_pool=test_db)

    alert_id = "ALT-TEST-PERSIST-001"
    now = datetime.now(UTC)
    test_alert = Alert(
        alert_id=alert_id,
        timestamp=now,
        threat_class="c2_beaconing",
        protocol="TCP",
        severity=SeverityLevel.CRITICAL,
        src_ip="192.168.1.100",
        dst_ip="203.0.113.5",
        title="Persistent C2 Beacon Detected",
        description="Persistent store validation alert across process lifecycle",
        confidence=0.98,
        risk_score=94.5,
    )

    # Save through store
    initial_store.save_alert(test_alert)
    assert alert_id in initial_store.alerts

    # 2. Simulate complete service crash/restart by destroying initial store
    del initial_store

    # 3. Spin up brand new store instance pointing to same database
    restarted_store = AlertManagerStore(db_pool=test_db)

    # 4. Verify alert is retrieved from database persistence
    retrieved = restarted_store.get_alert(alert_id)
    assert retrieved is not None, "Alert was lost across store restart!"
    assert retrieved.alert_id == alert_id
    assert retrieved.src_ip == "192.168.1.100"
    assert retrieved.dst_ip == "203.0.113.5"
    assert retrieved.severity == SeverityLevel.CRITICAL
    assert retrieved.title == "Persistent C2 Beacon Detected"

    all_alerts = restarted_store.get_alerts()
    assert any(a.alert_id == alert_id for a in all_alerts)


def test_incident_persistence_across_service_restart(test_db):
    """Test saving an incident, restarting store, and confirming retrieval."""
    initial_store = AlertManagerStore(db_pool=test_db)

    incident_id = "INC-PERSIST-001"
    test_incident = Incident(
        incident_id=incident_id,
        title="Coordinated Kill Chain Campaign",
        summary="Recon followed by C2 communication",
        primary_host_ip="192.168.1.50",
        status=IncidentStatus.ACTIVE,
        severity=SeverityLevel.HIGH,
        risk_score=85.0,
        attack_chain=AttackChainProgression.RECON_TO_C2,
        alert_ids=["ALT-TEST-001", "ALT-TEST-002"],
    )

    initial_store.save_incident(test_incident)
    del initial_store

    # Restart store instance
    restarted_store = AlertManagerStore(db_pool=test_db)
    retrieved_inc = restarted_store.get_incident(incident_id)

    assert retrieved_inc is not None, "Incident was lost across store restart!"
    assert retrieved_inc.incident_id == incident_id
    assert retrieved_inc.title == "Coordinated Kill Chain Campaign"
    assert retrieved_inc.risk_score == 85.0
    assert "ALT-TEST-001" in retrieved_inc.alert_ids
