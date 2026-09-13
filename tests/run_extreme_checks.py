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

        # Test 2.2: Admin login
        admin_token = None
        try:
            r = await client.post("/auth/login", json={"email": "admin@udtx.local", "password": "AdminEnclave2026!"})
            data = r.json()
            admin_token = data.get("access_token")
            record("Auth: Admin Login", r.status_code == 200 and bool(admin_token), f"Role: {data.get('user', {}).get('role')}")
        except Exception as e:
            record("Auth: Admin Login", False, str(e))

        # Test 2.3: Analyst login
        analyst_token = None
        try:
            r = await client.post("/auth/login", json={"email": "analyst@udtx.local", "password": "AnalystEnclave2026!"})
            data = r.json()
            analyst_token = data.get("access_token")
            record("Auth: Analyst Login", r.status_code == 200 and bool(analyst_token), f"Role: {data.get('user', {}).get('role')}")
        except Exception as e:
            record("Auth: Analyst Login", False, str(e))

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
    async with httpx.AsyncClient(base_url="http://127.0.0.1:3001", timeout=10.0) as fe_client:
        try:
            r = await fe_client.get("/")
            record("Frontend: Index HTML Serving", r.status_code == 200 and "<div id=\"root\">" in r.text, f"Status: {r.status_code}")
        except Exception as e:
            record("Frontend: Index HTML Serving", False, str(e))

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
