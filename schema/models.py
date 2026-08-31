"""UDT-X Canonical Pydantic Models for FlowEvent, Alert, and FeatureVector."""

import ipaddress
import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ==============================================================================
# Enumerations
# ==============================================================================
class FlowDirection(StrEnum):
    """Direction of network traffic relative to the monitored boundary."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"
    INTERNAL = "internal"
    EXTERNAL = "external"
    UNKNOWN = "unknown"


class FlowSource(StrEnum):
    """Ingestion sensor or collection mechanism."""

    PCAP = "pcap"
    NETFLOW = "netflow"
    IPFIX = "ipfix"
    SFLOW = "sflow"
    ZEEK = "zeek"
    SURICATA = "suricata"


class SeverityLevel(StrEnum):
    """Alert severity classification."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(StrEnum):
    """Incident handling lifecycle status."""

    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    FALSE_POSITIVE = "false_positive"


# ==============================================================================
# Helper Validators
# ==============================================================================
def validate_ip_address(v: str) -> str:
    """Validate that a given string is a valid IPv4 or IPv6 address."""
    if not isinstance(v, str) or not v.strip():
        raise ValueError("IP address must be a non-empty string.")
    try:
        ipaddress.ip_address(v.strip())
        return v.strip()
    except ValueError as e:
        raise ValueError(f"Invalid IP address format '{v}': {e}") from e


# ==============================================================================
# FlowEvent Models
# ==============================================================================
class DNSData(BaseModel):
    """Deep Packet Inspection (DPI) metadata for DNS transactions."""

    model_config = ConfigDict(extra="allow")

    query: str = Field(..., min_length=1, description="Queried domain name.")
    qtype: str | int | None = Field(
        default=None, description="DNS query type (e.g., 'A', 'AAAA', 1, 28)."
    )
    entropy: float | None = Field(
        default=None, ge=0.0, description="Shannon entropy score of the query."
    )


class TLSData(BaseModel):
    """Deep Packet Inspection (DPI) metadata for TLS sessions."""

    model_config = ConfigDict(extra="allow")

    ja3: str | None = Field(default=None, description="Client JA3 fingerprint.")
    ja3s: str | None = Field(default=None, description="Server JA3S fingerprint.")
    sni: str | None = Field(
        default=None, description="Server Name Indication hostname."
    )
    cipher: str | int | None = Field(
        default=None, description="Negotiated cipher suite."
    )
    packet_size_sequence: list[int] | None = Field(
        default=None, description="Packet payload size sequence."
    )


