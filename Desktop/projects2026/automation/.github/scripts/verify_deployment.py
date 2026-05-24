#!/usr/bin/env python3
"""
Post-deployment verification: checks that the update and download endpoints
are working correctly and that the downloaded file is a valid Windows EXE.
Exits with code 1 on failure to fail the CI/CD pipeline.
"""
import requests
import sys

BASE_URL = "http://devash.in"

print("=" * 50)
print("Post-Deployment Verification")
print("=" * 50)

# --- Step 1: Update check endpoint ---
print("\n[1] Checking /api/update_check ...")
try:
    r1 = requests.get(f"{BASE_URL}/api/update_check", timeout=10)
    print(f"    HTTP {r1.status_code} | {r1.text[:100]}")
    if r1.status_code != 200:
        print("FAIL: update_check returned non-200")
        sys.exit(1)
    data = r1.json()
    print(f"    Latest version: {data.get('latest_version')}")
    print("    PASS")
except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)

# --- Step 2: Download endpoint ---
print("\n[2] Checking /download/latest.exe ...")
try:
    r2 = requests.get(f"{BASE_URL}/download/latest.exe", timeout=90)
    print(f"    HTTP {r2.status_code} | Size: {len(r2.content):,} bytes")

    if r2.status_code != 200:
        print(f"FAIL: download returned HTTP {r2.status_code}")
        print(f"    Body: {r2.content[:120]}")
        sys.exit(1)

    if r2.content[:2] != b"MZ":
        print("FAIL: downloaded file is NOT a valid Windows EXE (missing MZ header)")
        print(f"    Got: {r2.content[:60]}")
        sys.exit(1)

    size_mb = len(r2.content) / 1024 / 1024
    if size_mb < 10:
        print(f"FAIL: file too small ({size_mb:.1f} MB) — likely an error page")
        sys.exit(1)

    print(f"    Valid EXE: {size_mb:.1f} MB with MZ header")
    print("    PASS")
except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)

# --- Step 3: /download_latest endpoint ---
print("\n[3] Checking /download_latest ...")
try:
    r3 = requests.get(f"{BASE_URL}/download_latest", timeout=90)
    print(f"    HTTP {r3.status_code} | Size: {len(r3.content):,} bytes")

    if r3.status_code == 200 and r3.content[:2] == b"MZ":
        print(f"    Valid EXE: {len(r3.content)/1024/1024:.1f} MB")
        print("    PASS")
    elif r3.status_code in (301, 302, 307, 308):
        print(f"    Redirect to: {r3.headers.get('location','?')[:80]}")
        print("    PASS (redirect)")
    else:
        print(f"FAIL: /download_latest returned HTTP {r3.status_code}")
        print(f"    Body: {r3.content[:120]}")
        sys.exit(1)
except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("All checks PASSED - deployment is healthy")
print("=" * 50)
