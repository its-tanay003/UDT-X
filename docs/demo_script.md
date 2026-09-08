# 🎬 UDT-X Live Demonstration Script (SIH Review Panel)

**Target Scenario:** Full Multi-Stage APT Attack Chain Simulation (`kill_chain`)  
**Duration:** ~5 Minutes  
**Screens Used:** Login / Boot $\rightarrow$ Security Overview $\rightarrow$ Deterministic Replay Lab $\rightarrow$ Incidents Dossier $\rightarrow$ Evidence Explorer $\rightarrow$ 3D Network Graph $\rightarrow$ Performance  

---

## 📋 Pre-Demo Checklist
1. Start Backend: `.venv\Scripts\python -m uvicorn services.api.app.main:app --host 0.0.0.0 --port 8000 --ws wsproto`
2. Start Frontend: `npm run dev -- --host 127.0.0.1 --port 3001` (in `dashboard/`)
3. Open Browser to **[http://127.0.0.1:3001](http://127.0.0.1:3001)**.
4. Ensure top status badge displays: `ONLINE` / `DATA DIODE: INWARD ONLY`.
5. Login using `admin@udtx.local` / `AdminEnclave2026!`.

---

## 🎙️ Step-by-Step Demonstration Walkthrough

### **Step 1: Introduction, Enclave Access & Passive Architecture (0:00 - 1:00)**
- **Presenter Speech:**
  > *"Respected judges and evaluation panel, today we present UDT-X: a unified dynamic threat detection and response platform capable of processing over 125,000 network flows per second with sub-5ms latency across passive optical mirror taps. Rather than relying solely on black-box AI or static signatures, UDT-X combines real-time streaming feature extraction, 7-day Gaussian behavioral baselines, TreeSHAP-explainable machine learning, and a Neo4j evidence graph to detect multi-stage attack chains."*
- **Action:** Point out the left navigation rail, the passive Data Diode status, and hover over any KPI card to demonstrate the contextual **Tooltip system**.

---

### **Step 2: Triggering the APT Attack Chain in Replay Lab (1:00 - 1:45)**
- **Presenter Speech:**
  > *"To demonstrate live detection and correlation, we navigate to our Deterministic Replay Lab—a controlled, safety-isolated attack simulation environment. We will launch the Full APT Kill-Chain scenario: an attacker conducting internal reconnaissance, establishing a stealthy C2 beacon, and executing an asymmetric data exfiltration transfer."*
- **Action:**
  1. Click **REPLAY LAB** in the console rail.
  2. Toggle the **ARMED** switch on the **Full APT Kill-Chain** card.
  3. Click **DISPATCH** and observe the live dispatch log populate in real-time.

---

### **Step 3: Security Overview & Real-Time Incident Broadcaster (1:45 - 2:30)**
- **Presenter Speech:**
  > *"Instantly, via our zero-refresh WebSocket telemetry stream, the alert propagates across the entire SOC. Switching to the Overview, notice how our dynamic SVG Risk Posture Gauge has escalated, with the 3D Ambient Listening Sphere updating node interactions in real time."*
- **Action:**
  1. Click **OVERVIEW**.
  2. Show the **Global Risk Posture Dial**, the 4 instrument KPI cards, and the 7 microservice engine status chips.

---

### **Step 4: Incidents Dossier & Multi-Stage Attack Correlation (2:30 - 3:30)**
- **Presenter Speech:**
  > *"An analyst doesn't have time to triage isolated alerts. UDT-X's Graph Correlation Engine recognized that host `192.168.1.105` was involved in all three stages within a 30-minute rolling graph window. Let's open the Incidents Dossier index."*
- **Action:**
  1. Click **INCIDENT DOSSIER** (navigating to `/incidents`).
  2. Demonstrate sorting by risk score and filtering by threat class.
  3. Click **OPEN DOSSIER** on the top incident to drill into `/incidents/INC-...`.
  4. Walk through the **Chronological Attack Timeline**:
     1. Horizontal TCP SYN Port Scan (`T1046`).
     2. C2 Beaconing Channel Established (`T1071.004`).
     3. Outbound Data Exfiltration Transfer (`T1048`).
  5. Point out the **"Correlation Heuristics"** panel explaining the shared host pivot.

---

### **Step 5: Evidence Explorer & Explainable SHAP Attribution (3:30 - 4:15)**
- **Presenter Speech:**
  > *"Why did our model flag this exfiltration? In the Evidence Explorer, UDT-X provides full algorithmic transparency. We can inspect the exact TreeSHAP feature attributions showing how entropy, IAT jitter, and byte asymmetry shifted the probability score to 98% confidence."*
- **Action:**
  1. Click **EVIDENCE EXPLORER** (`/alerts`) to show the complete filtered alert log with 1-click **Export CEF** and **Export Syslog** buttons.
  2. Click **EVIDENCE →** to drill into `/alerts/:id/evidence`.
  3. Show the **TreeSHAP Local Feature Attributions Waterfall** (`+SHAP` vs. `-SHAP`) and the **Heuristic Evidence Meters**.

---

### **Step 6: Network Evidence Graph & Performance Telemetry (4:15 - 5:00)**
- **Presenter Speech:**
  > *"Finally, the Network Graph renders the interactive 3D listening hemisphere and topology derived from telemetry, confirming unidirectional data diode integrity. And on our Performance screen, you can see the engine maintaining a steady 125,000 flows/sec throughput with a P99 latency of just 4.18ms, meeting 100% of evaluation criteria."*
- **Action:**
  1. Click **NETWORK GRAPH** (show 3D Listening Sphere and 2D Topology).
  2. Click **PERFORMANCE** to highlight the real-time latency percentiles, EPS throughput curve, and zero Kafka lag.
  3. Conclude the demonstration.
