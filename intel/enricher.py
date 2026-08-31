"""UDT-X Threat Intelligence & MITRE ATT&CK Enrichment Engine.

Enriches raw alerts with MITRE ATT&CK techniques and local offline IOC reputation.
Fails open if IOC feeds or mapping tables are missing/corrupted.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from schema.models import Alert, EvidenceItem, MitreAttack

logger = logging.getLogger("udtx.intel.enricher")


class ThreatIntelEnricher:
    """Enriches alerts with static MITRE mappings and offline IOC reputation."""

    def __init__(
        self,
        mitre_map_path: str | Path = "intel/mitre_map.json",
        ioc_feed_path: str | Path | None = "intel/data/sample_iocs.json",
    ) -> None:
        self.mitre_map_path = Path(mitre_map_path)
        self.ioc_feed_path = Path(ioc_feed_path) if ioc_feed_path else None

        self.mitre_map: dict[str, list[dict[str, str]]] = {}
        self.ioc_database: dict[str, dict[str, Any]] = {}

        self._load_mitre_map()
        self._load_ioc_feed()

    def _load_mitre_map(self) -> None:
        """Load static MITRE ATT&CK technique mapping table."""
        if not self.mitre_map_path.exists():
            logger.warning(
                "MITRE map file %s not found. Fail-open mode active.",
                self.mitre_map_path,
            )
            return
        try:
            with open(self.mitre_map_path, encoding="utf-8") as f:
                self.mitre_map = json.load(f)
            logger.info(
                "Loaded MITRE mapping for %d threat classes",
                len(self.mitre_map),
            )
        except Exception as exc:
            logger.warning("Failed to load MITRE map: %s. Failing open.", exc)
            self.mitre_map = {}

    def _load_ioc_feed(self) -> None:
        """Load local offline IOC feed without network calls."""
        if not self.ioc_feed_path or not self.ioc_feed_path.exists():
            logger.info(
                "Local IOC feed not present. Proceeding without IOC enrichment."
            )
            return
        try:
            with open(self.ioc_feed_path, encoding="utf-8") as f:
                self.ioc_database = json.load(f)
            logger.info("Loaded %d local IOC indicators", len(self.ioc_database))
        except Exception as exc:
            logger.warning("Failed to load local IOC feed: %s. Failing open.", exc)
            self.ioc_database = {}

    def enrich_alert(self, alert: Alert) -> Alert:
        """Enrich alert with MITRE techniques and optional IOC tags.

        Guaranteed to fail-open and return the Alert even if enrichment fails.
        """
        try:
            # 1. MITRE Technique Mapping
            tc_key = alert.threat_class.upper()
            mitre_entries = self.mitre_map.get(tc_key, [])

            existing_tech_ids = {m.technique_id for m in alert.mitre}
            for entry in mitre_entries:
                if entry.get("technique_id") not in existing_tech_ids:
                    alert.mitre.append(
                        MitreAttack(
                            technique_id=entry["technique_id"],
                            technique_name=entry["technique_name"],
                            url=entry.get("url"),
                        )
                    )
                    existing_tech_ids.add(entry["technique_id"])

            # 2. Local IOC Lookup for src_ip, dst_ip, and domains
            matched_iocs: list[dict[str, Any]] = []

            if alert.src_ip in self.ioc_database:
                matched_iocs.append(self.ioc_database[alert.src_ip])
            if alert.dst_ip in self.ioc_database:
                matched_iocs.append(self.ioc_database[alert.dst_ip])

            if matched_iocs:
                # Add IOC evidence and boost confidence
                for ioc in matched_iocs:
                    alert.evidence.append(
                        EvidenceItem(
                            key="IOC_MATCH",
                            value=ioc.get("indicator", ""),
                            context={
                                "threat_actor": ioc.get("threat_actor"),
                                "feed": ioc.get("feed"),
                                "confidence": ioc.get("confidence"),
                                "description": ioc.get("description"),
                            },
                        )
                    )
                # Escalate risk score and confidence if verified IOC matched
                alert.confidence = min(1.0, max(alert.confidence, 0.95))
                alert.risk_score = min(100.0, alert.risk_score + 15.0)

        except Exception as exc:
            logger.warning(
                "Enrichment exception for alert %s: %s (failing open)",
                alert.alert_id,
                exc,
            )

        return alert
