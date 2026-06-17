import os
import subprocess
import hashlib
import boto3
import time

REGION     = "ap-south-1"
BUCKET     = "nexus-sync-artifacts-802346121670"

spec_file   = "NexusSyncPro_Advanced.spec"
local_exe   = "dist/Ashish_Kumar_NexusSyncPro_v15.4-BETA.exe"
s3_key      = "beta/Ashish_Kumar_NexusSyncPro_v15.4-BETA.exe"

# ── Step 1: Patch spec name to BETA ──────────────────────────────────────────
print("\nStep 1: Patching spec exe name for BETA build...")
with open(spec_file, "r", encoding="utf-8") as f:
    spec_src = f.read()

# Replace any previous beta tag or production name
patched_spec = spec_src.replace(
    "name='Ashish_Kumar_NexusSyncPro'",
    "name='Ashish_Kumar_NexusSyncPro_v15.4-BETA'"
).replace(
    "name='Ashish_Kumar_NexusSyncPro_v15.3-BETA'",
    "name='Ashish_Kumar_NexusSyncPro_v15.4-BETA'"
)

with open(spec_file, "w", encoding="utf-8") as f:
    f.write(patched_spec)
print("   Spec patched.")

# ── Step 2: Build exe ─────────────────────────────────────────────────────────
print("\nStep 2: Building BETA executable with PyInstaller...")
result = subprocess.run(["pyinstaller", "--clean", "-y", spec_file])
if result.returncode != 0:
    print("[FAIL] PyInstaller build failed.")
    with open(spec_file, "w", encoding="utf-8") as f:
        f.write(spec_src)
    exit(1)
print("   Build successful!")

# Restore spec to production name
with open(spec_file, "w", encoding="utf-8") as f:
    f.write(spec_src)
print("   Spec restored to production name.")

# ── Step 3: Hash ──────────────────────────────────────────────────────────────
print("\nStep 3: Computing SHA-256 hash...")
if not os.path.exists(local_exe):
    print(f"[FAIL] Exe not found at: {local_exe}")
    exit(1)

sha256_hash = hashlib.sha256()
with open(local_exe, "rb") as f:
    for chunk in iter(lambda: f.read(65536), b""):
        sha256_hash.update(chunk)
binary_hash = sha256_hash.hexdigest()
print(f"   SHA-256: {binary_hash}")

# ── Step 4: Upload to S3 /beta/ ───────────────────────────────────────────────
print(f"\nStep 4: Uploading BETA to s3://{BUCKET}/{s3_key}...")
s3 = boto3.client("s3", region_name=REGION)
s3.upload_file(local_exe, BUCKET, s3_key,
               ExtraArgs={"ContentType": "application/octet-stream"})
print("   Upload successful!")

# ── Step 5: Generate 7-day presigned URL ─────────────────────────────────────
print("\nStep 5: Generating 7-day download link...")
try:
    download_url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": BUCKET, "Key": s3_key},
        ExpiresIn=604800
    )
except Exception as e:
    download_url = f"(failed: {e})"

print("\n" + "="*72)
print("  BETA BUILD COMPLETE  --  TESTERS ONLY, DO NOT BROADCAST")
print("="*72)
print(f"  Version  : v15.4-BETA")
print(f"  SHA-256  : {binary_hash}")
print(f"  S3 Path  : s3://{BUCKET}/{s3_key}")
print(f"  Download : {download_url}")
print("="*72)
print("  NOT published to Control Tower.")
print("  Production clients remain on v15.2.")
print()

# ── Step 6: Save build info locally ──────────────────────────────────────────
info_path = "dist/v15.4-beta-build-info.txt"
with open(info_path, "w") as f:
    f.write(f"Version: 15.4-BETA\n")
    f.write(f"Built  : {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"SHA-256: {binary_hash}\n")
    f.write(f"S3     : s3://{BUCKET}/{s3_key}\n")
    f.write(f"DL URL : {download_url}\n")
    f.write(f"Status : BETA - NOT published to OTA server\n")
print(f"   Build info saved to: {info_path}")
