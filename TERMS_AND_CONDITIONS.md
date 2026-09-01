# Terms and Conditions of Use & Enterprise Warranty Framework

**Effective Date:** August 31, 2026  
**Platform:** Unified Dynamic Threat Identification and Defense Platform (UDT-X)  
**License:** Apache License, Version 2.0  
**Version:** 1.0.0 Enterprise Defense Edition  

---

## 1. Acceptance of Terms

By deploying, compiling, accessing, or integrating the UDT-X Platform (including its Kafka telemetry consumers, Rust/Python normalizers, heuristic detection microservices, LightGBM TreeSHAP explainability engine, Neo4j temporal graph correlator, and React SOC mission-control dashboard), you agree to be bound by these Terms and Conditions and the [Apache License 2.0](LICENSE).

---

## 2. Open Source Licensing & Patent Grants

UDT-X is distributed as open-source software under the **Apache License, Version 2.0**:
- **Perpetual Royalty-Free License:** Full rights to run, modify, distribute, and commercially deploy the platform.
- **Express Patent Grant:** Every contributor grants a perpetual, irrevocable patent license covering their contributions, protecting downstream users and enterprises against patent litigation.
- **Trademark Protection:** Use of the UDT-X name, logo, or badges in marketing requires adherence to customary descriptive references without implying endorsement.

---

## 3. Commercial Warranty & Enterprise SLA Addendum (Apache 2.0 Section 9)

Pursuant to **Section 9 of the Apache License 2.0 (*Accepting Warranty or Additional Liability*)**, distributors, vendors, and enterprise integrators are explicitly permitted to:
1. **Offer Commercial Support & Maintenance:** Provide paid technical support, 24/7 incident response, and mission-control enclave deployment services.
2. **Provide Service Level Agreements (SLAs):** Guarantee sub-5ms P99 pipeline latency and 99.999% high-availability uptime under custom enterprise agreements.
3. **Accept Additional Liability & Indemnification:** Issue custom liability warranties, compliance indemnifications (e.g. ISO 27001, SOC 2, NIST 800-53), and cybersecurity insurance coverage directly to end-user organizations under separate bilateral contracts.

> **Default Community Provision:** In the absence of an executed Enterprise Support Agreement, the open-source software is provided on an *"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND*.

---

## 4. Passive Monitoring & Authorization Requirement

- **Authorized Enclave Deployment Only:** UDT-X is designed strictly for passive, read-only network monitoring on networks, mirror ports, or data diodes for which you have explicit, documented authorization to capture and inspect telemetry.
- **Privacy Compliance:** Organizations deploying UDT-X are solely responsible for ensuring compliance with local, national, and international privacy laws (e.g., GDPR, HIPAA, Indian DPDP Act) regarding packet inspection and metadata logging.

---

## 5. Replay Lab & Attack Simulation Ethical Use

- **Controlled Lab Environments Only:** The `replay_lab/` attack simulation engine and scripts are provided **exclusively for defensive benchmarking, model validation, and security training** in isolated lab networks.
- **Prohibition on Unauthorized Testing:** You agree **never** to use any UDT-X scenario generator against external networks, third-party infrastructure, or unauthorized endpoints without written consent. The software includes safety mechanisms (`replay_lab/safety.py`) designed to prevent accidental transmission on non-loopback interfaces; tampering with these guards to launch unauthorized attacks is strictly prohibited.

---

## 6. Modifications & Updates

The maintainers reserve the right to revise these Terms and Conditions at any time. Updates will be tracked transparently in the repository [CHANGELOG.md](CHANGELOG.md).