class FlowEvent(BaseModel):
    """Canonical FlowEvent normalized across all telemetry collectors."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    flow_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        min_length=1,
        description="Unique identifier for the network flow.",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="ISO 8601 UTC timestamp of flow observation.",
    )
    src_ip: str = Field(..., description="Source IPv4 or IPv6 address.")
    dst_ip: str = Field(..., description="Destination IPv4 or IPv6 address.")
    src_port: int = Field(..., ge=0, le=65535, description="Source port (0-65535).")
    dst_port: int = Field(
        ..., ge=0, le=65535, description="Destination port (0-65535)."
    )
    protocol: str = Field(
        ..., min_length=1, description="Transport/application protocol (e.g. TCP, UDP)."
    )
    direction: FlowDirection = Field(
        default=FlowDirection.UNKNOWN,
        description="Traffic direction relative to perimeter.",
    )
    bytes: int = Field(..., ge=0, description="Total transferred bytes.")
    packets: int = Field(..., ge=0, description="Total transferred packets.")
    duration_ms: float = Field(
        default=0.0, ge=0.0, description="Duration in milliseconds."
    )
    dns: DNSData | None = Field(
        default=None, description="Optional DNS protocol metadata."
    )
    tls: TLSData | None = Field(
        default=None, description="Optional TLS protocol metadata."
    )
    source: FlowSource = Field(
        ...,
        description="Collector engine (pcap, netflow, ipfix, sflow, zeek, suricata).",
    )
    schema_version: str = Field(
        default="1.0.0", description="Semantic version of schema."
    )

    @field_validator("src_ip", "dst_ip", mode="before")
    @classmethod
    def validate_ips(cls, v: Any) -> str:
        return validate_ip_address(str(v))

    @field_validator("protocol", mode="before")
    @classmethod
    def normalize_protocol(cls, v: Any) -> str:
        if isinstance(v, str):
            return v.strip().upper()
        return str(v)


# ==============================================================================
# Feature Vector Models (Sections 8 & 9 Specifications)
# ==============================================================================
class NetworkFeatures(BaseModel):
    """Network volume, throughput, and distribution features."""

    model_config = ConfigDict(extra="allow")

    packets_per_sec: float = Field(
        default=0.0, ge=0.0, description="Packet rate per second."
    )
    bytes_per_sec: float = Field(
        default=0.0, ge=0.0, description="Byte throughput rate per second."
    )
    packet_size_mean: float = Field(
        default=0.0, ge=0.0, description="Mean packet size in bytes."
    )
    packet_size_stddev: float = Field(
        default=0.0, ge=0.0, description="Standard deviation of packet sizes."
    )
    window_flow_count: int = Field(
        default=1, ge=0, description="Flow count for host in sliding window."
    )
    window_unique_dst_ips: int = Field(
        default=1, ge=0, description="Unique destination IPs in sliding window."
    )
    window_unique_dst_ports: int = Field(
        default=1, ge=0, description="Unique destination ports in sliding window."
    )


class DirectionalFeatures(BaseModel):
    """Traffic asymmetry and directional flow metrics."""

    model_config = ConfigDict(extra="allow")

    direction: FlowDirection = Field(
        default=FlowDirection.UNKNOWN, description="Traffic direction."
    )
    outbound_bytes_window: int = Field(
        default=0, ge=0, description="Outbound byte volume in window."
    )
    inbound_bytes_window: int = Field(
        default=0, ge=0, description="Inbound byte volume in window."
    )
    byte_ratio_out_in: float = Field(
        default=1.0, ge=0.0, description="Ratio of outbound to inbound bytes."
    )
    packet_ratio_out_in: float = Field(
        default=1.0, ge=0.0, description="Ratio of outbound to inbound packets."
    )


class TemporalFeatures(BaseModel):
    """Timing, inter-arrival time (IAT), jitter, and autocorrelation metrics."""

    model_config = ConfigDict(extra="allow")

    duration_ms: float = Field(default=0.0, ge=0.0, description="Flow duration in ms.")
    inter_arrival_time_ms: float = Field(
        default=0.0, ge=0.0, description="Time since preceding flow from host."
    )
    jitter_ms: float = Field(
        default=0.0, ge=0.0, description="Variance in inter-arrival times."
    )
    periodicity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Autocorrelation-based periodicity regularity score (0.0 to 1.0).",
    )


class DNSFeatures(BaseModel):
    """DNS metadata, query entropy, and n-gram anomaly scores."""

    model_config = ConfigDict(extra="allow")

    query: str | None = Field(default=None, description="DNS queried domain.")
    query_length: int | None = Field(
        default=None, ge=0, description="Character length of query."
    )
    domain_entropy: float | None = Field(
        default=None, ge=0.0, description="Shannon entropy score of domain."
    )
    ngram_score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="N-gram anomaly probability score."
    )
    dns_query_frequency_window: int | None = Field(
        default=None, ge=0, description="DNS queries from host in window."
    )


class TLSFeatures(BaseModel):
    """TLS/QUIC handshake metadata and packet dynamics without payload decryption."""

    model_config = ConfigDict(extra="allow")

    ja3: str | None = Field(default=None, description="Client JA3 fingerprint.")
    ja3s: str | None = Field(default=None, description="Server JA3S fingerprint.")
    sni: str | None = Field(default=None, description="Server Name Indication.")
    cipher: str | int | None = Field(
        default=None, description="Negotiated cipher suite."
    )
    packet_size_sequence: list[int] | None = Field(
        default=None, description="Packet size distribution sequence."
    )
    handshake_duration_ms: float | None = Field(
        default=None, ge=0.0, description="TLS handshake duration in ms."
    )


class FeatureVector(BaseModel):
    """Calculated FeatureVector per flow with sliding time-window context."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    flow_id: str = Field(..., min_length=1, description="Associated Flow ID.")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp of feature extraction.",
    )
    src_ip: str = Field(..., description="Source IPv4/IPv6 address.")
    dst_ip: str = Field(..., description="Destination IPv4/IPv6 address.")
    protocol: str = Field(..., min_length=1, description="Protocol name.")
    network: NetworkFeatures = Field(
        default_factory=NetworkFeatures, description="Network throughput features."
    )
    directional: DirectionalFeatures = Field(
        default_factory=DirectionalFeatures,
        description="Directional traffic features.",
    )
    temporal: TemporalFeatures = Field(
        default_factory=TemporalFeatures, description="Temporal & periodicity features."
    )
    dns: DNSFeatures | None = Field(default=None, description="DNS metadata features.")
    tls: TLSFeatures | None = Field(
        default=None, description="TLS/QUIC metadata features."
    )
    schema_version: str = Field(default="1.0.0", description="Semantic schema version.")

    @field_validator("src_ip", "dst_ip", mode="before")
    @classmethod
    def validate_ips(cls, v: Any) -> str:
        return validate_ip_address(str(v))

    @field_validator("protocol", mode="before")
    @classmethod
    def normalize_protocol(cls, v: Any) -> str:
        if isinstance(v, str):
            return v.strip().upper()
        return str(v)


