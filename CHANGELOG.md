# Changelog

All notable changes to the **Unified Dynamic Threat Identification and Defense Platform (UDT-X)** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.4.0] - 2026-09-08

### 🤖 AI-Native Sentinel Copilot & Offline Fallback Subsystem
- **Controlled Tool Execution Pipeline:**
  - Implemented the strict sequential agent workflow: `Understand -> Retrieve Context -> Determine Intent -> Check Permissions -> Select Tool -> Execute -> Verify -> Respond`.
- **Website Capability Graph & Action Registry:**
  - Created `capability_registry.py` & `capabilityRegistry.ts` defining all 10 console routes, actions, schema parameters, role requirements (`analyst` vs `admin`), and offline compatibility flags.
- **ML Personalization & Recommendation Engine:**
  - Developed `personalization.py` generating dynamic shift guidance based on active kill-chain severity, recent alerts, and operator clearances.
- **Offline RAG & Action Staging Queue:**
  - Built `offlineCopilot.ts` enabling full in-browser natural language understanding, local concept explanations, safe route navigation, and staging of online-only operations when air-gapped.
- **Mission-Control Copilot Modal (`CopilotModal.tsx`):**
  - Cyberpunk floating terminal accessible via global `Ctrl + K` or console rail button with real-time online/offline connection badges, sensitive operation authorization modals, and verified navigation execution.

---

## [1.3.0] - 2026-09-08

### 🎨 Motion & Micro-Interaction Overhaul
- **Dynamic Physics KPI Counter Animations:** Created `AnimatedNumber.tsx` with Framer Motion `useSpring` and `useTransform` with automatic numeric flash updates on live telemetry changes.
- **Route-Transition Motion:** Wrapped `App.tsx` router view in `AnimatePresence mode="wait"` with subtle vertical translation and fade transitions.
- **Staggered Table & List Cascades:** Added 30ms offset fade-in animations across `Alerts.tsx`, `Incidents.tsx`, and `LiveMonitor.tsx` for desktop tables and mobile stacked cards.
- **Interactive Micro-Interactions:** Implemented `hover:bg-[#1B2540]`, soft cyan glow borders, and `active:scale-[0.97]` click compressions across all interactive cards, forensic links, and action buttons.
- **Enhanced 3D Listening Sphere Bloom:** Tuned post-processing bloom parameters (`luminanceThreshold: 0.25`, `intensity: 1.2`, `mipmapBlur`) for clear visibility at normal viewing distance.

---

## [1.2.0] - 2026-09-08

### 📱 Responsive & Mobile-First Overhaul
- **Collapsible Console Rail Navigation:**
  - Below `md` viewport, primary sidebar navigation collapses to an icon-only rail with on-hover tooltips.
  - Added full mobile drawer mode with hamburger menu button toggle and backdrop overlay.
- **Adaptive KPI & Metric Reflow:**
  - `Overview.tsx` & `Performance.tsx`: Metric and KPI cards systematically reflow from 4-column desktop down to 2-column tablet, and 1-column mobile.
- **Dynamic 3D Canvas Resizing:**
  - `ListeningSphere.tsx`: Implemented container-aware `ResizeObserver` and Three.js canvas auto-resizing. Automatically steps down particle density on narrow screens while honoring the server-persisted user display settings.
- **Adaptive D3 Radial Sonar:**
  - `SonarRadialChart.tsx`: Added `ResizeObserver` listener with dynamic radius and coordinate recalculation for tablet and mobile containers.
- **Mobile Stacked Cards for Data Tables:**
  - `LiveMonitor.tsx` and `Alerts.tsx`: Responsive table views that switch to stacked forensic cards on viewports `< md`, eliminating horizontal scrolling on smaller laptop displays.
- **Responsive Auth & Bootstrap Views:**
  - `Login.tsx` and `BootSequence.tsx`: Centered responsive container scaling guaranteed down to 1024px minimum resolution and up to 4K ultra-wide displays.
- **Responsive Tour Guide:**
  - `TourGuide.tsx`: Adaptive spotlight tracking and floating panel bounding on mobile, tablet, and widescreen.

---

## [1.1.0] - 2026-09-08

### 🚀 Added & Improved
- **Navigation & Discoverability Redesign:**
  - Built `pages/Incidents.tsx` (`/incidents`): Real-time index of correlated multi-stage incidents with multi-factor sorting (Risk, Recency, Alert count), search, and direct links to dossiers.
  - Built `pages/Alerts.tsx` (`/alerts`): Anomaly feed index with threat class and severity filters, search, direct evidence links, and 1-click SIEM export (CEF and RFC 5424 Syslog).
  - Updated primary navigation rail in `App.tsx` to point to `/incidents` and `/alerts` index screens while preserving deep links (`/incidents/:id` and `/alerts/:id/evidence`).
- **Reusable UX Components:**
  - `EmptyState`: Reusable on-theme empty/filtered panel component with actionable guidance (used across Incidents, Alerts, Live Monitor, Incident Detail, and Evidence Explorer).
  - `Tooltip`: On-theme floating popover with glassmorphism backdrop (`bg-[#1B2540]`, border `#3FC7D4/30`) explaining technical metrics (EPS, P99, TreeSHAP, MITRE ATT&CK IDs, JA3, Risk calculation).
- **Plain-Language Page Subtitles:** Added clear, functional subtitles across all 12 SOC consoles.
- **Enterprise Licensing:** Upgraded to Apache 2.0 with Enterprise Warranty & SLA addendum (`TERMS_AND_CONDITIONS.md`).
- **Test Suite Health:** All 111 pytest unit & integration tests passing with 100% success rate.

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
