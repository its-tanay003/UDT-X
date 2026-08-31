# Terms and Conditions of Use

**Effective Date:** August 31, 2026  
**Platform:** Unified Dynamic Threat Identification and Defense Platform (UDT-X)  
**Version:** 1.0.0 Enterprise  

---

## 1. Acceptance of Terms

By deploying, accessing, compiling, or using the UDT-X Platform (including its backend microservices, detection heuristics, machine learning inference engines, and React SOC dashboard), you agree to be bound by these Terms and Conditions and all applicable laws and regulations. If you do not agree with any of these terms, you are prohibited from using or accessing this software.

---

## 2. License & Intellectual Property

UDT-X is distributed under the terms of the **MIT License** (see [LICENSE](LICENSE)). You are free to inspect, modify, fork, and distribute the software in accordance with the license conditions, subject to the safety and ethical restrictions outlined below.

---

## 3. Passive Monitoring & Authorization Requirement

- **Authorized Enclave Deployment Only:** UDT-X is designed strictly for passive, read-only network monitoring on networks, mirror ports, or data diodes for which you have explicit, documented authorization to capture and inspect telemetry.
- **Privacy Compliance:** Organizations deploying UDT-X are solely responsible for ensuring compliance with local, national, and international privacy laws (e.g., GDPR, HIPAA, Indian DPDP Act) regarding packet inspection and metadata logging.

---

## 4. Replay Lab & Attack Simulation Ethical Use

- **Controlled Lab Environments Only:** The `replay_lab/` attack simulation engine and scripts are provided **exclusively for defensive benchmarking, model validation, and security training** in isolated lab networks.
- **Prohibition on Unauthorized Testing:** You agree **never** to use any UDT-X scenario generator against external networks, third-party infrastructure, or unauthorized endpoints without written consent. The software includes safety mechanisms (`replay_lab/safety.py`) designed to prevent accidental transmission on non-loopback interfaces; tampering with these guards to launch unauthorized attacks is strictly prohibited.

---

## 5. Disclaimer of Warranties

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, HIGH-AVAILABILITY DEFENSE, AND NON-INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS, CONTRIBUTORS, OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES, DATA LOSS, OR OTHER LIABILITY ARISING FROM THE USE OF OR INABILITY TO USE THE PLATFORM.

---

## 6. Modifications & Updates

The maintainers reserve the right to revise these Terms and Conditions at any time. By continuing to use the software after updates are committed to the repository, you accept and agree to the revised terms.
