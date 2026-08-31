"""UDT-X Alert & Incident Exporter (CEF & Syslog RFC 5424).

Generates standard format strings for SIEM / SOC ingestion.
"""

from __future__ import annotations

from datetime import UTC

from schema.models import Alert


class AlertExporter:
    """Exports UDT-X Alerts and Incidents to CEF and Syslog RFC 5424 formats."""

    @staticmethod
    def to_cef(alert: Alert) -> str:
        """Format an Alert into Common Event Format (CEF:0)."""
        # Map 0-100 risk score to CEF severity 1-10
        cef_severity = max(1, min(10, int(alert.risk_score / 10)))

        # Format extensions
        ext_parts: list[str] = [
            f"src={alert.src_ip}",
            f"dst={alert.dst_ip}",
            f"proto={alert.protocol}",
            f"cat={alert.threat_class}",
            f"cs1={alert.confidence:.2f}",
            "cs1Label=Confidence",
            f"cn1={alert.risk_score:.1f}",
            "cn1Label=RiskScore",
            f"msg={alert.title}",
        ]
        if alert.mitre:
            mitre_ids = ",".join(m.technique_id for m in alert.mitre)
            ext_parts.append(f"cs2={mitre_ids}")
            ext_parts.append("cs2Label=MitreTechniques")

        ext_str = " ".join(ext_parts)
        vendor = "UDTX"
        prod = "UDT-X Telemetry Platform"
        return (
            f"CEF:0|{vendor}|{prod}|1.0.0|{alert.threat_class}|"
            f"{alert.title}|{cef_severity}|{ext_str}"
        )

    @staticmethod
    def to_syslog_rfc5424(alert: Alert) -> str:
        """Format an Alert into Syslog RFC 5424 format."""
        # Facility 1 (user-level) * 8 + Severity (2=Critical, 4=Warning, 6=Info)
        pri = 14
        if alert.severity.value == "critical":
            pri = 10
        elif alert.severity.value == "high":
            pri = 12

        ts_str = alert.timestamp.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        hostname = "udtx-sensor"
        app_name = "udtx-risk-engine"
        procid = "-"
        msgid = alert.threat_class

        sd = (
            f'[alert@54240 alert_id="{alert.alert_id}" src="{alert.src_ip}" '
            f'dst="{alert.dst_ip}" proto="{alert.protocol}" '
            f'confidence="{alert.confidence:.2f}" risk_score="{alert.risk_score:.1f}"]'
        )

        msg = (
            f"{alert.title} (Threat: {alert.threat_class}, "
            f"Severity: {alert.severity.value})"
        )
        return f"<{pri}>1 {ts_str} {hostname} {app_name} {procid} {msgid} {sd} {msg}"

    @staticmethod
    def export_all(alerts: list[Alert], format_type: str = "cef") -> str:
        """Export multiple alerts as newline-delimited CEF or Syslog string."""
        if format_type.lower() == "cef":
            return "\n".join(AlertExporter.to_cef(a) for a in alerts)
        elif format_type.lower() in ("syslog", "rfc5424"):
            return "\n".join(AlertExporter.to_syslog_rfc5424(a) for a in alerts)
        else:
            return "\n".join(a.model_dump_json() for a in alerts)
