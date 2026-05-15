import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
from datetime import datetime
import os
import threading
import schedule
import time
import glob
import requests
from bs4 import BeautifulSoup
import urllib3
import re
import urllib.parse
from dotenv import load_dotenv
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Border, Side, Alignment
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import selenium.webdriver.chrome.webdriver 
from webdriver_manager.chrome import ChromeDriverManager
import winreg as reg

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pandas")

# ── 📦 APPDATA RESOLVER ──
import sys
_APPDATA = os.getenv("APPDATA")
if not _APPDATA:
    _APPDATA = os.path.expanduser("~")

_BASE_DIR = os.path.join(_APPDATA, "NexusSyncPro")
os.makedirs(_BASE_DIR, exist_ok=True)

# Load secure credentials explicitly from the app folder
load_dotenv(os.path.join(_BASE_DIR, ".env"))

# ==========================================
# ⚙️ MASTER CONFIGURATION
# ==========================================
PORTAL_URL = "http://122.186.209.30:8068/NCC/Sitapur/Sign-In-Users.php"
CONFIG_FILE = os.path.join(_BASE_DIR, "nexus_config.json")

def _load_app_config():
    """Load credentials from nexus_config.json if it exists, else fall back to .env."""
    import json
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                cfg = json.load(f)
            return cfg.get("portal_user") or os.getenv("PORTAL_USER"), \
                   cfg.get("portal_pass") or os.getenv("PORTAL_PASS"), \
                   cfg.get("district", "Sitapur"), \
                   cfg.get("tg_token", "")
        except Exception:
            pass
    return os.getenv("PORTAL_USER"), os.getenv("PORTAL_PASS"), os.getenv("PORTAL_DISTRICT", "Sitapur"), ""

MY_USER, MY_PASS, MY_DISTRICT, _SAVED_TG_TOKEN = _load_app_config()

CHROME_DATA_DIR = os.path.join(_BASE_DIR, "Nexus_Chrome_Profile")
CONTACT_FILE = os.path.join(_BASE_DIR, "whatsapp_contacts.txt")

# Bright "Arctic Ice" Theme
CLR_BG = "#f8f9fa"         # Light crisp gray
CLR_SIDEBAR = "#ffffff"    # Pure white
CLR_CARD = "#ffffff"       # Pure white cards
CLR_BORDER = "#d1d5db"     # Soft gray borders
CLR_CYAN = "#0ea5e9"       # Sky Blue
CLR_GREEN = "#10b981"      # Emerald Green
CLR_GOLD = "#f59e0b"       # Bright Amber
CLR_TEXT = "#111827"       # Very dark gray (almost black)
CLR_DIM = "#6b7280"        # Slate gray for secondary text

# Telegram Bot Config
TG_BASE = "https://api.telegram.org/bot"
CRED_FILE = os.path.join(_BASE_DIR, "bot_credentials.json")

class NexusSyncPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("NEXUS SYNC | Enterprise Suite v13.1 (Production)")
        
        # --- Dynamic Resolution Discovery & Auto-Scaling ---
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        
        # Calculate optimal size based on display
        if screen_w <= 1280:
            # For 1024x768 or similar, use almost full screen
            width = int(screen_w * 0.95)
            height = int(screen_h * 0.9)
            ctk.set_widget_scaling(0.85) # Scale down to fit all metrics
        else:
            # For 1080p and above, use balanced proportions
            width = min(1366, int(screen_w * 0.8))
            height = min(800, int(screen_h * 0.8))
            ctk.set_widget_scaling(1.0)

        # Center the window
        x = (screen_w // 2) - (width // 2)
        y = (screen_h // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        self.after(0, lambda: self.state('zoomed')) # Start Maximized for best visibility
        self.configure(fg_color=CLR_BG)
        
        self.license_file = os.path.join(_BASE_DIR, ".nexus_license")
        if self._verify_saved_license():
            if self._has_credentials():
                self.boot_system()
            else:
                self.show_setup_wizard()
        else:
            self.show_license_screen()

    def _verify_saved_license(self):
        if os.path.exists(self.license_file):
            try:
                with open(self.license_file, "r") as f:
                    key = f.read().strip()
                return self._is_key_valid(key)
            except Exception: pass
        return False

    def _get_hwid(self):
        import uuid
        return str(uuid.getnode())

    def _is_key_valid(self, key):
        import requests
        try:
            hwid = self._get_hwid()
            resp = requests.post("http://devash.in/api/verify_license", json={"key": key, "hwid": hwid}, timeout=5)
            if resp.status_code == 200:
                return True
            else:
                self.last_license_error = resp.json().get("detail", "Invalid License")
                return False
        except Exception:
            # Graceful Degradation: If the Control Tower server is offline, allow the user to continue working
            return True

    def show_license_screen(self):
        for w in self.winfo_children(): w.destroy()
        
        frame = ctk.CTkFrame(self, fg_color=CLR_CARD, corner_radius=10)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(frame, text="🔒 ENTERPRISE LICENSE REQUIRED", font=("Segoe UI", 22, "bold"), text_color=CLR_CYAN).pack(pady=(30, 10), padx=50)
        ctk.CTkLabel(frame, text="Please enter a valid Product Key to unlock the Nexus Sync Engine.", font=("Segoe UI", 12), text_color=CLR_DIM).pack(pady=(0, 20))
        
        self.key_entry = ctk.CTkEntry(frame, width=320, height=45, font=("Consolas", 16, "bold"), justify="center", placeholder_text="XXXX-XXXX-XXXX")
        self.key_entry.pack(pady=10)
        
        self.err_lbl = ctk.CTkLabel(frame, text="", text_color="#ff4d4d", font=("Segoe UI", 12))
        self.err_lbl.pack(pady=5)
        
        ctk.CTkButton(frame, text="ACTIVATE NOW", width=220, height=45, font=("Segoe UI", 14, "bold"), fg_color=CLR_GREEN, hover_color="#059669", command=self.submit_license).pack(pady=(10, 30))
        
    def submit_license(self):
        key = self.key_entry.get().strip().upper()
        if self._is_key_valid(key):
            try:
                with open(self.license_file, "w") as f:
                    f.write(key)
            except Exception: pass
            self.err_lbl.configure(text="✅ Activation Successful!", text_color=CLR_GREEN)
            self.after(800, self.show_setup_wizard)  # Go to credentials wizard next
        else:
            err_msg = getattr(self, 'last_license_error', "❌ Invalid Product Key.")
            self.err_lbl.configure(text=f"❌ {err_msg}", text_color="#ff4d4d")

    def _has_credentials(self):
        """Check if user has already completed the setup wizard."""
        import json
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE) as f:
                    cfg = json.load(f)
                return bool(cfg.get("portal_user") and cfg.get("portal_pass"))
            except Exception: pass
        return False

    def show_setup_wizard(self):
        """Full-screen credentials setup wizard shown on first launch."""
        for w in self.winfo_children(): w.destroy()

        outer = ctk.CTkFrame(self, fg_color="#0f172a")
        outer.place(relx=0, rely=0, relwidth=1, relheight=1)

        frame = ctk.CTkFrame(outer, fg_color=CLR_CARD, corner_radius=14, width=520)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        # Header
        ctk.CTkLabel(frame, text="⚙️ FIRST-TIME SETUP", font=("Segoe UI", 22, "bold"), text_color=CLR_CYAN).pack(pady=(30, 4), padx=40)
        ctk.CTkLabel(frame, text="Enter your portal credentials below.\nThese are saved securely on this device only.",
                     font=("Segoe UI", 12), text_color=CLR_DIM, justify="center").pack(pady=(0, 20))

        ctk.CTkFrame(frame, fg_color=CLR_BORDER, height=1).pack(fill="x", padx=30, pady=(0, 20))

        # ── Portal credentials section ──
        ctk.CTkLabel(frame, text="🌐  PORTAL LOGIN", font=("Segoe UI", 11, "bold"), text_color=CLR_GOLD).pack(anchor="w", padx=40)

        self.setup_user = ctk.CTkEntry(frame, width=440, height=40, placeholder_text="Portal Username",
                                        font=("Segoe UI", 13), fg_color="#f1f5f9", border_color=CLR_BORDER)
        self.setup_user.pack(pady=(8, 6), padx=40)

        self.setup_pass = ctk.CTkEntry(frame, width=440, height=40, placeholder_text="Portal Password",
                                        font=("Segoe UI", 13), show="●", fg_color="#f1f5f9", border_color=CLR_BORDER)
        self.setup_pass.pack(pady=(0, 6), padx=40)

        self.setup_district = ctk.CTkEntry(frame, width=440, height=40, placeholder_text="District (e.g. Sitapur)",
                                            font=("Segoe UI", 13), fg_color="#f1f5f9", border_color=CLR_BORDER)
        self.setup_district.insert(0, "Sitapur")
        self.setup_district.pack(pady=(0, 16), padx=40)

        ctk.CTkFrame(frame, fg_color=CLR_BORDER, height=1).pack(fill="x", padx=30, pady=(0, 16))

        # ── Telegram section ──
        ctk.CTkLabel(frame, text="🤖  TELEGRAM BOT (Optional)", font=("Segoe UI", 11, "bold"), text_color=CLR_GOLD).pack(anchor="w", padx=40)
        self.setup_tg = ctk.CTkEntry(frame, width=440, height=40, placeholder_text="Bot Token from @BotFather (leave blank to skip)",
                                      font=("Segoe UI", 13), show="●", fg_color="#f1f5f9", border_color=CLR_BORDER)
        self.setup_tg.pack(pady=(8, 16), padx=40)

        # Error label
        self.setup_err = ctk.CTkLabel(frame, text="", text_color="#ff4d4d", font=("Segoe UI", 12))
        self.setup_err.pack(pady=(0, 6))

        # Save button
        ctk.CTkButton(frame, text="✅  SAVE & LAUNCH", width=440, height=48,
                      font=("Segoe UI", 15, "bold"), fg_color=CLR_GREEN, hover_color="#059669",
                      command=self.submit_setup).pack(pady=(0, 30), padx=40)

    def submit_setup(self):
        """Validate and save credentials from the setup wizard."""
        import json
        global MY_USER, MY_PASS, MY_DISTRICT

        user = self.setup_user.get().strip()
        pwd  = self.setup_pass.get().strip()
        dist = self.setup_district.get().strip() or "Sitapur"
        tg   = self.setup_tg.get().strip()

        if not user or not pwd:
            self.setup_err.configure(text="❌ Username and Password are required.")
            return

        cfg = {"portal_user": user, "portal_pass": pwd, "district": dist, "tg_token": tg}
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(cfg, f, indent=2)
        except Exception as e:
            self.setup_err.configure(text=f"❌ Could not save: {e}")
            return

        # Update globals in-memory so the current session uses them immediately
        MY_USER   = user
        MY_PASS   = pwd
        MY_DISTRICT = dist

        self.boot_system()

    def reboot_to_main(self):
        for w in self.winfo_children(): w.destroy()
        if self._has_credentials():
            self.boot_system()
        else:
            self.show_setup_wizard()


    def boot_system(self):
        self.service_active = tk.BooleanVar(value=True)
        
        self.contacts = self.load_contacts()
        self.browser_lock = threading.Lock()
        self._jjm_cache = {"count": {"total": "0", "live": "0", "not_received": "0", "leftover": "0"}, "timestamp": 0.0}
        self.scada_data = {}
        self.jjm_list_data = {
            "total": ["Detailed per-scheme list not locally extracted.", "JJM portal aggregates these numbers at district level."],
            "live": ["Detailed per-scheme list not locally extracted.", "JJM portal aggregates these numbers at district level."],
            "not_recv": ["Detailed per-scheme list not locally extracted.", "JJM portal aggregates these numbers at district level."],
            "leftover": ["Detailed per-scheme list not locally extracted.", "(Computed aggregate difference)."]
        }
        
        # Telegram Bot state
        self.bot_running = False
        self.bot_thread = None
        self.last_update_id = 0
        self.token_var = tk.StringVar()
        self._load_creds()
        
        self.setup_ui()
        
        os.makedirs(CHROME_DATA_DIR, exist_ok=True)
        self.today_str = datetime.today().strftime("%d-%m-%Y")

        # ── OTA Update Check — runs every 2 hours throughout the day ──
        threading.Thread(target=self._periodic_update_check, daemon=True).start()

        # ── Remote Command Listener ──
        threading.Thread(target=self._remote_command_listener, daemon=True).start()

        # ── What's New Popup (shown once per version) ──
        self.after(1500, self._check_whats_new)

        # ── INITIALIZE WORKSPACE (Auto-selects last location) ──
        self.watch_folder = self._select_workspace_folder()

        self.safe_log_update("[SYS] System Architecture v14.0 (Production Ready) Initialized.")
        self.safe_log_update(f"[SYS] Daily data directory mapped: {self.watch_folder}")
        if os.listdir(self.watch_folder):
            self.safe_log_update(f"[SYS] Existing files detected in today's folder — reusing workspace.")
        
        self._register_startup()
        
        if self.service_active.get() and self.token_var.get().strip():
            self.start_bot()
        
        threading.Thread(target=self.run_scheduler, daemon=True).start()
        threading.Thread(target=self.startup_check, daemon=True).start()

    def _check_whats_new(self):
        """Show What's New popup once per version after an update."""
        CURRENT_VER = "14.0"
        ver_file = os.path.join(_BASE_DIR, ".last_seen_version")
        try:
            if os.path.exists(ver_file):
                with open(ver_file, "r") as f:
                    last_seen = f.read().strip()
                if last_seen == CURRENT_VER:
                    return  # Already seen this version, don't show
            # Show the popup
            self._show_whats_new(CURRENT_VER)
            # Record that we've shown it
            with open(ver_file, "w") as f:
                f.write(CURRENT_VER)
        except Exception:
            pass

    def _show_whats_new(self, version):
        """Display a premium What's New popup for the current version."""
        popup = ctk.CTkToplevel(self)
        popup.title(f"What's New in v{version}")
        popup.attributes("-topmost", True)
        popup.grab_set()
        popup.configure(fg_color="#0f172a")

        # Center the popup
        pw, ph = 520, 540
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        popup.geometry(f"{pw}x{ph}+{(sw-pw)//2}+{(sh-ph)//2}")
        popup.resizable(False, False)

        # Header
        header = ctk.CTkFrame(popup, fg_color="#1e3a5f", corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(header, text="⚡", font=("Segoe UI", 36)).pack(pady=(20, 0))
        ctk.CTkLabel(header, text=f"What's New in v{version}",
                     font=("Segoe UI", 22, "bold"), text_color="#60a5fa").pack(pady=(4, 4))
        ctk.CTkLabel(header, text="Nexus Sync Enterprise Suite",
                     font=("Segoe UI", 11), text_color="#94a3b8").pack(pady=(0, 16))

        # Features list
        scroll = ctk.CTkScrollableFrame(popup, fg_color="#0f172a", height=320)
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        features = [
            ("📡", "Telegram Remote Control",
             "Trigger Pull Data or Broadcast reports on any field machine directly from your phone via Telegram — without being in the office."),
            ("🔐", "OTP Command Verification",
             "Every remote Telegram command now requires a unique 6-digit One-Time Password that expires in 60 seconds, preventing accidental or unauthorized actions."),
            ("🖥", "Admin Desktop Control Panel",
             "New Nexus Admin Control app lets you start/stop the cloud server, generate/revoke licenses, and monitor live server logs — all without opening a browser."),
            ("🛡", "Hardware-Bound Licensing",
             "Each license key now permanently locks to your specific PC hardware. The same key cannot be used on a second device."),
            ("📂", "Secure AppData Storage",
             "All configuration files and credentials are now stored invisibly in your system's AppData folder instead of visible Downloads locations."),
        ]

        for icon, title, desc in features:
            row = ctk.CTkFrame(scroll, fg_color="#1e293b", corner_radius=10)
            row.pack(fill="x", pady=6, padx=4)
            top = ctk.CTkFrame(row, fg_color="transparent")
            top.pack(fill="x", padx=14, pady=(12, 2))
            ctk.CTkLabel(top, text=icon, font=("Segoe UI", 20), width=30).pack(side="left")
            ctk.CTkLabel(top, text=title, font=("Segoe UI", 13, "bold"),
                         text_color="#e2e8f0").pack(side="left", padx=8)
            ctk.CTkLabel(row, text=desc, font=("Segoe UI", 11),
                         text_color="#94a3b8", wraplength=440, justify="left").pack(
                             padx=14, pady=(0, 12), anchor="w")

        # Close button
        ctk.CTkButton(
            popup, text="Got it — Let's Go! 🚀",
            font=("Segoe UI", 13, "bold"), height=44,
            fg_color="#3b82f6", hover_color="#2563eb",
            command=popup.destroy
        ).pack(fill="x", padx=20, pady=(0, 20))

    def manual_check_updates(self):
        """Manually triggered update check from sidebar button."""
        CURRENT_VER = "14.1"
        try:
            resp = requests.get("http://devash.in/api/update_check", timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                latest_ver = data.get("latest_version", "0.0")
                dl_url = data.get("download_url", "")
                has_update = float(latest_ver) > float(CURRENT_VER)
                self.after(0, lambda: self._show_update_status_popup(CURRENT_VER, latest_ver, dl_url, has_update, online=True))
            else:
                self.after(0, lambda: self._show_update_status_popup(CURRENT_VER, "?", "", False, online=False))
        except Exception:
            self.after(0, lambda: self._show_update_status_popup(CURRENT_VER, "?", "", False, online=False))

    def _show_update_status_popup(self, current_ver, latest_ver, dl_url, has_update, online=True):
        """Show a rich update status popup."""
        popup = ctk.CTkToplevel(self)
        popup.title("Software Update")
        popup.attributes("-topmost", True)
        popup.grab_set()
        popup.configure(fg_color="#0f172a")
        pw, ph = 500, 540
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        popup.geometry(f"{pw}x{ph}+{(sw-pw)//2}+{(sh-ph)//2}")
        popup.resizable(False, False)

        # ── Header ──
        hdr_color = "#14532d" if (online and not has_update) else ("#1e3a5f" if has_update else "#3b1f00")
        header = ctk.CTkFrame(popup, fg_color=hdr_color, corner_radius=0)
        header.pack(fill="x")

        if not online:
            icon, title, subtitle = "⚠️", "Server Unreachable", "Could not connect to the update server"
            hdr_text_color = "#fbbf24"
        elif has_update:
            icon, title, subtitle = "🚀", f"Update Available — v{latest_ver}", "A new version of Nexus Sync is ready"
            hdr_text_color = "#60a5fa"
        else:
            icon, title, subtitle = "✅", "You're Up to Date!", f"Nexus Sync v{current_ver} is the latest version"
            hdr_text_color = "#4ade80"

        ctk.CTkLabel(header, text=icon, font=("Segoe UI", 32)).pack(pady=(18, 0))
        ctk.CTkLabel(header, text=title, font=("Segoe UI", 20, "bold"), text_color=hdr_text_color).pack(pady=(4, 2))
        ctk.CTkLabel(header, text=subtitle, font=("Segoe UI", 11), text_color="#94a3b8").pack(pady=(0, 14))

        # ── Version badge row ──
        badge_frame = ctk.CTkFrame(popup, fg_color="#1e293b", corner_radius=8)
        badge_frame.pack(fill="x", padx=20, pady=12)
        left = ctk.CTkFrame(badge_frame, fg_color="transparent")
        left.pack(side="left", padx=20, pady=10)
        ctk.CTkLabel(left, text="INSTALLED", font=("Segoe UI", 9, "bold"), text_color="#64748b").pack(anchor="w")
        ctk.CTkLabel(left, text=f"v{current_ver}", font=("Segoe UI", 20, "bold"), text_color="#e2e8f0").pack(anchor="w")
        if online:
            right = ctk.CTkFrame(badge_frame, fg_color="transparent")
            right.pack(side="right", padx=20, pady=10)
            ctk.CTkLabel(right, text="LATEST", font=("Segoe UI", 9, "bold"), text_color="#64748b").pack(anchor="e")
            color = "#4ade80" if not has_update else "#60a5fa"
            ctk.CTkLabel(right, text=f"v{latest_ver}", font=("Segoe UI", 20, "bold"), text_color=color).pack(anchor="e")

        # ── What's New list ──
        ctk.CTkLabel(popup, text="📌  WHAT'S IN v14.0", font=("Segoe UI", 11, "bold"),
                     text_color="#94a3b8").pack(anchor="w", padx=24, pady=(4, 0))
        scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent", height=190)
        scroll.pack(fill="x", padx=20, pady=(4, 0))

        features = [
            ("📡", "Telegram Remote Control — trigger field machines from your phone"),
            ("🔐", "OTP Command Verification — 6-digit one-time code before every action"),
            ("🖥", "Admin Desktop Control Panel — manage licenses & server without browser"),
            ("🛡", "Hardware-Bound Licensing — key locks to your specific machine"),
            ("📂", "Secure AppData Storage — invisible, safe credential management"),
            ("🔄", "Overnight Auto-Update — updates apply silently at 7PM shutdown"),
        ]
        for icon_f, text_f in features:
            row = ctk.CTkFrame(scroll, fg_color="#1e293b", corner_radius=8)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=icon_f, font=("Segoe UI", 14), width=28).pack(side="left", padx=(10, 4), pady=8)
            ctk.CTkLabel(row, text=text_f, font=("Segoe UI", 11), text_color="#cbd5e1",
                         wraplength=380, justify="left").pack(side="left", padx=4, pady=8)

        # ── Action buttons ──
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=12)

        if has_update:
            def _start_download():
                dl_btn.configure(state="disabled", text="⏳ Downloading...")
                threading.Thread(target=self.check_for_updates, daemon=True).start()
                popup.after(2000, popup.destroy)
            dl_btn = ctk.CTkButton(btn_frame, text="⬇ Download & Install",
                font=("Segoe UI", 13, "bold"), height=44, fg_color="#3b82f6",
                hover_color="#2563eb", command=_start_download)
            dl_btn.pack(fill="x", pady=(0, 6))

        close_text = "Close" if not has_update else "Later"
        ctk.CTkButton(btn_frame, text=close_text,
            font=("Segoe UI", 12), height=36,
            fg_color="transparent", border_width=1, border_color=CLR_BORDER,
            text_color=CLR_DIM, command=popup.destroy).pack(fill="x")

    def _select_workspace_folder(self, force_prompt=False):
        """Pick a base folder. Auto-selects if config exists unless force_prompt is True."""
        config_path = os.path.join(_BASE_DIR, ".nexus_workspace_path")
        last_dir = None
        if os.path.exists(config_path):
            with open(config_path, "r") as fp:
                last_dir = fp.read().strip() or None

        if not force_prompt and last_dir and os.path.exists(last_dir):
            chosen = last_dir
        else:
            self.safe_log_update("[SYS] Requesting workspace folder selection...")
            self.update()
            chosen = filedialog.askdirectory(
                title="Select Base Workspace Folder for NEXUS SYNC Data",
                initialdir=last_dir or os.path.expanduser("~"),
                mustexist=True,
            )

        if not chosen:
            if last_dir: 
                chosen = last_dir 
            else:
                self.safe_log_update("[SYS] No folder chosen — using default workspace.")
                chosen = os.path.join(_BASE_DIR, "JJM_Daily_Data")

        # Persist the base folder choice
        with open(config_path, "w") as fp:
            fp.write(chosen)

        dated_folder = os.path.join(chosen, self.today_str)
        os.makedirs(dated_folder, exist_ok=True)
        return dated_folder

    def manual_change_workspace(self):
        new_folder = self._select_workspace_folder(force_prompt=True)
        if new_folder:
            self.watch_folder = new_folder
            self.safe_log_update(f"[SYS] Workspace switched: {self.watch_folder}")
            self.rebuild_history_log()
            # Run a fresh analysis on the new folder context
            files = glob.glob(os.path.join(self.watch_folder, '*.xlsx'))
            raw_files = [f for f in files if not os.path.basename(f).startswith("Final_Daily_Report")]
            if raw_files:
                self.analyze_data(max(raw_files, key=os.path.getctime))

    def _periodic_update_check(self):
        """Run OTA update check at startup and then every 2 hours throughout the day."""
        while True:
            self.check_for_updates()
            time.sleep(2 * 60 * 60)  # 2 hours

    def _show_update_banner(self):
        """Show the orange update-ready banner in the sidebar."""
        try:
            self.update_banner.pack(side="bottom", fill="x", padx=12, pady=(0, 4), before=self.sidebar.winfo_children()[-1])
        except Exception:
            pass

    def _restart_app(self):
        """Restart the application immediately (applies staged update if present)."""
        import subprocess
        import shutil
        current_exe = sys.executable if getattr(sys, 'frozen', False) else sys.executable
        update_path = getattr(self, '_update_pending_path', None)

        if update_path and os.path.exists(update_path):
            current_exe_path = sys.executable if getattr(sys, 'frozen', False) else None
            if current_exe_path and current_exe_path.endswith(".exe"):
                old_exe_path = current_exe_path + ".old"
                if os.path.exists(old_exe_path):
                    try:
                        os.remove(old_exe_path)
                    except:
                        pass
                # Rename the running executable so we can free up its filename
                try:
                    os.rename(current_exe_path, old_exe_path)
                    shutil.copy2(update_path, current_exe_path)
                    # Launch the new EXE and kill this old process
                    subprocess.Popen([current_exe_path] + sys.argv,
                                     creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                                     close_fds=True)
                    os._exit(0)
                except Exception as e:
                    self.safe_log_update(f"[OTA] ⚠️ Restart fail (Privilege Error): {e}")
            
            # Fallback if uncompiled
            subprocess.Popen([current_exe] + sys.argv,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
            os._exit(0)
        else:
            # No update — just restart the current exe
            subprocess.Popen([current_exe] + sys.argv,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
            os._exit(0)

    def check_for_updates(self):
        try:
            self.safe_log_update("[SYS] Checking Control Tower for updates...")
            resp = requests.get("http://devash.in/api/update_check", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                latest_ver = data.get("latest_version", "0.0")
                current_ver = "14.1"

                if float(latest_ver) > float(current_ver):
                    self.safe_log_update(f"[OTA] Update available: v{latest_ver}. Downloading silently...")
                    dl_url = f"http://devash.in{data.get('download_url')}"
                    exe_data = requests.get(dl_url, timeout=60).content
                    new_file = os.path.join(_BASE_DIR, "NexusSyncPro_Update.exe")
                    with open(new_file, "wb") as f:
                        f.write(exe_data)
                    self._update_pending_path = new_file
                    self.safe_log_update("[OTA] ✅ Update staged. Applies at 7:00 PM shutdown (or restart now).")
                    self.after(0, self._show_update_banner)
                else:
                    self.safe_log_update("[SYS] Application is up to date.")
        except Exception:
            self.safe_log_update("[SYS] Control Tower offline. Running locally.")

    def _register_startup(self):
        """Register the app in the Windows Registry (Boot) AND Task Scheduler (8 AM Daily)."""
        app_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
        if not app_path.endswith(".exe"):
            return # Skip if not compiled

        # 1. Windows startup registry (for boot)
        try:
            key = reg.HKEY_CURRENT_USER
            sub_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with reg.OpenKey(key, sub_key, 0, reg.KEY_ALL_ACCESS) as registry_key:
                reg.SetValueEx(registry_key, "NexusSyncPro", 0, reg.REG_SZ, f'"{app_path}"')
            self.safe_log_update("[SYS] Configured automatic startup on Windows boot.")
        except Exception as e:
            self.safe_log_update(f"[SYS] ⚠️ Registry startup fail: {str(e)}")

        # 2. Windows Task Scheduler (for 8 AM Daily Re-open)
        try:
            # We use standard user privileges (/rl limited) to ensure no Admin popups
            cmd = f'schtasks /create /tn "NexusSyncPro_DailyOpen" /tr "\\"{app_path}\\"" /sc daily /st 08:00 /f'
            os.system(cmd)
            self.safe_log_update("[SYS] Configured Daily Re-open Task for 08:00 AM (Standard User).")
        except Exception as e:
            self.safe_log_update(f"[SYS] ⚠️ Task Scheduler fail: {str(e)}")

    def _remote_command_listener(self):
        """Polls the cloud server for commands issued by the Admin."""
        import time, requests
        hwid = self._get_hwid()
        while True:
            try:
                r = requests.get(f"http://devash.in/api/poll_commands?hwid={hwid}", timeout=5)
                if r.status_code == 200:
                    commands = r.json()
                    for cmd in commands:
                        c_id = cmd["id"]
                        c_text = cmd["command"]
                        self.safe_log_update(f"[REMOTE] Received cloud command: {c_text}")
                        
                        if c_text == "PULL_DATA":
                            self.trigger_manual_pull()
                        elif c_text == "BROADCAST":
                            self.trigger_manual_send()
                            
                        # Acknowledge execution so it's removed from queue
                        requests.post("http://devash.in/api/ack_command", json={"command_id": c_id}, timeout=5)
            except Exception:
                pass # Fail silently if server is offline
            time.sleep(15)

    def auto_close_app(self):
        """End of day clean shutdown. Applies any pending OTA update before exiting."""
        self.safe_log_update("\n[SYS] 7:00 PM REACHED. System performing scheduled shutdown...")
        self.update()

        # ── OTA AUTO-SWAP: If an update was downloaded today, apply it now ──
        update_path = getattr(self, '_update_pending_path', None)
        if update_path and os.path.exists(update_path):
            try:
                current_exe = sys.executable if getattr(sys, 'frozen', False) else None
                if current_exe and current_exe.endswith(".exe"):
                    self.safe_log_update("[OTA] Staging overnight update swap...")
                    # Write a bat that: waits 3s, replaces exe, updates Task Scheduler, launches new version
                    bat_path = os.path.join(_BASE_DIR, "nexus_updater.bat")
                    bat_content = f"""@echo off
:: Nexus Auto-Updater - Runs after app closes at 7 PM
ping -n 4 127.0.0.1 > nul
copy /Y "{update_path}" "{current_exe}"
del "{update_path}"
schtasks /create /tn "NexusSyncPro_DailyOpen" /tr "\"{current_exe}\"" /sc daily /st 08:00 /f > nul
del "%~f0"
"""
                    with open(bat_path, 'w') as f:
                        f.write(bat_content)
                    # Launch the bat detached so it runs after this process exits
                    import subprocess
                    subprocess.Popen(
                        ['cmd', '/c', bat_path],
                        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                        close_fds=True
                    )
                    self.safe_log_update("[OTA] ✅ Auto-updater launched. New version will be ready at 8:00 AM.")
            except Exception as e:
                self.safe_log_update(f"[OTA] ⚠️ Update swap failed: {e}")

        time.sleep(2)
        os._exit(0)

    def setup_ui(self):
        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, fg_color=CLR_SIDEBAR, width=260, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # Scrollable area for sidebar content
        self.sidebar_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent", corner_radius=0, label_text="")
        self.sidebar_scroll.pack(fill="both", expand=True)
        
        ctk.CTkLabel(self.sidebar_scroll, text="NEXUS SYNC", font=("Segoe UI", 24, "bold"), text_color=CLR_CYAN).pack(pady=(30, 5))
        ctk.CTkLabel(self.sidebar_scroll, text="PRODUCTION BUILD", font=("Segoe UI", 9, "bold"), text_color=CLR_GOLD).pack(pady=(0, 20))

        ctrl_frame = ctk.CTkFrame(self.sidebar_scroll, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=20, pady=10)
        
        self.service_switch = ctk.CTkSwitch(self.sidebar_scroll, text="AUTO-PILOT MODE", variable=self.service_active, font=("Segoe UI", 12, "bold"), fg_color=CLR_DIM, progress_color=CLR_GREEN, command=self.on_autopilot_toggle)
        self.service_switch.pack(pady=(0, 20))

        self.pull_btn = ctk.CTkButton(ctrl_frame, text="📥 PULL NEW DATA", fg_color="#f1f5f9", hover_color="#e2e8f0", 
                                     border_width=1, border_color=CLR_CYAN, text_color=CLR_CYAN, font=("Segoe UI", 13, "bold"), height=40, command=self.trigger_manual_pull)
        self.pull_btn.pack(fill="x", pady=5)
        
        self.send_btn = ctk.CTkButton(ctrl_frame, text="📤 BROADCAST REPORT", fg_color=CLR_GREEN, hover_color="#059669", 
                                     text_color="#ffffff", font=("Segoe UI", 13, "bold"), height=40, command=self.trigger_manual_send)
        self.send_btn.pack(fill="x", pady=5)

        self.report_btn = ctk.CTkButton(ctrl_frame, text="📊 GENERATE DAILY REPORT", fg_color=CLR_GOLD, hover_color="#d97706", 
                                     text_color="#ffffff", font=("Segoe UI", 13, "bold"), height=40, command=self.generate_final_report)
        self.report_btn.pack(fill="x", pady=5)

        self.ws_btn = ctk.CTkButton(ctrl_frame, text="📁 CHANGE WORKSPACE", fg_color="transparent", border_width=1, border_color=CLR_BORDER,
                                     text_color=CLR_TEXT, font=("Segoe UI", 13, "bold"), height=40, command=self.manual_change_workspace)
        self.ws_btn.pack(fill="x", pady=5)

        ctk.CTkFrame(self.sidebar_scroll, fg_color=CLR_BORDER, height=2).pack(fill="x", padx=30, pady=20)

        ctk.CTkLabel(self.sidebar_scroll, text="📒 CONTACT BOOK", font=("Segoe UI", 10, "bold"), text_color=CLR_CYAN).pack(anchor="w", padx=30, pady=(0, 6))

        cb_frame = ctk.CTkFrame(self.sidebar_scroll, fg_color="transparent")
        cb_frame.pack(fill="x", padx=20)
        ctk.CTkLabel(cb_frame, text="Name", font=("Segoe UI", 10), text_color="#9599a1").pack(anchor="w")
        self.contact_name_entry = ctk.CTkEntry(cb_frame, placeholder_text="e.g. Gopi Sir", height=34, fg_color=CLR_BG, border_color=CLR_BORDER)
        self.contact_name_entry.pack(fill="x", pady=(2, 6))
        ctk.CTkLabel(cb_frame, text="Phone (with country code)", font=("Segoe UI", 10), text_color="#9599a1").pack(anchor="w")
        self.contact_phone_entry = ctk.CTkEntry(cb_frame, placeholder_text="e.g. 919951092727", height=34, fg_color=CLR_BG, border_color=CLR_BORDER)
        self.contact_phone_entry.pack(fill="x", pady=(2, 8))
        ctk.CTkButton(cb_frame, text="+ Add Contact", command=self.add_contact,
                      fg_color="transparent", border_width=1, border_color=CLR_BORDER,
                      font=("Segoe UI", 12, "bold"), height=34).pack(fill="x")

        self.contact_listbox = tk.Listbox(self.sidebar_scroll, bg=CLR_BG, fg=CLR_TEXT, borderwidth=0,
                                          highlightthickness=0, font=("Segoe UI", 11),
                                          selectbackground=CLR_CYAN, selectforeground=CLR_BG)
        self.contact_listbox.pack(fill="both", expand=True, padx=25, pady=10)
        self.refresh_contact_ui()
        ctk.CTkButton(self.sidebar_scroll, text="🗑 Remove Selected", text_color="#ff4d4d",
                      fg_color="transparent", command=self.remove_contact).pack(pady=(0, 10))

        # ── UPDATE READY BANNER (hidden until update is staged) ──
        self.update_banner = ctk.CTkFrame(self.sidebar, fg_color="#92400e", corner_radius=8)
        # Not packed yet — shown dynamically when update is ready
        self.update_banner_label = ctk.CTkLabel(
            self.update_banner,
            text="📦 Update Ready!",
            font=("Segoe UI", 10, "bold"), text_color="#fef3c7"
        )
        self.update_banner_label.pack(pady=(6, 0))
        ctk.CTkLabel(
            self.update_banner,
            text="Applies tonight at 7 PM",
            font=("Segoe UI", 9), text_color="#fde68a"
        ).pack(pady=(0, 4))
        ctk.CTkButton(
            self.update_banner,
            text="⏰ Restart Now to Apply",
            font=("Segoe UI", 10, "bold"),
            fg_color="#d97706", hover_color="#b45309",
            text_color="#ffffff", height=30,
            command=self._restart_app
        ).pack(fill="x", padx=8, pady=(0, 8))

        # ── BOTTOM BUTTONS (Check Updates + Restart) ──
        bottom_btns = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_btns.pack(side="bottom", fill="x", padx=20, pady=(0, 6))

        ctk.CTkButton(
            bottom_btns,
            text="🔄 Check Updates",
            font=("Segoe UI", 10, "bold"),
            fg_color="transparent", border_width=1, border_color=CLR_BORDER,
            text_color=CLR_DIM, height=30,
            command=lambda: threading.Thread(target=self.manual_check_updates, daemon=True).start()
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            bottom_btns,
            text="↻",
            font=("Segoe UI", 13, "bold"),
            fg_color="transparent", border_width=1, border_color=CLR_BORDER,
            text_color=CLR_DIM, height=30, width=36,
            command=self._restart_app
        ).pack(side="right")

        # ── DEVELOPER CREDIT ──
        ctk.CTkLabel(self.sidebar, text="DEVELOPED BY: ASHISH KUMAR", font=("Segoe UI", 9, "italic"), text_color=CLR_DIM).pack(side="bottom", pady=(10, 4))
        ctk.CTkLabel(self.sidebar, text="v14.1 • Enterprise Suite", font=("Segoe UI", 9), text_color=CLR_DIM).pack(side="bottom", pady=(0, 0))

        # --- MAIN TABVIEW ---
        self.main_tabs = ctk.CTkTabview(self, fg_color="transparent")
        self.main_tabs.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        self.tab_dash = self.main_tabs.add("📊 SCADA DASHBOARD")
        self.tab_bot = self.main_tabs.add("🤖 TELEGRAM BOT")
        
        # --- DASHBOARD TAB ---
        self.display = ctk.CTkScrollableFrame(self.tab_dash, fg_color="transparent")
        self.display.pack(fill="both", expand=True)

        # Top Split Frame (Logs & History)
        self.top_split = ctk.CTkFrame(self.display, fg_color="transparent")
        self.top_split.pack(fill="x", pady=(0, 15))

        # 1. System Log Terminal
        self.log_container = ctk.CTkFrame(self.top_split, fg_color=CLR_CARD, border_width=1, border_color=CLR_BORDER, height=220)
        self.log_container.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.log_container.pack_propagate(False) 
        ctk.CTkLabel(self.log_container, text="📡 SYSTEM LOG ENGINE", font=("Segoe UI", 11, "bold"), text_color=CLR_CYAN).pack(anchor="w", padx=15, pady=5)
        self.log_terminal = ctk.CTkTextbox(self.log_container, fg_color="#f3f4f6", text_color=CLR_TEXT, font=("Consolas", 11))
        self.log_terminal.pack(fill="both", expand=True, padx=10, pady=10)

        # 2. Daily Mapping History Terminal
        self.history_container = ctk.CTkFrame(self.top_split, fg_color=CLR_CARD, border_width=1, border_color=CLR_BORDER, height=220)
        self.history_container.pack(side="right", fill="both", expand=True, padx=(10, 0))
        self.history_container.pack_propagate(False)
        ctk.CTkLabel(self.history_container, text="⏱️ DAILY MAPPING HISTORY", font=("Segoe UI", 11, "bold"), text_color=CLR_CYAN).pack(anchor="w", padx=15, pady=5)
        self.history_terminal = ctk.CTkTextbox(self.history_container, fg_color="#f3f4f6", text_color=CLR_CYAN, font=("Consolas", 11))
        self.history_terminal.pack(fill="both", expand=True, padx=10, pady=10)

        # Middle Metrics Frame (JJM)
        self.metrics_container = ctk.CTkFrame(self.display, fg_color="transparent")
        self.metrics_container.pack(fill="x", pady=(0, 15))
        
        self.jjm_total_lbl = self._create_metric_card(self.metrics_container, "TOTAL JJM SCHEMES", "0", CLR_CYAN, command=lambda e: self.show_list_popup("JJM TOTAL", self.jjm_list_data.get("total", [])))
        self.jjm_live_lbl = self._create_metric_card(self.metrics_container, "LIVE CONNECTED", "0", CLR_GREEN, command=lambda e: self.show_list_popup("JJM LIVE CONNECTED", self.jjm_list_data.get("live", [])))
        self.jjm_not_recv_lbl = self._create_metric_card(self.metrics_container, "DATA NOT RECEIVED", "0", CLR_GOLD, command=lambda e: self.show_list_popup("JJM NOT RECEIVED", self.jjm_list_data.get("not_recv", [])))
        self.jjm_leftover_lbl = self._create_metric_card(self.metrics_container, "OFF-GRID / MISSING", "0", "#ff4d4d", command=lambda e: self.show_list_popup("JJM OFF-GRID / MISSING", self.jjm_list_data.get("leftover", [])))

        # SCADA Metrics Frame
        self.scada_metrics_container = ctk.CTkFrame(self.display, fg_color="transparent")
        self.scada_metrics_container.pack(fill="x", pady=(0, 15))
        
        self.scada_total_lbl = self._create_metric_card(self.scada_metrics_container, "SCADA TOTAL (EXCEL)", "0", CLR_CYAN, command=lambda e: self.show_list_popup("SCADA TOTAL SCHEMES", self.scada_data.get("total", [])))
        self.scada_sync_lbl = self._create_metric_card(self.scada_metrics_container, "NOW SCADA SYNCED", "0", CLR_GREEN, command=lambda e: self.show_list_popup("SCADA SYNCED SCHEMES", self.scada_data.get("synced", [])))
        self.scada_unsync_lbl = self._create_metric_card(self.scada_metrics_container, "NOT YET SYNCED", "0", CLR_GOLD, command=lambda e: self.show_list_popup("SCADA NOT SYNCED", self.scada_data.get("not_synced", [])))
        self.scada_new_lbl = self._create_metric_card(self.scada_metrics_container, "NEWLY ADDED IN SCADA", "0", "#ff4d4d", command=lambda e: self.show_list_popup("SCADA NEWLY ADDED", self.scada_data.get("new", [])))

        # Bottom Split Frame (Reports & WhatsApp)
        self.bottom_split = ctk.CTkFrame(self.display, fg_color="transparent")
        self.bottom_split.pack(fill="both", expand=True)

        # 3. Data Analysis Report
        self.report_container = ctk.CTkFrame(self.bottom_split, fg_color=CLR_CARD, border_width=1, border_color=CLR_BORDER, height=350)
        self.report_container.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.report_container.pack_propagate(False)
        ctk.CTkLabel(self.report_container, text="📊 DATA ANALYSIS REPORT", font=("Segoe UI", 11, "bold"), text_color=CLR_GOLD).pack(anchor="w", padx=15, pady=5)
        self.report_terminal = ctk.CTkTextbox(self.report_container, fg_color="#f3f4f6", text_color=CLR_TEXT, font=("Consolas", 12))
        self.report_terminal.pack(fill="both", expand=True, padx=10, pady=10)

        # 4. WhatsApp Preview Terminal
        self.preview_container = ctk.CTkFrame(self.bottom_split, fg_color=CLR_CARD, border_width=1, border_color=CLR_BORDER, height=350)
        self.preview_container.pack(side="right", fill="both", expand=True, padx=(10, 0))
        self.preview_container.pack_propagate(False)
        ctk.CTkLabel(self.preview_container, text="📱 WHATSAPP PAYLOAD PREVIEW", font=("Segoe UI", 11, "bold"), text_color=CLR_GREEN).pack(anchor="w", padx=15, pady=5)
        self.preview_terminal = ctk.CTkTextbox(self.preview_container, fg_color="#f3f4f6", text_color=CLR_TEXT, font=("Segoe UI", 12))
        self.preview_terminal.pack(fill="both", expand=True, padx=10, pady=10)

        # --- TELEGRAM BOT TAB ---
        self.setup_telegram_ui()

    def _load_creds(self):
        import json
        # 1. Try loading from the unified nexus_config.json (setup wizard)
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE) as f:
                    cfg = json.load(f)
                tok = cfg.get("tg_token", "")
                if tok:
                    self.token_var.set(tok)
                    return
            except Exception: pass
        # 2. Fall back to old bot_credentials.json
        if os.path.exists(CRED_FILE):
            try:
                with open(CRED_FILE) as f:
                    self.token_var.set(json.load(f).get("tg_token", ""))
            except Exception: pass

    def _save_creds(self):
        import json
        with open(CRED_FILE, "w") as f:
            json.dump({"tg_token": self.token_var.get().strip()}, f)

    def setup_telegram_ui(self):
        # Bot Control Panel
        bot_ctrl = ctk.CTkFrame(self.tab_bot, fg_color=CLR_CARD, border_width=1, border_color=CLR_BORDER)
        bot_ctrl.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(bot_ctrl, text="Bot Token  (from @BotFather)", font=("Segoe UI", 11, "bold"), text_color=CLR_DIM).pack(anchor="w", padx=15, pady=(15,0))
        self.token_entry = ctk.CTkEntry(bot_ctrl, textvariable=self.token_var, placeholder_text="123456:ABCdef...", height=38, fg_color=CLR_BG, border_color=CLR_BORDER, show="*")
        self.token_entry.pack(fill="x", padx=15, pady=(5, 15))

        btn_frm = ctk.CTkFrame(bot_ctrl, fg_color="transparent")
        btn_frm.pack(fill="x", padx=15, pady=(0, 15))

        self.start_bot_btn = ctk.CTkButton(btn_frm, text="▶ START TELEGRAM BOT", height=42, fg_color=CLR_GREEN, hover_color="#059669", font=("Segoe UI", 13, "bold"), command=self.start_bot)
        self.start_bot_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.stop_bot_btn = ctk.CTkButton(btn_frm, text="■ STOP BOT", height=42, fg_color="#ff4d4d", hover_color="#cc0000", font=("Segoe UI", 13, "bold"), command=self.stop_bot, state="disabled")
        self.stop_bot_btn.pack(side="left", expand=True, fill="x", padx=(5, 0))

        self.bot_status_lbl = ctk.CTkLabel(bot_ctrl, text="● OFFLINE", font=("Segoe UI", 12, "bold"), text_color="#ff4d4d")
        self.bot_status_lbl.pack(pady=(0, 15))

        # Bot Terminal
        bot_term_frm = ctk.CTkFrame(self.tab_bot, fg_color=CLR_CARD, border_width=1, border_color=CLR_BORDER)
        bot_term_frm.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        ctk.CTkLabel(bot_term_frm, text="📡 BOT COMMUNICATION LOGS", font=("Segoe UI", 12, "bold"), text_color=CLR_CYAN).pack(anchor="w", padx=15, pady=5)
        self.bot_terminal = ctk.CTkTextbox(bot_term_frm, fg_color="#f3f4f6", text_color=CLR_TEXT, font=("Consolas", 12))
        self.bot_terminal.pack(fill="both", expand=True, padx=10, pady=10)

    def log_bot(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.after(0, lambda: self._log_bot_gui(f"[{ts}] {msg}"))

    def _log_bot_gui(self, text):
        self.bot_terminal.insert("end", f"{text}\n")
        self.bot_terminal.see("end")

    # ─── BOT LOGIC ───
    def start_bot(self):
        tok = self.token_var.get().strip()
        if not tok:
            self.log_bot("❌ Error: No token provided.")
            return
        self._save_creds()
        self.start_bot_btn.configure(state="disabled")
        self.token_entry.configure(state="disabled")
        self.stop_bot_btn.configure(state="normal")
        self.bot_status_lbl.configure(text="● ONLINE", text_color=CLR_GREEN)
        self.bot_running = True
        self.bot_thread = threading.Thread(target=self._poll_tg, args=(tok,), daemon=True)
        self.bot_thread.start()

    def stop_bot(self):
        self.bot_running = False
        self.start_bot_btn.configure(state="normal")
        self.token_entry.configure(state="normal")
        self.stop_bot_btn.configure(state="disabled")
        self.bot_status_lbl.configure(text="● OFFLINE", text_color="#ff4d4d")
        self.log_bot("[BOT] Stopped.")

    def on_autopilot_toggle(self):
        if self.service_active.get():
            self.safe_log_update("[SYS] Auto-Pilot enabled.")
            if not self.bot_running and self.token_var.get().strip():
                self.start_bot()
        else:
            self.safe_log_update("[SYS] Auto-Pilot disabled.")
            if self.bot_running:
                self.stop_bot()

    def _poll_tg(self, tok):
        self.log_bot("🔄 Connecting to Telegram API...")
        try:
            r = requests.get(f"{TG_BASE}{tok}/getMe", timeout=10)
            if r.status_code == 200:
                bn = r.json().get("result", {}).get("username", "Bot")
                self.log_bot(f"✅ Connected to @{bn}")
            else:
                self.log_bot(f"❌ Token rejected. Code: {r.status_code}")
                self.after(0, self.stop_bot)
                return
        except Exception as e:
            self.log_bot(f"❌ Connection error: {e}")
            self.after(0, self.stop_bot)
            return

        self.log_bot("📡 Listening for messages...")
        while self.bot_running:
            try:
                url = f"{TG_BASE}{tok}/getUpdates?offset={self.last_update_id}&timeout=20"
                resp = requests.get(url, timeout=25)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("ok"):
                        updates = data.get("result", [])
                        for u in updates:
                            self.last_update_id = u["update_id"] + 1
                            if "message" in u and "text" in u["message"]:
                                text = u["message"]["text"].strip()
                                chat_id = u["message"]["chat"]["id"]
                                sender = u["message"]["from"].get("first_name", "User")
                                self.log_bot(f"📩 [{sender}]: {text}")
                                reply = self._build_bot_reply(text)
                                if reply:
                                    self._send_bot_msg(tok, chat_id, reply)
            except Exception as e:
                pass
            time.sleep(1)

    def _send_bot_msg(self, tok, chat_id, text):
        try:
            r = requests.post(f"{TG_BASE}{tok}/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=15)
            if r.status_code == 200:
                self.log_bot(f"📤 Reply sent.")
            else:
                self.log_bot(f"❌ Failed to send reply: {r.text}")
        except Exception as e:
            self.log_bot(f"❌ Send error: {e}")

    def _build_bot_reply(self, text):
        cmd = text.upper()
        h = datetime.now().hour
        greet = "Good Evening" if h >= 16 else ("Good Afternoon" if h >= 12 else "Good Morning")

        if cmd in ["HI", "HELLO", "MENU", "STATUS", "HELP", "START", "GET DATA", "/START"]:
            return (
                f"{greet}! 👋\n"
                f"Welcome to <b>Nexus Sync — JJM Sitapur</b>\n"
                f"Automated service by <b>Ashish Kumar</b>\n\n"
                f"🤖 <b>Reply with a Number:</b>\n\n"
                f"<b>1</b> — 📊 Full Status Summary scada and jjm\n"
                f"<b>2</b> — ✅ Live Connected List in jjm\n"
                f"<b>3</b> — ⚠️ Not Connected List in jjm\n"
                f"<b>4</b> — 🚨 Off-Grid Schemes in jjm\n"
                f"<b>5</b> — ⭐ Newly Added Schemes in scada\n\n"
                f"<i>Data fetched live from server</i> ✅"
            )

        if cmd == "1":
            self.log_bot("[BOT] Building SCADA + JJM summary...")
            if not self.scada_data or not self.jjm_list_data:
                return "❌ No live data found on server yet. Please Pull New Data."
            
            j_tot = self.jjm_total_lbl.cget("text")
            j_liv = self.jjm_live_lbl.cget("text")
            j_nr = self.jjm_not_recv_lbl.cget("text")
            j_miss = self.jjm_leftover_lbl.cget("text")
            
            s_tot = self.scada_total_lbl.cget("text")
            s_sync = self.scada_sync_lbl.cget("text")
            s_unsync = self.scada_unsync_lbl.cget("text")
            s_new = self.scada_new_lbl.cget("text")
            
            return (
                f"📈 <b>FULL DAILY STATUS REPORT</b>\n"
                f"📅 {datetime.now().strftime('%d-%m-%Y %I:%M %p')}\n\n"
                f"🔵 <b>JJM PORTAL</b>\n"
                f"  Total Integrated : {j_tot}\n"
                f"  Live Connected   : {j_liv}\n"
                f"  Not Receiving    : {j_nr}\n"
                f"  Off-Grid/Missing : {j_miss}\n\n"
                f"🟢 <b>SCADA</b>\n"
                f"  Total Schemes : {s_tot}\n"
                f"  Synced Today  : {s_sync}\n"
                f"  Not Synced    : {s_unsync}\n"
                f"  Newly Added   : {s_new}"
            )

        if cmd == "2":
            self.log_bot("[BOT] Fetching live connected schemes...")
            lst = self.jjm_list_data.get("live", [])
            if not lst or (isinstance(lst, list) and lst[0].startswith("Detailed")):
                return "❌ Live Connected list not yet fetched from portal."
            lines = "\n".join(f"{i+1}. {x}" for i, x in enumerate(lst))
            return f"✅ <b>LIVE CONNECTED (Count: {len(lst)})</b>\n{lines}"

        if cmd == "3":
            self.log_bot("[BOT] Fetching not connected schemes...")
            lst = self.jjm_list_data.get("not_recv", [])
            if not lst or (isinstance(lst, list) and lst[0].startswith("Detailed")):
                return "❌ Not Receiving list not yet fetched from portal."
            lines = "\n".join(f"{i+1}. {x}" for i, x in enumerate(lst))
            return f"⚠️ <b>NOT CONNECTED (Count: {len(lst)})</b>\n{lines}"

        if cmd == "4":
            self.log_bot("[BOT] Fetching off-grid schemes...")
            lst = self.jjm_list_data.get("leftover", [])
            if not lst or (isinstance(lst, list) and lst[0].startswith("Detailed")):
                return "❌ Off-Grid list not yet computed from portal."
            lines = "\n".join(f"{i+1}. {x}" for i, x in enumerate(lst))
            return f"🚨 <b>OFF-GRID / MISSING (Count: {len(lst)})</b>\n{lines}"

        if cmd == "5":
            self.log_bot("[BOT] Fetching newly added SCADA schemes...")
            n = self.scada_data.get("new", [])
            if n:
                lines = "\n".join(f"{i+1}. {x}" for i, x in enumerate(n))
                return f"⭐ <b>NEWLY ADDED (Count: {len(n)})</b>\n{lines}"
            return "⭐ No new schemes added today yet."
        return None

    def _create_metric_card(self, parent, title, val, color, command=None):
        card = ctk.CTkFrame(parent, fg_color=CLR_CARD, border_width=1, border_color=CLR_BORDER, height=85)
        card.pack(side="left", fill="both", expand=True, padx=(0, 8))
        card.pack_propagate(False)
        title_lbl = ctk.CTkLabel(card, text=title, font=("Segoe UI", 10, "bold"), text_color=CLR_DIM, fg_color="transparent")
        title_lbl.pack(pady=(12, 0), anchor="center")
        lbl = ctk.CTkLabel(card, text=val, font=("Segoe UI", 24, "bold"), text_color=color, fg_color="transparent")
        lbl.pack(expand=True, anchor="center")
        
        if command:
            card.bind("<Button-1>", command)
            title_lbl.bind("<Button-1>", command)
            lbl.bind("<Button-1>", command)
            card.configure(cursor="hand2")
            lbl.configure(cursor="hand2")
            title_lbl.configure(cursor="hand2")
            
        return lbl

    def show_list_popup(self, title, items):
        if not items:
            items = ["No data available or empty list."]
            
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("450x600")
        popup.attributes("-topmost", True)
        
        # Center the popup relative to main window
        popup.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (450 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (600 // 2)
        popup.geometry(f"+{x}+{y}")
        
        header_lbl = ctk.CTkLabel(popup, text=f"{title} (Count: {len(items)})", font=("Segoe UI", 14, "bold"), text_color=CLR_CYAN)
        header_lbl.pack(pady=(15, 5))
        
        # Search Box
        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(popup, placeholder_text="🔍 Search schemes...", height=35, fg_color="#f3f4f6", border_color=CLR_BORDER, textvariable=search_var)
        search_entry.pack(fill="x", padx=15, pady=(0, 10))
        
        textbox = ctk.CTkTextbox(popup, font=("Consolas", 12), fg_color="#f3f4f6", text_color=CLR_TEXT)
        textbox.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        def update_list(*args):
            query = search_var.get().strip().lower()
            filtered = [it for it in items if query in str(it).lower()]
            textbox.configure(state="normal")
            textbox.delete("1.0", "end")
            textbox.insert("end", "\n".join(filtered))
            textbox.configure(state="disabled")
            header_lbl.configure(text=f"{title} (Filtered: {len(filtered)} / Total: {len(items)})")

        search_var.trace_add("write", update_list)
        
        # Initial fill
        textbox.insert("end", "\n".join(items))
        textbox.configure(state="disabled")
        search_entry.focus()

    # --- UI Thread Safety Wrappers ---
    def safe_log_update(self, text):
        self.after(0, lambda: self._log_update(text))

    def _log_update(self, text):
        self.log_terminal.insert("end", f"{text}\n")
        self.log_terminal.see("end")

    def safe_history_update(self, text):
        self.after(0, lambda: self._history_update(text))

    def _history_update(self, text):
        self.history_terminal.insert("end", f"{text}\n")
        self.history_terminal.see("end")

    def safe_report_update(self, report_text, preview_text):
        self.after(0, lambda: self._report_update(report_text, preview_text))

    def _report_update(self, report_text, preview_text):
        self.report_terminal.delete("1.0", "end")
        self.report_terminal.insert("end", report_text)
        self.preview_terminal.delete("1.0", "end")
        self.preview_terminal.insert("end", preview_text)

    # ==================================================
    # 🤖 CORE LOGIC
    # ==================================================
    
    def rebuild_history_log(self):
        self.after(0, lambda: self.history_terminal.delete("1.0", "end"))
        files = glob.glob(os.path.join(self.watch_folder, '*.xlsx'))
        raw_files = [f for f in files if not os.path.basename(f).startswith("Final_Daily_Report")]
        raw_files.sort(key=os.path.getctime)
        
        if raw_files:
            self.safe_history_update(f"[SYS] Fetched {len(raw_files)} data modules from workspace.")
            self.safe_history_update("[SYS] Initializing core engine...\n")
            for f in raw_files:
                try:
                    df = pd.read_excel(f, header=None, nrows=15)
                    header_row = df.notna().sum(axis=1).idxmax()
                    df = pd.read_excel(f, header=header_row)
                    df.columns = [str(c).strip().lower() for c in df.columns]
                    dt_col = next((c for c in df.columns if "date" in c or "time" in c), df.columns[-1])
                    df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce", format="mixed")
                    today = datetime.today().date()
                    
                    synced = len(df[df[dt_col].dt.date == today])
                    not_synced = len(df[df[dt_col].dt.date != today])
                    
                    c_time = datetime.fromtimestamp(os.path.getctime(f))
                    timestamp = c_time.strftime("%b %d - %I:%M %p")
                    self.safe_history_update(f"[+] Mapped: {timestamp} | Sync: {synced:03d} | Unsync: {not_synced:03d}")
                except Exception:
                    pass
        else:
             self.safe_history_update("[SYS] Workspace empty. Awaiting first download...")

    def auto_fetch_jjm_count(self):
        """Lightweight HTTP fetch — cached for 2 minutes."""
        if (time.time() - self._jjm_cache["timestamp"]) < 120:
            return self._jjm_cache["count"]

        self.safe_log_update("> [WEB] Connecting to JJM UP Portal...")
        url = "https://jjm.up.gov.in/site/OS_AutomationIntegration_DistrictWise"
        try:
            hdrs = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
            response = requests.get(url, headers=hdrs, timeout=15, verify=False)

            if response.status_code != 200:
                self.safe_log_update(f"❌ [WEB] Website rejected connection (HTTP {response.status_code})")
                return "0"

            self.safe_log_update("> [WEB] Connection successful! Reading data table...")
            soup = BeautifulSoup(response.text, 'html.parser')
            tables = soup.find_all('table')

            if not tables:
                self.safe_log_update("❌ [WEB] Error: Table not found on the page.")
                return "0"

            current_district = ""
            for row in tables[0].find_all('tr'):
                cells = row.find_all(['td', 'th'])
                texts = [c.text.strip() for c in cells]

                # Track district across rows (Sitapur & NCC may be on different rows)
                for text in texts:
                    if "Sitapur" in text:
                        current_district = "Sitapur"
                        break

                if current_district == "Sitapur":
                    agency_idx = -1
                    for i, t in enumerate(texts):
                        if "NCC" in t.upper():
                            agency_idx = i
                            break

                    if agency_idx != -1:
                        self.safe_log_update("🎯 [WEB] Found Sitapur → NCC Ltd!")
                        try:
                            tot_val = texts[agency_idx + 8]
                            live_val = texts[agency_idx + 10]
                            not_recv_val = texts[agency_idx + 11]
                            
                            def fetch_list(col_idx):
                                try:
                                    a_tag = cells[col_idx].find('a')
                                    if a_tag and a_tag.has_attr('href'):
                                        link_url = 'https://jjm.up.gov.in' + a_tag['href']
                                        r = requests.get(link_url, headers=hdrs, timeout=15, verify=False)
                                        s = BeautifulSoup(r.text, 'html.parser')
                                        t = s.find_all('table')
                                        if t:
                                            names = []
                                            for r_ in t[0].find_all('tr')[1:]:
                                                c_ = [c.text.strip() for c in r_.find_all(['td', 'th'])]
                                                if len(c_) > 6 and c_[0].isdigit():
                                                    names.append(c_[6])
                                            return sorted(names)
                                except Exception:
                                    pass
                                return []

                            self.safe_log_update("> [WEB] Deeply fetching per-scheme JJM breakdowns (may take a few seconds)...")
                            tot_list = fetch_list(agency_idx + 8)
                            live_list = fetch_list(agency_idx + 10)
                            not_recv_list = fetch_list(agency_idx + 11)
                            
                            leftover_list = sorted(list(set(tot_list) - set(live_list) - set(not_recv_list)))
                            
                            tot_connected = int(re.sub(r'\D', '', tot_val) or 0)
                            live_connected = int(re.sub(r'\D', '', live_val) or 0)
                            not_received = int(re.sub(r'\D', '', not_recv_val) or 0)
                            leftover = tot_connected - live_connected - not_received
                            
                            self.safe_log_update(f"⮑ [WEB] Fetched -> Total: {tot_connected}, Live: {live_connected}, Not Received: {not_received}, Remaining: {leftover}")
                            
                            result = {
                                "total": str(tot_connected),
                                "live": str(live_connected),
                                "not_received": str(not_received),
                                "leftover": str(leftover),
                                "_lists": {
                                    "total": tot_list,
                                    "live": live_list,
                                    "not_received": not_recv_list,
                                    "leftover": leftover_list
                                }
                            }
                            self._jjm_cache = {"count": result, "timestamp": time.time()}
                            return result
                        except IndexError:
                            self.safe_log_update("❌ [WEB] Table structure mismatch — column offset wrong.")
                            return {"total": "0", "live": "0", "not_received": "0", "leftover": "0"}

            self.safe_log_update("❌ [WEB] Sitapur NCC Ltd data not found in table.")
            return {"total": "0", "live": "0", "not_received": "0", "leftover": "0"}
        except Exception as e:
            self.safe_log_update(f"❌ [WEB] Connection failed: {str(e)}")
            return {"total": "0", "live": "0", "not_received": "0", "leftover": "0"}

    def robot_portal_download(self, force=False):
        with self.browser_lock:
            self.safe_log_update("\n[SYS] Initiating portal data pull...")

            # ── ANTI-DUPLICATE DEBOUNCE: Skip if we just downloaded data ──
            existing_files = glob.glob(os.path.join(self.watch_folder, '*.xlsx'))
            if not force and existing_files:
                latest_file = max(existing_files, key=os.path.getctime)
                if (time.time() - os.path.getctime(latest_file)) < 60: # 1 minute
                    self.safe_log_update("⚠️ System pulled data less than a minute ago. Using recent data...")
                    self.analyze_data(latest_file)
                    return

            driver = None
            downloaded_file = None
            try:
                if not MY_USER or not MY_PASS:
                    self.safe_log_update("❌ Error: Credentials missing in .env file.")
                    return

                # Snapshot files before download so we can detect the NEW one
                before_files = set(glob.glob(os.path.join(self.watch_folder, '*.xlsx')))

                self.safe_log_update("> [PORTAL] Launching browser & navigating to login page...")
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.get_armored_options())
                driver.get(PORTAL_URL)
                wait = WebDriverWait(driver, 25)

                self.safe_log_update("> [PORTAL] Waiting for login form...")
                wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(MY_USER)
                driver.find_element(By.ID, "password").send_keys(MY_PASS)

                self.safe_log_update(f"> [PORTAL] Selecting district: {MY_DISTRICT}...")
                dropdown = Select(driver.find_element(By.ID, "selectDistt"))
                for opt in dropdown.options:
                    if MY_DISTRICT.lower() in opt.text.lower():
                        dropdown.select_by_visible_text(opt.text)
                        break

                driver.find_element(By.NAME, "login").click()
                self.safe_log_update("> [PORTAL] Login submitted. Waiting for dashboard to load...")
                time.sleep(6)

                self.safe_log_update("> [PORTAL] Dashboard loaded. Triggering Excel export...")
                btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'buttons-excel')]")))
                driver.execute_script("arguments[0].click();", btn)
                self.safe_log_update("> [PORTAL] Export clicked. Polling for downloaded file (max 60s)...")

                # Poll until a NEW .xlsx appears in watch_folder (up to 60 seconds)
                timeout, elapsed = 60, 0
                while elapsed < timeout:
                    time.sleep(2); elapsed += 2
                    current_files = set(glob.glob(os.path.join(self.watch_folder, '*.xlsx')))
                    new_files = [f for f in current_files - before_files
                                 if not os.path.basename(f).startswith("Final_Daily_Report")]
                    if new_files:
                        df_tmp = max(new_files, key=os.path.getctime)
                        try:
                            # Verify no temporary chrome downloads are active & file has data
                            if os.path.getsize(df_tmp) > 0 and not glob.glob(os.path.join(self.watch_folder, '*.crdownload')):
                                time.sleep(1) # Extra buffer for I/O flush
                                downloaded_file = df_tmp
                                self.safe_log_update(f"✅ [PORTAL] File captured: {os.path.basename(downloaded_file)}")
                                break
                        except Exception:
                            pass

                if not downloaded_file:
                    self.safe_log_update("❌ [PORTAL] Download timed out — no new file detected.")

            except Exception as e:
                self.safe_log_update(f"❌ Portal Error: {str(e)}")
            finally:
                # ⚠️ CRITICAL: Close portal browser BEFORE opening JJM browser
                # Both use the same Chrome profile — only one can be open at a time
                if driver:
                    driver.quit()
                    self.safe_log_update("> [PORTAL] Browser closed.")

            # Analyze AFTER browser is fully closed (avoids Chrome profile conflict)
            if downloaded_file:
                self.rebuild_history_log()
                self.analyze_data(downloaded_file)

    def analyze_data(self, latest_file_path):
        try:
            jjm_data = self.auto_fetch_jjm_count()
            if isinstance(jjm_data, str) or not jjm_data:
                jjm_data = {"total": "0", "live": "0", "not_received": "0", "leftover": "0"}
                
            jjm_live = jjm_data.get("live", "0")
            jjm_total = jjm_data.get("total", "0")
            jjm_not_recv = jjm_data.get("not_received", "0")
            jjm_leftover = jjm_data.get("leftover", "0")
            
            jjm_lists = jjm_data.get("_lists", {})
            if jjm_lists:
                self.jjm_list_data["total"] = jjm_lists.get("total", ["Data could not be fetched internally."])
                self.jjm_list_data["live"] = jjm_lists.get("live", ["Data could not be fetched internally."])
                self.jjm_list_data["not_recv"] = jjm_lists.get("not_received", ["Data could not be fetched internally."])
                self.jjm_list_data["leftover"] = jjm_lists.get("leftover", ["Data could not be fetched internally."])

            df = pd.read_excel(latest_file_path, header=None, nrows=15)
            header_row = df.notna().sum(axis=1).idxmax()
            df = pd.read_excel(latest_file_path, header=header_row)
            df.columns = [str(c).strip().lower() for c in df.columns]
            
            gp_col = next((c for c in df.columns if "gp" in c or "panchayat" in c or "name" in c), df.columns[1])
            dt_col = next((c for c in df.columns if "date" in c or "time" in c), df.columns[-1])
            
            df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce", format="mixed")
            today = datetime.today().date()
            
            synced = df[df[dt_col].dt.date == today]
            not_synced = df[df[dt_col].dt.date != today]
            
            # Identify Newly Added GPs by comparing against the FIRST file of today
            files = glob.glob(os.path.join(self.watch_folder, '*.xlsx'))
            raw_files = [f for f in files if not os.path.basename(f).startswith("Final_Daily_Report")]
            raw_files.sort(key=os.path.getctime)
            
            daily_new_gps = []
            if len(raw_files) > 1:
                first_file = raw_files[0]
                if first_file != latest_file_path:
                    try:
                        df_old = pd.read_excel(first_file, header=None, nrows=15)
                        h_row = df_old.notna().sum(axis=1).idxmax()
                        df_old = pd.read_excel(first_file, header=h_row)
                        df_old.columns = [str(c).strip().lower() for c in df_old.columns]
                        old_gp_col = next((c for c in df_old.columns if "gp" in c or "panchayat" in c or "name" in c), df_old.columns[1])
                        old_gps_baseline = set(df_old[old_gp_col].dropna().astype(str).unique())
                        
                        current_gps = set(df[gp_col].dropna().astype(str).unique())
                        daily_new_gps = list(current_gps - old_gps_baseline)
                    except: pass
            
            new_gp_count = len(daily_new_gps)
            
            new_gp_text = ""
            if new_gp_count > 0:
                joined_names = ", ".join(sorted(daily_new_gps))
                new_gp_text = f"\nNewly Added Schemes- {new_gp_count} ({joined_names})"
            
            report = f"JJM PORTAL LIVE: {jjm_live} | TOTAL: {jjm_total} | NOT REC: {jjm_not_recv} | MISSING: {jjm_leftover}\nSCADA TOTAL: {len(df)}\nSYNCED: {len(synced)}\nUNSYNCED: {len(not_synced)}\nNEW ADDED: {new_gp_count}\n\n"
            report += "✅ SYNCED LIST:\n" + ", ".join(synced[gp_col].astype(str).tolist()) + "\n\n"
            report += "❌ NOT SYNCED LIST:\n" + ", ".join(not_synced[gp_col].astype(str).tolist()) + "\n\n"
            if new_gp_count > 0:
                report += "⭐ NEWLY ADDED LIST:\n" + joined_names
            
            greet = "Good Evening Sir," if datetime.now().hour >= 16 else ("Good Afternoon Sir," if datetime.now().hour >= 12 else "Good Morning Sir,")
            preview = f"Date: {datetime.today().strftime('%d.%m.%Y')}\n\n{greet}\nNo of schemes connected with SCADA- {len(synced)}\nNo of schemes Lives in JJM Portal- {jjm_live}{new_gp_text}\n\nToday Schemes listed in SCADA- {len(df)}."
            
            self.last_analysis_msg = preview
            self.safe_report_update(report, preview)
            
            # --- Update UI Labels ---
            self.scada_data["total"] = sorted(df[gp_col].dropna().astype(str).tolist())
            self.scada_data["synced"] = sorted(synced[gp_col].dropna().astype(str).tolist())
            self.scada_data["not_synced"] = sorted(not_synced[gp_col].dropna().astype(str).tolist())
            self.scada_data["new"] = sorted(daily_new_gps)
            
            # --- Update UI Labels ---
            self.after(0, lambda: self.jjm_total_lbl.configure(text=str(jjm_total)))
            self.after(0, lambda: self.jjm_live_lbl.configure(text=str(jjm_live)))
            self.after(0, lambda: self.jjm_not_recv_lbl.configure(text=str(jjm_not_recv)))
            self.after(0, lambda: self.jjm_leftover_lbl.configure(text=str(jjm_leftover)))

            self.after(0, lambda: self.scada_total_lbl.configure(text=str(len(self.scada_data["total"]))))
            self.after(0, lambda: self.scada_sync_lbl.configure(text=str(len(self.scada_data["synced"]))))
            self.after(0, lambda: self.scada_unsync_lbl.configure(text=str(len(self.scada_data["not_synced"]))))
            self.after(0, lambda: self.scada_new_lbl.configure(text=str(len(self.scada_data["new"]))))
            
            timestamp = datetime.now().strftime("%b %d - %I:%M %p")
            history_line = f"[+] Mapped: {timestamp} | Sync: {len(synced):03d} | Unsync: {len(not_synced):03d}"
            self.safe_history_update(history_line)
            
            # --- Export Live Data for Bot ---
            try:
                import json
                export_data = {
                    "jjm": {
                        "total": str(jjm_total),
                        "live": str(jjm_live),
                        "not_received": str(jjm_not_recv),
                        "leftover": str(jjm_leftover),
                        "_lists": self.jjm_list_data
                    },
                    "scada": {
                        "total": str(len(self.scada_data["total"])),
                        "synced": str(len(self.scada_data["synced"])),
                        "unsynced": str(len(self.scada_data["not_synced"])),
                        "new_count": str(len(self.scada_data["new"])),
                        "new_list": self.scada_data["new"]
                    },
                    "timestamp": datetime.now().isoformat()
                }
                export_path = os.path.join(self.watch_folder, "nexus_live_data.json")
                with open(export_path, "w") as f:
                    json.dump(export_data, f)
                self.safe_log_update("[SYS] Live data JSON exported for bot.")
            except Exception as e:
                self.safe_log_update(f"⚠️ Could not export live JSON: {e}")
                
            self.safe_log_update("[SYS] Data structured and ready for export.")
            
        except Exception as e: self.safe_log_update(f"❌ Analysis Fail: {str(e)}")

    def generate_final_report(self):
        self.safe_log_update("\n[SYS] Generating End of Day Final Report...")
        files = glob.glob(os.path.join(self.watch_folder, '*.xlsx'))
        raw_files = [f for f in files if not os.path.basename(f).startswith("Final_Daily_Report")]
        
        if not raw_files:
            self.safe_log_update("❌ No raw data files found for today.")
            return

        def detect_hour(filepath):
            filename = os.path.basename(filepath)
            date_match = re.search(r'(\d{8})_(\d{4})', filename)
            if date_match:
                try:
                    dt_obj = datetime.strptime(f"{date_match.group(1)}_{date_match.group(2)}", "%Y%m%d_%H%M")
                    return dt_obj, dt_obj.strftime("%b %d - %I:%M %p")
                except ValueError: pass

            time_match = re.search(r'_(\d{4})|(\d{4})', filename)
            if time_match:
                t = time_match.group(1) or time_match.group(2)
                try:
                    time_obj = datetime.strptime(t, "%H%M").time()
                    file_date = datetime.fromtimestamp(os.path.getmtime(filepath)).date()
                    dt_obj = datetime.combine(file_date, time_obj)
                    return dt_obj, dt_obj.strftime("%b %d - %I:%M %p")
                except ValueError: pass
                    
            try:
                timestamp = os.path.getmtime(filepath)
                dt_obj = datetime.fromtimestamp(timestamp)
                return dt_obj, dt_obj.strftime("%b %d - %I:%M %p")
            except Exception: pass
            return None, None
            
        def sort_by_time(filepath):
            dt_obj, _ = detect_hour(filepath)
            return dt_obj if dt_obj else datetime.max 

        raw_files.sort(key=sort_by_time)

        try:
            # 1. READ ALL FILES AND BUILD HOURLY DATA
            hourly_data = []
            today = datetime.today().date()
            previous_hour_gps = set()

            # Find actual columns from the first file
            df_first = pd.read_excel(raw_files[0], header=None, nrows=15)
            header_row_first = df_first.notna().sum(axis=1).idxmax()
            if isinstance(header_row_first, str): header_row_first = 0
            df_first = pd.read_excel(raw_files[0], header=header_row_first)
            df_first.columns = [str(c).strip() for c in df_first.columns]
            headers = list(df_first.columns)
            
            actual_sno = next((c for c in headers if "s no" in str(c).lower() or "s.no" in str(c).lower() or "sl" in str(c).lower() or "serial" in str(c).lower()), headers[0])
            rem_h = [c for c in headers if c != actual_sno]
            actual_primary = next((c for c in rem_h if "name" in str(c).lower() or "gp" in str(c).lower() or "panchayat" in str(c).lower()), rem_h[0] if rem_h else headers[0])
            rem_h2 = [c for c in rem_h if c != actual_primary]
            actual_dt = next((c for c in rem_h2 if "date" in str(c).lower() or "time" in str(c).lower()), rem_h2[0] if rem_h2 else headers[-1])

            for idx, f in enumerate(raw_files):
                hour, display = detect_hour(f)
                if hour is None: continue
                
                # Smart read
                df_raw = pd.read_excel(f, header=None, nrows=15)
                header_row = 0
                for i, row in df_raw.iterrows():
                    if row.notna().sum() >= 3:
                        header_row = i
                        break
                df = pd.read_excel(f, header=header_row)
                df.columns = [str(c).strip() for c in df.columns]
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

                primary_col = actual_primary if actual_primary in df.columns else df.columns[0]
                dt_col = actual_dt if actual_dt in df.columns else df.columns[1]

                current_hour_gps = set(df[primary_col].dropna().astype(str).unique())
                previous_hour_gps = current_hour_gps

                df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce", format="mixed")
                syncing = df[df[dt_col].dt.date == today]
                unsync = df[df[dt_col].dt.date != today]

                hourly_data.append({"hour": hour, "display": display, "sync": syncing, "unsync": unsync, "raw": df})

            if not hourly_data:
                self.safe_log_update("❌ No readable data in today's files.")
                return

            # 2. EXPORT MATRIX TO EXCEL
            final_filename = f"Final_Daily_Report_{self.today_str}.xlsx"
            final_path = os.path.join(self.watch_folder, final_filename)

            from openpyxl import Workbook
            from openpyxl.styles import PatternFill, Font, Border, Side, Alignment

            wb = Workbook()
            ws = wb.active
            ws.freeze_panes = "A2"
            
            sync_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
            unsync_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
            new_gp_fill = PatternFill(start_color="FEF08A", end_color="FEF08A", fill_type="solid") 
            header_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid") 
            total_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
            border = Border(left=Side(style='thin', color="CBD5E1"), right=Side(style='thin', color="CBD5E1"), top=Side(style='thin', color="CBD5E1"), bottom=Side(style='thin', color="CBD5E1"))

            extra_cols = []
            master_df = pd.concat([h["raw"] for h in hourly_data]).drop_duplicates(subset=[actual_primary])
            def get_priority(pk):
                for h in hourly_data:
                    if pk in h["sync"][actual_primary].values: return 0
                return 1
            master_df['_priority'] = master_df[actual_primary].apply(get_priority)
            master_df = master_df.sort_values(by=['_priority', actual_primary])

            all_headers = [actual_sno, actual_primary] + extra_cols + [h["display"] for h in hourly_data]
            for c, text in enumerate(all_headers, 1):
                cell = ws.cell(row=1, column=c, value=text)
                cell.font, cell.fill, cell.border = Font(bold=True, color="FFFFFF", size=11), header_fill, border
                cell.alignment = Alignment(horizontal="center")

            new_gp_counts = {i: 0 for i in range(len(hourly_data))}
            r_idx = 2
            
            for _, row_data in master_df.iterrows():
                ws.cell(row=r_idx, column=1, value=row_data.get(actual_sno, "-")).border = border
                ws.cell(row=r_idx, column=2, value=row_data.get(actual_primary, "-")).border = border
                
                for i, col in enumerate(extra_cols, 3):
                    ws.cell(row=r_idx, column=i, value=row_data.get(col, "-")).border = border

                for i, h_data in enumerate(hourly_data, len(extra_cols) + 3):
                    cell = ws.cell(row=r_idx, column=i)
                    cell.border = border
                    list_idx = i - (len(extra_cols) + 3) 

                    pk = row_data[actual_primary]
                    s_match = h_data["sync"][h_data["sync"][actual_primary] == pk]
                    u_match = h_data["unsync"][h_data["unsync"][actual_primary] == pk]

                    is_newly_added = False
                    if list_idx > 0: 
                        prev_h_data = hourly_data[list_idx - 1]
                        in_current = (not s_match.empty) or (not u_match.empty)
                        in_prev = pk in prev_h_data["raw"][actual_primary].values
                        if in_current and not in_prev:
                            is_newly_added = True
                            new_gp_counts[list_idx] += 1 

                    if not s_match.empty:
                        val = s_match.iloc[0][actual_dt]
                        cell.value = val.strftime("%Y-%m-%d %H:%M") if pd.notnull(val) else "N/A"
                        cell.fill = new_gp_fill if is_newly_added else sync_fill
                    elif not u_match.empty:
                        val = u_match.iloc[0][actual_dt]
                        cell.value = val.strftime("%Y-%m-%d %H:%M") if pd.notnull(val) else "N/A"
                        cell.fill = new_gp_fill if is_newly_added else unsync_fill
                    else:
                        cell.value = "-"
                r_idx += 1

            r_idx += 1
            ws.cell(row=r_idx, column=2, value="SUCCESS COUNT (TODAY)").font = Font(bold=True)
            ws.cell(row=r_idx+1, column=2, value="STALE COUNT (OLD)").font = Font(bold=True)
            ws.cell(row=r_idx+2, column=2, value="NEW GP COUNT (ADDED)").font = Font(bold=True) 

            for i, h_data in enumerate(hourly_data, len(extra_cols) + 3):
                list_idx = i - (len(extra_cols) + 3)
                s_c = ws.cell(row=r_idx, column=i, value=len(h_data["sync"]))
                u_c = ws.cell(row=r_idx+1, column=i, value=len(h_data["unsync"]))
                n_c = ws.cell(row=r_idx+2, column=i, value=new_gp_counts[list_idx]) 
                for c in [s_c, u_c, n_c]:
                    c.fill, c.font, c.border, c.alignment = total_fill, Font(bold=True), border, Alignment(horizontal="center")

            wb.save(final_path)
            self.safe_log_update(f"✅ Final Matrix Report Saved: {final_path}")

        except Exception as e:
            self.safe_log_update(f"❌ Failed to generate matrix report: {str(e)}")

    # ==================================================
    # 📱 WHATSAPP ENGINE (RESTORED MANUAL METHOD)
    # ==================================================
    
    def robot_whatsapp_blast(self):
        with self.browser_lock:
            self.safe_log_update("\n--- 📱 WHATSAPP BROADCAST ENGINE ---")
            if not self.contacts or not self.last_analysis_msg:
                self.safe_log_update("⚠️ Missing contacts or report. Pull data first.")
                return

            driver = None
            try:
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.get_armored_options(False))
                driver.get("https://web.whatsapp.com")
                self.safe_log_update("[WA] Browser opened. Scan QR if needed. Waiting 20s for interface...")
                time.sleep(20)

                for contact in self.contacts:
                    name  = contact.get('name', '')
                    phone = contact.get('phone', '')
                    self.safe_log_update(f"\n-> Sending to: {name} ({phone})")
                    try:
                        # Always use direct URL — 100% reliable since all contacts have a phone
                        driver.get(f"https://web.whatsapp.com/send?phone={phone}")
                        time.sleep(7)

                        # ── FIND MESSAGE BOX ──
                        msg_box = None
                        for xpath in [
                            '//div[@contenteditable="true"][@data-tab="10"]',
                            '//div[@title="Type a message"]',
                            '//div[contains(@aria-label,"Type a message")][@contenteditable="true"]',
                            '//div[contains(@aria-label,"message")][@contenteditable="true"]',
                        ]:
                            try:
                                msg_box = WebDriverWait(driver, 12).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                                break
                            except: continue

                        if not msg_box:
                            self.safe_log_update(f"   ❌ Message box not found. Is {phone} on WhatsApp?")
                            continue

                        msg_box.click(); time.sleep(0.5)

                        # ── TYPE MESSAGE line by line (Shift+Enter between lines) ──
                        self.safe_log_update("   [WA] Injecting payload...")
                        for line in self.last_analysis_msg.split('\n'):
                            msg_box.send_keys(line)
                            ActionChains(driver).key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT).perform()
                            time.sleep(0.08)

                        time.sleep(0.5)
                        msg_box.send_keys(Keys.ENTER)
                        self.safe_log_update(f"   ✅ Sent to {name}!")
                        time.sleep(3)

                    except Exception as e:
                        self.safe_log_update(f"   ❌ Failed for {name}: {str(e)}")
                        continue

            except Exception as e:
                self.safe_log_update(f"❌ WhatsApp Engine Error: {str(e)}")
            finally:
                if driver:
                    driver.quit()
                    self.safe_log_update("\n[WA] Session closed.")

            # ── AUTO-EXPORT: Generate Final Report after broadcast ──
            self.safe_log_update("\n[SYS] Auto-generating Final Daily Report post-broadcast...")
            self.generate_final_report()

    # ==================================================
    # ⚙️ UTILITIES & BOOT
    # ==================================================
    def get_armored_options(self, is_download=True):
        o = webdriver.ChromeOptions()
        o.add_argument(f"user-data-dir={CHROME_DATA_DIR}")
        o.add_argument("--no-sandbox")
        o.add_argument("--disable-dev-shm-usage")
        o.add_argument("--disable-gpu")
        o.add_argument("--remote-allow-origins=*")
        o.add_argument("--ignore-certificate-errors")
        o.add_argument("--allow-running-insecure-content")
        o.add_argument("--disable-features=InsecureDownloadWarnings")
        o.add_argument("--unsafely-treat-insecure-origin-as-secure=http://122.186.209.30:8068")
        if is_download: 
            prefs = {
                "download.default_directory": os.path.abspath(self.watch_folder), 
                "download.prompt_for_download": False, 
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False,
                "safebrowsing.disable_download_protection": True,
                "safebrowsing_for_trusted_sources_enabled": False,
                "profile.default_content_setting_values.automatic_downloads": 1,
                "profile.default_content_settings.popups": 0
            }
            o.add_experimental_option("prefs", prefs)
        return o

    def load_contacts(self):
        """Load contacts as list of dicts {name, phone}. Supports old plain-number format."""
        contacts = []
        if os.path.exists(CONTACT_FILE):
            with open(CONTACT_FILE, "r") as f:
                for line in f.readlines():
                    line = line.strip()
                    if not line: continue
                    if "|" in line:
                        parts = line.split("|", 1)
                        contacts.append({"name": parts[0].strip(), "phone": parts[1].strip()})
                    else:
                        # Backward compat: plain number entry
                        contacts.append({"name": line, "phone": re.sub(r'\D', '', line)})
        return contacts

    def save_contacts(self):
        with open(CONTACT_FILE, "w") as f:
            for c in self.contacts:
                f.write(f"{c['name']}|{c['phone']}\n")

    def add_contact(self):
        name  = self.contact_name_entry.get().strip()
        phone = re.sub(r'\D', '', self.contact_phone_entry.get().strip())
        if not name or not phone:
            return
        # Prevent duplicate phones
        if any(c['phone'] == phone for c in self.contacts):
            return
        self.contacts.append({"name": name, "phone": phone})
        self.save_contacts()
        self.refresh_contact_ui()
        self.contact_name_entry.delete(0, 'end')
        self.contact_phone_entry.delete(0, 'end')

    def remove_contact(self):
        sel = self.contact_listbox.curselection()
        if sel:
            del self.contacts[sel[0]]
            self.save_contacts()
            self.refresh_contact_ui()

    def show_robot_alert(self, task_name):
        """Centered, self-dismissing warning to notify user of robot takeover."""
        def create_popup():
            popup = ctk.CTkToplevel(self)
            popup.attributes("-topmost", True)
            popup.overrideredirect(True)
            
            # Center on screen
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            w, h = 450, 150
            x, y = (sw // 2) - (w // 2), (sh // 2) - (h // 2)
            popup.geometry(f"{w}x{h}+{x}+{y}")
            
            # Minimalist 'Glass' aesthetics
            frame = ctk.CTkFrame(popup, fg_color="#1e293b", border_width=2, border_color=CLR_GOLD)
            frame.pack(fill="both", expand=True)
            
            ctk.CTkLabel(frame, text="⚠️ NEXUS ROBOT ACTIVATING", font=("Segoe UI", 16, "bold"), text_color=CLR_GOLD).pack(pady=(20, 5))
            ctk.CTkLabel(frame, text=f"System will start: {task_name}", font=("Segoe UI", 12), text_color="#cbd5e1").pack()
            ctk.CTkLabel(frame, text="Please STOP using your system now.", font=("Segoe UI", 11, "italic"), text_color="#94a3b8").pack(pady=10)
            
            self.after(3000, popup.destroy)
        
        self.after(0, create_popup)

    def refresh_contact_ui(self):
        self.contact_listbox.delete(0, 'end')
        for c in self.contacts:
            self.contact_listbox.insert('end', f"  {c['name']}  •  {c['phone']}")

    def trigger_manual_pull(self): threading.Thread(target=self.robot_portal_download, kwargs={'force': True}, daemon=True).start()
    def trigger_manual_send(self): threading.Thread(target=self.robot_whatsapp_blast, daemon=True).start()
    
    def startup_check(self):
        self.rebuild_history_log()
        time.sleep(1)
        files = glob.glob(os.path.join(self.watch_folder, '*.xlsx'))
        raw_files = [f for f in files if not os.path.basename(f).startswith("Final_Daily_Report")]
        
        if raw_files:
            latest_file = max(raw_files, key=os.path.getctime)
            latest_time = datetime.fromtimestamp(os.path.getmtime(latest_file))
            
            if latest_time.hour != datetime.now().hour:
                self.safe_log_update(f"[SYS] No data found for current hour ({datetime.now().hour}:00). Auto-pulling...")
                self.show_robot_alert("INITIAL STARTUP SYNC")
                time.sleep(20)
                self.robot_portal_download()
            else:
                self.analyze_data(latest_file)
        else:
            self.safe_log_update("[SYS] No data found for today. Auto-pulling from portal...")
            self.show_robot_alert("FIRST DAILY SYNC")
            time.sleep(20)
            self.robot_portal_download()

    def run_scheduler(self):
        def scheduled_pull():
            self.show_robot_alert("HOURLY DATA REFRESH")
            time.sleep(20)
            self.robot_portal_download()

        def scheduled_blast():
            self.show_robot_alert("EOD WHATSAPP BROADCAST")
            time.sleep(20)
            self.robot_whatsapp_blast()

        for h in range(8, 20): schedule.every().day.at(f"{h:02d}:00").do(self.safe_execute, scheduled_pull)
        schedule.every().day.at("18:05").do(self.safe_execute, scheduled_blast)
        schedule.every().day.at("19:00").do(self.auto_close_app)

        while True:
            schedule.run_pending()
            
            # ── HOURLY DRIFT WATCHDOG ──
            # If it's midway through the hour and we still haven't got data (e.g. net was down)
            if self.service_active.get():
                now = datetime.now()
                if 8 <= now.hour < 19:
                    files = glob.glob(os.path.join(self.watch_folder, '*.xlsx'))
                    raw_files = [f for f in files if not os.path.basename(f).startswith("Final_Daily_Report")]
                    has_current_hour = False
                    for f in raw_files:
                        if datetime.fromtimestamp(os.path.getmtime(f)).hour == now.hour:
                            has_current_hour = True
                            break
                    
                    if not has_current_hour:
                        # Only retry after 10 mins past the hour to allow standard scheduler some buffer
                        if now.minute >= 10: 
                            self.safe_log_update(f"[SYS] Watchdog: Missing data for {now.hour}:00. Attempting recovery pull...")
                            threading.Thread(target=self.robot_portal_download, daemon=True).start()

            time.sleep(60) # Heartbeat: 60 seconds
            
    def safe_execute(self, func):
        """Universal exception wrapper for scheduled tasks."""
        try:
            if not self.service_active.get():
                self.safe_log_update("[SYS] Auto-Pilot is OFF. Skipping scheduled task.")
                return
            func()
        except Exception as e:
            self.safe_log_update(f"[ERR] Scheduler breakdown: {str(e)}")

if __name__ == "__main__":
    app = NexusSyncPro()
    app.mainloop()