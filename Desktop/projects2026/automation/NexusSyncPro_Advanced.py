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
import json

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
CLIENT_VERSION = "15.2"
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
        self.title(f"NEXUS SYNC | Enterprise Suite v{CLIENT_VERSION} (Production)")
        
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
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
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
            resp = requests.post("http://devash.in/api/verify_license", json={"key": key, "hwid": hwid, "version": CLIENT_VERSION}, timeout=5)
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
            "leftover": ["Detailed per-scheme list not locally extracted.", "(Computed aggregate difference)."],
            "new": []
        }
        
        # Telegram Bot state
        self.bot_running = False
        self.bot_thread = None
        self.last_update_id = 0
        self.token_var = tk.StringVar()
        self._load_creds()
        
        self.setup_ui()
        
        # Clean up old executable backup from recent updates
        try:
            current_exe_path = sys.executable if getattr(sys, 'frozen', False) else None
            if current_exe_path:
                old_exe_path = current_exe_path + ".old"
                if os.path.exists(old_exe_path):
                    os.remove(old_exe_path)
                    self.safe_log_update("[OTA] Cleaned up previous version update backup.")
                    self.after(2000, lambda: self.safe_log_update(f"[OTA] 🎉 System successfully upgraded to v{CLIENT_VERSION}!"))
        except Exception:
            pass

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
        self.refresh_historical_dates()

        self.safe_log_update(f"[SYS] System Architecture v{CLIENT_VERSION} (Production Ready) Initialized.")
        self.safe_log_update(f"[SYS] Daily data directory mapped: {self.watch_folder}")
        if os.listdir(self.watch_folder):
            self.safe_log_update(f"[SYS] Existing files detected in today's folder — reusing workspace.")
        
        self._register_startup()
        
        threading.Thread(target=self.run_scheduler, daemon=True).start()
        threading.Thread(target=self.startup_check, daemon=True).start()

    def _check_whats_new(self):
        """Show What's New popup once per version after an update."""
        CURRENT_VER = CLIENT_VERSION
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
            ("🔄", "Interactive Update Manager",
             "Over-The-Air updates now feature a real-time download progress bar and installation status display."),
            ("🔌", "Remote Force Updates",
             "Administrators can now remotely trigger immediate updates and restarts directly from the Control Tower admin dashboard."),
            ("🌐", "WhatsApp Debug Chrome Profile",
             "Open the client's dedicated WhatsApp Chrome profile using a sidebar button for troubleshooting and manual re-login."),
            ("📡", "Control Tower Version Reporting",
             "Connected clients now report their active running version, displayed on the Control Tower admin panel."),
            ("🔒", "Hardware-Bound Licensing",
             "Each license key now permanently locks to your specific PC hardware, preventing unauthorized duplicate activations."),
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
        CURRENT_VER = CLIENT_VERSION
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
                popup.destroy()
                self.show_download_progress_popup(latest_ver)
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

        self.workspace_base = chosen
        dated_folder = os.path.join(chosen, self.today_str)
        os.makedirs(dated_folder, exist_ok=True)
        return dated_folder

    def manual_change_workspace(self):
        new_folder = self._select_workspace_folder(force_prompt=True)
        if new_folder:
            self.watch_folder = new_folder
            self.safe_log_update(f"[SYS] Workspace switched: {self.watch_folder}")
            self.rebuild_history_log()
            self.refresh_historical_dates()
            # Run a fresh analysis on the new folder context
            files = glob.glob(os.path.join(self.watch_folder, '*.xlsx'))
            raw_files = [f for f in files if not os.path.basename(f).startswith("Final_Daily_Report")]
            if raw_files:
                self.analyze_data(max(raw_files, key=os.path.getctime))

    def manual_open_chrome_profile(self):
        """Launches a visible Chrome window using the client's WhatsApp profile and keeps it open."""
        def run_chrome():
            with self.browser_lock:
                self.safe_log_update("\n--- 🌐 LAUNCHING CHROME PROFILE ---")
                self.safe_log_update("[SYS] Opening Chrome with your WhatsApp profile. Please do not run broadcasts or pulls until you close this browser window.")
                driver = None
                try:
                    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.get_armored_options(False))
                    driver.get("https://web.whatsapp.com")
                    self.safe_log_update("[SYS] Chrome is open. Close the Chrome window when you are finished.")
                    
                    while True:
                        try:
                            # Ping window handles to check if closed by user
                            _ = driver.window_handles
                            time.sleep(1)
                        except Exception:
                            break
                except Exception as e:
                    self.safe_log_update(f"[SYS] ❌ Failed to open Chrome: {e}")
                finally:
                    if driver:
                        try:
                            driver.quit()
                        except: pass
                    self.safe_log_update("[SYS] Chrome session closed. Control returned to Nexus.")
        
        threading.Thread(target=run_chrome, daemon=True).start()

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

        # Prepare clean environment for the new PyInstaller process
        env = os.environ.copy()
        env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
        
        # Remove all PyInstaller-specific environment variables to force
        # the new subprocess to perform a clean boot and extract its files.
        for key in list(env.keys()):
            if key.upper().startswith("_MEIPASS") or key.upper().startswith("_PYI_"):
                try:
                    del env[key]
                except:
                    pass

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
                                     close_fds=True,
                                     env=env)
                    os._exit(0)
                except Exception as e:
                    self.safe_log_update(f"[OTA] ⚠️ Restart fail (Privilege Error): {e}")
            
            # Fallback if uncompiled
            subprocess.Popen([current_exe] + sys.argv,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                env=env)
            os._exit(0)
        else:
            # No update — just restart the current exe
            subprocess.Popen([current_exe] + sys.argv,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                env=env)
            os._exit(0)

    def check_for_updates(self, progress_callback=None):
        try:
            self.safe_log_update("[SYS] Checking Control Tower for updates...")
            resp = requests.get("http://devash.in/api/update_check", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                latest_ver = data.get("latest_version", "0.0")
                current_ver = CLIENT_VERSION

                if float(latest_ver) > float(current_ver):
                    self.safe_log_update(f"[OTA] Update available: v{latest_ver}. Initiating download...")
                    dl_url = f"http://devash.in{data.get('download_url')}"
                    
                    # Stream the download
                    response = requests.get(dl_url, stream=True, timeout=60)
                    if response.status_code != 200:
                        self.safe_log_update(f"[OTA] ⚠️ Update download failed (HTTP {response.status_code}).")
                        if progress_callback:
                            progress_callback("error", f"HTTP {response.status_code}")
                        return

                    total_size = int(response.headers.get('content-length', 0))
                    new_file = os.path.join(_BASE_DIR, "NexusSyncPro_Update.exe")
                    downloaded_size = 0
                    chunk_size = 65536 # 64KB
                    
                    with open(new_file, "wb") as f:
                        for chunk in response.iter_content(chunk_size=chunk_size):
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            if progress_callback:
                                progress_callback("progress", (downloaded_size, total_size))
                    
                    # Validate: check PE MZ headers
                    if os.path.exists(new_file) and os.path.getsize(new_file) > 1024:
                        with open(new_file, "rb") as f_check:
                            magic = f_check.read(2)
                        if magic != b'MZ':
                            self.safe_log_update("[OTA] ⚠️ Downloaded file is not a valid Windows executable. Skipping.")
                            try:
                                os.remove(new_file)
                            except: pass
                            if progress_callback:
                                progress_callback("error", "Invalid PE executable magic bytes")
                            return
                        
                        # Validate SHA-256 if provided by server
                        server_sha = data.get("sha256", "")
                        if server_sha:
                            import hashlib
                            sha256_hash = hashlib.sha256()
                            with open(new_file, "rb") as f_hash:
                                for byte_block in iter(lambda: f_hash.read(4096), b""):
                                    sha256_hash.update(byte_block)
                            calc_sha = sha256_hash.hexdigest()
                            if calc_sha.lower() != server_sha.lower():
                                self.safe_log_update(f"[OTA] ⚠️ Checksum mismatch! Expected: {server_sha}, Got: {calc_sha}")
                                try:
                                    os.remove(new_file)
                                except: pass
                                if progress_callback:
                                    progress_callback("error", "Checksum verification failed")
                                return
                            else:
                                self.safe_log_update("[OTA] SHA-256 Checksum verified successfully.")
                        
                        self._update_pending_path = new_file
                        self.safe_log_update(f"[OTA] Update v{latest_ver} downloaded successfully ({downloaded_size//1024//1024} MB). Ready to install.")
                        self.after(0, self._show_update_banner)
                        if progress_callback:
                            progress_callback("complete", downloaded_size)
                    else:
                        if progress_callback:
                            progress_callback("error", "Downloaded file empty or truncated")
                else:
                    self.safe_log_update("[SYS] Application is up to date.")
                    if progress_callback:
                        progress_callback("up_to_date", None)
            else:
                self.safe_log_update("[SYS] Control Tower returned non-200. Running locally.")
                if progress_callback:
                    progress_callback("error", "Control Tower update response error")
        except Exception as e:
            self.safe_log_update(f"[SYS] Update error: {e}")
            if progress_callback:
                progress_callback("error", str(e))

    def show_download_progress_popup(self, latest_ver):
        """Show a premium download progress meter and installation status dialog."""
        popup = ctk.CTkToplevel(self)
        popup.title("Downloading Software Update")
        popup.attributes("-topmost", True)
        popup.grab_set()
        popup.configure(fg_color="#0f172a")
        
        pw, ph = 460, 360
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        popup.geometry(f"{pw}x{ph}+{(sw-pw)//2}+{(sh-ph)//2}")
        popup.resizable(False, False)
        
        # Header Frame
        header = ctk.CTkFrame(popup, fg_color="#1e293b", corner_radius=0)
        header.pack(fill="x")
        
        ctk.CTkLabel(header, text="⬇️", font=("Segoe UI", 36)).pack(pady=(16, 0))
        title_lbl = ctk.CTkLabel(header, text=f"Downloading Update v{latest_ver}", font=("Segoe UI", 18, "bold"), text_color="#60a5fa")
        title_lbl.pack(pady=(4, 2))
        subtitle_lbl = ctk.CTkLabel(header, text="Please wait while the update package is retrieved...", font=("Segoe UI", 11), text_color="#94a3b8")
        subtitle_lbl.pack(pady=(0, 14))
        
        # Progress Bar and Info
        info_frame = ctk.CTkFrame(popup, fg_color="transparent")
        info_frame.pack(fill="x", padx=30, pady=20)
        
        progress_bar = ctk.CTkProgressBar(info_frame, fg_color="#1e293b", progress_color="#0ea5e9", height=12)
        progress_bar.set(0.0)
        progress_bar.pack(fill="x", pady=(0, 6))
        
        stats_lbl = ctk.CTkLabel(info_frame, text="Starting download...", font=("Segoe UI", 12), text_color="#cbd5e1")
        stats_lbl.pack(anchor="w")
        
        status_lbl = ctk.CTkLabel(info_frame, text="Status: Connecting to Control Tower...", font=("Segoe UI", 11, "italic"), text_color="#94a3b8")
        status_lbl.pack(anchor="w", pady=(8, 0))
        
        # Bottom controls frame
        ctrl_frame = ctk.CTkFrame(popup, fg_color="transparent")
        ctrl_frame.pack(fill="x", side="bottom", padx=30, pady=20)
        
        action_btn = ctk.CTkButton(ctrl_frame, text="Later (Background)", font=("Segoe UI", 12, "bold"), height=38,
                                   fg_color="transparent", border_width=1, border_color=CLR_BORDER, text_color=CLR_DIM,
                                   command=popup.destroy)
        action_btn.pack(fill="x")
        
        def progress_callback(status, detail):
            if status == "progress":
                downloaded, total = detail
                percent = (downloaded / total) if total > 0 else 0
                mb_downloaded = downloaded / (1024 * 1024)
                mb_total = total / (1024 * 1024)
                
                self.after(0, lambda: progress_bar.set(percent))
                self.after(0, lambda: stats_lbl.configure(text=f"Downloaded: {mb_downloaded:.1f} MB / {mb_total:.1f} MB ({percent*100:.0f}%)"))
                self.after(0, lambda: status_lbl.configure(text="Status: Downloading files..."))
            
            elif status == "complete":
                mb_downloaded = detail / (1024 * 1024)
                self.after(0, lambda: progress_bar.set(1.0))
                self.after(0, lambda: progress_bar.configure(progress_color="#10b981"))
                self.after(0, lambda: title_lbl.configure(text="Update Ready to Install!", text_color="#4ade80"))
                self.after(0, lambda: subtitle_lbl.configure(text=f"v{latest_ver} downloaded and verified successfully."))
                self.after(0, lambda: stats_lbl.configure(text=f"Verification complete: {mb_downloaded:.1f} MB received."))
                self.after(0, lambda: status_lbl.configure(text="Status: Ready to install. Application restart required."))
                
                def trigger_restart():
                    popup.destroy()
                    self._restart_app()
                
                self.after(0, lambda: action_btn.configure(
                    text="🔄 Restart & Install Now",
                    fg_color="#10b981",
                    hover_color="#059669",
                    text_color="#ffffff",
                    border_width=0,
                    command=trigger_restart
                ))
            
            elif status == "error":
                self.after(0, lambda: title_lbl.configure(text="Download Failed", text_color="#ef4444"))
                self.after(0, lambda: subtitle_lbl.configure(text="An error occurred during update download."))
                self.after(0, lambda: status_lbl.configure(text=f"Error: {detail}"))
                self.after(0, lambda: action_btn.configure(text="Close", command=popup.destroy))
            
            elif status == "up_to_date":
                self.after(0, lambda: title_lbl.configure(text="Already Up to Date", text_color="#4ade80"))
                self.after(0, lambda: subtitle_lbl.configure(text="You are already running the latest version."))
                self.after(0, lambda: status_lbl.configure(text="Status: No action required."))
                self.after(0, lambda: action_btn.configure(text="Close", command=popup.destroy))
        
        threading.Thread(target=self.check_for_updates, args=(progress_callback,), daemon=True).start()

    def trigger_force_update(self):
        """Called when FORCE_UPDATE command is received. Resolves latest version and shows progress UI."""
        def run_force():
            try:
                resp = requests.get("http://devash.in/api/update_check", timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    latest_ver = data.get("latest_version", "0.0")
                    current_ver = CLIENT_VERSION
                    if float(latest_ver) > float(current_ver):
                        self.safe_log_update(f"[REMOTE] Update v{latest_ver} available. Opening progress UI...")
                        self.after(0, lambda: self.show_download_progress_popup(latest_ver))
                    else:
                        self.safe_log_update("[REMOTE] Force update received, but app is already at the latest version.")
                else:
                    self.safe_log_update("[REMOTE] Force update failed: Control Tower update check failed.")
            except Exception as e:
                self.safe_log_update(f"[REMOTE] Force update check failed: {e}")
        
        threading.Thread(target=run_force, daemon=True).start()

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
                r = requests.get(f"http://devash.in/api/poll_commands?hwid={hwid}&version={CLIENT_VERSION}", timeout=5)
                if r.status_code == 200:
                    commands = r.json()
                    for cmd in commands:
                        c_id = cmd["id"]
                        c_text = cmd["command"]
                        self.safe_log_update(f"[REMOTE] Received cloud command: {c_text}")
                        
                        if c_text == "PULL_DATA":
                            self.trigger_manual_pull()
                        elif c_text == "PULL_JJM":
                            self.trigger_manual_jjm_pull()
                        elif c_text == "BROADCAST":
                            self.trigger_manual_send()
                        elif c_text == "FORCE_UPDATE":
                            self.safe_log_update("[REMOTE] Force Update command received. Triggering update manager UI...")
                            self.trigger_force_update()
                            
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

    def on_closing(self):
        """Handle window close event manually. Silently applies any pending update before exiting."""
        update_path = getattr(self, '_update_pending_path', None)
        if update_path and os.path.exists(update_path):
            try:
                current_exe = sys.executable if getattr(sys, 'frozen', False) else None
                if current_exe and current_exe.endswith(".exe"):
                    bat_path = os.path.join(_BASE_DIR, "nexus_updater.bat")
                    bat_content = f"""@echo off
ping -n 3 127.0.0.1 > nul
copy /Y "{update_path}" "{current_exe}"
del "{update_path}"
schtasks /create /tn "NexusSyncPro_DailyOpen" /tr "\"{current_exe}\"" /sc daily /st 08:00 /f > nul
del "%~f0"
"""
                    with open(bat_path, 'w') as f:
                        f.write(bat_content)
                    import subprocess
                    subprocess.Popen(
                        ['cmd', '/c', bat_path],
                        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                        close_fds=True
                    )
            except Exception:
                pass
        self.destroy()

    def setup_ui(self):
        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, fg_color=CLR_SIDEBAR, width=260, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # Scrollable area for sidebar content
        self.sidebar_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent", corner_radius=0, label_text="")
        self.sidebar_scroll.pack(fill="both", expand=True)
        
        ctk.CTkLabel(self.sidebar_scroll, text="NEXUS SYNC", font=("Segoe UI", 24, "bold"), text_color=CLR_CYAN).pack(pady=(30, 5))
        ctk.CTkLabel(self.sidebar_scroll, text=f"PRODUCTION BUILD v{CLIENT_VERSION}", font=("Segoe UI", 9, "bold"), text_color=CLR_GOLD).pack(pady=(0, 20))

        ctrl_frame = ctk.CTkFrame(self.sidebar_scroll, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=20, pady=10)
        
        self.service_switch = ctk.CTkSwitch(self.sidebar_scroll, text="AUTO-PILOT MODE", variable=self.service_active, font=("Segoe UI", 12, "bold"), fg_color=CLR_DIM, progress_color=CLR_GREEN, command=self.on_autopilot_toggle)
        self.service_switch.pack(pady=(0, 20))

        self.pull_btn = ctk.CTkButton(ctrl_frame, text="📥 PULL NEW DATA", fg_color="#f1f5f9", hover_color="#e2e8f0", 
                                     border_width=1, border_color=CLR_CYAN, text_color=CLR_CYAN, font=("Segoe UI", 13, "bold"), height=40, command=self.trigger_manual_pull)
        self.pull_btn.pack(fill="x", pady=5)
        
        self.pull_jjm_btn = ctk.CTkButton(ctrl_frame, text="💧 PULL JJM DATA", fg_color="#f1f5f9", hover_color="#e2e8f0", 
                                     border_width=1, border_color=CLR_CYAN, text_color=CLR_CYAN, font=("Segoe UI", 13, "bold"), height=40, command=self.trigger_manual_jjm_pull)
        self.pull_jjm_btn.pack(fill="x", pady=5)
        
        self.send_btn = ctk.CTkButton(ctrl_frame, text="📤 BROADCAST REPORT", fg_color=CLR_GREEN, hover_color="#059669", 
                                     text_color="#ffffff", font=("Segoe UI", 13, "bold"), height=40, command=self.trigger_manual_send)
        self.send_btn.pack(fill="x", pady=5)

        self.report_btn = ctk.CTkButton(ctrl_frame, text="📊 GENERATE DAILY REPORT", fg_color=CLR_GOLD, hover_color="#d97706", 
                                     text_color="#ffffff", font=("Segoe UI", 13, "bold"), height=40, command=self.generate_final_report)
        self.report_btn.pack(fill="x", pady=5)

        self.ws_btn = ctk.CTkButton(ctrl_frame, text="📁 CHANGE WORKSPACE", fg_color="transparent", border_width=1, border_color=CLR_BORDER,
                                     text_color=CLR_TEXT, font=("Segoe UI", 13, "bold"), height=40, command=self.manual_change_workspace)
        self.ws_btn.pack(fill="x", pady=5)

        # Hidden Chrome Button: Personal WhatsApp access protected.
        # Trigger manually using double-click on version/dev credits in sidebar OR Ctrl+Shift+W shortcut.


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

        # ── DEVELOPER CREDIT (Double-Click Secret Shortcut to Open WhatsApp Chrome) ──
        dev_lbl = ctk.CTkLabel(self.sidebar, text="DEVELOPED BY: ASHISH KUMAR", font=("Segoe UI", 9, "italic"), text_color=CLR_DIM)
        dev_lbl.pack(side="bottom", pady=(10, 4))
        dev_lbl.bind("<Double-Button-1>", lambda e: self.manual_open_chrome_profile())

        ver_lbl = ctk.CTkLabel(self.sidebar, text=f"v{CLIENT_VERSION} • Enterprise Suite", font=("Segoe UI", 9), text_color=CLR_DIM)
        ver_lbl.pack(side="bottom", pady=(0, 0))
        ver_lbl.bind("<Double-Button-1>", lambda e: self.manual_open_chrome_profile())

        # Global Keyboard Shortcut: Ctrl + Shift + W to open WhatsApp Chrome
        self.bind_all("<Control-Shift-W>", lambda e: self.manual_open_chrome_profile())


        # --- MAIN TABVIEW ---
        self.main_tabs = ctk.CTkTabview(self, fg_color="transparent", command=self.on_tab_changed)
        self.main_tabs.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        self.tab_dash = self.main_tabs.add("📊 SCADA DASHBOARD")
        self.tab_history = self.main_tabs.add("📂 HISTORICAL VIEWER")

        
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

        # Bottom Split Frame (Metrics & WhatsApp)
        self.bottom_split = ctk.CTkFrame(self.display, fg_color="transparent")
        self.bottom_split.pack(fill="both", expand=True)

        # Left side: Metrics wrapper container
        self.metrics_wrapper = ctk.CTkFrame(self.bottom_split, fg_color="transparent")
        self.metrics_wrapper.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Middle Metrics Frame (JJM) - Row 1
        self.metrics_container = ctk.CTkFrame(self.metrics_wrapper, fg_color="transparent")
        self.metrics_container.pack(fill="x", pady=(0, 10))
        
        self.jjm_total_lbl = self._create_metric_card(self.metrics_container, "TOTAL JJM SCHEMES", "0", CLR_CYAN, command=lambda e: self.show_list_popup("JJM TOTAL", self.jjm_list_data.get("total", [])))
        self.jjm_live_lbl = self._create_metric_card(self.metrics_container, "LIVE CONNECTED", "0", CLR_GREEN, command=lambda e: self.show_list_popup("JJM LIVE CONNECTED", self.jjm_list_data.get("live", [])))
        self.jjm_not_recv_lbl = self._create_metric_card(self.metrics_container, "DATA NOT RECEIVED", "0", CLR_GOLD, command=lambda e: self.show_list_popup("JJM NOT RECEIVED", self.jjm_list_data.get("not_recv", [])))

        # Middle Metrics Frame (JJM) - Row 2
        self.metrics_container_2 = ctk.CTkFrame(self.metrics_wrapper, fg_color="transparent")
        self.metrics_container_2.pack(fill="x", pady=(0, 10))
        
        self.jjm_leftover_lbl = self._create_metric_card(self.metrics_container_2, "OFF-GRID / MISSING", "0", "#ff4d4d", command=lambda e: self.show_list_popup("JJM OFF-GRID / MISSING", self.jjm_list_data.get("leftover", [])))
        self.jjm_new_lbl = self._create_metric_card(self.metrics_container_2, "NEWLY ADDED IN JJM", "0", "#ff4d4d", command=lambda e: self.show_list_popup("JJM NEWLY ADDED", self.jjm_list_data.get("new", [])))

        # SCADA Metrics Frame
        self.scada_metrics_container = ctk.CTkFrame(self.metrics_wrapper, fg_color="transparent")
        self.scada_metrics_container.pack(fill="x", pady=(0, 10))
        
        self.scada_total_lbl = self._create_metric_card(self.scada_metrics_container, "SCADA TOTAL (EXCEL)", "0", CLR_CYAN, command=lambda e: self.show_list_popup("SCADA TOTAL SCHEMES", self.scada_data.get("total", [])))
        self.scada_sync_lbl = self._create_metric_card(self.scada_metrics_container, "NOW SCADA SYNCED", "0", CLR_GREEN, command=lambda e: self.show_list_popup("SCADA SYNCED SCHEMES", self.scada_data.get("synced", [])))
        self.scada_unsync_lbl = self._create_metric_card(self.scada_metrics_container, "NOT YET SYNCED", "0", CLR_GOLD, command=lambda e: self.show_list_popup("SCADA NOT SYNCED", self.scada_data.get("not_synced", [])))
        self.scada_new_lbl = self._create_metric_card(self.scada_metrics_container, "NEWLY ADDED IN SCADA", "0", "#ff4d4d", command=lambda e: self.show_list_popup("SCADA NEWLY ADDED", self.scada_data.get("new", [])))

        # 4. WhatsApp Preview Terminal (Right side of bottom split)
        self.preview_container = ctk.CTkFrame(self.bottom_split, fg_color=CLR_CARD, border_width=1, border_color=CLR_BORDER, height=350)
        self.preview_container.pack(side="right", fill="both", expand=True, padx=(10, 0))
        self.preview_container.pack_propagate(False)
        ctk.CTkLabel(self.preview_container, text="📱 WHATSAPP PAYLOAD PREVIEW", font=("Segoe UI", 11, "bold"), text_color=CLR_GREEN).pack(anchor="w", padx=15, pady=5)
        self.preview_terminal = ctk.CTkTextbox(self.preview_container, fg_color="#f3f4f6", text_color=CLR_TEXT, font=("Segoe UI", 12))
        self.preview_terminal.pack(fill="both", expand=True, padx=10, pady=10)

        # 5. Broadcast Activity / Last Sync Status Block
        self.activity_outer = ctk.CTkFrame(self.display, fg_color="transparent")
        self.activity_outer.pack(fill="x", pady=(10, 0))

        self.broadcast_status_frame = ctk.CTkFrame(self.activity_outer, fg_color=CLR_CARD, border_width=1, border_color=CLR_BORDER)
        self.broadcast_status_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))
        ctk.CTkLabel(self.broadcast_status_frame, text="📡 LAST BROADCAST STATUS", font=("Segoe UI", 11, "bold"), text_color=CLR_GOLD).pack(anchor="w", padx=15, pady=(10, 2))
        self.broadcast_status_lbl = ctk.CTkLabel(self.broadcast_status_frame, text="No broadcast sent yet.", font=("Segoe UI", 11), text_color=CLR_DIM, wraplength=380, justify="left")
        self.broadcast_status_lbl.pack(anchor="w", padx=15, pady=(0, 8))
        self.broadcast_count_lbl = ctk.CTkLabel(self.broadcast_status_frame, text="Contacts Reached: --", font=("Segoe UI", 10, "bold"), text_color=CLR_GREEN)
        self.broadcast_count_lbl.pack(anchor="w", padx=15, pady=(0, 10))

        self.sync_status_frame = ctk.CTkFrame(self.activity_outer, fg_color=CLR_CARD, border_width=1, border_color=CLR_BORDER)
        self.sync_status_frame.pack(side="left", fill="both", expand=True, padx=(8, 8))
        ctk.CTkLabel(self.sync_status_frame, text="⏱️ LAST DATA SYNC", font=("Segoe UI", 11, "bold"), text_color=CLR_CYAN).pack(anchor="w", padx=15, pady=(10, 2))
        self.sync_status_lbl = ctk.CTkLabel(self.sync_status_frame, text="No sync recorded yet.", font=("Segoe UI", 11), text_color=CLR_DIM, wraplength=380, justify="left")
        self.sync_status_lbl.pack(anchor="w", padx=15, pady=(0, 8))
        self.sync_file_lbl = ctk.CTkLabel(self.sync_status_frame, text="Latest File: --", font=("Segoe UI", 10, "bold"), text_color=CLR_TEXT)
        self.sync_file_lbl.pack(anchor="w", padx=15, pady=(0, 10))

        self.report_status_frame = ctk.CTkFrame(self.activity_outer, fg_color=CLR_CARD, border_width=1, border_color=CLR_BORDER)
        self.report_status_frame.pack(side="left", fill="both", expand=True, padx=(8, 0))
        ctk.CTkLabel(self.report_status_frame, text="📊 DAILY REPORT STATUS", font=("Segoe UI", 11, "bold"), text_color="#a78bfa").pack(anchor="w", padx=15, pady=(10, 2))
        self.report_status_lbl = ctk.CTkLabel(self.report_status_frame, text="No report generated yet.", font=("Segoe UI", 11), text_color=CLR_DIM, wraplength=380, justify="left")
        self.report_status_lbl.pack(anchor="w", padx=15, pady=(0, 8))
        self.report_path_lbl = ctk.CTkLabel(self.report_status_frame, text="Saved to: --", font=("Segoe UI", 10, "bold"), text_color=CLR_TEXT)
        self.report_path_lbl.pack(anchor="w", padx=15, pady=(0, 10))


        # --- HISTORICAL VIEWER TAB ---
        self.setup_history_ui()


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

    def setup_history_ui(self):
        # 📂 HISTORICAL VIEWER Tab controls
        controls_frame = ctk.CTkFrame(self.tab_history, fg_color=CLR_CARD, border_width=1, border_color=CLR_BORDER)
        controls_frame.pack(fill="x", padx=15, pady=(10, 5))

        # LEFT: Calendar picker block
        date_block = ctk.CTkFrame(controls_frame, fg_color="transparent")
        date_block.pack(side="left", padx=15, pady=12)

        ctk.CTkLabel(date_block, text="📅 Report Date:", font=("Segoe UI", 11, "bold"), text_color=CLR_DIM).pack(anchor="w", pady=(0, 4))

        picker_row = ctk.CTkFrame(date_block, fg_color="transparent")
        picker_row.pack(fill="x")

        self.selected_date_var = tk.StringVar(value="No reports found")
        self.cal_date_display = ctk.CTkLabel(
            picker_row,
            textvariable=self.selected_date_var,
            font=("Segoe UI", 13, "bold"),
            text_color=CLR_CYAN,
            fg_color="#1e293b",
            corner_radius=6,
            padx=12, pady=6,
            width=160
        )
        self.cal_date_display.pack(side="left", padx=(0, 8))

        self.cal_open_btn = ctk.CTkButton(
            picker_row,
            text="📆 Open Calendar",
            font=("Segoe UI", 11, "bold"),
            fg_color="#0ea5e9", hover_color="#0284c7",
            text_color="#ffffff", height=34, width=140,
            command=self._open_calendar_picker
        )
        self.cal_open_btn.pack(side="left")

        self.refresh_dates_btn = ctk.CTkButton(
            picker_row, text="🔄", width=34, height=34,
            fg_color="transparent", border_width=1, border_color=CLR_BORDER,
            text_color=CLR_TEXT, font=("Segoe UI", 14),
            command=self.refresh_historical_dates
        )
        self.refresh_dates_btn.pack(side="left", padx=(6, 0))

        # MIDDLE: Zoom Control
        zoom_sep = ctk.CTkFrame(controls_frame, fg_color=CLR_BORDER, width=1)
        zoom_sep.pack(side="left", fill="y", padx=16, pady=8)

        zoom_block = ctk.CTkFrame(controls_frame, fg_color="transparent")
        zoom_block.pack(side="left", pady=12)
        ctk.CTkLabel(zoom_block, text="🔍 Zoom:", font=("Segoe UI", 11, "bold"), text_color=CLR_DIM).pack(anchor="w", pady=(0, 4))
        zoom_row = ctk.CTkFrame(zoom_block, fg_color="transparent")
        zoom_row.pack(fill="x")
        self.zoom_var = tk.IntVar(value=100)
        self.zoom_label = ctk.CTkLabel(zoom_row, text="100%", font=("Segoe UI", 11, "bold"), text_color=CLR_CYAN, width=44)
        self.zoom_label.pack(side="left", padx=(0, 6))
        self.zoom_slider = ctk.CTkSlider(
            zoom_row, from_=10, to=200, number_of_steps=38,
            variable=self.zoom_var, width=180,
            command=self._on_zoom_change
        )
        self.zoom_slider.pack(side="left")

        # RIGHT: Save button
        self.save_edit_btn = ctk.CTkButton(
            controls_frame, text="💾 Save Changes",
            fg_color=CLR_GREEN, hover_color="#059669",
            text_color="#ffffff", command=self.save_historical_changes, state="disabled"
        )
        self.save_edit_btn.pack(side="right", padx=15, pady=12)

        # Grid View Frame
        self.grid_frame = ctk.CTkFrame(self.tab_history, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.history_tree = None
        self.loaded_df = None
        self.loaded_filepath = None
        self.active_cell_entry = None
        self._current_zoom = 100
        self._available_report_dates = []   # list of datetime objects with reports
        self._all_dated_folders = {}        # date_str -> folder path (all data folders)

        # File strip panel (shown after date pick)
        self.file_strip_frame = ctk.CTkFrame(self.tab_history, fg_color="#0f172a", border_width=1, border_color=CLR_BORDER)
        # Not packed yet — shown dynamically when a date is chosen

        self.refresh_historical_dates()

    def on_tab_changed(self):
        if hasattr(self, 'main_tabs'):
            try:
                current_tab = self.main_tabs.get()
                if current_tab == "📂 HISTORICAL VIEWER":
                    self.refresh_historical_dates()
            except Exception:
                pass

    def refresh_historical_dates(self):
        if not hasattr(self, 'workspace_base') or not os.path.exists(self.workspace_base):
            if hasattr(self, 'watch_folder') and os.path.exists(self.watch_folder):
                base_dir = os.path.dirname(self.watch_folder)
            else:
                return
        else:
            base_dir = self.workspace_base

        # ── Discover Final Daily Report dates (for calendar highlight) ──
        final_files = glob.glob(os.path.join(base_dir, '**', 'Final_Daily_Report_*.xlsx'), recursive=True)
        report_dates = []
        self.history_file_map = {}
        for f in final_files:
            basename = os.path.basename(f)
            match = re.search(r'Final_Daily_Report_(.*?)\.xlsx', basename)
            if match:
                date_str = match.group(1)
                report_dates.append(date_str)
                self.history_file_map[date_str] = f

        # ── Discover ALL dated folders (dd-mm-yyyy pattern) with any xlsx ──
        self._all_dated_folders = {}
        try:
            for entry in os.scandir(base_dir):
                if entry.is_dir():
                    folder_name = entry.name
                    # Match dd-mm-yyyy OR ddmm (legacy) folder patterns
                    if re.match(r'^\d{2}-\d{2}-\d{4}$', folder_name):
                        xlsx_in_folder = glob.glob(os.path.join(entry.path, '*.xlsx'))
                        if xlsx_in_folder:
                            self._all_dated_folders[folder_name] = entry.path
        except Exception:
            pass

        def parse_date(d):
            try:
                return datetime.strptime(d, "%d-%m-%Y")
            except:
                return datetime.min
        report_dates.sort(key=parse_date, reverse=True)

        # All known calendar dates = union of report dates + all data folder dates
        all_calendar_dates = set(report_dates) | set(self._all_dated_folders.keys())

        def update_gui():
            self._available_report_dates = []
            for d in all_calendar_dates:
                try:
                    self._available_report_dates.append(datetime.strptime(d, "%d-%m-%Y"))
                except:
                    pass

            if report_dates:
                if not self.selected_date_var.get() or self.selected_date_var.get() not in report_dates:
                    self.selected_date_var.set(report_dates[0])
                    self._show_file_strip(report_dates[0])
                    self.load_historical_file(report_dates[0])
            elif self._all_dated_folders:
                first_date = sorted(self._all_dated_folders.keys(), key=parse_date, reverse=True)[0]
                self.selected_date_var.set(first_date)
                self._show_file_strip(first_date)
            else:
                self.selected_date_var.set("No reports found")

        self.after(0, update_gui)

    def _open_calendar_picker(self):
        """Open a premium dark-themed calendar popup with report dates highlighted."""
        try:
            from tkcalendar import Calendar as TkCalendar
        except ImportError:
            messagebox.showerror("Missing Library", "tkcalendar is not installed.\nRun: pip install tkcalendar")
            return

        popup = ctk.CTkToplevel(self)
        popup.title("Select Report Date")
        popup.resizable(False, False)
        popup.attributes("-topmost", True)
        popup.configure(fg_color="#0f172a")

        popup.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 210
        y = self.winfo_y() + (self.winfo_height() // 2) - 220
        popup.geometry(f"420+{x}+{y}")

        ctk.CTkLabel(
            popup, text="📅  Select Date",
            font=("Segoe UI", 15, "bold"), text_color=CLR_CYAN
        ).pack(pady=(16, 4))
        ctk.CTkLabel(
            popup, text="🟢 Blue = Final Report  │  ⚪ Grey = Raw data only",
            font=("Segoe UI", 10), text_color=CLR_DIM
        ).pack(pady=(0, 10))

        current_str = self.selected_date_var.get()
        try:
            init_date = datetime.strptime(current_str, "%d-%m-%Y")
        except:
            init_date = datetime.today()

        cal = TkCalendar(
            popup,
            selectmode='day',
            year=init_date.year,
            month=init_date.month,
            day=init_date.day,
            background="#1e293b",
            foreground="#f1f5f9",
            bordercolor="#334155",
            headersbackground="#0f172a",
            headersforeground="#0ea5e9",
            selectbackground="#0ea5e9",
            selectforeground="#0f172a",
            normalbackground="#1e293b",
            normalforeground="#f1f5f9",
            weekendbackground="#1e293b",
            weekendforeground="#94a3b8",
            othermonthbackground="#0f172a",
            othermonthforeground="#475569",
            othermonthwebackground="#0f172a",
            othermonthweforeground="#475569",
            disabledbackground="#0f172a",
            cursor="hand2",
            font=("Segoe UI", 10),
            date_pattern="dd-mm-yyyy",
        )
        cal.pack(padx=20, pady=6, fill="both", expand=True)

        # Blue highlight = has Final Daily Report
        for dt in getattr(self, '_available_report_dates', []):
            date_str_check = dt.strftime("%d-%m-%Y")
            if date_str_check in self.history_file_map:
                cal.calevent_create(dt, "Final Report", "report_day")
            else:
                cal.calevent_create(dt, "Raw Data", "raw_day")
        cal.tag_config("report_day", background="#0ea5e9", foreground="#0f172a")
        cal.tag_config("raw_day",    background="#475569", foreground="#f1f5f9")

        btn_row = ctk.CTkFrame(popup, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(8, 16))

        def on_select():
            chosen = cal.get_date()   # dd-mm-yyyy
            folder_has_data = chosen in self.history_file_map or chosen in getattr(self, '_all_dated_folders', {})
            if folder_has_data:
                self.selected_date_var.set(chosen)
                self._show_file_strip(chosen)
                # Auto-load Final report if it exists; else let user pick from strip
                if chosen in self.history_file_map:
                    self.load_historical_file(chosen)
                popup.destroy()
            else:
                err_lbl.configure(text=f"❌ No data found for {chosen}")

        ctk.CTkButton(
            btn_row, text="✅  Open Date",
            font=("Segoe UI", 12, "bold"),
            fg_color=CLR_GREEN, hover_color="#059669",
            text_color="#ffffff", height=38,
            command=on_select
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            btn_row, text="✕  Cancel",
            font=("Segoe UI", 12, "bold"),
            fg_color="transparent", border_width=1, border_color=CLR_BORDER,
            text_color=CLR_DIM, height=38,
            command=popup.destroy
        ).pack(side="left", fill="x", expand=True, padx=(6, 0))

        err_lbl = ctk.CTkLabel(popup, text="", font=("Segoe UI", 10), text_color="#f87171")
        err_lbl.pack(pady=(0, 8))

    def _show_file_strip(self, date_str):
        """Show a horizontal scrollable strip of all xlsx files for the chosen date folder."""
        # Clear old strip contents
        for w in self.file_strip_frame.winfo_children():
            w.destroy()

        # Gather files: Final report + raw data files from folder
        files_info = []   # list of (label, filepath, is_final)

        # Final report
        final_path = self.history_file_map.get(date_str)
        if final_path and os.path.exists(final_path):
            files_info.append(("★ FINAL REPORT", final_path, True))

        # Raw GP data files from folder
        folder = getattr(self, '_all_dated_folders', {}).get(date_str)
        if folder and os.path.exists(folder):
            for f in sorted(os.listdir(folder)):
                if f.endswith('.xlsx') and not f.startswith('Final_Daily_Report'):
                    files_info.append((os.path.splitext(f)[0], os.path.join(folder, f), False))

        if not files_info:
            self.file_strip_frame.pack_forget()
            return

        # Header row
        header_row = ctk.CTkFrame(self.file_strip_frame, fg_color="transparent")
        header_row.pack(fill="x", padx=12, pady=(8, 4))
        ctk.CTkLabel(
            header_row,
            text=f"📂  Files in {date_str}  —  {len(files_info)} file(s) found",
            font=("Segoe UI", 11, "bold"), text_color=CLR_CYAN
        ).pack(side="left")
        ctk.CTkLabel(
            header_row,
            text="Click any file to load it into the viewer →",
            font=("Segoe UI", 10), text_color=CLR_DIM
        ).pack(side="right")

        # Scrollable horizontal card strip
        scroll_canvas = tk.Canvas(
            self.file_strip_frame,
            height=72, bg="#0f172a", highlightthickness=0
        )
        h_scroll = tk.Scrollbar(self.file_strip_frame, orient="horizontal", command=scroll_canvas.xview)
        scroll_canvas.configure(xscrollcommand=h_scroll.set)
        h_scroll.pack(side="bottom", fill="x", padx=12)
        scroll_canvas.pack(side="left", fill="x", expand=True, padx=12)

        inner_frame = tk.Frame(scroll_canvas, bg="#0f172a")
        scroll_canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        def on_inner_configure(e):
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))
        inner_frame.bind("<Configure>", on_inner_configure)

        # Mouse-wheel horizontal scroll
        def on_mousewheel(e):
            scroll_canvas.xview_scroll(int(-1 * (e.delta / 120)), "units")
        scroll_canvas.bind("<MouseWheel>", on_mousewheel)

        for label, fpath, is_final in files_info:
            card_bg  = "#1a3a52" if is_final else "#1e293b"
            card_hl  = "#0ea5e9" if is_final else "#334155"
            tag_color = CLR_GOLD if is_final else CLR_CYAN
            tag_text  = "FINAL" if is_final else "RAW"
            fname = os.path.basename(fpath)

            card = tk.Frame(inner_frame, bg=card_bg, padx=8, pady=6, cursor="hand2",
                            highlightbackground=card_hl, highlightthickness=1)
            card.pack(side="left", padx=(0, 8), pady=4)

            tag_lbl = tk.Label(card, text=f"  {tag_text}  ", bg=tag_color,
                               fg="#0f172a", font=("Segoe UI", 7, "bold"))
            tag_lbl.pack(anchor="w")

            name_lbl = tk.Label(card, text=label[:30] + ("..." if len(label) > 30 else ""),
                                bg=card_bg, fg="#f1f5f9",
                                font=("Segoe UI", 9, "bold"), wraplength=160, justify="left")
            name_lbl.pack(anchor="w", pady=(2, 0))

            size_kb = os.path.getsize(fpath) // 1024
            size_lbl = tk.Label(card, text=f"{size_kb} KB",
                                bg=card_bg, fg="#64748b", font=("Segoe UI", 8))
            size_lbl.pack(anchor="w")

            def make_loader(fp, lbl):
                def _load(e=None):
                    self._load_any_file(fp, lbl)
                return _load

            loader = make_loader(fpath, label)
            for widget in [card, tag_lbl, name_lbl, size_lbl]:
                widget.bind("<Button-1>", loader)
                widget.bind("<Enter>", lambda e, c=card, h=card_hl: c.config(highlightbackground="#38bdf8", highlightthickness=2))
                widget.bind("<Leave>", lambda e, c=card, h=card_hl: c.config(highlightbackground=h, highlightthickness=1))

        # Show the strip between controls and grid
        self.file_strip_frame.pack(fill="x", padx=15, pady=(0, 5),
                                   before=self.grid_frame)

    def _load_any_file(self, filepath, label):
        """Load any xlsx into the viewer grid (final report or raw GP data)."""
        if not filepath or not os.path.exists(filepath):
            messagebox.showerror("File Not Found", f"Cannot find:\n{filepath}")
            return
        try:
            df = pd.read_excel(filepath, header=None, nrows=20)
            # Auto-detect header row (row with most non-null values)
            header_row = int(df.notna().sum(axis=1).idxmax())
            df = pd.read_excel(filepath, header=header_row)
            df.columns = [str(c).strip() for c in df.columns]
            if df.empty:
                messagebox.showwarning("Empty File", "The selected file has no readable data.")
                return

            self.loaded_filepath = filepath
            self.loaded_df = df

            for child in self.grid_frame.winfo_children():
                child.destroy()

            import tkinter.ttk as ttk
            style = ttk.Style()
            style.theme_use('clam')
            zoom = getattr(self, '_current_zoom', 100)
            rh = max(14, int(28 * zoom / 100))
            fs = max(7, int(10 * zoom / 100))
            style.configure("Nexus.Treeview",
                            background="#1e293b", foreground="#f1f5f9",
                            rowheight=rh, fieldbackground="#1e293b",
                            font=("Segoe UI", fs))
            style.map("Nexus.Treeview",
                      background=[('selected', '#0ea5e9')],
                      foreground=[('selected', '#0f172a')])
            style.configure("Nexus.Treeview.Heading",
                            background="#0f172a", foreground="#0ea5e9",
                            font=("Segoe UI", fs, "bold"),
                            borderwidth=1, bordercolor="#334155")

            cols = ["sr_no"] + list(df.columns)
            self.grid_frame.rowconfigure(0, weight=1)
            self.grid_frame.columnconfigure(0, weight=1)

            self.history_tree = ttk.Treeview(self.grid_frame, columns=cols, show="headings", style="Nexus.Treeview")
            self.history_tree.grid(row=0, column=0, sticky="nsew")

            self.history_tree.heading("sr_no", text="Sr.No", command=lambda: self.sort_history_column("sr_no", False))
            self.history_tree.column("sr_no", width=55, minwidth=50, anchor="center")
            for col in df.columns:
                self.history_tree.heading(col, text=str(col), command=lambda c=col: self.sort_history_column(c, False))
                self.history_tree.column(col, width=150, minwidth=80, anchor="w")

            v_scroll = ctk.CTkScrollbar(self.grid_frame, orientation="vertical", command=self.history_tree.yview)
            v_scroll.grid(row=0, column=1, sticky="ns")
            h_scroll = ctk.CTkScrollbar(self.grid_frame, orientation="horizontal", command=self.history_tree.xview)
            h_scroll.grid(row=1, column=0, sticky="ew")
            self.history_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

            # File info banner
            row_count = len(df)
            col_count = len(df.columns)
            info_lbl = ctk.CTkLabel(
                self.grid_frame,
                text=f"📄  {os.path.basename(filepath)}  │  {row_count} rows × {col_count} columns",
                font=("Segoe UI", 10, "bold"), text_color=CLR_DIM,
                fg_color="#0f172a", anchor="w"
            )
            info_lbl.grid(row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=(2, 0))

            for idx, row in enumerate(df.values, 1):
                vals = [idx] + ["" if pd.isna(x) else str(x) for x in row]
                self.history_tree.insert("", "end", values=vals)

            self.history_tree.bind("<Double-1>", self.on_history_cell_double_click)
            self.save_edit_btn.configure(state="normal")

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load file:\n{os.path.basename(filepath)}\n\n{e}")

    def load_historical_file(self, date_str):
        filepath = getattr(self, 'history_file_map', {}).get(date_str)
        if not filepath or not os.path.exists(filepath):
            return
        
        try:
            self.loaded_filepath = filepath
            self.loaded_df = pd.read_excel(filepath)
            if self.loaded_df.empty:
                return
                
            for child in self.grid_frame.winfo_children():
                child.destroy()
                
            import tkinter.ttk as ttk
            style = ttk.Style()
            style.theme_use('clam')
            style.configure("Nexus.Treeview",
                            background="#1e293b",
                            foreground="#f1f5f9",
                            rowheight=28,
                            fieldbackground="#1e293b",
                            gridcolor="#334155",
                            font=("Segoe UI", 10))
            style.map("Nexus.Treeview",
                      background=[('selected', '#0ea5e9')],
                      foreground=[('selected', '#0f172a')])
            style.configure("Nexus.Treeview.Heading",
                            background="#0f172a",
                            foreground="#0ea5e9",
                            font=("Segoe UI", 10, "bold"),
                            borderwidth=1,
                            bordercolor="#334155")
            
            cols = ["sr_no"] + list(self.loaded_df.columns)
            self.grid_frame.rowconfigure(0, weight=1)
            self.grid_frame.columnconfigure(0, weight=1)
            
            self.history_tree = ttk.Treeview(self.grid_frame, columns=cols, show="headings", style="Nexus.Treeview")
            self.history_tree.grid(row=0, column=0, sticky="nsew")
            
            self.history_tree.heading("sr_no", text="Sr. No.", command=lambda: self.sort_history_column("sr_no", False))
            self.history_tree.column("sr_no", width=60, minwidth=60, anchor="center")
            
            for col in self.loaded_df.columns:
                self.history_tree.heading(col, text=str(col), command=lambda c=col: self.sort_history_column(c, False))
                self.history_tree.column(col, width=150, minwidth=100, anchor="w")
                
            v_scroll = ctk.CTkScrollbar(self.grid_frame, orientation="vertical", command=self.history_tree.yview)
            v_scroll.grid(row=0, column=1, sticky="ns")
            
            h_scroll = ctk.CTkScrollbar(self.grid_frame, orientation="horizontal", command=self.history_tree.xview)
            h_scroll.grid(row=1, column=0, sticky="ew")
            
            self.history_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
            
            for idx, row in enumerate(self.loaded_df.values, 1):
                vals = [idx] + ["" if pd.isna(x) else str(x) for x in row]
                self.history_tree.insert("", "end", values=vals)
                
            self.history_tree.bind("<Double-1>", self.on_history_cell_double_click)
            self.save_edit_btn.configure(state="normal")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load daily report:\n{e}")

    def _on_zoom_change(self, value):
        """Scale treeview row height and font size based on zoom slider."""
        zoom = int(float(value))
        self._current_zoom = zoom
        self.zoom_label.configure(text=f"{zoom}%")
        if not self.history_tree:
            return
        import tkinter.ttk as ttk
        base_row_height = 28
        base_font_size = 10
        new_row_height = max(14, int(base_row_height * zoom / 100))
        new_font_size = max(7, int(base_font_size * zoom / 100))
        style = ttk.Style()
        style.configure("Nexus.Treeview", rowheight=new_row_height, font=("Segoe UI", new_font_size))
        style.configure("Nexus.Treeview.Heading", font=("Segoe UI", new_font_size, "bold"))

    def on_history_cell_double_click(self, event):
        # Close any previously opened cell editor first
        if self.active_cell_entry is not None:
            try:
                self.active_cell_entry.destroy()
            except Exception:
                pass
            self.active_cell_entry = None

        region = self.history_tree.identify_region(event.x, event.y)
        if region != "cell":
            return
            
        column_id = self.history_tree.identify_column(event.x)
        item_id = self.history_tree.identify_row(event.y)
        if not item_id or not column_id:
            return
            
        col_idx = int(column_id.replace("#", "")) - 1
        if col_idx == 0:
            return
            
        x, y, w, h = self.history_tree.bbox(item_id, column_id)
        entry = ctk.CTkEntry(self.history_tree, width=w, height=h, font=("Segoe UI", 10), fg_color="#f3f4f6", text_color=CLR_TEXT, border_width=1, border_color=CLR_CYAN)
        self.active_cell_entry = entry
        current_val = self.history_tree.item(item_id, "values")[col_idx]
        entry.insert(0, current_val)
        entry.place(x=x, y=y)
        entry.focus()
        
        def save_cell_edit(event=None):
            new_val = entry.get().strip()
            vals = list(self.history_tree.item(item_id, "values"))
            vals[col_idx] = new_val
            self.history_tree.item(item_id, values=vals)
            all_items = self.history_tree.get_children("")
            row_idx = all_items.index(item_id)
            self.loaded_df.iat[row_idx, col_idx - 1] = new_val
            if self.active_cell_entry is entry:
                self.active_cell_entry = None
            try:
                entry.destroy()
            except Exception:
                pass
            
        def cancel_cell_edit(event=None):
            if self.active_cell_entry is entry:
                self.active_cell_entry = None
            try:
                entry.destroy()
            except Exception:
                pass
            
        entry.bind("<Return>", save_cell_edit)
        entry.bind("<FocusOut>", save_cell_edit)
        entry.bind("<Escape>", cancel_cell_edit)

    def save_historical_changes(self):
        if self.loaded_df is None or not self.loaded_filepath:
            return
        try:
            self.loaded_df.to_excel(self.loaded_filepath, index=False)
            messagebox.showinfo("Success", f"Changes successfully saved to:\n{os.path.basename(self.loaded_filepath)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save changes: {e}")

    def sort_history_column(self, col, reverse):
        if not self.history_tree:
            return
        l = [(self.history_tree.set(k, col), k) for k in self.history_tree.get_children("")]
        if col == "sr_no":
            try:
                l.sort(key=lambda t: int(t[0]), reverse=reverse)
            except:
                l.sort(key=lambda t: t[0], reverse=reverse)
        else:
            def try_numeric(val):
                try:
                    return float(val)
                except ValueError:
                    return val.lower()
            l.sort(key=lambda t: try_numeric(t[0]), reverse=reverse)
            
        for index, (val, k) in enumerate(l):
            self.history_tree.move(k, "", index)
            self.history_tree.set(k, "sr_no", index + 1)
            
        self.history_tree.heading(col, command=lambda: self.sort_history_column(col, not reverse))

    def on_autopilot_toggle(self):
        if self.service_active.get():
            self.safe_log_update("[SYS] Auto-Pilot enabled.")
        else:
            self.safe_log_update("[SYS] Auto-Pilot disabled.")


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
        popup.geometry("720x600")
        popup.attributes("-topmost", True)
        popup.configure(fg_color="#0f172a")
        
        # Center the popup relative to main window
        popup.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (720 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (600 // 2)
        popup.geometry(f"+{x}+{y}")
        
        header_lbl = ctk.CTkLabel(popup, text=f"{title} (Count: {len(items)})", font=("Segoe UI", 14, "bold"), text_color=CLR_CYAN)
        header_lbl.pack(pady=(15, 5))
        
        # Search Box
        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(popup, placeholder_text="🔍 Search schemes...", height=35, fg_color="#f3f4f6", border_color=CLR_BORDER, text_color=CLR_TEXT, placeholder_text_color="#64748b", textvariable=search_var)
        search_entry.pack(fill="x", padx=15, pady=(0, 10))
        
        # Style configuration for a premium, Excel-like dark table
        import tkinter.ttk as ttk
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("Nexus.Treeview",
                        background="#1e293b",
                        foreground="#f1f5f9",
                        rowheight=28,
                        fieldbackground="#1e293b",
                        gridcolor="#334155",
                        font=("Segoe UI", 10))
                        
        style.map("Nexus.Treeview",
                  background=[('selected', '#0ea5e9')],
                  foreground=[('selected', '#0f172a')])
                  
        style.configure("Nexus.Treeview.Heading",
                        background="#0f172a",
                        foreground="#0ea5e9",
                        font=("Segoe UI", 10, "bold"),
                        borderwidth=1,
                        bordercolor="#334155")
                        
        # Create a container frame for Treeview & Scrollbar
        table_frame = ctk.CTkFrame(popup, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Columns definition
        cols = ("sr_no", "name", "timestamp")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", style="Nexus.Treeview")
        
        # Define sorting logic
        def sort_column(col, reverse):
            l = [(tree.set(k, col), k) for k in tree.get_children("")]
            if col == "sr_no":
                try:
                    l.sort(key=lambda t: int(t[0]), reverse=reverse)
                except ValueError:
                    l.sort(key=lambda t: t[0], reverse=reverse)
            elif col == "timestamp":
                def parse_dt(val):
                    if val == "No recent data" or not val:
                        return datetime.min
                    for fmt in ("%d-%m-%Y %H:%M:%S", "%d-%m-%Y %I:%M %p", "%d-%m-%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                        try:
                            return datetime.strptime(val, fmt)
                        except ValueError:
                            pass
                    return datetime.min
                l.sort(key=lambda t: parse_dt(t[0]), reverse=reverse)
            else:
                l.sort(key=lambda t: t[0].lower(), reverse=reverse)

            for index, (val, k) in enumerate(l):
                tree.move(k, "", index)
                tree.set(k, "sr_no", index + 1)
                
            tree.heading(col, command=lambda: sort_column(col, not reverse))

        # Define headings
        tree.heading("sr_no", text="Sr. No.", command=lambda: sort_column("sr_no", False))
        tree.heading("name", text="Scheme / Gram Panchayat Name", command=lambda: sort_column("name", False))
        tree.heading("timestamp", text="Last Data Receive Date", command=lambda: sort_column("timestamp", False))
        
        # Define columns layout
        tree.column("sr_no", width=60, minwidth=60, anchor="center")
        tree.column("name", width=420, minwidth=300, anchor="w")
        tree.column("timestamp", width=200, minwidth=150, anchor="w")
        
        # Scrollbars
        v_scrollbar = ctk.CTkScrollbar(table_frame, orientation="vertical", command=tree.yview)
        tree.configure(yscrollcommand=v_scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        
        def update_list(*args):
            query = search_var.get().strip().lower()
            filtered = [it for it in items if query in str(it).lower()]
            
            # Clear old rows
            tree.delete(*tree.get_children())
            
            # Insert new rows
            for idx, it in enumerate(filtered, 1):
                name_str = str(it)
                time_str = ""
                if hasattr(self, "jjm_gp_times") and name_str in self.jjm_gp_times:
                    time_str = self.jjm_gp_times[name_str]
                elif hasattr(self, "scada_gp_times") and name_str in self.scada_gp_times:
                    time_str = self.scada_gp_times[name_str]
                
                if not time_str or time_str == "N/A":
                    time_str = "No recent data"
                    
                tree.insert("", "end", values=(idx, name_str, time_str))
                
            header_lbl.configure(text=f"{title} (Filtered: {len(filtered)} / Total: {len(items)})")

        search_var.trace_add("write", update_list)
        
        # Initial fill
        update_list()
        search_entry.focus()

        # Add Action Buttons Frame at the bottom
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        def copy_data():
            lines = ["Sr. No.\tScheme / Gram Panchayat Name\tLast Data Receive Date"]
            for k in tree.get_children(""):
                vals = tree.item(k, "values")
                lines.append(f"{vals[0]}\t{vals[1]}\t{vals[2]}")
            data_str = "\n".join(lines)
            popup.clipboard_clear()
            popup.clipboard_append(data_str)
            messagebox.showinfo("Success", "Table data copied to clipboard!", parent=popup)

        def download_data():
            filepath = filedialog.asksaveasfilename(
                parent=popup,
                title="Export Table Data",
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("Text Files", "*.txt")],
                initialfile=f"{title.replace(' ', '_')}_export.csv"
            )
            if filepath:
                try:
                    import csv
                    with open(filepath, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow(["Sr. No.", "Scheme / Gram Panchayat Name", "Last Data Receive Date"])
                        for k in tree.get_children(""):
                            writer.writerow(tree.item(k, "values"))
                    messagebox.showinfo("Success", f"Data exported successfully to:\n{filepath}", parent=popup)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to export data: {e}", parent=popup)

        copy_btn = ctk.CTkButton(btn_frame, text="📋 Copy Table", width=120, height=36, font=("Segoe UI", 12, "bold"), fg_color=CLR_CYAN, hover_color="#0284c7", command=copy_data)
        copy_btn.pack(side="left", padx=(0, 10))
        
        export_btn = ctk.CTkButton(btn_frame, text="💾 Export CSV", width=120, height=36, font=("Segoe UI", 12, "bold"), fg_color=CLR_GREEN, hover_color="#059669", command=download_data)
        export_btn.pack(side="left")
        
        close_btn = ctk.CTkButton(btn_frame, text="Close", width=100, height=36, font=("Segoe UI", 12, "bold"), fg_color="transparent", border_width=1, border_color=CLR_BORDER, text_color=CLR_DIM, command=popup.destroy)
        close_btn.pack(side="right")


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
        if hasattr(self, 'report_terminal'):
            try:
                self.report_terminal.delete("1.0", "end")
                self.report_terminal.insert("end", report_text)
            except Exception: pass
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

    def auto_fetch_jjm_count(self, force=False):
        """Lightweight HTTP fetch — cached for 2 minutes unless forced."""
        if not force and (time.time() - self._jjm_cache["timestamp"]) < 120:
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
                            
                            if not hasattr(self, "jjm_gp_times"):
                                self.jjm_gp_times = {}

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
                                                if len(c_) > 9 and c_[0].isdigit():
                                                    name = c_[6]
                                                    last_date = c_[9]
                                                    names.append(name)
                                                    self.jjm_gp_times[name] = last_date
                                            return sorted(names)
                                except Exception:
                                    pass
                                return []

                            self.safe_log_update("> [WEB] Deeply fetching per-scheme JJM breakdowns (may take a few seconds)...")
                            tot_list = fetch_list(agency_idx + 8)
                            live_list = fetch_list(agency_idx + 10)
                            not_recv_list = fetch_list(agency_idx + 11)
                            
                            leftover_list = sorted(list(set(tot_list) - set(live_list) - set(not_recv_list)))
                            
                            # Determine daily new JJM schemes
                            daily_new_jjm = []
                            if tot_list:
                                try:
                                    os.makedirs(self.watch_folder, exist_ok=True)
                                    baseline_path = os.path.join(self.watch_folder, "jjm_baseline.json")
                                    if not os.path.exists(baseline_path):
                                        with open(baseline_path, "w", encoding="utf-8") as f_base:
                                            json.dump(tot_list, f_base)
                                    else:
                                        with open(baseline_path, "r", encoding="utf-8") as f_base:
                                            baseline_list = json.load(f_base)
                                        if isinstance(baseline_list, list):
                                            daily_new_jjm = list(set(tot_list) - set(baseline_list))
                                except Exception as e_base:
                                    self.safe_log_update(f"⚠️ Could not process JJM baseline: {e_base}")

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
                                    "leftover": leftover_list,
                                    "new": sorted(daily_new_jjm)
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
                self.jjm_list_data["new"] = jjm_lists.get("new", [])

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
                
            new_jjm_count = len(self.jjm_list_data.get("new", []))
            new_jjm_text = ""
            if new_jjm_count > 0:
                joined_jjm_names = ", ".join(sorted(self.jjm_list_data["new"]))
                new_jjm_text = f"\nNewly Added Schemes in JJM- {new_jjm_count} ({joined_jjm_names})"
            
            report = f"JJM PORTAL LIVE: {jjm_live} | TOTAL: {jjm_total} | NOT REC: {jjm_not_recv} | MISSING: {jjm_leftover} | NEW ADDED: {new_jjm_count}\nSCADA TOTAL: {len(df)}\nSYNCED: {len(synced)}\nUNSYNCED: {len(not_synced)}\nNEW ADDED: {new_gp_count}\n\n"
            report += "✅ SYNCED LIST:\n" + ", ".join(synced[gp_col].astype(str).tolist()) + "\n\n"
            report += "❌ NOT SYNCED LIST:\n" + ", ".join(not_synced[gp_col].astype(str).tolist()) + "\n\n"
            if new_gp_count > 0:
                report += "⭐ NEWLY ADDED LIST:\n" + joined_names + "\n\n"
            if new_jjm_count > 0:
                report += "🌟 NEWLY ADDED IN JJM:\n" + joined_jjm_names
            
            greet = "Good Evening Sir," if datetime.now().hour >= 16 else ("Good Afternoon Sir," if datetime.now().hour >= 12 else "Good Morning Sir,")
            preview = f"Date: {datetime.today().strftime('%d.%m.%Y')}\n\n{greet}\nNo of schemes connected with SCADA- {len(synced)}\nNo of schemes Lives in JJM Portal- {jjm_live}{new_gp_text}{new_jjm_text}\n\nToday Schemes listed in SCADA- {len(df)}."
            
            self.last_analysis_msg = preview
            self.safe_report_update(report, preview)
            
            # --- Update UI Labels ---
            self.scada_gp_times = {}
            for _, row in df.iterrows():
                gp_name = str(row[gp_col]).strip()
                dt_val = row[dt_col]
                if pd.notna(dt_val):
                    dt_str = dt_val.strftime("%Y-%m-%d %H:%M")
                else:
                    dt_str = "N/A"
                self.scada_gp_times[gp_name] = dt_str

            self.scada_data["total"] = sorted(df[gp_col].dropna().astype(str).tolist())
            self.scada_data["synced"] = sorted(synced[gp_col].dropna().astype(str).tolist())
            self.scada_data["not_synced"] = sorted(not_synced[gp_col].dropna().astype(str).tolist())
            self.scada_data["new"] = sorted(daily_new_gps)
            
            # --- Update UI Labels ---
            self.after(0, lambda: self.jjm_total_lbl.configure(text=str(jjm_total)))
            self.after(0, lambda: self.jjm_live_lbl.configure(text=str(jjm_live)))
            self.after(0, lambda: self.jjm_not_recv_lbl.configure(text=str(jjm_not_recv)))
            self.after(0, lambda: self.jjm_leftover_lbl.configure(text=str(jjm_leftover)))
            self.after(0, lambda: self.jjm_new_lbl.configure(text=str(new_jjm_count)))
 
            self.after(0, lambda: self.scada_total_lbl.configure(text=str(len(self.scada_data["total"]))))
            self.after(0, lambda: self.scada_sync_lbl.configure(text=str(len(self.scada_data["synced"]))))
            self.after(0, lambda: self.scada_unsync_lbl.configure(text=str(len(self.scada_data["not_synced"]))))
            self.after(0, lambda: self.scada_new_lbl.configure(text=str(len(self.scada_data["new"]))))
            
            timestamp = datetime.now().strftime("%b %d - %I:%M %p")
            history_line = f"[+] Mapped: {timestamp} | Sync: {len(synced):03d} | Unsync: {len(not_synced):03d}"
            self.safe_history_update(history_line)
            
            # --- Export Live Data for Bot ---
            try:
                export_data = {
                    "jjm": {
                        "total": str(jjm_total),
                        "live": str(jjm_live),
                        "not_received": str(jjm_not_recv),
                        "leftover": str(jjm_leftover),
                        "new_count": str(new_jjm_count),
                        "new_list": self.jjm_list_data.get("new", []),
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

            # ── JJM PORTAL SUMMARY SHEET ──
            if hasattr(self, "jjm_list_data") and self.jjm_list_data:
                try:
                    ws_jjm = wb.create_sheet(title="JJM Portal Summary")
                    ws_jjm.cell(row=1, column=1, value="Metric").font = Font(bold=True)
                    ws_jjm.cell(row=1, column=2, value="Count").font = Font(bold=True)
                    
                    jjm_total = "0"
                    jjm_live = "0"
                    jjm_not_recv = "0"
                    jjm_leftover = "0"
                    if hasattr(self, "_jjm_cache") and "count" in self._jjm_cache:
                        c_dict = self._jjm_cache["count"]
                        if isinstance(c_dict, dict):
                            jjm_total = c_dict.get("total", "0")
                            jjm_live = c_dict.get("live", "0")
                            jjm_not_recv = c_dict.get("not_received", "0")
                            jjm_leftover = c_dict.get("leftover", "0")

                    metrics = [
                        ("Total JJM Schemes", jjm_total),
                        ("Live Connected", jjm_live),
                        ("Data Not Received", jjm_not_recv),
                        ("Off-Grid / Missing", jjm_leftover),
                        ("Newly Added Schemes", str(len(self.jjm_list_data.get("new", []))))
                    ]
                    for idx, (m, val) in enumerate(metrics, 2):
                        ws_jjm.cell(row=idx, column=1, value=m)
                        ws_jjm.cell(row=idx, column=2, value=val)
                    
                    ws_jjm.cell(row=8, column=1, value="TOTAL SCHEMES").font = Font(bold=True)
                    ws_jjm.cell(row=8, column=2, value="LIVE SCHEMES").font = Font(bold=True)
                    ws_jjm.cell(row=8, column=3, value="NOT RECEIVED").font = Font(bold=True)
                    ws_jjm.cell(row=8, column=4, value="OFF-GRID / MISSING").font = Font(bold=True)
                    ws_jjm.cell(row=8, column=5, value="NEWLY ADDED").font = Font(bold=True)
                    
                    tot_lst = self.jjm_list_data.get("total", [])
                    live_lst = self.jjm_list_data.get("live", [])
                    nr_lst = self.jjm_list_data.get("not_recv", [])
                    lo_lst = self.jjm_list_data.get("leftover", [])
                    new_lst = self.jjm_list_data.get("new", [])
                    
                    max_len = max(len(tot_lst), len(live_lst), len(nr_lst), len(lo_lst), len(new_lst))
                    for r in range(max_len):
                        t_val = tot_lst[r] if r < len(tot_lst) else ""
                        li_val = live_lst[r] if r < len(live_lst) else ""
                        nr_val = nr_lst[r] if r < len(nr_lst) else ""
                        lo_val = lo_lst[r] if r < len(lo_lst) else ""
                        new_val = new_lst[r] if r < len(new_lst) else ""
                        
                        ws_jjm.cell(row=9+r, column=1, value=t_val)
                        ws_jjm.cell(row=9+r, column=2, value=li_val)
                        ws_jjm.cell(row=9+r, column=3, value=nr_val)
                        ws_jjm.cell(row=9+r, column=4, value=lo_val)
                        ws_jjm.cell(row=9+r, column=5, value=new_val)
                except Exception as e_jjm:
                    self.safe_log_update(f"⚠️ Could not write JJM Portal sheet: {e_jjm}")

            wb.save(final_path)
            self.safe_log_update(f"✅ Final Matrix Report Saved: {final_path}")
            self.refresh_historical_dates()

            # Upload final matrix report to Control Tower server
            try:
                self.safe_log_update("> [PORTAL] Uploading report to Control Tower...")
                with open(final_path, 'rb') as f_upload:
                    files_payload = {'file': (final_filename, f_upload, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                    upload_resp = requests.post("http://devash.in/api/upload_report", files=files_payload, timeout=30)
                    if upload_resp.status_code == 200:
                        self.safe_log_update("✅ [PORTAL] Report uploaded successfully to Control Tower server.")
                    else:
                        self.safe_log_update(f"❌ [PORTAL] Upload failed (HTTP {upload_resp.status_code}): {upload_resp.text}")
            except Exception as e:
                self.safe_log_update(f"⚠️ Report upload failed: {e}")

        except Exception as e:
            self.safe_log_update(f"❌ Failed to generate matrix report: {str(e)}")

    # ==================================================
    # 📱 WHATSAPP ENGINE (RESTORED MANUAL METHOD)
    # ==================================================
    
    def _wait_for_message_delivery(self, driver, timeout=15):
        """Waits for the last message to be delivered (status changing to sent/delivered/read)."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                status_elements = driver.find_elements(By.CSS_SELECTOR, "span[aria-label], span[data-icon]")
                if status_elements:
                    last_el = status_elements[-1]
                    label = last_el.get_attribute("aria-label") or ""
                    icon = last_el.get_attribute("data-icon") or ""
                    
                    label_l = label.lower()
                    icon_l = icon.lower()
                    
                    if any(x in label_l for x in ["sent", "delivered", "read"]) or any(x in icon_l for x in ["check", "dblcheck"]):
                        return "sent"
                    elif "alert" in label_l or "failed" in label_l or "status-alert" in icon_l:
                        return "failed"
            except Exception:
                pass
            time.sleep(1)
        return "pending"

    def _is_logged_out(self, driver):
        """Checks if the WhatsApp Web page shows the QR code scan screen."""
        try:
            qr_canvas = driver.find_elements(By.CSS_SELECTOR, "canvas[aria-label*='Scan me'], div[data-ref]")
            if qr_canvas:
                return True
        except Exception:
            pass
        return False

    def show_whatsapp_error_prompt(self, title, message):
        """Displays an on-screen dialog blocking the thread until user resolves/resumes."""
        self.safe_log_update(f"\n[WA] ⚠️ ERROR: {message}")
        self.update()
        response = messagebox.askretrycancel(title, f"{message}\n\nClick 'Retry' once you have resolved this in Chrome, or 'Cancel' to abort.")
        return response

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
                    
                    retry_count = 0
                    success = False
                    
                    while retry_count < 3 and not success:
                        try:
                            # 1. Check if logged out
                            if self._is_logged_out(driver):
                                self.safe_log_update("[WA] ❌ Session logged out! Requesting user login...")
                                if self.show_whatsapp_error_prompt("WhatsApp Logged Out", "WhatsApp session has logged out. Please scan the QR code to log back in."):
                                    time.sleep(5)
                                    continue
                                else:
                                    raise Exception("User aborted broadcast due to logout.")
                                    
                            # 2. Open chat URL
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
                                if self._is_logged_out(driver):
                                    continue
                                self.safe_log_update(f"   ❌ Message box not found. Is {phone} on WhatsApp?")
                                break
                                
                            msg_box.click()
                            time.sleep(0.5)
                            
                            # ── TYPE MESSAGE ──
                            self.safe_log_update("   [WA] Injecting payload...")
                            for line in self.last_analysis_msg.split('\n'):
                                msg_box.send_keys(line)
                                ActionChains(driver).key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT).perform()
                                time.sleep(0.08)
                                
                            time.sleep(0.5)
                            msg_box.send_keys(Keys.ENTER)
                            
                            # ── WAIT FOR DELIVERY STATUS ──
                            status = self._wait_for_message_delivery(driver, timeout=15)
                            if status == "sent":
                                self.safe_log_update(f"   ✅ Sent to {name}!")
                                success = True
                                time.sleep(10)
                            elif status == "pending" or status == "failed":
                                retry_count += 1
                                self.safe_log_update(f"   ⚠️ Message stuck in '{status}' state. Refreshing browser (Attempt {retry_count}/3)...")
                                driver.refresh()
                                time.sleep(10)
                            else:
                                self.safe_log_update(f"   ✅ Sent to {name} (Status: assumed sent).")
                                success = True
                                time.sleep(10)
                                
                        except Exception as e:
                            retry_count += 1
                            self.safe_log_update(f"   ❌ Error (Attempt {retry_count}/3): {str(e)}")
                            if "user aborted" in str(e).lower():
                                raise e
                            time.sleep(5)
                            
                    if not success:
                        self.safe_log_update(f"   ❌ Failed to send message to {name} after multiple retries.")
                        if not self.show_whatsapp_error_prompt("WhatsApp Message Failed", f"Failed to deliver message to {name} ({phone}). WhatsApp might be stuck or logged out."):
                            self.safe_log_update("   [WA] Broadcast aborted by user.")
                            break

            except Exception as e:
                self.safe_log_update(f"❌ WhatsApp Engine Error: {str(e)}")
            finally:
                if driver:
                    driver.quit()
                    self.safe_log_update("\n[WA] Session closed.")

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
    def trigger_manual_jjm_pull(self): threading.Thread(target=self.pull_jjm_portal_data, daemon=True).start()
    def trigger_manual_send(self): threading.Thread(target=self.robot_whatsapp_blast, daemon=True).start()
    
    def pull_jjm_portal_data(self):
        self.safe_log_update("\n[SYS] Initiating manual JJM portal data pull...")
        jjm_data = self.auto_fetch_jjm_count(force=True)
        if isinstance(jjm_data, str) or not jjm_data or jjm_data.get("total") == "0":
            self.safe_log_update("❌ [JJM] Pull failed or returned empty data.")
            return
        
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
            self.jjm_list_data["new"] = jjm_lists.get("new", [])

        # Update UI Labels
        self.after(0, lambda: self.jjm_total_lbl.configure(text=str(jjm_total)))
        self.after(0, lambda: self.jjm_live_lbl.configure(text=str(jjm_live)))
        self.after(0, lambda: self.jjm_not_recv_lbl.configure(text=str(jjm_not_recv)))
        self.after(0, lambda: self.jjm_leftover_lbl.configure(text=str(jjm_leftover)))
        self.after(0, lambda: self.jjm_new_lbl.configure(text=str(len(self.jjm_list_data.get("new", [])))))
        
        timestamp = datetime.now().strftime("%b %d - %I:%M %p")
        self.safe_history_update(f"[+] JJM Pulled: {timestamp} | Live: {jjm_live} | Total: {jjm_total}")
        
        # Update export JSON
        try:
            export_path = os.path.join(self.watch_folder, "nexus_live_data.json")
            scada_part = {
                "total": str(len(self.scada_data.get("total", []))),
                "synced": str(len(self.scada_data.get("synced", []))),
                "unsynced": str(len(self.scada_data.get("not_synced", []))),
                "new_count": str(len(self.scada_data.get("new", []))),
                "new_list": self.scada_data.get("new", [])
            }
            if os.path.exists(export_path):
                try:
                    with open(export_path, "r") as f:
                        old_data = json.load(f)
                        if "scada" in old_data:
                            scada_part = old_data["scada"]
                except Exception:
                    pass
                    
            export_data = {
                "jjm": {
                    "total": str(jjm_total),
                    "live": str(jjm_live),
                    "not_received": str(jjm_not_recv),
                    "leftover": str(jjm_leftover),
                    "new_count": str(len(self.jjm_list_data.get("new", []))),
                    "new_list": self.jjm_list_data.get("new", []),
                    "_lists": self.jjm_list_data
                },
                "scada": scada_part,
                "timestamp": datetime.now().isoformat()
            }
            with open(export_path, "w") as f:
                json.dump(export_data, f)
            self.safe_log_update("[SYS] Live data JSON exported for bot (JJM pull only).")
        except Exception as e:
            self.safe_log_update(f"⚠️ Could not export live JSON: {e}")
            
        self.safe_log_update("✅ [JJM] JJM portal data pulled successfully.")
    
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