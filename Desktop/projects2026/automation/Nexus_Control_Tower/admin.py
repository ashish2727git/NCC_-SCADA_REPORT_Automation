import sqlite3
import shutil
import os
import sys

DB_FILE = "nexus_db.sqlite"
ARTIFACTS_DIR = "artifacts"

def get_db():
    return sqlite3.connect(DB_FILE)

def add_license():
    key = input("Enter new license key (e.g., NEXUS-2026-ABC): ").strip()
    client = input("Enter client name: ").strip()
    
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO licenses (key, client_name) VALUES (?, ?)", (key, client))
        conn.commit()
        print(f"✅ License {key} created successfully for {client}.")
    except sqlite3.IntegrityError:
        print("❌ Error: License key already exists.")
    conn.close()

def upload_release():
    version = input("Enter version string (e.g., 14.0): ").strip()
    file_path = input("Enter full path to the executable or zip file: ").strip()
    
    if not os.path.exists(file_path):
        print("❌ Error: File not found.")
        return
    
    filename = os.path.basename(file_path)
    dest_path = os.path.join(ARTIFACTS_DIR, filename)
    
    print(f"Copying {filename} to artifacts directory...")
    shutil.copy2(file_path, dest_path)
    
    conn = get_db()
    c = conn.cursor()
    # Demote old latest
    c.execute("UPDATE versions SET is_latest = 0 WHERE is_latest = 1")
    # Insert new
    c.execute("INSERT INTO versions (version_str, filename, is_latest) VALUES (?, ?, 1)", (version, filename))
    conn.commit()
    conn.close()
    
    print(f"✅ Release {version} ({filename}) uploaded and set as LATEST.")

def list_licenses():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT key, client_name, hwid, is_active FROM licenses")
    rows = c.fetchall()
    print("\n--- ACTIVE LICENSES ---")
    for r in rows:
        status = "ACTIVE" if r[3] else "REVOKED"
        hw = r[2] if r[2] else "Unbound"
        print(f"Key: {r[0]} | Client: {r[1]} | Status: {status} | HWID: {hw}")
    print("-----------------------\n")
    conn.close()

if __name__ == "__main__":
    while True:
        print("\n=== NEXUS CONTROL TOWER ADMIN ===")
        print("1. Generate New License")
        print("2. Upload New App Version (OTA)")
        print("3. List All Licenses")
        print("4. Exit")
        
        choice = input("Select an option: ")
        
        if choice == "1":
            add_license()
        elif choice == "2":
            upload_release()
        elif choice == "3":
            list_licenses()
        elif choice == "4":
            sys.exit(0)
        else:
            print("Invalid choice.")
