import os
import sqlite3
import logging
import threading
import time
import requests as http_client
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn

# Configure logging
LOG_FILE = "nexus_server.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("NexusControlTower")

ADMIN_HTML = os.path.join(os.path.dirname(__file__), "admin_dashboard.html")

app = FastAPI(title="Nexus Control Tower")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    client_ip = request.client.host if request.client else "Unknown"
    logger.info(f"Incoming: {request.method} {request.url.path} from {client_ip}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

DB_FILE = "nexus_db.sqlite"
ARTIFACTS_DIR = "artifacts"

os.makedirs(ARTIFACTS_DIR, exist_ok=True)

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
    # Table for versions
    c.execute('''CREATE TABLE IF NOT EXISTS versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_str TEXT,
                    filename TEXT,
                    is_latest INTEGER DEFAULT 0
                 )''')
    # Table for remote commands
    c.execute('''CREATE TABLE IF NOT EXISTS remote_commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hwid TEXT,
                    command TEXT,
                    is_executed INTEGER DEFAULT 0
                 )''')
    conn.commit()
    conn.close()

init_db()

# ─── Admin Secret (simple protection) ─────────────────────────────────────
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "nexus-admin-2026")

# ─── Telegram Bot Config ───────────────────────────────────────────────────
# Set these as environment variables in your Docker/ECS task definition:
#   TG_BOT_TOKEN  : your bot token from @BotFather
#   TG_ADMIN_CHAT : your personal Telegram chat ID (get it from @userinfobot)
TG_BOT_TOKEN  = os.environ.get("TG_BOT_TOKEN", "")
TG_ADMIN_CHAT = os.environ.get("TG_ADMIN_CHAT", "")

class LicenseCheck(BaseModel):
    key: str
    hwid: str

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

class CommandAck(BaseModel):
    command_id: int

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "Nexus Control Tower"}

@app.post("/api/admin/add_license")
def admin_add_license(data: AdminLicense):
    if data.admin_secret != ADMIN_SECRET:
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
    return {"status": "success", "message": f"License {data.key} added"}

@app.post("/api/admin/logs")
def get_admin_logs(data: RevokeRequest):
    if data.admin_secret != ADMIN_SECRET:
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
def admin_revoke_license(data: RevokeRequest):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE licenses SET is_active=0 WHERE key=?", (data.key,))
    if conn.total_changes == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="License key not found")
    conn.commit()
    conn.close()
    return {"status": "revoked", "key": data.key}

@app.get("/api/admin/list_licenses")
def admin_list_licenses():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT key, client_name, hwid, is_active FROM licenses")
    rows = c.fetchall()
    conn.close()
    return [
        {"key": r[0], "client_name": r[1], "hwid": r[2], "is_active": bool(r[3])}
        for r in rows
    ]

@app.post("/api/admin/issue_command")
def issue_remote_command(data: CommandIssue):
    if data.admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Unauthorized")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO remote_commands (hwid, command) VALUES (?, ?)", (data.hwid, data.command))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Command queued for execution."}

@app.get("/api/poll_commands")
def poll_commands(hwid: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, command FROM remote_commands WHERE hwid=? AND is_executed=0 ORDER BY id ASC", (hwid,))
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "command": r[1]} for r in rows]

@app.post("/api/ack_command")
def ack_command(data: CommandAck):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE remote_commands SET is_executed=1 WHERE id=?", (data.command_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.post("/api/verify_license")
def verify_license(data: LicenseCheck):
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
    
    # If hwid in DB is empty, this is the first activation, bind it
    if not saved_hwid:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("UPDATE licenses SET hwid=? WHERE key=?", (data.hwid, data.key))
        conn.commit()
        conn.close()
        return {"status": "success", "message": "License activated and bound to this device."}
    
    # If hwid exists, it must match
    if saved_hwid != data.hwid:
        raise HTTPException(status_code=403, detail="License is bound to another device")

    return {"status": "success", "message": "License verified."}

@app.get("/api/update_check")
def check_update():
    # Returns the actual latest version so clients only update when necessary
    return {
        "latest_version": "14.0",
        "download_url": "/download/latest.exe"
    }

