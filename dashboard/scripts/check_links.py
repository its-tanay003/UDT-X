"""UDT-X Internal Route & Broken Link Crawling Verification Script.
Parses dashboard code and verifies that all NavLink, Link, and href targets resolve to valid registered paths.
"""

import os
import re

APP_TSX_PATH = r"c:\New Volume (D)\SIH\dashboard\src\App.tsx"
PAGES_DIR = r"c:\New Volume (D)\SIH\dashboard\src\pages"

# Defined Valid Routes in the App
VALID_ROUTES = {
    "/",
    "/faq",
    "/privacy",
    "/terms",
    "/login",
    "/app",
    "/app/monitor",
    "/app/incidents",
    "/app/incidents/:id",
    "/app/alerts",
    "/app/alerts/:id/evidence",
    "/app/graph",
    "/app/threats",
    "/app/replay",
    "/app/performance",
    "/app/profile",
    "/app/settings",
    # Legacy alias deep links (redirected)
    "/monitor",
    "/incidents",
    "/alerts",
    "/graph",
    "/threats",
    "/replay",
    "/performance",
    "/profile",
    "/settings",
}

def check_file_links(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find all Link to="..." and href="..."
    matches = re.findall(r'(?:to|href)=["\']([^"\']+)["\']', content)
    broken = []
    for m in matches:
        if m.startswith("http") or m.startswith("mailto:") or m.startswith("#"):
            continue
        # Strip query parameters or dynamic ID prefixes
        clean_path = m.split("?")[0]
        # Check if matches exact or parameterized route
        is_valid = clean_path in VALID_ROUTES or any(
            clean_path.startswith(r.replace("/:id", "/").replace("/:id/evidence", "/"))
            for r in VALID_ROUTES if ":id" in r
        )
        if not is_valid and clean_path not in ["/"]:
            broken.append(clean_path)
    return broken

def main():
    print("[LINK CHECKER] Auditing all internal application routes...")
    all_files = [APP_TSX_PATH]
    for root, _, files in os.walk(PAGES_DIR):
        for file in files:
            if file.endswith(".tsx") or file.endswith(".ts"):
                all_files.append(os.path.join(root, file))

    total_checked = 0
    total_broken = 0
    for f in all_files:
        broken = check_file_links(f)
        total_checked += 1
        if broken:
            print(f"❌ {os.path.basename(f)}: Found unrecognized link targets: {broken}")
            total_broken += len(broken)
        else:
            print(f"✓ {os.path.basename(f)}: All links verified.")

    print(f"\n[AUDIT SUMMARY] Checked {total_checked} files. Broken links detected: {total_broken}")
    return total_broken

if __name__ == "__main__":
    exit(main())