# ==============================================================================
# Alert Models (Section 11 Specification)
# ==============================================================================
class EvidenceItem(BaseModel):
    """Forensic evidence artifact supporting a threat alert."""

    model_config = ConfigDict(extra="allow")

    key: str = Field(..., min_length=1, description="Feature or metric name.")
    value: Any = Field(..., description="Observed evidence value.")
    threshold: Any | None = Field(
        default=None, description="Expected baseline or threshold violated."
    )
    description: str | None = Field(
        default=None, description="Human-readable context for the evidence item."
    )


class MitreAttack(BaseModel):
    """MITRE ATT&CK technique reference mapping."""

    model_config = ConfigDict(extra="allow")

    tactic: str | None = Field(
        default=None, description="ATT&CK tactic (e.g., Command and Control)."
    )
    technique_id: str = Field(
        ..., min_length=1, description="ATT&CK technique ID (e.g., T1071.004)."
    )
    technique_name: str = Field(
        ..., min_length=1, description="ATT&CK technique name (e.g., DNS Tunneling)."
    )
    url: str | None = Field(
        default=None, description="Direct URL to MITRE ATT&CK technique page."
    )


class Alert(BaseModel):
    """Security and anomaly detection alert per Section 11 specification."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    alert_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        min_length=1,
        description="Unique identifier for the alert incident.",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="ISO 8601 UTC timestamp of trigger.",
    )
    flow_id: str | None = Field(
        default=None,
        description="Associated FlowEvent ID (or null if aggregate alert).",
    )
    src_ip: str = Field(..., description="Attacker or source IP address.")
    dst_ip: str = Field(..., description="Target or destination IP address.")
    protocol: str = Field(..., min_length=1, description="Observed network protocol.")
    threat_class: str = Field(
        ..., min_length=1, description="Threat categorization (e.g. c2_beaconing)."
    )
    severity: SeverityLevel = Field(
        ..., description="Threat severity level (info, low, medium, high, critical)."
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Detection confidence score (0.0 - 1.0)."
    )
    risk_score: float = Field(
        ..., ge=0.0, le=100.0, description="Composite risk score (0.0 - 100.0)."
    )
    evidence: list[EvidenceItem] = Field(
        default_factory=list, description="List of forensic evidence items."
    )
    mitre: list[MitreAttack] = Field(
        default_factory=list, description="Mapped MITRE ATT&CK techniques."
    )
    title: str | None = Field(
        default=None, description="Concise human-readable alert title."
    )
    description: str | None = Field(
        default=None, description="Detailed threat narrative."
    )
    status: AlertStatus = Field(
        default=AlertStatus.OPEN, description="Incident status."
    )
    schema_version: str = Field(
        default="1.0.0", description="Semantic version of schema."
    )

    @field_validator("src_ip", "dst_ip", mode="before")
    @classmethod
    def validate_ips(cls, v: Any) -> str:
        return validate_ip_address(str(v))

    @field_validator("protocol", mode="before")
    @classmethod
    def normalize_protocol(cls, v: Any) -> str:
        if isinstance(v, str):
            return v.strip().upper()
        return str(v)
