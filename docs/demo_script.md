# 🎬 UDT-X Live Demonstration Script (SIH Review Panel)

**Target Scenario:** Full Multi-Stage APT Attack Chain Simulation (`kill_chain`)  
**Duration:** ~5 Minutes  
**Screens Used:** Replay Lab $\rightarrow$ Security Overview $\rightarrow$ Live Monitor $\rightarrow$ Incident Dossier $\rightarrow$ Evidence Explorer $\rightarrow$ Network Graph  

---

## 📋 Pre-Demo Checklist
1. Open Browser to **[http://localhost:3001](http://localhost:3001)** (UDT-X SOC Dashboard).
2. Ensure top-right status badge displays: `ONLINE` / `KAFKA & WS STREAM ACTIVE`.
3. Open a secondary browser window / tab to **Performance** to show real-time metrics.

---

## 🎙️ Step-by-Step Demonstration Walkthrough

### **Step 1: Introduction & Architecture Setup (0:00 - 1:00)**
- **Presenter Speech:**
  > *"Respected judges and panel members, today we present UDT-X: a unified dynamic threat detection and response platform capable of processing over 125,000 network flows per second with sub-5ms latency. Rather than relying solely on black-box AI or static signatures, UDT-X combines real-time streaming feature extraction, 7-day Gaussian behavioral baselines, TreeSHAP-explainable machine learning, and a Neo4j evidence graph to detect multi-stage attack chains."*
- **Action:** Point out the global navigation bar showing the 8 analyst screens.

---

### **Step 2: Triggering the APT Attack Chain in Replay Lab (1:00 - 1:45)**
- **Presenter Speech:**
  > *"To demonstrate live detection and correlation, we navigate to our Replay Lab—a controlled, safety-isolated attack simulation environment. We will launch the Full APT Kill-Chain scenario: an attacker conducting internal reconnaissance, establishing a stealthy C2 beacon, and executing an asymmetric data exfiltration transfer."*
- **Action:**
  1. Click **Replay Lab (SIH Demo)** tab.
  2. Click the **LAUNCH** button on the **Full APT Kill-Chain** card.
  3. Observe the live table immediately populate with the 3 generated alerts, and the top card generate a correlated incident (`INC-...`).

---

### **Step 3: Security Overview & Real-Time Incident Broadcaster (1:45 - 2:30)**
- **Presenter Speech:**
  > *"Instantly, via our zero-refresh WebSocket telemetry stream, the alert propagates to the entire SOC. Switching to the Security Overview, notice how our dynamic SVG Risk Posture Gauge has updated to Critical Risk (94.5/100), with Active Threats and Critical Incidents incremented in real time without refreshing the page."*
- **Action:**
  1. Click **Security Overview**.
  2. Point out the **Risk Posture Gauge (Red Zone)**, the 4 summary metric cards, and the cluster container health status indicators.

---

### **Step 4: Live Monitor & Incident Dossier Attack Correlation (2:30 - 3:30)**
- **Presenter Speech:**
  > *"In the Live Monitor, we see the individual alerts flowing in. But an analyst doesn't have time to triage 3 separate alerts. UDT-X's Phase 8 Graph Correlation Engine recognized that host `192.168.1.105` was involved in all three stages within a 30-minute rolling graph window. Let's open the Incident Dossier."*
- **Action:**
  1. Click **Incident Dossier**.
  2. Walk through:
     - The **Chronological Attack Timeline**:
       1. `12:00:00` — Horizontal TCP SYN Port Scan (`T1046`).
       2. `12:05:00` — C2 Beaconing Channel Established (`T1071.004`).
       3. `12:12:00` — Outbound Data Exfiltration Transfer (`T1048`).
     - Point out the **"Why This Is One Incident"** panel explaining the shared host pivot and attack chain tag.

---

### **Step 5: Evidence Explorer & Explainable SHAP Attribution (3:30 - 4:15)**
- **Presenter Speech:**
  > *"Why did our model flag this exfiltration? In the Evidence Explorer, UDT-X provides full algorithmic transparency. We can inspect the exact TreeSHAP feature attributions showing that `byte_ratio` (+16.4) and `payload_entropy` (7.92 bits/byte) pushed the prediction score to 98% confidence, alongside our 7-day Gaussian baseline comparison showing a +5.4σ anomaly."*
- **Action:**
  1. Click **Evidence Explorer**.
  2. Show the **SHAP Feature Attribution Bar Chart** and the **Baseline vs. Observed Metric Comparisons**.

---

### **Step 6: Network Graph Visualization & Performance Telemetry (4:15 - 5:00)**
- **Presenter Speech:**
  > *"Finally, the Network Graph renders the interactive topology from Neo4j, showing the infected host node connected to the attacker's C2 server and internal gateway. And on our Performance screen, you can see the engine maintaining a steady 125,000 flows/sec throughput with a P99 latency of just 4.18ms, fulfilling all evaluation criteria."*
- **Action:**
  1. Click **Network Graph** (demonstrate interactive zoom and node drag with Cytoscape.js).
  2. Click **Performance** to highlight the real-time latency percentiles and zero Kafka lag.
  3. Conclude the demonstration.
