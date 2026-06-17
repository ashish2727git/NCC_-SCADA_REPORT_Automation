import os
import subprocess
import hashlib
import requests
import boto3

ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "YOUR_ACCESS_KEY")
SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "YOUR_SECRET_KEY")
REGION = "ap-south-1"
BUCKET = "nexus-sync-artifacts-802346121670"

spec_file = "NexusSyncPro_Advanced.spec"
local_exe = "dist/Ashish_Kumar_NexusSyncPro.exe"
s3_filename = "Ashish_Kumar_NexusSyncPro_v15.6.exe"
s3_key = f"releases/{s3_filename}"

print("Step 1: Building client executable using PyInstaller...")
cmd = ["pyinstaller", "--clean", "-y", spec_file]
result = subprocess.run(cmd, cwd="..", capture_output=True, text=True)
if result.returncode != 0:
    print("Build failed!")
    print(result.stderr)
    exit(1)
print("Build successful!")

exe_path = os.path.join("..", local_exe)
if not os.path.exists(exe_path):
    print(f"Error: Executable not found at {exe_path}")
    exit(1)

print("Step 2: Calculating SHA-256 hash of the binary...")
sha256_hash = hashlib.sha256()
with open(exe_path, "rb") as f:
    for byte_block in iter(lambda: f.read(4096), b""):
        sha256_hash.update(byte_block)
binary_hash = sha256_hash.hexdigest()
print(f"SHA-256 Hash: {binary_hash}")

print(f"Step 3: Uploading binary to S3: s3://{BUCKET}/{s3_key}...")
s3 = boto3.client(
    's3',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name=REGION
)
s3.upload_file(exe_path, BUCKET, s3_key)
print("Upload successful!")

print("Step 4: Publishing version 15.6 to Control Tower server...")
url = "http://devash.in/api/admin/publish_version"
payload = {
    "version_str": "15.6",
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
