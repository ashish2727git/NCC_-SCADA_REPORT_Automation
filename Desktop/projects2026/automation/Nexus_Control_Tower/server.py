import os
import sqlite3
import logging
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
    conn.commit()
    conn.close()

init_db()

# ─── Admin Secret (simple protection) ─────────────────────────────────────
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "nexus-admin-2026")

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
    # Returns a high version number so the client will always update if they click "Check for Updates"
    return {
        "latest_version": "99.99",
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
