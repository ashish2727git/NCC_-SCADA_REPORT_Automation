"""
=============================================================
  NEXUS CONTROL TOWER — Admin CLI
  Talks directly to the live API at devash.in
=============================================================
"""
import sys
import secrets
import string
import requests

BASE_URL = "http://devash.in"   # ← your live server

# ─── Helpers ─────────────────────────────────────────────────────────────────

def generate_key():
    """Generate a random NEXUS-XXXX-XXXX-XXXX style key."""
    alphabet = string.ascii_uppercase + string.digits
    parts = ["".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(3)]
    return "NEXUS-" + "-".join(parts)

def api_post(endpoint, payload):
    try:
        r = requests.post(f"{BASE_URL}{endpoint}", json=payload, timeout=10)
        return r
    except requests.ConnectionError:
        print(f"\n❌ Cannot reach {BASE_URL}. Is the server online?")
        return None

def api_get(endpoint):
    try:
        r = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        return r
    except requests.ConnectionError:
        print(f"\n❌ Cannot reach {BASE_URL}. Is the server online?")
        return None

# ─── Actions ─────────────────────────────────────────────────────────────────

def generate_license():
    client = input("Enter client name: ").strip()
    if not client:
        print("❌ Client name cannot be empty.")
        return

    key = generate_key()
    r = api_post("/api/admin/add_license", {"key": key, "client_name": client})
    if r and r.status_code == 200:
        print(f"\n✅ License created successfully!")
        print(f"   Client : {client}")
        print(f"   Key    : {key}")
        print(f"\n   👉 Send this key to your client. It will bind to their device on first use.\n")
    elif r:
        print(f"❌ Server error: {r.status_code} — {r.text}")


def revoke_license():
    key = input("Enter the license key to revoke: ").strip()
    r = api_post("/api/admin/revoke_license", {"key": key})
    if r and r.status_code == 200:
        print(f"✅ License {key} has been revoked.")
    elif r:
        print(f"❌ Server error: {r.status_code} — {r.text}")


def list_licenses():
    r = api_get("/api/admin/list_licenses")
    if r and r.status_code == 200:
        data = r.json()
        if not data:
            print("\n  (No licenses found)")
            return
        print(f"\n{'KEY':<25} {'CLIENT':<20} {'STATUS':<10} {'HWID'}")
        print("-" * 80)
        for lic in data:
            hw = lic.get("hwid") or "Unbound"
            status = "ACTIVE" if lic.get("is_active") else "REVOKED"
            print(f"{lic['key']:<25} {lic['client_name']:<20} {status:<10} {hw}")
        print()
    elif r:
        print(f"❌ Server error: {r.status_code} — {r.text}")


def check_server():
    r = api_get("/api/health")
    if r and r.status_code == 200:
        print(f"✅ Server is ONLINE at {BASE_URL}")
    elif r:
        print(f"⚠️  Server responded with {r.status_code}")
    else:
        print(f"❌ Server is OFFLINE or unreachable")


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    while True:
        print("\n╔══════════════════════════════════════╗")
        print("║   NEXUS CONTROL TOWER — ADMIN CLI    ║")
        print("╠══════════════════════════════════════╣")
        print("║  1. Generate New License Key         ║")
        print("║  2. Revoke a License Key             ║")
        print("║  3. List All Licenses                ║")
        print("║  4. Check Server Status              ║")
        print("║  5. Exit                             ║")
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
            sys.exit(0)
        else:
            print("Invalid option.")
