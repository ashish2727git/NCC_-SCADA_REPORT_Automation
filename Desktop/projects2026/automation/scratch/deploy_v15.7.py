import os
import subprocess
import hashlib
import requests
import boto3
import re

REGION = "ap-south-1"
BUCKET = "nexus-sync-artifacts-802346121670"

spec_file = "NexusSyncPro_Advanced.spec"
local_exe = "dist/Ashish_Kumar_NexusSyncPro.exe"
s3_filename = "Ashish_Kumar_NexusSyncPro_v15.7.exe"
s3_key = f"releases/{s3_filename}"

# Step 0: Read credentials from deploy_v15.5.py dynamically
scratch_dir = os.path.dirname(os.path.abspath(__file__))
v15_5_path = os.path.join(scratch_dir, "deploy_v15.5.py")
print(f"Reading S3 credentials from {v15_5_path}...")
with open(v15_5_path, "r", encoding="utf-8") as f:
    deploy_content = f.read()

access_key = re.search(r'ACCESS_KEY\s*=\s*"([^"]+)"', deploy_content).group(1)
secret_key = re.search(r'SECRET_KEY\s*=\s*"([^"]+)"', deploy_content).group(1)

# Step 1: Patch spec file in parent directory to name='Ashish_Kumar_NexusSyncPro'
spec_path = os.path.join(scratch_dir, "..", spec_file)
print(f"Step 1: Patching {spec_path} to use production name...")
with open(spec_path, "r", encoding="utf-8") as f:
    spec_src = f.read()

patched_spec = spec_src.replace(
    "name='Ashish_Kumar_NexusSyncPro_v15.4-BETA'",
    "name='Ashish_Kumar_NexusSyncPro'"
)

with open(spec_path, "w", encoding="utf-8") as f:
    f.write(patched_spec)

try:
    print("Step 2: Building client executable using PyInstaller...")
    # Run PyInstaller with clean cache
    cmd = ["pyinstaller", "--clean", "-y", spec_file]
    result = subprocess.run(cmd, cwd=os.path.join(scratch_dir, ".."), capture_output=True, text=True)
    if result.returncode != 0:
        print("Build failed!")
        print(result.stderr)
        exit(1)
    print("Build successful!")
finally:
    # Always restore the spec file
    print("Restoring spec file to beta name...")
    with open(spec_path, "w", encoding="utf-8") as f:
        f.write(spec_src)

exe_path = os.path.join(scratch_dir, "..", local_exe)
if not os.path.exists(exe_path):
    print(f"Error: Executable not found at {exe_path}")
    exit(1)

print("Step 3: Calculating SHA-256 hash of the binary...")
sha256_hash = hashlib.sha256()
with open(exe_path, "rb") as f:
    for byte_block in iter(lambda: f.read(4096), b""):
        sha256_hash.update(byte_block)
binary_hash = sha256_hash.hexdigest()
print(f"SHA-256 Hash: {binary_hash}")

print(f"Step 4: Uploading binary to S3: s3://{BUCKET}/{s3_key}...")
s3 = boto3.client(
    's3',
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name=REGION
)
s3.upload_file(exe_path, BUCKET, s3_key)
print("Upload successful!")

print("Step 5: Publishing version 15.7 to Control Tower server...")
url = "http://devash.in/api/admin/publish_version"
payload = {
    "version_str": "15.7",
    "filename": s3_filename,
    "admin_secret": "nexus-admin-2026",
    "sha256": binary_hash
}
try:
    resp = requests.post(url, json=payload, timeout=10)
    print("Status:", resp.status_code)
    print("Response:", resp.json())
except Exception as e:
    print(f"Failed to publish to server: {e}")
