# Security Policy & Vulnerability Disclosure

## 🛡️ Supported Versions

We provide security updates and patches for the following versions of the UDT-X Platform:

| Version | Supported |
|---|---|
| `1.0.x` (Enterprise / Current) | :white_check_mark: Supported |
| `< 1.0.0` | :x: End of Life |

---

## 🔒 Reporting a Vulnerability

The UDT-X security engineering team takes the security of our platform and monitored environments seriously. If you discover a potential security vulnerability, please follow responsible disclosure practices:

1. **Do NOT file a public GitHub issue.**
2. Send an email with a detailed vulnerability report to:  
   📧 **security@udtx-platform.local** / **team@udtx.io**
3. Include the following details in your advisory:
   - Type of vulnerability (e.g., Cypher injection, buffer overflow, authentication bypass, data leakage)
   - Step-by-step reproduction instructions or proof-of-concept (PoC)
   - Impact assessment and affected components (e.g., `services/api`, `normalizer`, `correlation`)
   - Any proposed remediation or mitigation patches

### Response Timeline
- **Initial Acknowledgment:** Within 48 hours of receipt.
- **Triage & Validation:** Within 5 business days.
- **Patch & Advisory Release:** Coordinated disclosure once fixes are tested and merged.

---

## 🔐 Security Architecture Highlights

UDT-X incorporates defense-in-depth security principles:
- **Zero-Trust Network Isolation:** Microservices communicate strictly over private container bridge networks.
- **Fail-Open Dead-Letter Queueing:** Corrupt, malformed, or malicious ingestion packets are routed to `raw-events-dlq` to prevent sensor blinding or memory corruption.
- **Strict Pydantic v2 Models:** Rejecting unknown fields (`extra="forbid"`) and validating RFC IP formats across all endpoints.
- **Replay Lab Safety Guard:** `replay_lab/safety.py` programmatically terminates packet generation if non-isolated physical network interfaces are targeted.
