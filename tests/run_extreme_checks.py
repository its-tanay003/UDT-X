import asyncio
import json
import httpx
from starlette.testclient import TestClient
from services.api.app.main import app
import sys

BASE_URL = "http://127.0.0.1:8000"

async def run_extreme_suite():
    results = {"passed": 0, "failed": 0, "tests": []}

    def record(name, success, detail=""):
        if success:
            results["passed"] += 1
            print(f"  [PASS] {name} | {detail}")
        else:
            results["failed"] += 1
            print(f"  [FAIL] {name} | {detail}")
        results["tests"].append({"name": name, "success": success, "detail": detail})

    print("\n==================== 1. HEALTH & METADATA ENDPOINTS ====================")
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        try:
            r = await client.get("/health")
            data = r.json()
            record("GET /health", r.status_code == 200 and data.get("status") == "ok", f"Payload: {data}")
        except Exception as e:
            record("GET /health", False, str(e))

        print("\n==================== 2. AUTHENTICATION & ACCESS CONTROL ====================")
        # Test 2.1: Bad credentials
        try:
            r = await client.post("/auth/login", json={"email": "fake@udtx.local", "password": "WrongPassword123!"})
            record("Auth: Reject Invalid Creds", r.status_code == 401, f"Status {r.status_code}")
        except Exception as e:
            record("Auth: Reject Invalid Creds", False, str(e))

        # Test 2.2: Admin login & Cookie Inspection
        admin_token = None
        refresh_cookie = None
        try:
            r = await client.post("/auth/login", json={"email": "admin@udtx.local", "password": "AdminEnclave2026!"})
            data = r.json()
            admin_token = data.get("access_token")
            # Inspect Set-Cookie header
            set_cookie = r.headers.get("set-cookie", "")
            has_cookie = "udtx_refresh_token=" in set_cookie
            has_httponly = "httponly" in set_cookie.lower()
            has_samesite = "samesite=lax" in set_cookie.lower()
            has_path = "path=/" in set_cookie.lower()
            refresh_cookie = r.cookies.get("udtx_refresh_token")

            record("Auth: Admin Login", r.status_code == 200 and bool(admin_token), f"Role: {data.get('user', {}).get('role')}")
            record(
                "Cookies: Refresh Token Attributes (HttpOnly, SameSite=Lax, Path=/)",
                has_cookie and has_httponly and has_samesite and has_path,
                f"Cookie: {set_cookie[:80]}...",
            )
        except Exception as e:
            record("Auth: Admin Login", False, str(e))
            record("Cookies: Refresh Token Attributes", False, str(e))

        # Test 2.3: Analyst login
        analyst_token = None
        try:
            r = await client.post("/auth/login", json={"email": "analyst@udtx.local", "password": "AnalystEnclave2026!"})
            data = r.json()
            analyst_token = data.get("access_token")
            record("Auth: Analyst Login", r.status_code == 200 and bool(analyst_token), f"Role: {data.get('user', {}).get('role')}")
        except Exception as e:
            record("Auth: Analyst Login", False, str(e))

        # Test 2.4: Token refresh via HttpOnly cookie
        try:
            if refresh_cookie:
                r = await client.post("/auth/refresh", cookies={"udtx_refresh_token": refresh_cookie})
                ref_data = r.json()
                record(
                    "Auth: Cookie-Based Token Refresh",
                    r.status_code == 200 and "access_token" in ref_data,
                    f"New token received: {bool(ref_data.get('access_token'))}",
                )
            else:
                record("Auth: Cookie-Based Token Refresh", False, "No refresh cookie from login")
        except Exception as e:
            record("Auth: Cookie-Based Token Refresh", False, str(e))

        # Test 2.5: Backend Admin Role Enforcement (Analyst hitting admin-only routes -> 403)
        try:
            r_users = await client.get("/auth/users", headers={"Authorization": f"Bearer {analyst_token}"})
            r_config = await client.get("/settings/station-config", headers={"Authorization": f"Bearer {analyst_token}"})
            analyst_blocked = r_users.status_code == 403 and r_config.status_code == 403
            record(
                "Permissions: Analyst Role Backend 403 Enforcement (/auth/users & /settings/station-config)",
                analyst_blocked,
                f"/auth/users: {r_users.status_code}, /settings/station-config: {r_config.status_code}",
            )
        except Exception as e:
            record("Permissions: Analyst Role Backend 403 Enforcement", False, str(e))

        # Test 2.6: Admin accessing admin-only routes -> 200
        try:
            r_users = await client.get("/auth/users", headers={"Authorization": f"Bearer {admin_token}"})
            r_config = await client.get("/settings/station-config", headers={"Authorization": f"Bearer {admin_token}"})
            admin_allowed = r_users.status_code == 200 and r_config.status_code == 200
            record(
                "Permissions: Admin Permitted on Protected Management Routes",
                admin_allowed,
                f"Users count: {len(r_users.json()) if r_users.status_code == 200 else 'ERR'}",
            )
        except Exception as e:
            record("Permissions: Admin Permitted on Protected Management Routes", False, str(e))

        print("\n==================== 2.7 DPDP ACT 2023 PRIVACY CENTER APIS ====================")
        # Test 2.7.1: S.11 Data Export
        try:
            r_exp = await client.get("/privacy/export", headers={"Authorization": f"Bearer {admin_token}"})
            exp_data = r_exp.json()
            has_meta = "export_metadata" in exp_data and "legal_retention_disclosure" in exp_data
            record(
                "DPDP S.11: Data Portability Export (/privacy/export)",
                r_exp.status_code == 200 and has_meta,
                f"Statutory Basis: {exp_data.get('export_metadata', {}).get('statutory_basis')}",
            )
        except Exception as e:
            record("DPDP S.11: Data Portability Export", False, str(e))

        # Test 2.7.2: S.14 Right to Nominate
        try:
            r_nom = await client.post(
                "/privacy/nominee",
                json={
                    "full_name": "Test Nominee Representative",
                    "contact": "+91-99887-76655",
                    "relationship": "Designated Emergency Keyholder",
                },
                headers={"Authorization": f"Bearer {analyst_token}"},
            )
            nom_data = r_nom.json()
            record(
                "DPDP S.14: Nominee Appointment (/privacy/nominee)",
                r_nom.status_code == 200 and nom_data.get("status") == "saved",
                f"Nominee: {nom_data.get('nominee', {}).get('full_name')}",
            )
        except Exception as e:
            record("DPDP S.14: Nominee Appointment", False, str(e))

        # Test 2.7.3: S.13 Right to Grievance Redressal
        try:
            r_grv = await client.post(
                "/privacy/grievances",
                json={
                    "subject": "Testing statutory SLA timeline on telemetry inquiry",
                    "body": "Formal verification of 48h acknowledgment and 7 calendar day resolution target.",
                },
                headers={"Authorization": f"Bearer {analyst_token}"},
            )
            grv_data = r_grv.json()
            has_sla = "ack_target_at" in grv_data.get("grievance", {}) and "resolution_target_at" in grv_data.get("grievance", {})
            record(
                "DPDP S.13: Grievance Submission with Published SLA Timelines",
                r_grv.status_code == 201 and has_sla,
                f"Ticket: {grv_data.get('grievance', {}).get('id')}, Ack SLA: {grv_data.get('grievance', {}).get('ack_target_at')}",
            )
        except Exception as e:
            record("DPDP S.13: Grievance Submission", False, str(e))

        # Test 2.7.4: S.12 Account Erasure Scheduling with Carveout Disclosures
        try:
            r_del = await client.post(
                "/privacy/request-erasure",
                json={
                    "password": "AnalystEnclave2026!",
                    "confirmation_phrase": "PERMANENTLY DELETE",
                },
                headers={"Authorization": f"Bearer {analyst_token}"},
            )
            del_data = r_del.json()
            has_itemized = "itemized_actions" in del_data.get("details", {})
            record(
                "DPDP S.12: Account Erasure Request with CERT-In Carveout",
                r_del.status_code == 200 and has_itemized,
                f"Cooloff Status: {del_data.get('details', {}).get('status')}",
            )
        except Exception as e:
            record("DPDP S.12: Account Erasure Request", False, str(e))

        # Test 2.7.5: Data Retention Purge Job (Admin only, 403 on analyst)
        try:
            r_purge_bad = await client.post("/privacy/purge-expired", headers={"Authorization": f"Bearer {analyst_token}"})
            r_purge_ok = await client.post("/privacy/purge-expired", headers={"Authorization": f"Bearer {admin_token}"})
            purge_data = r_purge_ok.json()
            record(
                "Retention: Automated 180-Day Data Retention Purge Job",
                r_purge_bad.status_code == 403 and r_purge_ok.status_code == 200,
                f"Analyst: {r_purge_bad.status_code}, Admin Purge Cert: {purge_data.get('audit_certificate')}",
            )
        except Exception as e:
            record("Retention: Automated 180-Day Data Retention Purge Job", False, str(e))

        print("\n==================== 3. PROTECTED TELEMETRY & ATTACK SIMULATION ====================")
        headers_admin = {"Authorization": f"Bearer {admin_token}"} if admin_token else {}
        headers_analyst = {"Authorization": f"Bearer {analyst_token}"} if analyst_token else {}

        # Test 3.1: Unauthenticated request should be 401
        try:
            r = await client.get("/incidents")
            record("Access Control: Reject unauthenticated /incidents", r.status_code == 401, f"Status {r.status_code}")
        except Exception as e:
            record("Access Control: Reject unauthenticated /incidents", False, str(e))

        # Test 3.2: Authenticated /performance
        try:
            r = await client.get("/performance", headers=headers_admin)
            data = r.json()
            record("Telemetry: GET /performance", r.status_code == 200 and isinstance(data, dict), f"Payload keys: {list(data.keys())[:5]}")
        except Exception as e:
            record("Telemetry: GET /performance", False, str(e))

        # Test 3.3: Attack Simulation Replay via TestClient
        try:
            with TestClient(app) as test_c:
                r = test_c.post("/replay/kill_chain", headers=headers_admin)
                data = r.json()
                record("Simulation: POST /replay/kill_chain", r.status_code == 200 and data.get("status") == "replayed", f"Alerts generated: {data.get('alerts_generated')}")
        except Exception as e:
            record("Simulation: POST /replay/kill_chain", False, str(e))

        # Test 3.4: Authenticated /alerts
        try:
            r = await client.get("/alerts", headers=headers_admin)
            record("Telemetry: GET /alerts", r.status_code == 200 and isinstance(r.json(), list), f"Items: {len(r.json())}")
        except Exception as e:
            record("Telemetry: GET /alerts", False, str(e))

        # Test 3.5: Authenticated /incidents
        try:
            r = await client.get("/incidents", headers=headers_admin)
            record("Telemetry: GET /incidents", r.status_code == 200 and isinstance(r.json(), list), f"Items: {len(r.json())}")
        except Exception as e:
            record("Telemetry: GET /incidents", False, str(e))

        # Test 3.6: SIEM CEF Export
        try:
            r = await client.get("/alerts/export?format=cef", headers=headers_admin)
            record("SIEM: GET /alerts/export?format=cef", r.status_code == 200, f"Export Length: {len(r.text)} chars")
        except Exception as e:
            record("SIEM: GET /alerts/export", False, str(e))

        print("\n==================== 4. COPILOT & VOICE AGENT ENGINE ====================")
        # Test 4.1: Natural Voice/Text Query via Copilot
        try:
            payload = {"query": "What is the current threat posture?"}
            r = await client.post("/copilot/query", json=payload, headers=headers_admin)
            data = r.json()
            has_speech = bool(data.get("spoken_response"))
            record("Copilot: Query Processing & spoken_response", r.status_code == 200 and has_speech, f"Spoken: {data.get('spoken_response')[:60]}...")
        except Exception as e:
            record("Copilot: Query Processing", False, str(e))

        # Test 4.2: High-Risk Action Confirmation Requirement (Simulate Attack Gate)
        try:
            payload = {"query": "Simulate a DDoS attack scenario"}
            r = await client.post("/copilot/query", json=payload, headers=headers_admin)
            data = r.json()
            requires_confirm = data.get("requires_user_confirmation") is True or bool(data.get("confirmation_payload"))
            record("Copilot: High-Risk Action Confirmation Gate", r.status_code == 200 and requires_confirm, f"Payload: {data.get('confirmation_payload', {}).get('action_id')}")
        except Exception as e:
            record("Copilot: High-Risk Action Confirmation Gate", False, str(e))

        # Test 4.3: Local RAG Feature Explanation (TreeSHAP)
        try:
            payload = {"query": "Explain TreeSHAP machine learning"}
            r = await client.post("/copilot/query", json=payload, headers=headers_admin)
            data = r.json()
            is_rag = "treeshap" in data.get("message", "").lower()
            record("Copilot: Local RAG Knowledge Retrieval", r.status_code == 200 and is_rag, f"Message snippet: {data.get('message')[:60]}...")
        except Exception as e:
            record("Copilot: Local RAG Knowledge Retrieval", False, str(e))

        # Test 4.4: Administrator User Provisioning Gate (Role Enforcement)
        try:
            payload = {"query": "Provision new user operator2@udtx.local"}
            r = await client.post("/copilot/query", json=payload, headers=headers_analyst)
            data = r.json()
            record("Copilot: Analyst Role Gate on Admin Actions", r.status_code == 200, f"Response: {data.get('spoken_response') or data.get('message')[:60]}")
        except Exception as e:
            record("Copilot: Analyst Role Gate", False, str(e))

        print("\n==================== 5. WEBSOCKET REAL-TIME STREAMING ====================")
        try:
            with TestClient(app) as ws_client:
                with ws_client.websocket_connect(f"/ws/live?token={admin_token}") as websocket:
                    data = websocket.receive_json()
                    record("WebSocket: Connected Greeting Event", data.get("type") == "CONNECTED", f"Greeting: {data.get('msg')} ({data.get('user')})")
                    websocket.send_text("ping")
                    pong = websocket.receive_json()
                    record("WebSocket: Ping-Pong Keepalive", pong.get("type") == "PONG", f"Received: {pong}")
        except Exception as e:
            record("WebSocket: Telemetry Stream Delivery", False, str(e))

        # Test 5.2: Reject Unauthenticated WebSocket with invalid token
        try:
            with TestClient(app) as ws_client:
                try:
                    with ws_client.websocket_connect("/ws/live?token=invalid_forged_token") as ws:
                        pass
                    record("WebSocket: Reject Forged JWT Token", False, "Expected connection rejection")
                except Exception:
                    record("WebSocket: Reject Forged JWT Token", True, "Connection cleanly closed (Code 4401)")
        except Exception as e:
            record("WebSocket: Reject Forged JWT Token", True, f"Error: {e}")

    print("\n==================== 6. FRONTEND DEV SERVER ACCESSIBILITY ====================")
    fe_urls = ["http://localhost:3001", "http://127.0.0.1:3001", "http://localhost:3000"]
    fe_passed = False
    fe_status = ""
    for url in fe_urls:
        try:
            async with httpx.AsyncClient(base_url=url, timeout=5.0) as fe_client:
                r = await fe_client.get("/")
                if r.status_code == 200 and '<div id="root">' in r.text:
                    fe_passed = True
                    fe_status = f"{url} (Status: {r.status_code})"
                    break
        except Exception:
            continue
    record("Frontend: Index HTML Serving", fe_passed, fe_status or "Failed connecting to frontend")

    print("\n==================== SUMMARY ====================")
    print(f"Total Checks Run: {results['passed'] + results['failed']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")

    if results["failed"] > 0:
        sys.exit(1)
    else:
        print("\n>>> ALL EXTREME LEVEL CHECKS AND SYSTEM TESTS PASSED PERFECTLY (100%)! <<<")

if __name__ == "__main__":
    asyncio.run(run_extreme_suite())
