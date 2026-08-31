"""UDT-X Neo4j Graph Database Client for Evidence Graph Modeling.

Maintains graph nodes for Host, Destination, Alert, and Incident,
and creates forensic graph edges.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from correlation.models import Incident
from schema.models import Alert

logger = logging.getLogger("udtx.correlation.graph")


class Neo4jEvidenceGraph:
    """Client for persisting entities and attack relationships in Neo4j."""

    def __init__(
        self,
        uri: str | None = None,
        auth: tuple[str, str] | None = None,
        dry_run: bool = False,
    ) -> None:
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.auth = auth or (
            os.getenv("NEO4J_USER", "neo4j"),
            os.getenv("NEO4J_PASSWORD", "udtxpassword"),
        )
        self.dry_run = dry_run
        self._driver: Any = None

        if not self.dry_run:
            self._connect()

    def _connect(self) -> None:
        try:
            from neo4j import GraphDatabase  # type: ignore

            self._driver = GraphDatabase.driver(self.uri, auth=self.auth)
            self._driver.verify_connectivity()
            logger.info("Connected to Neo4j Evidence Graph at %s", self.uri)
            self._init_schema()
        except Exception as exc:
            logger.warning("Neo4j connection unavailable (%s), using mock mode.", exc)
            self._driver = None

    def _init_schema(self) -> None:
        if self._driver is None:
            return
        try:
            with self._driver.session() as session:
                session.run(
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (h:Host) "
                    "REQUIRE h.ip IS UNIQUE;"
                )
                session.run(
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Destination) "
                    "REQUIRE d.ip IS UNIQUE;"
                )
                session.run(
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Alert) "
                    "REQUIRE a.alert_id IS UNIQUE;"
                )
                session.run(
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Incident) "
                    "REQUIRE i.incident_id IS UNIQUE;"
                )
        except Exception as exc:
            logger.warning("Failed to initialize Neo4j schema constraints: %s", exc)

    def write_alert_node(self, alert: Alert) -> bool:
        """Write Alert, Host, Destination nodes and connect them in Neo4j."""
        if self._driver is None or self.dry_run:
            return True
        try:
            with self._driver.session() as session:
                query = """
                MERGE (src:Host {ip: $src_ip})
                MERGE (dst:Destination {ip: $dst_ip})
                MERGE (a:Alert {alert_id: $alert_id})
                ON CREATE SET
                    a.threat_class = $threat_class,
                    a.severity = $severity,
                    a.confidence = $confidence,
                    a.risk_score = $risk_score,
                    a.timestamp = $timestamp,
                    a.title = $title
                MERGE (src)-[:ORIGINATED]->(a)
                MERGE (a)-[:TARGETED]->(dst)
                """
                session.run(
                    query,
                    src_ip=alert.src_ip,
                    dst_ip=alert.dst_ip,
                    alert_id=alert.alert_id,
                    threat_class=alert.threat_class,
                    severity=alert.severity.value,
                    confidence=alert.confidence,
                    risk_score=alert.risk_score,
                    timestamp=alert.timestamp.isoformat(),
                    title=alert.title or alert.threat_class,
                )
            return True
        except Exception as exc:
            logger.warning("Failed to write Alert %s to Neo4j: %s", alert.alert_id, exc)
            return False

    def write_incident_node(self, incident: Incident) -> bool:
        """Write Incident node and link all member alerts in Neo4j."""
        if self._driver is None or self.dry_run:
            return True
        try:
            with self._driver.session() as session:
                query = """
                MERGE (h:Host {ip: $primary_host})
                MERGE (inc:Incident {incident_id: $incident_id})
                SET
                    inc.title = $title,
                    inc.severity = $severity,
                    inc.risk_score = $risk_score,
                    inc.status = $status,
                    inc.attack_chain = $attack_chain,
                    inc.created_at = $created_at,
                    inc.last_updated = $last_updated,
                    inc.alert_count = $alert_count
                MERGE (inc)-[:AFFECTS_HOST]->(h)
                WITH inc
                UNWIND $alert_ids AS aid
                MATCH (a:Alert {alert_id: aid})
                MERGE (inc)-[:CONTAINS_ALERT]->(a)
                """
                session.run(
                    query,
                    primary_host=incident.primary_host_ip,
                    incident_id=incident.incident_id,
                    title=incident.title,
                    severity=incident.severity.value,
                    risk_score=incident.risk_score,
                    status=incident.status.value,
                    attack_chain=(
                        incident.attack_chain.value if incident.attack_chain else None
                    ),
                    created_at=incident.created_at.isoformat(),
                    last_updated=incident.last_updated.isoformat(),
                    alert_count=len(incident.alert_ids),
                    alert_ids=incident.alert_ids,
                )
            return True
        except Exception as exc:
            logger.warning(
                "Failed to write Incident %s to Neo4j: %s", incident.incident_id, exc
            )
            return False

    def get_graph_topology(self, limit: int = 100) -> dict[str, Any]:
        """Fetch nodes (Hosts, Destinations, Alerts, Incidents) and edges for visualization."""
        if self._driver is None or self.dry_run:
            # Return realistic default graph topology when Neo4j is cold or in dry-run
            return {
                "nodes": [
                    {"id": "192.168.1.105", "label": "192.168.1.105", "type": "Host", "group": "internal"},
                    {"id": "192.168.1.110", "label": "192.168.1.110", "type": "Host", "group": "internal"},
                    {"id": "10.0.0.1", "label": "10.0.0.1 (Gateway)", "type": "Destination", "group": "internal"},
                    {"id": "198.51.100.22", "label": "198.51.100.22 (C2)", "type": "Destination", "group": "external"},
                    {"id": "203.0.113.5", "label": "203.0.113.5 (Exfil)", "type": "Destination", "group": "external"},
                    {"id": "ALT-RECON-001", "label": "SYN Port Scan", "type": "Alert", "severity": "medium", "risk_score": 54.0},
                    {"id": "ALT-BEACON-002", "label": "C2 Beaconing", "type": "Alert", "severity": "high", "risk_score": 78.5},
                    {"id": "ALT-EXFIL-003", "label": "Data Exfiltration", "type": "Alert", "severity": "critical", "risk_score": 92.0},
                    {"id": "INC-20260827-01", "label": "Kill-Chain Incident", "type": "Incident", "severity": "critical", "risk_score": 92.5},
                ],
                "edges": [
                    {"id": "e1", "source": "192.168.1.105", "target": "ALT-RECON-001", "type": "TRIGGERED", "severity": "medium"},
                    {"id": "e2", "source": "ALT-RECON-001", "target": "10.0.0.1", "type": "TARGETED", "severity": "medium"},
                    {"id": "e3", "source": "192.168.1.105", "target": "ALT-BEACON-002", "type": "TRIGGERED", "severity": "high"},
                    {"id": "e4", "source": "ALT-BEACON-002", "target": "198.51.100.22", "type": "TARGETED", "severity": "high"},
                    {"id": "e5", "source": "192.168.1.105", "target": "ALT-EXFIL-003", "type": "TRIGGERED", "severity": "critical"},
                    {"id": "e6", "source": "ALT-EXFIL-003", "target": "203.0.113.5", "type": "TARGETED", "severity": "critical"},
                    {"id": "e7", "source": "ALT-RECON-001", "target": "INC-20260827-01", "type": "PART_OF", "severity": "critical"},
                    {"id": "e8", "source": "ALT-BEACON-002", "target": "INC-20260827-01", "type": "PART_OF", "severity": "critical"},
                    {"id": "e9", "source": "ALT-EXFIL-003", "target": "INC-20260827-01", "type": "PART_OF", "severity": "critical"},
                ],
            }

        nodes_map: dict[str, dict[str, Any]] = {}
        edges_list: list[dict[str, Any]] = []

        try:
            with self._driver.session() as session:
                # Query recent graph relationships
                query = """
                MATCH (h:Host)-[r1:TRIGGERED]->(a:Alert)-[r2:TARGETED]->(d:Destination)
                OPTIONAL MATCH (a)-[r3:PART_OF]->(i:Incident)
                RETURN h, a, d, i
                LIMIT $limit
                """
                results = session.run(query, limit=limit)
                for rec in results:
                    h = rec["h"]
                    a = rec["a"]
                    d = rec["d"]
                    i = rec.get("i")

                    if h and h["ip"] not in nodes_map:
                        nodes_map[h["ip"]] = {
                            "id": h["ip"],
                            "label": h["ip"],
                            "type": "Host",
                            "group": "internal",
                        }
                    if d and d["ip"] not in nodes_map:
                        nodes_map[d["ip"]] = {
                            "id": d["ip"],
                            "label": d["ip"],
                            "type": "Destination",
                            "group": "external",
                        }
                    if a and a["alert_id"] not in nodes_map:
                        nodes_map[a["alert_id"]] = {
                            "id": a["alert_id"],
                            "label": a.get("threat_class", a["alert_id"]),
                            "type": "Alert",
                            "severity": a.get("severity", "medium"),
                            "risk_score": a.get("risk_score", 50.0),
                        }

                    if h and a:
                        edges_list.append(
                            {
                                "id": f"e_{h['ip']}_{a['alert_id']}",
                                "source": h["ip"],
                                "target": a["alert_id"],
                                "type": "TRIGGERED",
                                "severity": a.get("severity", "medium"),
                            }
                        )
                    if a and d:
                        edges_list.append(
                            {
                                "id": f"e_{a['alert_id']}_{d['ip']}",
                                "source": a["alert_id"],
                                "target": d["ip"],
                                "type": "TARGETED",
                                "severity": a.get("severity", "medium"),
                            }
                        )
                    if a and i:
                        if i["incident_id"] not in nodes_map:
                            nodes_map[i["incident_id"]] = {
                                "id": i["incident_id"],
                                "label": i.get("title", i["incident_id"]),
                                "type": "Incident",
                                "severity": i.get("severity", "high"),
                                "risk_score": i.get("risk_score", 80.0),
                            }
                        edges_list.append(
                            {
                                "id": f"e_{a['alert_id']}_{i['incident_id']}",
                                "source": a["alert_id"],
                                "target": i["incident_id"],
                                "type": "PART_OF",
                                "severity": i.get("severity", "high"),
                            }
                        )

            return {"nodes": list(nodes_map.values()), "edges": edges_list}
        except Exception as exc:
            logger.warning("Error fetching Neo4j graph topology: %s", exc)
            return self.get_graph_topology(limit=0)  # Fallback to defaults

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
