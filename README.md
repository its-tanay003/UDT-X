# UDT-X: Unified Defense & Telemetry Platform

> **Comprehensive End-to-End Autonomous Network Defense & Telemetry Platform**
> Built for AI-driven multi-source ingestion, canonical normalisation, real-time feature extraction, multi-class threat detection, behavioral baselines, machine learning anomaly scoring, temporal correlation, MITRE ATT&CK enrichment, dynamic risk scoring, and SIEM/SOC interoperability.

---

## 🏗️ Architecture & End-to-End Pipeline

```mermaid
flowchart TD
    subgraph Ingestion & Normalization [Phases 1-2: Ingestion & Normalization]
        Pcap[PCAP Files / PCAP-NG] --> PcapWorker[udtx-pcap-reader]
        Netflow[NetFlow v5/v9 & IPFIX UDP:2055/4739] --> NetflowWorker[udtx-netflow-listener]
        Zeek[Zeek conn.log JSON] --> RawEventsTopic[Kafka: raw-events]
        Suricata[Suricata EVE JSON] --> RawEventsTopic
        PcapWorker --> RawEventsTopic
        NetflowWorker --> RawEventsTopic
        RawEventsTopic --> Normalizer[udtx-normalizer]
        Normalizer -->|Valid canonical FlowEvents| FlowEventsTopic[Kafka: flow-events]
        Normalizer -->|Malformed payloads| DLQTopic[Kafka: raw-events-dlq]
    end

    subgraph Feature Extraction & Behavioral Baseline [Phases 3, 4, 6: Features & Baselines]
        FlowEventsTopic --> FeaturesWorker[udtx-features]
        FlowEventsTopic --> BaselineWorker[udtx-baseline]
        FeaturesWorker -->|Sliding window stats & entropy| FeatureVectorsTopic[Kafka: feature-vectors]
        BaselineWorker -->|EWMA per-host stats| RedisStore[(Redis 7 State Cache)]
        BaselineWorker -->|Periodic baseline snapshots| TimescaleDB[(TimescaleDB Hypertable)]
    end

    subgraph Detection Layer [Phases 5a-5f & Phase 7: Rule & ML Engines]
        FeatureVectorsTopic --> DDOSEngine[udtx-ddos-engine]
        FeatureVectorsTopic --> ReconEngine[udtx-recon-engine]
        FeatureVectorsTopic --> C2Engine[udtx-c2-beacon-engine]
        FeatureVectorsTopic --> DGAEngine[udtx-dga-dns-tunnel-engine]
        FeatureVectorsTopic --> EncryptedEngine[udtx-encrypted-session-engine]
        FeatureVectorsTopic --> ExfilEngine[udtx-exfiltration-engine]
        FeatureVectorsTopic --> MLInference[udtx-ml-inference]
        
        DDOSEngine --> RawAlertsTopic[Kafka: raw-alerts]
        ReconEngine --> RawAlertsTopic
        C2Engine --> RawAlertsTopic
        DGAEngine --> RawAlertsTopic
        EncryptedEngine --> RawAlertsTopic
        ExfilEngine --> RawAlertsTopic
        MLInference --> MLScoresTopic[Kafka: ml-scores]
    end

    subgraph Correlation & Threat Intel [Phases 8 & 9: Graph & MITRE Intel]
        RawAlertsTopic --> CorrelationWorker[udtx-correlation]
        CorrelationWorker --> Neo4jGraph[(Neo4j 5 Evidence Graph)]
        CorrelationWorker -->|Grouped Attack Chains| CorrelatedIncidentsTopic[Kafka: correlated-incidents]
        
        RawAlertsTopic --> IntelWorker[udtx-intel]
        IntelWorker -->|MITRE ATT&CK & Offline IOCs| EnrichedAlertsTopic[Kafka: enriched-alerts]
    end

    subgraph Risk Engine & SOC Management [Phase 10: Risk Engine & Core API]
        EnrichedAlertsTopic --> RiskWorker[udtx-risk-engine]
        CorrelatedIncidentsTopic --> RiskWorker
        RiskWorker --> FinalAlertsTopic[Kafka: alerts]
        RiskWorker --> CoreAPI[udtx-api: FastAPI on Port 8000]
        CoreAPI -->|WebSocket Stream| SOCDashboard[Real-time /ws/live SOC Dashboard]
        CoreAPI -->|CEF / Syslog RFC 5424| ExternalSIEM[Enterprise SIEM / Splunk / Sentinel]
    end
```

