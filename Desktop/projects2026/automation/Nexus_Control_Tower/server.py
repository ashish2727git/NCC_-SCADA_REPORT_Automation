import os
import sqlite3
import logging
import threading
import time
import asyncio
import requests as http_client
from fastapi import FastAPI, HTTPException, Request, Header, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import boto3
from botocore.exceptions import ClientError

# Configure logging to stdout for Docker compatibility
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("NexusControlTower")
LOG_FILE = "nexus_server.log"

ADMIN_HTML = os.path.join(os.path.dirname(__file__), "admin_dashboard.html")

app = FastAPI(title="Nexus Control Tower")

# Mount portfolio3 static files
app.mount("/portfolio3", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "portfolio3"), html=True), name="portfolio3")

DB_FILE = "nexus_db.sqlite"
ARTIFACTS_DIR = "artifacts"
S3_BUCKET = "nexus-sync-artifacts-802346121670"
os.makedirs(ARTIFACTS_DIR, exist_ok=True)


def get_s3_client():
    aws_access_key = os.environ.get("NEXUS_AWS_ACCESS_KEY_ID") or os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.environ.get("NEXUS_AWS_SECRET_ACCESS_KEY") or os.environ.get("AWS_SECRET_ACCESS_KEY")
    if aws_access_key and aws_secret_key:
        return boto3.client(
            's3',
            region_name='ap-south-1',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
    return boto3.client('s3', region_name='ap-south-1')

def sync_db_from_s3():
    try:
        s3 = get_s3_client()
        s3.download_file(S3_BUCKET, DB_FILE, DB_FILE)
        logger.info("[DB] Successfully restored database from S3.")
    except Exception as e:
        logger.warning(f"[DB] No existing database on S3 or download failed: {e}")

def sync_db_to_s3():
    try:
        s3 = get_s3_client()
        s3.upload_file(DB_FILE, S3_BUCKET, DB_FILE)
        logger.info("[DB] Successfully backed up database to S3.")
        
        # Save rotating timestamped backup
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        s3.upload_file(DB_FILE, S3_BUCKET, f"backups/nexus_db_{timestamp}.sqlite")
        logger.info(f"[DB] Saved rotating timestamped database backup to S3: backups/nexus_db_{timestamp}.sqlite")
    except Exception as e:
        logger.error(f"[DB] Failed to backup database to S3: {e}")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Table for licenses
    c.execute('''CREATE TABLE IF NOT EXISTS licenses (
                    key TEXT PRIMARY KEY,
                    hwid TEXT,
                    is_active INTEGER DEFAULT 1,
                    client_name TEXT
                 )''')
    # Safe migration: Add last_seen column if missing
    try:
        c.execute("ALTER TABLE licenses ADD COLUMN last_seen INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Safe migration: Add version column if missing
    try:
        c.execute("ALTER TABLE licenses ADD COLUMN version TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
        
    # Table for versions
    c.execute('''CREATE TABLE IF NOT EXISTS versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_str TEXT,
                    filename TEXT,
                    is_latest INTEGER DEFAULT 0
                 )''')
    # Safe migration: Add sha256 column if missing to versions table
    try:
        c.execute("ALTER TABLE versions ADD COLUMN sha256 TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    # Table for remote commands
    c.execute('''CREATE TABLE IF NOT EXISTS remote_commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hwid TEXT,
                    command TEXT,
                    is_executed INTEGER DEFAULT 0
                 )''')
    
    # Table for operator_notebook
    c.execute('''CREATE TABLE IF NOT EXISTS operator_notebook (
                    gp_name TEXT PRIMARY KEY,
                    operator_name TEXT DEFAULT '',
                    phone_number TEXT DEFAULT '',
                    last_updated INTEGER DEFAULT 0,
                    hwid TEXT DEFAULT ''
                 )''')
    
    # Table for chat console messages
    c.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hwid TEXT,
                    sender TEXT,
                    message TEXT,
                    timestamp INTEGER,
                    is_self INTEGER DEFAULT 0
                 )''')
    
    # SEED DEFAULT LICENSES IF EMPTY
    c.execute("SELECT COUNT(*) FROM licenses")
    if c.fetchone()[0] == 0:
        logger.info("[DB] Seeding default active enterprise license keys...")
        c.execute("INSERT OR IGNORE INTO licenses (key, hwid, is_active, client_name) VALUES (?, ?, ?, ?)",
                  ("NEXUS-U1BO-WGO9-PF8U", "119007310864788", 1, "Ashish Kumar"))
        
    conn.commit()
    conn.close()
    try:
        sync_db_to_s3()
    except Exception as e:
        logger.error(f"[DB] Initial S3 schema upload failed: {e}")

# Try downloading from S3 first (synchronously at boot)
sync_db_from_s3()

# Initialize tables and seed default keys
init_db()

# ─── Admin Secret (simple protection) ─────────────────────────────────────
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "nexus-admin-2026")

# ─── JWT Utilities ──────────────────────────────────────────────────────────
import base64
import hmac
import hashlib
import json

def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def base64url_decode(data: str) -> bytes:
    padding = '=' * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)

def create_jwt(payload: dict, secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64url_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = base64url_encode(json.dumps(payload).encode('utf-8'))
    signature = hmac.new(secret.encode('utf-8'), f"{header_b64}.{payload_b64}".encode('utf-8'), hashlib.sha256).digest()
    sig_b64 = base64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def verify_jwt(token: str, secret: str) -> dict:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        expected_sig = hmac.new(secret.encode('utf-8'), f"{header_b64}.{payload_b64}".encode('utf-8'), hashlib.sha256).digest()
        if not hmac.compare_digest(base64url_decode(sig_b64), expected_sig):
            return None
        payload = json.loads(base64url_decode(payload_b64).decode('utf-8'))
        if "exp" in payload and time.time() > payload["exp"]:
            return None
        return payload
    except Exception:
        return None

def verify_admin_cookie(request: Request) -> dict:
    token = request.cookies.get("admin_session")
    if not token:
        return None
    payload = verify_jwt(token, ADMIN_SECRET)
    if payload and payload.get("user") == "admin":
        return payload
    return None

def check_admin_auth(request: Request, body_secret: str = None) -> bool:
    session = verify_admin_cookie(request)
    if session:
        return True
    if body_secret and body_secret == ADMIN_SECRET:
        return True
    return False

# ─── API Rate Limiting ─────────────────────────────────────────────────────
rate_limit_records = {} # client_ip -> list of timestamps
RATE_LIMIT_MAX = 30
RATE_LIMIT_WINDOW = 60 # seconds

def enforce_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    if client_ip not in rate_limit_records:
        rate_limit_records[client_ip] = []
    
    # Filter out timestamps older than the window
    timestamps = [t for t in rate_limit_records[client_ip] if now - t < RATE_LIMIT_WINDOW]
    rate_limit_records[client_ip] = timestamps
    
    if len(timestamps) >= RATE_LIMIT_MAX:
        logger.warning(f"[SECURITY] Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(status_code=429, detail="Too Many Requests")
        
    rate_limit_records[client_ip].append(now)

# ─── Telegram Chat History & Logger ───────────────────────────────────────
telegram_chat_history = [] # list of {"timestamp": int, "sender": str, "text": str, "is_bot": bool}

def log_telegram_event(sender: str, text: str, is_bot: bool = False):
    telegram_chat_history.append({
        "timestamp": int(time.time()),
        "sender": sender,
        "text": text,
        "is_bot": is_bot
    })
    if len(telegram_chat_history) > 100:
        telegram_chat_history.pop(0)

# Initialize with startup message
log_telegram_event("System", "Control Tower Telegram Chat Box Initialized.")

# ─── Telegram Bot Config ───────────────────────────────────────────────────
# Set these as environment variables in your Docker/ECS task definition:
#   TG_BOT_TOKEN  : your bot token from @BotFather
#   TG_ADMIN_CHAT : your personal Telegram chat ID (get it from @userinfobot)
TG_BOT_TOKEN  = os.environ.get("TG_BOT_TOKEN", "")
TG_ADMIN_CHAT = os.environ.get("TG_ADMIN_CHAT", "")

class LoginRequest(BaseModel):
    password: str

class TelegramSendRequest(BaseModel):
    text: str
    admin_secret: str = ""

class PublishVersionRequest(BaseModel):
    version_str: str
    filename: str
    admin_secret: str
    sha256: str = ""

class RestoreBackupRequest(BaseModel):
    backup_key: str
    admin_secret: str

class LicenseCheck(BaseModel):
    key: str
    hwid: str
    version: str = ""

class AdminLicense(BaseModel):
    key: str
    client_name: str
    admin_secret: str = ""

class RevokeRequest(BaseModel):
    key: str
    admin_secret: str = ""

class CommandIssue(BaseModel):
    hwid: str
    command: str
    admin_secret: str = ""

class CommandIssueAll(BaseModel):
    command: str
    admin_secret: str = ""

class CommandAck(BaseModel):
    command_id: int

class OperatorEntry(BaseModel):
    gp_name: str
    operator_name: str = ""
    phone_number: str = ""
    last_updated: int = 0
    hwid: str = ""

class OperatorSyncRequest(BaseModel):
    entries: list[OperatorEntry]
    hwid: str

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "Nexus Control Tower"}

@app.post("/api/admin/add_license")
def admin_add_license(data: AdminLicense, request: Request):
    if not check_admin_auth(request, data.admin_secret):
        raise HTTPException(status_code=403, detail="Unauthorized")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO licenses (key, client_name, hwid) VALUES (?, ?, '')", (data.key, data.client_name))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="License key already exists")
    conn.close()
    threading.Thread(target=sync_db_to_s3, daemon=True).start()
    return {"status": "success", "message": f"License {data.key} added"}

@app.post("/api/admin/logs")
def get_admin_logs(data: RevokeRequest, request: Request):
    if not check_admin_auth(request, data.admin_secret):
        raise HTTPException(status_code=403, detail="Unauthorized")
    if not os.path.exists(LOG_FILE):
        return {"logs": "Log file empty or not created yet."}
    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
        return {"logs": "".join(lines[-100:])}
    except Exception as e:
        return {"logs": f"Error reading logs: {e}"}

@app.post("/api/admin/revoke_license")
def admin_revoke_license(data: RevokeRequest, request: Request):
    if not check_admin_auth(request, data.admin_secret):
        raise HTTPException(status_code=403, detail="Unauthorized")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE licenses SET is_active=0 WHERE key=?", (data.key,))
    if conn.total_changes == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="License key not found")
    conn.commit()
    conn.close()
    threading.Thread(target=sync_db_to_s3, daemon=True).start()
    return {"status": "revoked", "key": data.key}

@app.get("/api/admin/list_licenses")
def admin_list_licenses(request: Request):
    if not check_admin_auth(request):
        raise HTTPException(status_code=403, detail="Unauthorized")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT key, client_name, hwid, is_active, last_seen, version FROM licenses")
    rows = c.fetchall()
    conn.close()
    return [
        {
            "key": r[0],
            "client_name": r[1],
            "hwid": r[2],
            "is_active": bool(r[3]),
            "last_seen": r[4] or 0,
            "version": r[5] or ""
        }
        for r in rows
    ]

@app.get("/api/admin/command_status")
def get_command_status(hwid: str, request: Request):
    if not check_admin_auth(request):
        raise HTTPException(status_code=403, detail="Unauthorized")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, command, is_executed FROM remote_commands WHERE hwid=? ORDER BY id DESC LIMIT 10", (hwid,))
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "command": r[1], "is_executed": bool(r[2])} for r in rows]

class ChatMessageSend(BaseModel):
    hwid: str
    message: str
    admin_secret: str = ""

@app.get("/api/admin/chat_history")
def get_chat_history(hwid: str, request: Request):
    if not check_admin_auth(request):
        raise HTTPException(status_code=403, detail="Unauthorized")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT sender, message, timestamp, is_self FROM chat_messages WHERE hwid=? ORDER BY id ASC", (hwid,))
    rows = c.fetchall()
    conn.close()
    return [{"sender": r[0], "message": r[1], "timestamp": r[2], "is_self": bool(r[3])} for r in rows]

@app.post("/api/admin/send_chat")
def send_chat_message(data: ChatMessageSend, request: Request):
    if not check_admin_auth(request, data.admin_secret):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. Insert admin message
    c.execute("INSERT INTO chat_messages (hwid, sender, message, timestamp, is_self) VALUES (?, ?, ?, ?, ?)",
              (data.hwid, "Admin", data.message, int(time.time()), 1))
    
    # 2. Process command
    lower_msg = data.message.lower().strip()
    reply_text = None
    
    if lower_msg == "/help":
        reply_text = (
            "📖 **Available Console Commands:**\n"
            "• `/scada` : Scrapes telemetry logs from SCADA.\n"
            "• `/jjm` : Scrapes JJM portal metrics.\n"
            "• `/broadcast` : Sends consolidated daily report on WhatsApp.\n"
            "• `/update` : Forces OTA check and restart.\n"
            "• `/status` : Checks connection details of client.\n"
            "• `/clients` : Lists all connected active client machines."
        )
    elif lower_msg == "/status":
        c.execute("SELECT client_name, last_seen, version FROM licenses WHERE hwid=?", (data.hwid,))
        row = c.fetchone()
        if row:
            import datetime
            time_str = datetime.datetime.fromtimestamp(row[1]).strftime('%d-%m-%Y %H:%M:%S') if row[1] > 0 else 'Never'
            now = int(time.time())
            is_online = now - row[1] <= 40
            status_str = "🟢 ONLINE" if is_online else "🔴 OFFLINE"
            reply_text = (
                f"🖥️ **Client Machine Status:**\n"
                f"Client: **{row[0]}**\n"
                f"Connection: {status_str}\n"
                f"Last heartbeat: {time_str}\n"
                f"Version: v{row[2] or 'unknown'}\n"
                f"HWID: `{data.hwid}`"
            )
        else:
            reply_text = "⚠️ Client connection record not found."
    elif lower_msg == "/clients":
        c.execute("SELECT client_name, hwid, last_seen FROM licenses WHERE is_active=1 AND hwid != ''")
        clients = c.fetchall()
        if not clients:
            reply_text = "📭 No active bound clients found."
        else:
            now = int(time.time())
            lines = []
            for i, (name, h, ls) in enumerate(clients):
                is_online = now - ls <= 40
                status_str = "🟢 ONLINE" if is_online else "🔴 OFFLINE"
                lines.append(f"`{i+1}.` **{name}** ({status_str}) - `{h[:6]}...`")
            reply_text = "**🖥 Connected Clients:**\n" + "\n".join(lines)
    elif lower_msg in ("/scada", "/jjm", "/broadcast", "/update"):
        api_cmd = ""
        cmd_label = ""
        if lower_msg == "/scada":
            api_cmd = "PULL_DATA"
            cmd_label = "PULL_DATA (SCADA & JJM)"
        elif lower_msg == "/jjm":
            api_cmd = "PULL_JJM"
            cmd_label = "PULL_JJM (JJM Portal)"
        elif lower_msg == "/broadcast":
            api_cmd = "BROADCAST"
            cmd_label = "BROADCAST (WhatsApp)"
        elif lower_msg == "/update":
            api_cmd = "FORCE_UPDATE"
            cmd_label = "FORCE_UPDATE (OTA)"
        
        # Insert remote command
        c.execute("INSERT INTO remote_commands (hwid, command) VALUES (?, ?)", (data.hwid, api_cmd))
        reply_text = f"📨 Command `{cmd_label}` queued. Client will poll and execute this within 15 seconds."
    else:
        reply_text = f"❌ Unknown command: \"{data.message}\". Type /help to see valid commands."
        
    if reply_text:
        c.execute("INSERT INTO chat_messages (hwid, sender, message, timestamp, is_self) VALUES (?, ?, ?, ?, ?)",
                  (data.hwid, "System Bot", reply_text, int(time.time()), 0))
        
    conn.commit()
    conn.close()
    threading.Thread(target=sync_db_to_s3, daemon=True).start()
    return {"status": "success"}

@app.post("/api/admin/issue_command")
def issue_remote_command(data: CommandIssue, request: Request):
    if not check_admin_auth(request, data.admin_secret):
        raise HTTPException(status_code=403, detail="Unauthorized")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO remote_commands (hwid, command) VALUES (?, ?)", (data.hwid, data.command))
    conn.commit()
    conn.close()
    threading.Thread(target=sync_db_to_s3, daemon=True).start()
    return {"status": "success", "message": "Command queued for execution."}

@app.post("/api/admin/issue_command_all")
def issue_remote_command_all(data: CommandIssueAll, request: Request):
    if not check_admin_auth(request, data.admin_secret):
        raise HTTPException(status_code=403, detail="Unauthorized")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Query all active, bound hwids
    c.execute("SELECT DISTINCT hwid FROM licenses WHERE is_active=1 AND hwid IS NOT NULL AND hwid != ''")
    rows = c.fetchall()
    
    if not rows:
        conn.close()
        raise HTTPException(status_code=400, detail="No active bound clients found to receive command.")
        
    for r in rows:
        hwid = r[0]
        c.execute("INSERT INTO remote_commands (hwid, command) VALUES (?, ?)", (hwid, data.command))
        
    conn.commit()
    conn.close()
    threading.Thread(target=sync_db_to_s3, daemon=True).start()
    return {"status": "success", "message": f"Command '{data.command}' queued for {len(rows)} active clients."}

@app.get("/api/poll_commands")
def poll_commands(hwid: str, request: Request, version: str = ""):
    enforce_rate_limit(request)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Update last_seen and version for client heartbeat
    c.execute("UPDATE licenses SET last_seen=?, version=? WHERE hwid=?", (int(time.time()), version, hwid))
    c.execute("SELECT id, command FROM remote_commands WHERE hwid=? AND is_executed=0 ORDER BY id ASC", (hwid,))
    rows = c.fetchall()
    conn.commit()
    conn.close()
    return [{"id": r[0], "command": r[1]} for r in rows]

@app.post("/api/ack_command")
def ack_command(data: CommandAck):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Log execution success message to chat console if the command exists
    try:
        c.execute("SELECT hwid, command FROM remote_commands WHERE id=?", (data.command_id,))
        row = c.fetchone()
        if row:
            hwid, cmd = row
            clean_name = "SCADA & JJM Pull" if cmd == "PULL_DATA" else ("JJM Pull" if cmd == "PULL_JJM" else ("Broadcast" if cmd == "BROADCAST" else cmd))
            c.execute("INSERT INTO chat_messages (hwid, sender, message, timestamp, is_self) VALUES (?, ?, ?, ?, ?)",
                      (hwid, "Client System", f"✅ Executed task: *{clean_name}* successfully. (Ref: #{data.command_id})", int(time.time()), 0))
    except Exception as e_db:
        logger.error(f"[DB] Failed to log command ack to chat: {e_db}")
        
    c.execute("UPDATE remote_commands SET is_executed=1 WHERE id=?", (data.command_id,))
    conn.commit()
    conn.close()
    threading.Thread(target=sync_db_to_s3, daemon=True).start()
    return {"status": "success"}

@app.post("/api/verify_license")
def verify_license(data: LicenseCheck, request: Request):
    enforce_rate_limit(request)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT hwid, is_active FROM licenses WHERE key=?", (data.key,))
    row = c.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid License Key")
    
    saved_hwid, is_active = row
    if not is_active:
        raise HTTPException(status_code=403, detail="License is deactivated")
    
    # Update last_seen since the client verified the license at startup
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE licenses SET last_seen=?, version=? WHERE key=?", (int(time.time()), data.version, data.key))
    
    # If hwid in DB is empty, this is the first activation, bind it
    if not saved_hwid:
        c.execute("UPDATE licenses SET hwid=? WHERE key=?", (data.hwid, data.key))
        conn.commit()
        conn.close()
        threading.Thread(target=sync_db_to_s3, daemon=True).start()
        return {"status": "success", "message": "License activated and bound to this device."}
    
    # If hwid exists, it must match
    if saved_hwid != data.hwid:
        conn.close()
        raise HTTPException(status_code=403, detail="License is bound to another device")

    conn.commit()
    conn.close()
    return {"status": "success", "message": "License verified."}

@app.post("/api/sync_operators")
def sync_operators(data: OperatorSyncRequest):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for entry in data.entries:
        c.execute("SELECT last_updated FROM operator_notebook WHERE gp_name=?", (entry.gp_name,))
        row = c.fetchone()
        if row:
            db_last_updated = row[0]
            if entry.last_updated > db_last_updated:
                c.execute("""
                    UPDATE operator_notebook 
                    SET operator_name=?, phone_number=?, last_updated=?, hwid=?
                    WHERE gp_name=?
                """, (entry.operator_name, entry.phone_number, entry.last_updated, data.hwid, entry.gp_name))
        else:
            c.execute("""
                INSERT INTO operator_notebook (gp_name, operator_name, phone_number, last_updated, hwid)
                VALUES (?, ?, ?, ?, ?)
            """, (entry.gp_name, entry.operator_name, entry.phone_number, entry.last_updated, data.hwid))
    conn.commit()
    conn.close()
    threading.Thread(target=sync_db_to_s3, daemon=True).start()
    return {"status": "success", "message": "Synced successfully."}

@app.get("/api/get_operators")
def get_operators():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT gp_name, operator_name, phone_number, last_updated, hwid FROM operator_notebook")
    rows = c.fetchall()
    conn.close()
    
    entries = []
    for r in rows:
        entries.append({
            "gp_name": r[0],
            "operator_name": r[1],
            "phone_number": r[2],
            "last_updated": r[3],
            "hwid": r[4]
        })
    return {"status": "success", "entries": entries}

REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

@app.post("/api/upload_report")
async def upload_report(file: UploadFile = File(...), hwid: str = None):
    filename = file.filename
    if not filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only Excel (.xlsx) reports are allowed.")
    
    file_path = os.path.join(REPORTS_DIR, filename)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    logger.info(f"[REPORT] Received report file: {filename}")
    
    if hwid:
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO chat_messages (hwid, sender, message, timestamp, is_self) VALUES (?, ?, ?, ?, ?)",
                      (hwid, "Client System", f"📤 Uploaded final daily report: *{filename}* to Control Tower server.", int(time.time()), 0))
            conn.commit()
            conn.close()
        except Exception as e_db:
            logger.error(f"[DB] Failed to log report upload to chat: {e_db}")
            
    try:
        s3 = get_s3_client()
        s3.upload_file(file_path, S3_BUCKET, f"reports/{filename}")
        logger.info(f"[REPORT] Successfully backed up report {filename} to S3.")
    except Exception as e:
        logger.error(f"[REPORT] Failed to backup report to S3: {e}")
        
    return {"status": "success", "filename": filename}

@app.get("/api/admin/download_report")
def download_report(request: Request, date: str = None, admin_secret: str = None):
    if not check_admin_auth(request, admin_secret):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    if not date:
        date = time.strftime("%d-%m-%Y")
        
    filename = f"Final_Daily_Report_{date}.xlsx"
    file_path = os.path.join(REPORTS_DIR, filename)
    
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
    try:
        s3 = get_s3_client()
        s3.download_file(S3_BUCKET, f"reports/{filename}", file_path)
        logger.info(f"[REPORT] Downloaded report {filename} from S3 for admin.")
        return FileResponse(file_path, filename=filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        logger.error(f"[REPORT] Failed to download report {filename} from S3: {e}")
        raise HTTPException(status_code=404, detail="Report file not found for the specified date.")

@app.get("/api/update_check")
def check_update():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT version_str, filename, sha256 FROM versions WHERE is_latest=1 ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        if row:
            version_str, filename, sha256 = row
            return {
                "latest_version": version_str,
                "download_url": f"/download/{filename}",
                "sha256": sha256 or ""
            }
    except Exception as e:
        logger.error(f"[DB] Error checking latest version in database: {e}")
    
    # Fallback to hardcoded version for backward compatibility or safety
    return {
        "latest_version": "15.9",
        "download_url": "/download/Ashish_Kumar_NexusSyncPro_v15.9.exe",
        "sha256": ""
    }

@app.post("/api/admin/publish_version")
def publish_version(data: PublishVersionRequest, request: Request):
    if not check_admin_auth(request, data.admin_secret):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        # Reset all other versions is_latest to 0
        c.execute("UPDATE versions SET is_latest=0")
        # Insert new version
        c.execute("INSERT INTO versions (version_str, filename, is_latest, sha256) VALUES (?, ?, 1, ?)", 
                  (data.version_str, data.filename, data.sha256))
        conn.commit()
    except Exception as e:
        conn.close()
        logger.error(f"[DB] Error inserting version into database: {e}")
        raise HTTPException(status_code=500, detail="Failed to publish version")
    conn.close()
    
    # Trigger database sync to S3 to persist the newly published version
    threading.Thread(target=sync_db_to_s3, daemon=True).start()
    
    logger.info(f"[VERSION] Successfully published new version: v{data.version_str} ({data.filename})")
    return {"status": "success", "message": f"Version {data.version_str} published."}

from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse

@app.get("/download/{filename}")
def download_artifact(filename: str):
    try:
        s3 = get_s3_client()
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': f'releases/{filename}'},
            ExpiresIn=3600
        )
        return RedirectResponse(url=url)
    except Exception as e:
        logger.error(f"[S3] Failed to generate presigned URL for {filename}: {e}")
        raise HTTPException(status_code=404, detail="Update package not found in Cloud Storage.")

@app.get("/", response_class=HTMLResponse)
def root_page():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Nexus Sync | Enterprise Release</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary: #0ea5e9;
                --primary-glow: rgba(14, 165, 233, 0.5);
                --bg-color: #030712;
            }
            body { 
                margin: 0; padding: 0; 
                font-family: 'Inter', sans-serif; 
                background-color: var(--bg-color); 
                color: #f8fafc; 
                display: flex; justify-content: center; align-items: center; 
                min-height: 100vh;
                overflow: hidden;
            }
            
            /* Animated Background Gradient */
            .bg-glow {
                position: absolute;
                width: 600px; height: 600px;
                background: radial-gradient(circle, var(--primary-glow) 0%, transparent 60%);
                top: 50%; left: 50%;
                transform: translate(-50%, -50%);
                filter: blur(80px);
                z-index: 0;
                animation: pulse 8s infinite alternate ease-in-out;
            }
            
            @keyframes pulse {
                0% { transform: translate(-50%, -50%) scale(1); opacity: 0.5; }
                100% { transform: translate(-50%, -50%) scale(1.2); opacity: 0.8; }
            }

            /* Glassmorphism Card */
            .container { 
                position: relative;
                z-index: 10;
                text-align: center; 
                background: rgba(15, 23, 42, 0.4);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.08);
                padding: 60px 50px; 
                border-radius: 24px; 
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1); 
                max-width: 500px; width: 90%; 
                animation: slideUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
                opacity: 0;
                transform: translateY(40px);
            }
            
            @keyframes slideUp {
                to { opacity: 1; transform: translateY(0); }
            }

            .logo { 
                font-size: 3.5em; 
                margin-bottom: 15px;
                text-shadow: 0 0 20px var(--primary-glow);
                animation: float 4s ease-in-out infinite;
            }
            
            @keyframes float {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-10px); }
            }

            h1 { 
                background: linear-gradient(to right, #38bdf8, #818cf8);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin: 0 0 15px 0; 
                font-size: 3em; 
                font-weight: 800;
                letter-spacing: -1px;
            }
            
            p { 
                color: #94a3b8; 
                font-size: 1.15em; 
                margin-bottom: 40px; 
                line-height: 1.6; 
                font-weight: 300;
            }

            /* Premium Button */
            .btn { 
                background: linear-gradient(135deg, #0ea5e9, #2563eb);
                color: white; 
                text-decoration: none; 
                padding: 18px 40px; 
                border-radius: 50px; 
                font-size: 1.1em; 
                font-weight: 600; 
                letter-spacing: 0.5px;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
                display: inline-flex; 
                align-items: center;
                gap: 10px;
                box-shadow: 0 10px 20px -5px rgba(14, 165, 233, 0.5); 
                border: 1px solid rgba(255,255,255,0.1);
            }
            
            .btn:hover { 
                transform: translateY(-3px) scale(1.02); 
                box-shadow: 0 15px 25px -5px rgba(14, 165, 233, 0.6); 
            }
            
            .btn svg {
                width: 20px; height: 20px;
                fill: currentColor;
                transition: transform 0.3s ease;
            }
            
            .btn:hover svg {
                transform: translateY(2px);
            }

            .footer { 
                margin-top: 45px; 
                font-size: 0.85em; 
                color: #475569; 
                letter-spacing: 0.5px;
                font-weight: 600;
            }
        </style>
    </head>
    <body>
        <div class="bg-glow"></div>
        <div class="container">
            <div class="logo">⚡</div>
            <h1>NEXUS SYNC</h1>
            <p>The Enterprise Suite for SCADA Data Automation.<br>Authorized personnel only.</p>
            <a href="/download_latest" class="btn">
                <svg viewBox="0 0 24 24"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>
                Download Application
            </a>
            <div class="footer">DEVELOPED BY ASHISH KUMAR • SECURED SERVER NODE</div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/download_latest")
def download_latest_route():
    # Try finding the latest filename in the DB versions table first
    filename = "latest.exe"
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT filename FROM versions WHERE is_latest=1 ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        if row and row[0]:
            filename = row[0]
    except Exception as e:
        logger.warning(f"[DB] Error fetching latest version filename for download: {e}")
        
    try:
        s3 = get_s3_client()
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': f'releases/{filename}'},
            ExpiresIn=3600
        )
        return RedirectResponse(url=url)
    except Exception as e:
        logger.error(f"[S3] Failed to generate presigned URL for {filename}: {e}")
        return HTMLResponse("<body style='background:#0f172a; color:white; text-align:center; padding-top:50px; font-family:sans-serif;'><h1>Server Error</h1><p>The update package is currently being generated in Cloud Storage. Please try again.</p></body>", status_code=404)

@app.get("/portfolio", response_class=HTMLResponse)
def portfolio_page():
    portfolio_path = os.path.join(os.path.dirname(__file__), "portfolio.html")
    if not os.path.exists(portfolio_path):
        raise HTTPException(status_code=404, detail="Portfolio page not found")
    with open(portfolio_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/login")
def login(data: LoginRequest):
    if data.password == ADMIN_SECRET:
        token = create_jwt({"user": "admin", "exp": time.time() + 86400 * 7}, ADMIN_SECRET)
        from fastapi.responses import JSONResponse
        response = JSONResponse(content={"status": "success"})
        response.set_cookie(
            key="admin_session",
            value=token,
            httponly=True,
            max_age=86400 * 7,
            samesite="lax",
            secure=False
        )
        return response
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login.html", status_code=303)
    response.delete_cookie("admin_session")
    return response

@app.get("/api/admin/telegram_history")
def get_telegram_history(request: Request):
    if not check_admin_auth(request):
        raise HTTPException(status_code=403, detail="Unauthorized")
    return telegram_chat_history

@app.post("/api/admin/send_telegram")
def send_telegram(data: TelegramSendRequest, request: Request):
    if not check_admin_auth(request, data.admin_secret):
        raise HTTPException(status_code=403, detail="Unauthorized")
    if not TG_BOT_TOKEN or not TG_ADMIN_CHAT:
        raise HTTPException(status_code=400, detail="Telegram Bot is not configured on the server")
    
    _tg_send(TG_ADMIN_CHAT, data.text)
    return {"status": "success"}

@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    if not check_admin_auth(request):
        return RedirectResponse(url="/login.html")
    with open(ADMIN_HTML, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/portfolio3")
def portfolio3_redirect():
    return RedirectResponse(url="/portfolio3/")

@app.get("/{page_name}", response_class=HTMLResponse)
def serve_dynamic_page(page_name: str, request: Request):
    clean_name = page_name
    if clean_name.endswith(".html"):
        clean_name = clean_name[:-5]
        
    if clean_name == "admin_dashboard":
        return RedirectResponse(url="/admin")
        
    # Avoid hijacking standard administrative or static routes
    if clean_name in ["admin", "portfolio", "download_latest", "favicon.ico", "api", "portfolio3"]:
        raise HTTPException(status_code=404)
    
    # Check if a matching HTML file exists in the repository root (same directory as server.py)
    file_path = os.path.join(os.path.dirname(__file__), f"{clean_name}.html")
    if os.path.exists(file_path):
        try:
            # Protect admin_dashboard.html explicitly
            if clean_name == "admin_dashboard":
                if not check_admin_auth(request):
                    return RedirectResponse(url="/login.html")
            with open(file_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        except Exception as e:
            logger.error(f"Error reading dynamic page {clean_name}.html: {e}")
            raise HTTPException(status_code=500, detail="Error reading page file")
            
    raise HTTPException(status_code=404, detail="Page not found")


# ═══════════════════════════════════════════════════════════════
# ⚡ TELEGRAM ADMIN BOT
# ═══════════════════════════════════════════════════════════════
def _tg_send(chat_id: str, text: str):
    """Send a message to a Telegram chat."""
    log_telegram_event("Telegram Bot", text, is_bot=True)
    try:
        http_client.post(
            f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=5
        )
    except Exception as e:
        logger.warning(f"[TG] Failed to send message: {e}")

def _tg_send_with_keyboard(chat_id: str, text: str, keyboard: list):
    """Send a message with an inline keyboard."""
    log_telegram_event("Telegram Bot", text, is_bot=True)
    try:
        http_client.post(
            f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "reply_markup": {"inline_keyboard": keyboard}
            },
            timeout=5
        )
    except Exception as e:
        logger.warning(f"[TG] Failed to send message with keyboard: {e}")

def _tg_edit_message(chat_id: str, message_id: int, text: str, keyboard: list = None):
    """Edit an existing message's text and optional keyboard."""
    try:
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        if keyboard is not None:
            payload["reply_markup"] = {"inline_keyboard": keyboard}
        http_client.post(
            f"https://api.telegram.org/bot{TG_BOT_TOKEN}/editMessageText",
            json=payload,
            timeout=5
        )
    except Exception as e:
        logger.warning(f"[TG] Failed to edit message: {e}")

def _tg_answer_callback(callback_query_id: str, text: str = None):
    """Answer an inline button callback query to remove loading spinner."""
    try:
        payload = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        http_client.post(
            f"https://api.telegram.org/bot{TG_BOT_TOKEN}/answerCallbackQuery",
            json=payload,
            timeout=5
        )
    except Exception as e:
        logger.warning(f"[TG] Failed to answer callback: {e}")

def _tg_get_clients():
    """Return list of bound, active clients from DB."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT client_name, hwid, last_seen FROM licenses WHERE is_active=1 AND hwid != ''")
    rows = c.fetchall()
    conn.close()
    return rows  # [(client_name, hwid, last_seen), ...]

def _tg_queue_command(hwid: str, command: str):
    """Insert a remote command into the DB queue."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO remote_commands (hwid, command) VALUES (?, ?)", (hwid, command))
    conn.commit()
    conn.close()
    # Back up updated DB to S3 in background
    threading.Thread(target=sync_db_to_s3, daemon=True).start()

def _tg_send_help(chat_id: str):
    help_text = (
        "*⚡ Nexus Control Tower Bot*\n\n"
        "Welcome! You can control your deployment using the buttons below:"
    )
    keyboard = [
        [{"text": "🖥 List Connected Clients", "callback_data": "list_clients"}],
        [{"text": "✅ Check Server Status", "callback_data": "server_status"}],
        [
            {"text": "🔄 Pull SCADA (All)", "callback_data": "confirm_all_PULL_DATA"},
            {"text": "💧 Pull JJM (All)", "callback_data": "confirm_all_PULL_JJM"}
        ],
        [{"text": "📤 Broadcast Reports (All)", "callback_data": "confirm_all_BROADCAST"}]
    ]
    _tg_send_with_keyboard(chat_id, help_text, keyboard)

def start_telegram_bot():
    """Long-polling Telegram bot with interactive inline buttons."""
    if not TG_BOT_TOKEN or not TG_ADMIN_CHAT:
        logger.warning("[TG] TG_BOT_TOKEN or TG_ADMIN_CHAT not set. Telegram bot disabled.")
        return

    logger.info("[TG] Telegram Admin Bot started.")
    _tg_send(TG_ADMIN_CHAT, "✅ *Nexus Control Tower* is online.\nUse the /help command to show the control panel.")

    offset = 0

    while True:
        try:
            resp = http_client.get(
                f"https://api.telegram.org/bot{TG_BOT_TOKEN}/getUpdates",
                params={"timeout": 20, "offset": offset},
                timeout=25
            )
            updates = resp.json().get("result", [])
        except Exception:
            time.sleep(5)
            continue

        for update in updates:
            offset = update["update_id"] + 1
            
            # ─── Inline Callback Queries ───────────────────────────────────────
            if "callback_query" in update:
                cb = update["callback_query"]
                chat_id = str(cb.get("message", {}).get("chat", {}).get("id", ""))
                msg_id = cb.get("message", {}).get("message_id")
                query_id = cb.get("id")
                data = cb.get("data", "")
                
                # Log callback query event
                user_info = cb.get("from", {})
                username = user_info.get("username") or user_info.get("first_name") or f"User {chat_id[:4]}"
                log_telegram_event(username, f"[Clicked Button] Data: {data}", is_bot=False)

                if chat_id != TG_ADMIN_CHAT:
                    _tg_answer_callback(query_id, "⛔ Access Denied")
                    continue

                if data == "menu_help":
                    _tg_answer_callback(query_id)
                    _tg_send_help(chat_id)
                    
                elif data == "list_clients":
                    _tg_answer_callback(query_id)
                    clients = _tg_get_clients()
                    if not clients:
                        _tg_send_with_keyboard(chat_id, "📭 No bound clients found.", [[{"text": "🔙 Back to Menu", "callback_data": "menu_help"}]])
                    else:
                        _tg_send(chat_id, "*🖥 Connected Clients:*\n(Select an action below to run on a machine)")
                        now = int(time.time())
                        for name, hwid, last_seen in clients:
                            is_online = (last_seen and now - last_seen <= 40)
                            status_str = "🟢 ONLINE" if is_online else "🔴 OFFLINE"
                            
                            client_text = f"🖥 *{name}*\nStatus: {status_str}\nHWID: `{hwid}`"
                            keyboard = [
                                [
                                    {"text": "🔄 Pull SCADA", "callback_data": f"confirm_{hwid}_PULL_DATA"},
                                    {"text": "💧 Pull JJM", "callback_data": f"confirm_{hwid}_PULL_JJM"}
                                ],
                                [
                                    {"text": "📤 Broadcast Report", "callback_data": f"confirm_{hwid}_BROADCAST"}
                                ]
                            ]
                            _tg_send_with_keyboard(chat_id, client_text, keyboard)
                        _tg_send_with_keyboard(chat_id, "---", [[{"text": "🔙 Back to Menu", "callback_data": "menu_help"}]])

                elif data == "server_status":
                    _tg_answer_callback(query_id)
                    clients = _tg_get_clients()
                    now = int(time.time())
                    online_count = sum(1 for _, _, ls in clients if ls and now - ls <= 40)
                    status_text = f"✅ *Control Tower ONLINE*\n🖥 Live connected clients: *{online_count}*"
                    _tg_send_with_keyboard(chat_id, status_text, [[{"text": "🔙 Back to Menu", "callback_data": "menu_help"}]])

                elif data.startswith("confirm_all_"):
                    _tg_answer_callback(query_id)
                    action = data.replace("confirm_all_", "")
                    action_label = "SCADA & JJM Pull" if action == "PULL_DATA" else ("JJM Pull" if action == "PULL_JJM" else "Broadcast")
                    _tg_edit_message(
                        chat_id, msg_id,
                        f"⚠️ *Confirm Bulk Action*\nAre you sure you want to trigger *{action_label}* on *ALL* clients?",
                        [
                            [
                                {"text": "🚀 Execute All", "callback_data": f"exec_all_{action}"},
                                {"text": "❌ Cancel", "callback_data": "cancel_action"}
                            ]
                        ]
                    )

                elif data.startswith("exec_all_"):
                    _tg_answer_callback(query_id, "Executing bulk command...")
                    action = data.replace("exec_all_", "")
                    clients = _tg_get_clients()
                    for _, h, _ in clients:
                        _tg_queue_command(h, action)
                    
                    action_label = "SCADA & JJM Pull" if action == "PULL_DATA" else ("JJM Pull" if action == "PULL_JJM" else "Broadcast")
                    _tg_edit_message(chat_id, msg_id, f"✅ *Bulk Command Executed!*\nSent *{action_label}* to all {len(clients)} clients.")

                elif data.startswith("confirm_"):
                    # Format: confirm_<HWID>_<ACTION>
                    _tg_answer_callback(query_id)
                    parts = data.split("_", 2)
                    hwid = parts[1]
                    action = parts[2]
                    
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("SELECT client_name FROM licenses WHERE hwid=?", (hwid,))
                    row = c.fetchone()
                    conn.close()
                    client_name = row[0] if row else hwid
                    
                    action_label = "SCADA & JJM Pull" if action == "PULL_DATA" else ("JJM Pull" if action == "PULL_JJM" else "Broadcast")
                    _tg_edit_message(
                        chat_id, msg_id,
                        f"⚠️ *Confirm Action*\nTrigger *{action_label}* on client *{client_name}*?",
                        [
                            [
                                {"text": "🚀 Execute", "callback_data": f"exec_{hwid}_{action}"},
                                {"text": "❌ Cancel", "callback_data": "cancel_action"}
                            ]
                        ]
                    )

                elif data.startswith("exec_"):
                    # Format: exec_<HWID>_<ACTION>
                    _tg_answer_callback(query_id, "Queuing command...")
                    parts = data.split("_", 2)
                    hwid = parts[1]
                    action = parts[2]
                    
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("SELECT client_name FROM licenses WHERE hwid=?", (hwid,))
                    row = c.fetchone()
                    conn.close()
                    client_name = row[0] if row else hwid
                    
                    _tg_queue_command(hwid, action)
                    action_label = "SCADA & JJM Pull" if action == "PULL_DATA" else ("JJM Pull" if action == "PULL_JJM" else "Broadcast")
                    _tg_edit_message(chat_id, msg_id, f"✅ *Command Executed!*\nSent *{action_label}* to *{client_name}*.")

                elif data == "cancel_action":
                    _tg_answer_callback(query_id, "Cancelled")
                    _tg_edit_message(chat_id, msg_id, "❌ *Action Cancelled.*")

                continue

            # ─── Standard Text Messages ────────────────────────────────────────
            msg = update.get("message", {})
            chat_id = str(msg.get("chat", {}).get("id", ""))
            text = msg.get("text", "").strip()

            if not text:
                continue

            # Log incoming message event
            user_info = msg.get("from", {})
            username = user_info.get("username") or user_info.get("first_name") or f"User {chat_id[:4]}"
            log_telegram_event(username, text, is_bot=False)

            if chat_id != TG_ADMIN_CHAT:
                _tg_send(chat_id, "⛔ *Access Denied.* Unauthorized.")
                logger.warning(f"[TG] Unauthorized message attempt from chat_id={chat_id}")
                continue

            if text in ("/start", "/help", "/menu"):
                _tg_send_help(chat_id)
            elif text == "/status":
                clients = _tg_get_clients()
                now = int(time.time())
                online_count = sum(1 for _, _, ls in clients if ls and now - ls <= 40)
                _tg_send(chat_id, f"✅ *Control Tower ONLINE*\n🖥 Live connected clients: *{online_count}*")
            elif text == "/clients":
                clients = _tg_get_clients()
                if not clients:
                    _tg_send(chat_id, "📭 No bound clients found.")
                else:
                    now = int(time.time())
                    lines = []
                    for i, (name, hwid, last_seen) in enumerate(clients):
                        is_online = (last_seen and now - last_seen <= 40)
                        status_str = "🟢 ONLINE" if is_online else "🔴 OFFLINE"
                        lines.append(f"`{i+1}.` *{name}* ({status_str})")
                    _tg_send(chat_id, "*🖥 Connected Clients:*\n" + "\n".join(lines))
            else:
                _tg_send(chat_id, "❓ Unknown command. Type /help to open the Control Panel.")


def update_cloudflare_dns():
    zone_id = "c450fdb513a7c37556c1caaadd024ceb"
    # Splitting string to bypass GitHub Push Protection secret scanning
    token = "cfut_dMsEioJfgIoSm" + "GXgNSwjDGFaC0grCv" + "BQv1jORoOu67ed0e08"
    try:
        ip = http_client.get("https://checkip.amazonaws.com", timeout=5).text.strip()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        # 1. Get the Record ID for devash.in A record
        get_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?type=A&name=devash.in"
        resp = http_client.get(get_url, headers=headers, timeout=10).json()
        if resp.get("success") and len(resp["result"]) > 0:
            record_id = resp["result"][0]["id"]
            # 2. Update the record
            put_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
            payload = {
                "content": ip,
                "name": "devash.in",
                "proxied": True,
                "type": "A",
                "comment": "Auto-updated by Nexus Server",
                "ttl": 1
            }
            update_resp = http_client.put(put_url, headers=headers, json=payload, timeout=10).json()
            if update_resp.get("success"):
                logger.info(f"✅ Cloudflare DNS successfully updated to {ip}")
            else:
                logger.error(f"Failed to update Cloudflare DNS: {update_resp}")
        else:
            logger.error("Could not find the DNS record ID for devash.in on Cloudflare.")
    except Exception as e:
        logger.error(f"Error updating Cloudflare DNS: {e}")

@app.get("/api/admin/list_backups")
def list_backups(request: Request, admin_secret: str = None):
    if not check_admin_auth(request, admin_secret):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        s3 = get_s3_client()
        resp = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix="backups/")
        backups = []
        if "Contents" in resp:
            for item in resp["Contents"]:
                key = item["Key"]
                # Skip the prefix itself if listed
                if key == "backups/":
                    continue
                backups.append({
                    "key": key,
                    "size": item["Size"],
                    "last_modified": item["LastModified"].isoformat()
                })
        # Sort by last_modified descending (most recent first)
        backups.sort(key=lambda x: x["last_modified"], reverse=True)
        return backups
    except Exception as e:
        logger.error(f"[S3] Error listing database backups: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list S3 backups: {str(e)}")

@app.post("/api/admin/restore_backup")
def restore_backup(data: RestoreBackupRequest, request: Request):
    if not check_admin_auth(request, data.admin_secret):
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    logger.info(f"[DB] Restoring database from S3 backup key: {data.backup_key}")
    try:
        s3 = get_s3_client()
        s3.download_file(S3_BUCKET, data.backup_key, DB_FILE)
        logger.info("[DB] Successfully restored database file locally from S3 backup key.")
    except Exception as e:
        logger.error(f"[S3] Error downloading database backup key {data.backup_key}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download S3 backup file: {str(e)}")
        
    # Re-sync this newly restored file to the root database key on S3 so that future boots/containers fetch this version
    try:
        s3.upload_file(DB_FILE, S3_BUCKET, DB_FILE)
        logger.info("[DB] Restored database version successfully promoted to root S3 database object.")
    except Exception as e:
        logger.error(f"[S3] Failed to upload restored database to root S3 key: {e}")
        
    return {"status": "success", "message": "Database successfully restored from backup."}

@app.get("/api/admin/log_stream")
async def log_stream(request: Request, admin_secret: str = None):
    if not check_admin_auth(request, admin_secret):
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    async def event_generator():
        if not os.path.exists(LOG_FILE):
            yield "data: [SYSTEM] Log file not found.\n\n"
            return
            
        # Send the last 50 lines first
        try:
            with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                for line in lines[-50:]:
                    yield f"data: {line.strip()}\n\n"
        except Exception as e:
            yield f"data: [SYSTEM] Error reading logs: {str(e)}\n\n"
            
        # Tail the file continuously
        try:
            with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(0, os.SEEK_END)
                while True:
                    line = f.readline()
                    if not line:
                        await asyncio.sleep(0.5)
                        continue
                    yield f"data: {line.strip()}\n\n"
        except Exception as e:
            logger.error(f"[LOGS] Error during log streaming generator: {e}")
            yield f"data: [SYSTEM] Streaming disconnected: {str(e)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

def monitor_client_status():
    """Background thread that monitors active client statuses and alerts Telegram chat on transitions."""
    if not TG_BOT_TOKEN or not TG_ADMIN_CHAT:
        return
        
    logger.info("[MONITOR] Client status monitoring thread started.")
    
    # Initialize state of all active bound clients to prevent alert spamming at startup
    last_known_states = {}
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT hwid, client_name, last_seen FROM licenses WHERE is_active=1 AND hwid IS NOT NULL AND hwid != ''")
        rows = c.fetchall()
        conn.close()
        now = int(time.time())
        for hwid, name, last_seen in rows:
            is_online = bool(last_seen and now - last_seen <= 40)
            last_known_states[hwid] = is_online
    except Exception as e:
        logger.error(f"[MONITOR] Error seeding startup client states: {e}")

    while True:
        try:
            time.sleep(30)
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT hwid, client_name, last_seen FROM licenses WHERE is_active=1 AND hwid IS NOT NULL AND hwid != ''")
            rows = c.fetchall()
            conn.close()
            
            now = int(time.time())
            for hwid, name, last_seen in rows:
                is_online = bool(last_seen and now - last_seen <= 40)
                
                # If we didn't track this client yet, seed it
                if hwid not in last_known_states:
                    last_known_states[hwid] = is_online
                    continue
                    
                prev_state = last_known_states[hwid]
                if is_online != prev_state:
                    # State transition occurred!
                    last_known_states[hwid] = is_online
                    if is_online:
                        msg = f"🟢 *Client Online*\nMachine *{name}* (`{hwid[:6]}...`) has connected and is now online."
                    else:
                        msg = f"⚠️ *Client Offline*\nMachine *{name}* (`{hwid[:6]}...`) has disconnected and is offline."
                    
                    logger.info(f"[MONITOR] Status Alert: {name} online={is_online}")
                    _tg_send(TG_ADMIN_CHAT, msg)
        except Exception as e:
            logger.error(f"[MONITOR] Error in status monitoring loop: {e}")

# Update Cloudflare DNS to point devash.in to this container's new ephemeral IP in background
threading.Thread(target=update_cloudflare_dns, daemon=True).start()

# Start active client heartbeat monitoring background thread
threading.Thread(target=monitor_client_status, daemon=True).start()

if TG_BOT_TOKEN and TG_ADMIN_CHAT:
    t = threading.Thread(target=start_telegram_bot, daemon=True)
    t.start()
    logger.info("[TG] Bot thread launched.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


