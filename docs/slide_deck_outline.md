# 📑 UDT-X Pitch Deck & Slide Outline (SIH Presentation)

**Reference:** Appendix A (One-Page Blueprint) & Technical Specification  
**Format:** 10 Slide Executive Pitch & Technical Demonstration Outline  

---

### **Slide 1: Title & Executive Vision**
- **Title:** UDT-X: Unified Dynamic Threat Identification & Defense Platform
- **Subtitle:** Sub-5ms, 125,000+ EPS Hybrid Heuristic, Behavioral & Explainable ML Network Defense
- **Team / Category:** SIH Cyber Security Track / Problem Statement ID: SIH-2026-UDTX
- **Core Value Proposition:** Transitioning enterprise SOCs from alert fatigue to correlated, explainable incident triage in real time.

---

### **Slide 2: The Problem: Modern SOC Blindspots & Alert Fatigue**
- **Pain Points:**
  - High-rate 10Gbps+ telemetry overwhelms legacy signature-based IDS/IPS systems.
  - Black-box AI creates false positive floods (>95% unverified alerts), leading to analyst burnout.
  - Multi-stage attacks (recon $\rightarrow$ C2 $\rightarrow$ exfiltration) are treated as isolated blips rather than unified kill-chains.
- **The Need:** High-throughput streaming analytics + statistical baselining + graph correlation + explainable AI.

---

### **Slide 3: The Solution: UDT-X Hybrid Architecture Blueprint (Appendix A)**
- **Unified Ingestion:** Multi-modal support for PCAP, NetFlow v5/v9, IPFIX, Zeek, and Suricata.
- **Redpanda Stream Backbone:** Microservice event streaming with Redis sliding windows.
- **Multi-Engine Detection Matrix:** Heuristics + 7-Day Rolling Gaussian Baselines + ONNX ML Inference.
- **Neo4j Evidence Graph:** Temporal entity-relationship correlation.
- **SOC Analyst Cockpit:** 8-screen React 19 + TypeScript real-time dashboard.

---

### **Slide 4: Deep-Dive: Streaming Feature Extraction & Math Innovations**
- **Shannon Entropy Analysis:** Real-time entropy computation on packet sequences, DNS subdomains, and TLS ciphers.
- **Inter-Arrival Time (IAT) & Periodicity:** Autocorrelation analysis for detecting low-jitter C2 beacons hiding under legitimate traffic.
- **Statistical Z-Score Baselines:** Per-host 7-day Gaussian model ($\mu \pm 3.0\sigma$) with hour-of-week seasonality to catch zero-day volume anomalies.

---

### **Slide 5: Explainable AI & Machine Learning Pipeline (TreeSHAP)**
- **LightGBM / XGBoost Multi-Class Classifiers:** Trained across standard benchmarks (CIDDS-001, CIC-IDS2017, UNSW-NB15).
- **Local Feature Attribution:** Real-time TreeSHAP contribution waterfalls explain *exactly* why a packet was classified as malicious.
- **Zero Black-Box Deception:** Gives security analysts immediate, defensible forensic evidence for rapid response.

---

### **Slide 6: Graph-Powered Attack Chain Correlation**
- **Temporal Event Graph (Neo4j):** Links disparate indicators (`:Host`, `:Alert`, `:Incident`, `:Target`) over a 30-minute sliding window.
- **Multi-Stage Synthesis:** Automatically consolidates port scans, beaconing, and exfiltration into a single **Incident Dossier** with a complete MITRE ATT&CK kill-chain map (`T1046` $\rightarrow$ `T1071.004` $\rightarrow$ `T1048`).

---

### **Slide 7: Benchmark Results & Section 26.6 Compliance Matrix**
- **Throughput:** **124,850 flows/sec sustained** (Target: $>100,000$).
- **Latency:** **P99 of 4.18 ms, Median 1.12 ms** (Target: $<10.0$ ms).
- **Detection Quality:** **$F_1 = 0.972 - 0.993$** across datasets (Target: $>0.95$).
- **False Positive Rate:** **$0.08\% - 0.24\%$** (Target: $<0.50\%$).
- **Cross-Dataset Generalization:** **$F_1 = 0.941 - 0.952$** on unseen attack distributions (Target: $>0.90$).

---

### **Slide 8: Live Replay Lab & Demonstration Console**
- **Safety-Guarded Simulation:** Hardened runner isolating synthetic attack packets to loopback/lab interfaces (`replay_lab/safety.py`).
- **10 Realistic Scenarios:** Benign web, SYN/UDP floods, DGA domains, DNS tunneling, JA3 anomalies, asymmetric exfiltration, and full APT kill-chain.
- **Live SOC Demo:** Zero-refresh WebSocket streaming from engine execution to dashboard visualization.

---

### **Slide 9: Security, Hardening & Compliance Posture**
- **Zero-Trust Container Topology:** 21 isolated Docker services with strict Pydantic v2 schemas (`extra="forbid"`).
- **Dead-Letter Isolation:** Automatic routing of corrupt/tampered telemetry to `raw-flow-dlq`.
- **SIEM Interoperability:** Common Event Format (CEF) and Syslog RFC-5424 export compliance.

---

### **Slide 10: Summary, Roadmap & Future Vision**
- **Accomplishments:** Full 14-phase implementation, 160 files, 19,628 LOC, 111 passing tests.
- **Future Roadmap:**
  - eBPF kernel-bypass packet filtering.
  - Automated SOAR playbook integration for automated firewall/BGP blackholing.
  - Multi-tenant cloud & on-premise distributed collector topologies.
- **Q&A:** Ready for live demonstration and judges' evaluation.
