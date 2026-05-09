# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
=============================================================
  NEXUS CONTROL TOWER -- Admin CLI
  Generates keys instantly, then syncs to the live server.
=============================================================
"""
import sys
import secrets
import string
import requests

BASE_URL = "http://devash.in"

def generate_key():
    """Generate a random NEXUS-XXXX-XXXX-XXXX style key."""
    alphabet = string.ascii_uppercase + string.digits
    parts = ["".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(3)]
    return "NEXUS-" + "-".join(parts)


def generate_license():
    client = input("Enter client name: ").strip()
    if not client:
        print("❌ Client name cannot be empty.")
        return

    # Generate key IMMEDIATELY (no server needed yet)
    key = generate_key()

    print(f"\n{'='*50}")
    print(f"  ✅ LICENSE KEY GENERATED")
    print(f"{'='*50}")
    print(f"  Client : {client}")
    print(f"  Key    : {key}")
    print(f"{'='*50}")
    print(f"\n  👉 Send this key to your client.")
    print(f"     It binds to their device on first use.\n")

    # Now try to register it on the live server
    print("  Registering key on live server...")
    try:
        r = requests.post(
            f"{BASE_URL}/api/admin/add_license",
            json={"key": key, "client_name": client},
            timeout=10
        )
        if r.status_code == 200:
            print("  ✅ Key registered on server successfully.\n")
        elif r.status_code == 404:
            print("  ⚠️  Server not updated yet. Save this key — re-register it later with option 5.\n")
        else:
            print(f"  ⚠️  Server responded: {r.status_code} — {r.text}\n")
    except Exception as e:
        print(f"  ⚠️  Could not reach server: {e}")
        print(f"  Save this key and re-register later with option 5.\n")


def revoke_license():
    key = input("Enter the license key to revoke: ").strip()
    try:
        r = requests.post(f"{BASE_URL}/api/admin/revoke_license", json={"key": key}, timeout=10)
        if r.status_code == 200:
            print(f"✅ License {key} has been revoked.")
        else:
            print(f"❌ Server error: {r.status_code} — {r.text}")
    except Exception as e:
        print(f"❌ Could not reach server: {e}")


def list_licenses():
    try:
        r = requests.get(f"{BASE_URL}/api/admin/list_licenses", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if not data:
                print("\n  (No licenses registered on server yet)")
                return
            print(f"\n{'KEY':<25} {'CLIENT':<20} {'STATUS':<10} {'HWID'}")
            print("-" * 80)
            for lic in data:
                hw = lic.get("hwid") or "Unbound"
                status = "ACTIVE" if lic.get("is_active") else "REVOKED"
                print(f"{lic['key']:<25} {lic['client_name']:<20} {status:<10} {hw}")
            print()
        else:
            print(f"❌ Server error: {r.status_code} — {r.text}")
    except Exception as e:
        print(f"❌ Could not reach server: {e}")


def register_existing():
    """Register a previously generated key onto the server."""
    key = input("Enter key to register: ").strip()
    client = input("Enter client name: ").strip()
    try:
        r = requests.post(f"{BASE_URL}/api/admin/add_license", json={"key": key, "client_name": client}, timeout=10)
        if r.status_code == 200:
            print(f"✅ Key {key} registered on server for {client}.")
        elif r.status_code == 409:
            print(f"⚠️  Key already exists on server.")
        else:
            print(f"❌ Server error: {r.status_code} — {r.text}")
    except Exception as e:
        print(f"❌ Could not reach server: {e}")


def check_server():
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=10)
        if r.status_code == 200:
            print(f"✅ Server is ONLINE at {BASE_URL}")
        else:
            print(f"⚠️  Server responded with {r.status_code}")
    except Exception as e:
        print(f"❌ Server is OFFLINE: {e}")


if __name__ == "__main__":
    while True:
        print("\n╔══════════════════════════════════════╗")
        print("║   NEXUS CONTROL TOWER — ADMIN CLI    ║")
        print("╠══════════════════════════════════════╣")
        print("║  1. Generate New License Key         ║")
        print("║  2. Revoke a License Key             ║")
        print("║  3. List All Licenses (from server)  ║")
        print("║  4. Check Server Status              ║")
        print("║  5. Register Existing Key on Server  ║")
        print("║  6. Exit                             ║")
        print("╚══════════════════════════════════════╝")

        choice = input("Select option: ").strip()

        if choice == "1":
            generate_license()
        elif choice == "2":
            revoke_license()
        elif choice == "3":
            list_licenses()
        elif choice == "4":
            check_server()
        elif choice == "5":
            register_existing()
        elif choice == "6":
            sys.exit(0)
        else:
            print("Invalid option.")
