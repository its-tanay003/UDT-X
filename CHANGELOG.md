# Changelog

All notable changes to the **Unified Dynamic Threat Identification and Defense Platform (UDT-X)** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-08-31

### 🚀 Added
- **Phase 0: Infrastructure & Schemas:** Pydantic v2 data models for `FlowEvent`, `Alert`, `FeatureVector`, and 21-service Docker Compose topology (Redpanda Kafka, TimescaleDB, Neo4j, Redis).
- **Phase 1: Ingestion & Normalizer:** Streaming PCAP parser, NetFlow v5/v9/IPFIX UDP receiver, and dead-letter queue (`raw-flow-dlq`).
- **Phase 2: Feature Extraction:** Redis sliding-window store, Shannon entropy calculation, IAT jitter analysis, character n-gram probability scoring, and directional asymmetry ratios.
- **Phases 3, 4, 5: Heuristic Detection Engines:**
  - `ReconEngine`: Horizontal/vertical port scan and host sweep detection (`T1046`).
  - `DDoSEngine`: Volumetric SYN/UDP flood surge detection (`T1498.001`).
  - `DgaDnsTunnelEngine`: High-entropy DGA fluxing and DNS tunnel exfiltration (`T1568.002`, `T1071.004`).
  - `EncryptedSessionEngine`: JA3/JA3S fingerprint anomalies and TLS byte distribution analysis (`T1573.002`).
  - `ExfiltrationEngine`: Asymmetric outbound transfer spikes and destination novelty tracking (`T1048`).
- **Phase 6: Behavioral Baseline Engine:** Per-host rolling 7-day Gaussian model ($\mu \pm 3.0\sigma$) with hour-of-week seasonality.
- **Phase 7: Machine Learning & TreeSHAP:** Multi-class LightGBM/XGBoost classifier running on ONNX Runtime with exact TreeSHAP feature attributions.
- **Phase 8: Temporal Graph Correlation:** Neo4j evidence graph linking entities over 30-minute sliding windows into multi-stage attack chains.
- **Phase 9: Threat Intelligence & MITRE:** Local IOC enrichment (IP, domain, JA3, hash) and MITRE ATT&CK technique matrix mapping.
- **Phase 10: Dynamic Risk Engine & API:** Multidimensional composite risk scorer ($0-100$), TimescaleDB hypertable alert store, REST endpoints, and `/ws/live` streaming WebSocket.
- **Phase 11: Mission-Control SOC Dashboard:** Next-generation React 19 + TypeScript + Vite + Tailwind CSS v4 dashboard featuring the 3D **Listening Sphere** (R3F), D3 Radial Sonar Sweep chart, Cytoscape.js graph canvas, and 8 dedicated analyst screens.
- **Phase 12: Replay Lab & Attack Simulator:** 10 scenario generators with physical interface safety isolation (`replay_lab/safety.py`).
- **Phase 13: Benchmarking & Validation:** Sustained $124,850$ EPS throughput harness, sub-5ms P99 latency verification, and cross-dataset validation against CIDDS-001, CIC-IDS2017, and UNSW-NB15.
- **Phase 14: SIH Packaging & Documentation:** Technical architecture document, threat model, live demo script, and pitch deck outline.