@app.get("/download/{filename}")
def download_artifact(filename: str):
    file_path = os.path.join(ARTIFACTS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=file_path, filename=filename, media_type='application/octet-stream')

@app.get("/", response_class=HTMLResponse)
def root_page():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Nexus Sync | Enterprise Release</title>
        <style>
            body { margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; }
            .container { text-align: center; background-color: #1e293b; padding: 50px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); border: 1px solid #334155; max-width: 500px; width: 90%; }
            .logo { font-size: 3em; margin-bottom: 10px; }
            h1 { color: #38bdf8; margin-bottom: 10px; font-size: 2.5em; letter-spacing: 1px;}
            p { color: #94a3b8; font-size: 1.1em; margin-bottom: 35px; line-height: 1.6; }
            .btn { background-color: #0ea5e9; color: white; text-decoration: none; padding: 15px 35px; border-radius: 8px; font-size: 1.2em; font-weight: bold; transition: all 0.3s ease; display: inline-block; box-shadow: 0 4px 15px rgba(14, 165, 233, 0.4); }
            .btn:hover { background-color: #0284c7; transform: translateY(-2px); box-shadow: 0 6px 20px rgba(14, 165, 233, 0.6); }
            .footer { margin-top: 40px; font-size: 0.85em; color: #64748b; letter-spacing: 0.5px;}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">⚡</div>
            <h1>NEXUS SYNC</h1>
            <p>Enterprise Suite for Data Automation.<br>Authorized personnel only.</p>
            <a href="/download_latest" class="btn">⬇ Download Application</a>
            <div class="footer">Developed by Ashish Kumar • Secured Server Node</div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/download_latest")
def download_latest_route():
    file_path = os.path.join(ARTIFACTS_DIR, "latest.exe")
    if not os.path.exists(file_path):
        return HTMLResponse("<body style='background:#0f172a; color:white; text-align:center; padding-top:50px; font-family:sans-serif;'><h1>Server Error</h1><p>The build pipeline is still compiling the EXE. Please try again in 2 minutes.</p></body>", status_code=404)
    return FileResponse(path=file_path, filename="NexusSyncPro_Enterprise.exe", media_type='application/octet-stream')

@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard():
    with open(ADMIN_HTML, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ═══════════════════════════════════════════════════════════════
# ⚡ TELEGRAM ADMIN BOT
# ═══════════════════════════════════════════════════════════════
def _tg_send(chat_id: str, text: str):
    """Send a message to a Telegram chat."""
    try:
        http_client.post(
            f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=5
        )
    except Exception as e:
        logger.warning(f"[TG] Failed to send message: {e}")

def _tg_get_clients():
    """Return list of bound, active clients from DB."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT client_name, hwid FROM licenses WHERE is_active=1 AND hwid != ''")
    rows = c.fetchall()
    conn.close()
    return rows  # [(client_name, hwid), ...]

def _tg_queue_command(hwid: str, command: str):
    """Insert a remote command into the DB queue."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO remote_commands (hwid, command) VALUES (?, ?)", (hwid, command))
    conn.commit()
    conn.close()

def start_telegram_bot():
    """Long-polling Telegram bot with OTP verification before command execution."""
    if not TG_BOT_TOKEN or not TG_ADMIN_CHAT:
        logger.warning("[TG] TG_BOT_TOKEN or TG_ADMIN_CHAT not set. Telegram bot disabled.")
        return

    logger.info("[TG] Telegram Admin Bot started.")
    _tg_send(TG_ADMIN_CHAT, "✅ *Nexus Control Tower* is online.\nType /help for commands.")

    # OTP store: { otp_code: {action, hwid, client_name, expires_at} }
    import random
    pending_otps = {}
    offset = 0

    def _generate_otp(action, hwid, client_name):
        """Generate a unique 6-digit OTP and store it with 60-second expiry."""
        otp = str(random.randint(100000, 999999))
        pending_otps[otp] = {
            "action": action,
            "hwid": hwid,
            "client_name": client_name,
            "expires_at": time.time() + 60
        }
        return otp

    def _cleanup_expired_otps():
        """Remove any expired OTPs."""
        now = time.time()
        expired = [k for k, v in pending_otps.items() if v["expires_at"] < now]
        for k in expired:
            del pending_otps[k]

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

        _cleanup_expired_otps()

        for update in updates:
            offset = update["update_id"] + 1
            msg = update.get("message", {})
            chat_id = str(msg.get("chat", {}).get("id", ""))
            text = msg.get("text", "").strip()

            # ── Security: only respond to designated admin chat ──
            if chat_id != TG_ADMIN_CHAT:
                _tg_send(chat_id, "⛔ *Access Denied.* You are not authorized to use this bot.")
                logger.warning(f"[TG] Unauthorized access attempt from chat_id={chat_id}")
                continue

            # ── OTP Confirmation check ──
            if text.isdigit() and len(text) == 6:
                if text in pending_otps:
                    entry = pending_otps.pop(text)
                    if time.time() > entry["expires_at"]:
                        _tg_send(chat_id, "⏰ *OTP Expired.* Please re-issue the command.")
                    else:
                        _tg_queue_command(entry["hwid"], entry["action"])
                        emoji = "📥" if entry["action"] == "PULL_DATA" else "📤"
                        _tg_send(chat_id,
                            f"✅ *Verified & Executed!*\n"
                            f"{emoji} *{entry['action']}* has been sent to *{entry['client_name']}*.\n"
                            f"They will execute it within 15 seconds."
                        )
                        logger.info(f"[TG] OTP confirmed. Queued {entry['action']} for {entry['client_name']}")
                else:
                    _tg_send(chat_id, "❌ *Invalid or expired OTP.* Please re-issue the command.")
                continue

            # ── Standard Commands ──
            if text in ("/start", "/help"):
                _tg_send(chat_id,
                    "*⚡ Nexus Admin Bot*\n\n"
                    "`/clients` — List all connected machines\n"
                    "`/pull <n>` — Pull Data on client #n\n"
                    "`/broadcast <n>` — Broadcast Report on client #n\n"
                    "`/pullall` — Pull Data on ALL clients\n"
                    "`/broadcastall` — Broadcast on ALL clients\n"
                    "`/status` — Server health check\n\n"
                    "⚠️ *All actions require OTP confirmation.*"
                )

            elif text == "/clients":
                clients = _tg_get_clients()
                if not clients:
                    _tg_send(chat_id, "📭 No active bound clients found.")
                else:
                    lines = [f"`{i+1}.` *{name}*" for i, (name, hwid) in enumerate(clients)]
                    _tg_send(chat_id, "*🖥 Connected Clients:*\n" + "\n".join(lines))

            elif text == "/status":
                count = len(_tg_get_clients())
                _tg_send(chat_id, f"✅ *Control Tower is ONLINE*\n🖥 Active clients: *{count}*")

            elif text.startswith("/pull ") or text.startswith("/broadcast "):
                parts = text.split()
                action = "PULL_DATA" if parts[0] == "/pull" else "BROADCAST"
                emoji = "📥" if action == "PULL_DATA" else "📤"
                try:
                    idx = int(parts[1]) - 1
                    clients = _tg_get_clients()
                    if idx < 0 or idx >= len(clients):
                        _tg_send(chat_id, "❌ Invalid number. Use /clients to see the list.")
                    else:
                        name, hwid = clients[idx]
                        otp = _generate_otp(action, hwid, name)
                        _tg_send(chat_id,
                            f"🔐 *Verification Required*\n\n"
                            f"Action: {emoji} *{action}*\n"
                            f"Target: *{name}*\n\n"
                            f"Reply with this OTP code to confirm:\n"
                            f"```\n{otp}\n```\n"
                            f"_Code expires in 60 seconds._"
                        )
                        logger.info(f"[TG] OTP {otp} generated for {action} → {name}")
                except (ValueError, IndexError):
                    _tg_send(chat_id, "❌ Usage: `/pull 1` or `/broadcast 2`\nUse /clients to get client numbers.")

            elif text in ("/pullall", "/broadcastall"):
                action = "PULL_DATA" if text == "/pullall" else "BROADCAST"
                emoji = "📥" if action == "PULL_DATA" else "📤"
                clients = _tg_get_clients()
                if not clients:
                    _tg_send(chat_id, "📭 No active clients found.")
                else:
                    otp = _generate_otp(action, "__ALL__", f"ALL {len(clients)} clients")
                    # Store all HWIDs in the entry for bulk execution
                    pending_otps[otp]["all_hwids"] = [hwid for _, hwid in clients]
                    _tg_send(chat_id,
                        f"🔐 *Bulk Verification Required*\n\n"
                        f"Action: {emoji} *{action}* on *ALL {len(clients)} clients*\n\n"
                        f"Reply with this OTP code to confirm:\n"
                        f"```\n{otp}\n```\n"
                        f"_Code expires in 60 seconds._"
                    )

            else:
                _tg_send(chat_id, "❓ Unknown command. Type /help for available commands.")

    # Override bulk command execution for __ALL__ targets
    # (handled inside OTP confirmation block above via all_hwids key)


# Patch the OTP confirmation to handle bulk commands
_original_start = start_telegram_bot

def start_telegram_bot():
    """Wrapper that patches bulk OTP handling."""
    import random
    if not TG_BOT_TOKEN or not TG_ADMIN_CHAT:
        logger.warning("[TG] Bot credentials missing. Disabled.")
        return

    logger.info("[TG] Telegram Admin Bot started (OTP-secured).")
    _tg_send(TG_ADMIN_CHAT, "✅ *Nexus Control Tower* is online.\nType /help for commands.")

    pending_otps = {}
    offset = 0

    def _generate_otp(action, hwid, client_name, all_hwids=None):
        otp = str(random.randint(100000, 999999))
        pending_otps[otp] = {
            "action": action,
            "hwid": hwid,
            "client_name": client_name,
            "all_hwids": all_hwids,
            "expires_at": time.time() + 60
        }
        return otp

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

        # Cleanup expired OTPs
        now = time.time()
        for k in list(pending_otps):
            if pending_otps[k]["expires_at"] < now:
                del pending_otps[k]

        for update in updates:
            offset = update["update_id"] + 1
            msg = update.get("message", {})
            chat_id = str(msg.get("chat", {}).get("id", ""))
            text = msg.get("text", "").strip()

            if chat_id != TG_ADMIN_CHAT:
                _tg_send(chat_id, "⛔ *Access Denied.* Unauthorized.")
                logger.warning(f"[TG] Unauthorized access from {chat_id}")
                continue

            # ─── OTP Confirmation ────────────────────────────────────────
            if text.isdigit() and len(text) == 6:
                if text in pending_otps:
                    entry = pending_otps.pop(text)
                    if time.time() > entry["expires_at"]:
                        _tg_send(chat_id, "⏰ *OTP Expired.* Please re-issue the command.")
                    else:
                        emoji = "📥" if entry["action"] == "PULL_DATA" else "📤"
                        if entry.get("all_hwids"):
                            for h in entry["all_hwids"]:
                                _tg_queue_command(h, entry["action"])
                            _tg_send(chat_id, f"✅ *Verified!* {emoji} *{entry['action']}* sent to *{entry['client_name']}*.")
                        else:
                            _tg_queue_command(entry["hwid"], entry["action"])
                            _tg_send(chat_id,
                                f"✅ *Verified & Executed!*\n"
                                f"{emoji} *{entry['action']}* → *{entry['client_name']}*\n"
                                f"_Will run within 15 seconds._"
                            )
                        logger.info(f"[TG] Command {entry['action']} queued for {entry['client_name']}")
                else:
                    _tg_send(chat_id, "❌ *Invalid or expired OTP.*")
                continue

            # ─── Commands ────────────────────────────────────────────────
            if text in ("/start", "/help"):
                _tg_send(chat_id,
                    "*⚡ Nexus Admin Bot*\n\n"
                    "`/clients` — List connected machines\n"
                    "`/pull <n>` — Pull Data (client #n)\n"
                    "`/broadcast <n>` — Broadcast Report (client #n)\n"
                    "`/pullall` — Pull Data on ALL clients\n"
                    "`/broadcastall` — Broadcast on ALL clients\n"
                    "`/status` — Server health\n\n"
                    "🔐 *All actions require OTP confirmation.*"
                )

            elif text == "/clients":
                clients = _tg_get_clients()
                if not clients:
                    _tg_send(chat_id, "📭 No bound clients found.")
                else:
                    lines = [f"`{i+1}.` *{name}*" for i, (name, _) in enumerate(clients)]
                    _tg_send(chat_id, "*🖥 Connected Clients:*\n" + "\n".join(lines))

            elif text == "/status":
                count = len(_tg_get_clients())
                _tg_send(chat_id, f"✅ *Control Tower ONLINE*\n🖥 Active clients: *{count}*")

            elif text.startswith("/pull ") or text.startswith("/broadcast "):
                parts = text.split()
                action = "PULL_DATA" if parts[0] == "/pull" else "BROADCAST"
                emoji = "📥" if action == "PULL_DATA" else "📤"
                try:
                    idx = int(parts[1]) - 1
                    clients = _tg_get_clients()
                    if idx < 0 or idx >= len(clients):
                        _tg_send(chat_id, "❌ Invalid number. Use /clients first.")
                    else:
                        name, hwid = clients[idx]
                        otp = _generate_otp(action, hwid, name)
                        _tg_send(chat_id,
                            f"🔐 *Verification Required*\n\n"
                            f"Action: {emoji} *{action}*\n"
                            f"Target: *{name}*\n\n"
                            f"Reply with OTP to confirm:\n"
                            f"```\n{otp}\n```\n"
                            f"_Expires in 60 seconds._"
                        )
                except (ValueError, IndexError):
                    _tg_send(chat_id, "❌ Usage: `/pull 1`  Use /clients for numbers.")

            elif text in ("/pullall", "/broadcastall"):
                action = "PULL_DATA" if text == "/pullall" else "BROADCAST"
                emoji = "📥" if action == "PULL_DATA" else "📤"
                clients = _tg_get_clients()
                if not clients:
                    _tg_send(chat_id, "📭 No active clients found.")
                else:
                    all_hwids = [h for _, h in clients]
                    otp = _generate_otp(action, "__ALL__", f"ALL {len(clients)} clients", all_hwids=all_hwids)
                    _tg_send(chat_id,
                        f"🔐 *Bulk Verification Required*\n\n"
                        f"Action: {emoji} *{action}* on *{len(clients)} clients*\n\n"
                        f"Reply with OTP to confirm:\n"
                        f"```\n{otp}\n```\n"
                        f"_Expires in 60 seconds._"
                    )

            else:
                _tg_send(chat_id, "❓ Unknown command. Type /help.")


def update_godaddy_dns():
    godaddy_key = os.environ.get("GODADDY_API_KEY")
    if not godaddy_key:
        logger.warning("GODADDY_API_KEY not set. Skipping auto-DNS update.")
        return
    try:
        ip = http_client.get("https://checkip.amazonaws.com", timeout=5).text.strip()
        url = "https://api.godaddy.com/v1/domains/devash.in/records/A/@"
        headers = {
            "Authorization": godaddy_key,
            "Content-Type": "application/json"
        }
        payload = [{"data": ip, "ttl": 600}]
        resp = http_client.put(url, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info(f"✅ GoDaddy DNS successfully updated to {ip}")
        else:
            logger.error(f"Failed to update GoDaddy DNS: {resp.status_code} - {resp.text}")
    except Exception as e:
        logger.error(f"Error updating GoDaddy DNS: {e}")

@app.on_event("startup")
def on_startup():
    # Update GoDaddy DNS to point devash.in to this container's new ephemeral IP
    threading.Thread(target=update_godaddy_dns, daemon=True).start()

    if TG_BOT_TOKEN and TG_ADMIN_CHAT:
        t = threading.Thread(target=start_telegram_bot, daemon=True)
        t.start()
        logger.info("[TG] Bot thread launched.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


