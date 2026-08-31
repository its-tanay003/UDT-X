"""UDT-X Temporal Incident Correlator & Attack Chain Progression Engine.

Groups raw alerts by host and time window (e.g. 30 min) and identifies multi-stage
attack chains (RECONNAISSANCE -> C2_BEACONING -> EXFILTRATION).
"""

from __future__ import annotations

import logging
from datetime import timedelta

from correlation.models import AttackChainProgression, Incident, IncidentStatus
from schema.models import Alert, SeverityLevel

logger = logging.getLogger("udtx.correlation.correlator")


class IncidentCorrelator:
    """Stateful temporal incident correlator grouping alerts into Incidents."""

    def __init__(self, window_minutes: int = 30) -> None:
        self.window_delta = timedelta(minutes=window_minutes)
        # Active incident per host IP: host_ip -> Incident
        self.active_incidents: dict[str, Incident] = {}
        # Chronological raw alert objects per incident_id
        self.incident_alerts: dict[str, list[Alert]] = {}

    def correlate_alert(self, alert: Alert) -> tuple[Incident, bool]:
        """Correlate an incoming raw Alert into an active or new Incident.

        Returns:
            (incident, is_new_incident)
        """
        host_ip = alert.src_ip
        existing = self.active_incidents.get(host_ip)

        # Check if an existing incident is within the active rolling time window
        if existing is not None:
            time_diff = alert.timestamp - existing.last_updated
            if time_diff <= self.window_delta:
                # Add alert to existing incident
                self._merge_alert_into_incident(existing, alert)
                self._update_attack_chain_tag(existing)
                return existing, False

        # Create new incident
        summary_txt = (
            f"Initial alert {alert.threat_class} detected targeting {alert.dst_ip}."
        )
        new_incident = Incident(
            title=f"Security Incident on {host_ip} ({alert.threat_class})",
            status=IncidentStatus.ACTIVE,
            severity=alert.severity,
            risk_score=alert.risk_score,
            created_at=alert.timestamp,
            last_updated=alert.timestamp,
            primary_host_ip=host_ip,
            target_destination_ips=[alert.dst_ip],
            alert_ids=[alert.alert_id],
            threat_classes=[alert.threat_class.upper()],
            mitre_techniques=list(alert.mitre),
            summary=summary_txt,
        )
        self.active_incidents[host_ip] = new_incident
        self.incident_alerts[new_incident.incident_id] = [alert]
        return new_incident, True

    def _merge_alert_into_incident(self, incident: Incident, alert: Alert) -> None:
        """Incrementally update incident attributes with new member alert."""
        if alert.alert_id not in incident.alert_ids:
            incident.alert_ids.append(alert.alert_id)
        if alert.dst_ip not in incident.target_destination_ips:
            incident.target_destination_ips.append(alert.dst_ip)

        tc_upper = alert.threat_class.upper()
        if tc_upper not in incident.threat_classes:
            incident.threat_classes.append(tc_upper)

        # Merge MITRE techniques
        existing_ids = {m.technique_id for m in incident.mitre_techniques}
        for m in alert.mitre:
            if m.technique_id not in existing_ids:
                incident.mitre_techniques.append(m)
                existing_ids.add(m.technique_id)

        # Update timing and risk scores
        if alert.timestamp > incident.last_updated:
            incident.last_updated = alert.timestamp

        # Severity escalation
        sev_rank = {
            SeverityLevel.INFO: 1,
            SeverityLevel.LOW: 2,
            SeverityLevel.MEDIUM: 3,
            SeverityLevel.HIGH: 4,
            SeverityLevel.CRITICAL: 5,
        }
        if sev_rank.get(alert.severity, 1) > sev_rank.get(incident.severity, 1):
            incident.severity = alert.severity

        # Combined risk score calculation
        incident.risk_score = min(
            100.0, max(incident.risk_score, alert.risk_score) + 5.0
        )

        # Append alert object
        self.incident_alerts.setdefault(incident.incident_id, []).append(alert)

    def _update_attack_chain_tag(self, incident: Incident) -> None:
        """Evaluate progression of threat classes to assign attack_chain tag."""
        alerts = self.incident_alerts.get(incident.incident_id, [])
        observed_sequence = [a.threat_class.upper() for a in alerts]

        has_recon = any("RECON" in tc for tc in observed_sequence)
        has_c2 = any("C2" in tc or "BEACON" in tc for tc in observed_sequence)
        has_exfil = any("EXFIL" in tc for tc in observed_sequence)
        has_dga = any("DGA" in tc or "TUNNEL" in tc for tc in observed_sequence)
        has_ddos = any("DDOS" in tc for tc in observed_sequence)

        if has_recon and has_c2 and has_exfil:
            incident.attack_chain = AttackChainProgression.FULL_KILL_CHAIN
            incident.severity = SeverityLevel.CRITICAL
            incident.risk_score = max(incident.risk_score, 95.0)
            incident.title = (
                f"Full Kill Chain Campaign Detected on {incident.primary_host_ip}"
            )
            incident.summary = (
                "Critical multi-stage attack: Host performed Reconnaissance, "
                "established C2 Beaconing, and executed Data Exfiltration."
            )
        elif has_recon and has_c2:
            incident.attack_chain = AttackChainProgression.RECON_TO_C2
            incident.severity = SeverityLevel.HIGH
            incident.risk_score = max(incident.risk_score, 85.0)
            incident.title = (
                f"Recon to C2 Intrusion Sequence on {incident.primary_host_ip}"
            )
        elif has_c2 and has_exfil:
            incident.attack_chain = AttackChainProgression.C2_TO_EXFIL
            incident.severity = SeverityLevel.CRITICAL
            incident.risk_score = max(incident.risk_score, 90.0)
            incident.title = (
                f"C2 to Data Exfiltration Operation on {incident.primary_host_ip}"
            )
        elif has_dga and has_exfil:
            incident.attack_chain = AttackChainProgression.DNS_EXFILTRATION
            incident.severity = SeverityLevel.HIGH
        elif has_recon and has_ddos:
            incident.attack_chain = AttackChainProgression.DDOS_DISTRACTION
        elif len(incident.threat_classes) > 1:
            incident.attack_chain = AttackChainProgression.GENERIC_MULTI_ALERT