---

## 📦 Subsystems & Delivered Components

| Subsystem | Service Name | Port / Protocol | Core Responsibility |
|---|---|---|---|
| **Pcap Ingestion** | `udtx-pcap-reader` | Native PCAP Stream | Real-time packet parsing & flow state reconstruction. |
| **NetFlow Ingestion** | `udtx-netflow-listener` | UDP `2055` / `4739` | High-throughput NetFlow v5/v9 & IPFIX decoding. |
| **Canonical Normalizer** | `udtx-normalizer` | Kafka Consumer | Schema enforcement, dead-letter routing to `raw-events-dlq`. |
| **Feature Extractor** | `udtx-features` | Kafka Stream Processor | Shannon entropy, IAT, burst rates, directional ratios. |
| **DDoS Surge Engine** | `udtx-ddos-engine` | Kafka Stream Processor | Volumetric flood, SYN surge, and protocol anomaly detection. |
| **Recon Scan Engine** | `udtx-recon-engine` | Kafka Stream Processor | Horizontal/vertical scanning & host sweep detection. |
| **C2 Beacon Engine** | `udtx-c2-beacon-engine` | Kafka Stream Processor | Autocorrelation, low-jitter periodic beaconing detection. |
| **DGA & DNS Tunnel** | `udtx-dga-dns-tunnel-engine`| Kafka Stream Processor | N-gram character entropy & base32/hex tunnel query detection. |
| **Encrypted Session** | `udtx-encrypted-session-engine` | Kafka Stream Processor | JA3 fingerprint matching, TLS cipher suite anomalies. |
| **Exfiltration Engine**| `udtx-exfiltration-engine` | Kafka Stream Processor | Asymmetric outbound volume spikes & destination novelty tracking. |
| **Behavioral Baseline** | `udtx-baseline` | Redis + TimescaleDB | 7-day Gaussian baseline models with hour-of-week seasonality. |
| **ML Inference** | `udtx-ml-inference` | ONNX Runtime | LightGBM/XGBoost classification + TreeSHAP explainability. |
| **Graph Correlator** | `udtx-correlation` | Neo4j 5 Graph DB | 30-minute sliding window multi-stage attack chain synthesis. |
| **Threat Intel** | `udtx-intel` | Local IOC Database | MITRE ATT&CK mapping & technique enrichment. |
| **Risk Engine & API** | `udtx-api` | HTTP `8000`, `/ws/live` | Dynamic composite risk scoring (0-100), REST endpoints & WebSocket. |
| **SOC Dashboard** | `udtx-dashboard` | HTTP `3001` | React 19 + TypeScript + 3D Listening Sphere mission-control cockpit. |

---

## 🏃 Quick Start Guide

### Prerequisites
- Docker & Docker Compose
- Python 3.12+ / 3.14 (with virtual environment)
- Node.js 20+

### 1. Launch Platform Infrastructure & Services
```bash
# Start all services in background
docker compose up -d

# Verify container status
docker compose ps
```

### 2. Access SOC & Management Dashboards
- **UDT-X Mission-Control Dashboard:** [http://localhost:3001](http://localhost:3001)
- **UDT-X Core API & Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Redpanda Kafka Web Console:** [http://localhost:8080](http://localhost:8080)
- **Neo4j Evidence Graph Browser:** [http://localhost:7474](http://localhost:7474) (Auth: `neo4j` / `udtxpassword`)
- **TimescaleDB PostgreSQL:** `localhost:5432` (`udtx_user` / `udtx_password`)

### 3. Stream Live SOC Events
Connect to the real-time WebSocket feed:
```javascript
const ws = new WebSocket("ws://localhost:8000/ws/live");
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("Live Security Telemetry:", data);
};
```

---

## 📜 License
Distributed under the **Apache License, Version 2.0** with full commercial warranty & enterprise SLA enablement. See [LICENSE](LICENSE) and [TERMS_AND_CONDITIONS.md](TERMS_AND_CONDITIONS.md) for details.
