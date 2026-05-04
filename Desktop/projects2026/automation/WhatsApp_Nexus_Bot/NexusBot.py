"""
NexusBot — Telegram Bot (Official API, 100% Free)
===================================================
Setup (one-time, 30 seconds):
  1. Open Telegram → search @BotFather → send /newbot
  2. Follow prompts → BotFather gives you a TOKEN (looks like 123456:ABCdef...)
  3. Paste the token below → click START BOT
  4. Share your bot link (t.me/YourBotName) with site engineers
"""

import os, re, glob, time, threading, json
from datetime import datetime
import requests, urllib3, pandas as pd
from bs4 import BeautifulSoup
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog

urllib3.disable_warnings()

TG_BASE   = "https://api.telegram.org/bot"
CRED_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_credentials.json")

C_BG    = "#0f172a"
C_CARD  = "#1e293b"
C_BORD  = "#334155"
C_CYAN  = "#38bdf8"
C_GREEN = "#34d399"
C_GOLD  = "#fbbf24"
C_RED   = "#f87171"
C_TEXT  = "#f1f5f9"
C_DIM   = "#94a3b8"


class NexusBotApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title("NEXUS SYNC | Telegram Auto-Bot")
        self.geometry("1050x650")
        self.configure(fg_color=C_BG)

        self.bot_running  = False
        self.token_var    = tk.StringVar()
        self.offset       = 0
        self.watch_folder = self._get_workspace()

        self._load_creds()
        self._build_ui()
        self.log("[SYS] NexusBot Telegram Mode Initialized.")
        self.log(f"[SYS] Workspace: {self.watch_folder}")
        self.log("[SYS] Get your bot token from @BotFather on Telegram.")

    # ─── workspace ────────────────────────────────────────────────────────────
    def _get_workspace(self):
        cfg = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            ".nexus_workspace_path"
        )
        if os.path.exists(cfg):
            with open(cfg) as f:
                d = f.read().strip()
            if d and os.path.exists(d):
                return d
        return os.getcwd()

    # ─── credentials ──────────────────────────────────────────────────────────
    def _load_creds(self):
        if os.path.exists(CRED_FILE):
            try:
                with open(CRED_FILE) as f:
                    self.token_var.set(json.load(f).get("tg_token", ""))
            except Exception:
                pass

    def _save_creds(self):
        with open(CRED_FILE, "w") as f:
            json.dump({"tg_token": self.token_var.get().strip()}, f)

    # ─── UI ───────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # sidebar
        side = ctk.CTkFrame(self, width=295, fg_color=C_CARD,
                             border_width=1, border_color=C_BORD, corner_radius=0)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        ctk.CTkLabel(side, text="⚡ NEXUS BOT",
                     font=("Segoe UI", 24, "bold"), text_color=C_CYAN).pack(pady=(25, 3))
        ctk.CTkLabel(side, text="TELEGRAM  •  API MODE",
                     font=("Segoe UI", 10), text_color=C_DIM).pack(pady=(0, 20))

        frm = ctk.CTkFrame(side, fg_color="transparent")
        frm.pack(fill="x", padx=18)

        ctk.CTkLabel(frm, text="Bot Token  (from @BotFather)",
                     font=("Segoe UI", 11, "bold"), text_color=C_DIM).pack(anchor="w")
        self.token_entry = ctk.CTkEntry(
            frm, textvariable=self.token_var,
            placeholder_text="123456:ABCdef...",
            height=38, fg_color=C_BG, border_color=C_BORD,
            text_color=C_TEXT, show="*"
        )
        self.token_entry.pack(fill="x", pady=(3, 15))

        self.start_btn = ctk.CTkButton(
            frm, text="▶  START BOT", height=42,
            fg_color="#166534", hover_color=C_GREEN,
            font=("Segoe UI", 13, "bold"), command=self.start_bot
        )
        self.start_btn.pack(fill="x", pady=(0, 8))

        self.stop_btn = ctk.CTkButton(
            frm, text="■  STOP BOT", height=42,
            fg_color="#7f1d1d", hover_color=C_RED,
            font=("Segoe UI", 13, "bold"),
            command=self.stop_bot, state="disabled"
        )
        self.stop_btn.pack(fill="x")

        # SCADA folder picker
        ctk.CTkFrame(frm, height=1, fg_color=C_BORD).pack(fill="x", pady=12)
        ctk.CTkLabel(frm, text="SCADA Data Folder",
                     font=("Segoe UI", 11, "bold"), text_color=C_DIM).pack(anchor="w")
        self.folder_lbl = ctk.CTkLabel(
            frm, text=self.watch_folder, font=("Segoe UI", 9),
            text_color=C_GOLD, wraplength=240, justify="left"
        )
        self.folder_lbl.pack(anchor="w", pady=(2, 6))
        ctk.CTkButton(
            frm, text="📁  Browse Folder", height=34,
            fg_color="transparent", border_width=1, border_color=C_BORD,
            font=("Segoe UI", 11), text_color=C_CYAN,
            command=self._browse_folder
        ).pack(fill="x")

        self.status_lbl = ctk.CTkLabel(
            side, text="● OFFLINE",
            font=("Segoe UI", 12, "bold"), text_color=C_RED
        )
        self.status_lbl.pack(pady=18)

        # divider
        ctk.CTkFrame(side, height=1, fg_color=C_BORD).pack(fill="x", padx=15, pady=5)

        # commands reference
        cmds_txt = (
            "Bot Commands:\n"
            "  hi / hello / menu  →  Main Menu\n"
            "  1  →  📊 Full Status Summary scada and jjm \n"
            "  2  →  ✅ Live Connected List in jjm\n"
            "  3  →  ⚠️ Not Connected List in jjm \n"
            "  4  →  🚨 Off-Grid Schemes in jjm \n"
            "  5  →  ⭐ Newly Added Schemes in scada "
        )
        ctk.CTkLabel(side, text=cmds_txt, font=("Consolas", 10),
                     text_color=C_DIM, justify="left").pack(padx=18, pady=10, anchor="w")

        ctk.CTkLabel(side,
                     text="Developed by Ashish Kumar",
                     font=("Segoe UI", 9, "italic"),
                     text_color=C_DIM).pack(side="bottom", pady=12)

        # terminal
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        hdr = ctk.CTkFrame(main, fg_color=C_CARD,
                            border_width=1, border_color=C_BORD, height=44)
        hdr.pack(fill="x", pady=(0, 10))
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="📡  LIVE BOT EVENT TERMINAL",
                     font=("Segoe UI", 13, "bold"), text_color=C_CYAN).pack(
            side="left", padx=15, pady=10)

        log_frm = ctk.CTkFrame(main, fg_color=C_CARD,
                                border_width=1, border_color=C_BORD)
        log_frm.pack(fill="both", expand=True)
        self.terminal = ctk.CTkTextbox(
            log_frm, fg_color="#0d1117",
            text_color="#a3e635", font=("Consolas", 13)
        )
        self.terminal.pack(fill="both", expand=True, padx=10, pady=10)

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select SCADA Excel Data Folder")
        if folder:
            self.watch_folder = folder
            self.folder_lbl.configure(text=folder)
            self.log(f"[SYS] SCADA folder updated: {folder}")
            # list xlsx files found
            files = [f for f in glob.glob(os.path.join(folder, '*.xlsx'))
                     if not os.path.basename(f).startswith("Final_Daily_Report")]
            self.log(f"[SYS] Found {len(files)} Excel file(s): {[os.path.basename(f) for f in files]}")

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.after(0, lambda: self._append(f"[{ts}] {msg}"))

    def _append(self, msg):
        self.terminal.insert("end", msg + "\n")
        self.terminal.see("end")

    # ─── start / stop ─────────────────────────────────────────────────────────
    def start_bot(self):
        tok = self.token_var.get().strip()
        if not tok:
            self.log("❌ Paste your Bot Token first!")
            return
        # verify token
        try:
            r = requests.get(f"{TG_BASE}{tok}/getMe", timeout=8)
            if r.status_code != 200 or not r.json().get("ok"):
                self.log("❌ Invalid token. Check and retry.")
                return
            bot_name = r.json()["result"]["username"]
            self.log(f"✅ Connected to @{bot_name}")
        except Exception as e:
            self.log(f"❌ Connection failed: {e}")
            return

        self._save_creds()
        self.offset      = 0
        self.bot_running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_lbl.configure(text="● ONLINE", text_color=C_GREEN)
        self.log("[BOT] Polling for messages every 2 seconds...")
        threading.Thread(target=self._poll, args=(tok,), daemon=True).start()

    def stop_bot(self):
        self.bot_running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_lbl.configure(text="● OFFLINE", text_color=C_RED)
        self.log("[BOT] Stopped.")

    # ─── Telegram polling ─────────────────────────────────────────────────────
    def _poll(self, tok):
        while self.bot_running:
            try:
                r = requests.get(
                    f"{TG_BASE}{tok}/getUpdates",
                    params={"offset": self.offset, "timeout": 10},
                    timeout=15
                )
                if r.status_code == 200:
                    data = r.json()
                    for update in data.get("result", []):
                        self.offset = update["update_id"] + 1
                        msg = update.get("message") or update.get("channel_post")
                        if msg and "text" in msg:
                            chat_id  = msg["chat"]["id"]
                            username = msg.get("from", {}).get("first_name", "User")
                            text     = msg["text"].strip()
                            cmd      = text.upper().lstrip("/")
                            self.log(f"[{username}] → '{text}'")
                            reply = self._build_reply(cmd)
                            if reply:
                                self._send(tok, chat_id, reply)
            except Exception as ex:
                self.log(f"[Poll error] {str(ex)[:100]}")
            time.sleep(2)

    def _send(self, tok, chat_id, text):
        try:
            r = requests.post(
                f"{TG_BASE}{tok}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
                timeout=15
            )
            if r.status_code == 200:
                self.log("[BOT] ✅ Reply sent.")
            else:
                self.log(f"[BOT] Send failed {r.status_code}: {r.text[:60]}")
        except Exception as e:
            self.log(f"[BOT] Send error: {e}")

    # ─── reply builder ────────────────────────────────────────────────────────
    def _build_reply(self, cmd):
        h = datetime.now().hour
        greet = "Good Evening" if h >= 16 else ("Good Afternoon" if h >= 12 else "Good Morning")

        if cmd in ["HI", "HELLO", "MENU", "STATUS", "HELP",
                   "START", "GET DATA", "/START"]:
            return (
                f"{greet}! 👋\n"
                f"Welcome to <b>Nexus Sync — JJM Sitapur</b>\n"
                f"Automated service by <b>Ashish Kumar</b>\n\n"
                f"🤖 <b>Reply with a Number:</b>\n\n"
                f"<b>1</b> — 📊 Full Status Summary (JJM + SCADA)\n"
                f"<b>2</b> — ✅ Live Connected Schemes List\n"
                f"<b>3</b> — ⚠️ Not Connected (Not Recv) List\n"
                f"<b>4</b> — 🚨 Off-Grid / Missing Schemes List\n"
                f"<b>5</b> — ⭐ Newly Added SCADA Schemes\n\n"
                f"<i>Data fetched live at time of request</i> ✅"
            )

        if cmd == "1":
            self.log("[BOT] Building SCADA + JJM summary...")
            s = self._scada()
            j = self._jjm()
            if s and j:
                missing = j.get('leftover', 0)
                nr = j.get('not_received', 0)
                sn = s.get('new_count', 0)
                return (
                    f"📈 <b>FULL DAILY STATUS REPORT</b>\n"
                    f"📅 {datetime.now().strftime('%d-%m-%Y %I:%M %p')}\n\n"
                    f"🔵 <b>JJM PORTAL</b>\n"
                    f"  Total Integrated : {j['total']}\n"
                    f"  Live Connected   : {j['live']}\n"
                    f"  Not Receiving    : {nr}\n"
                    f"  Off-Grid/Missing : {missing}\n\n"
                    f"🟢 <b>SCADA</b>\n"
                    f"  Total Schemes : {s['total']}\n"
                    f"  Synced Today  : {s['synced']}\n"
                    f"  Not Synced    : {s['unsynced']}\n"
                    f"  Newly Added   : {sn}"
                )
            return "❌ Could not fetch data from server."

        if cmd == "2":
            self.log("[BOT] Fetching live connected schemes...")
            j = self._jjm()
            if j:
                lst = j.get('_lists', {}).get('live', [])
                if lst:
                    lines = "\n".join(f"{i+1}. {x}" for i, x in enumerate(lst))
                    return f"✅ <b>LIVE CONNECTED (Count: {len(lst)})</b>\n{lines}"
                return "❌ No live connected schemes found."
            return "❌ JJM portal data unavailable."

        if cmd == "3":
            self.log("[BOT] Fetching not connected schemes...")
            j = self._jjm()
            if j:
                lst = j.get('_lists', {}).get('not_received', [])
                if lst:
                    lines = "\n".join(f"{i+1}. {x}" for i, x in enumerate(lst))
                    return f"⚠️ <b>NOT CONNECTED (Count: {len(lst)})</b>\n{lines}"
                return "❌ No 'Not Receiving' schemes found."
            return "❌ JJM portal data unavailable."

        if cmd == "4":
            self.log("[BOT] Fetching JJM off-grid schemes...")
            j = self._jjm()
            if j:
                lo = j.get('_lists', {}).get('leftover', [])
                if lo:
                    lines = "\n".join(f"{i+1}. {x}" for i, x in enumerate(lo))
                    return f"🚨 <b>OFF-GRID / MISSING (Count: {len(lo)})</b>\n{lines}"
                return "❌ No off-grid schemes found."
            return "❌ JJM portal fetch failed."

        if cmd == "5":
            self.log("[BOT] Fetching newly added SCADA schemes...")
            s = self._scada()
            if s:
                n = s.get('new_list', [])
                if n:
                    lines = "\n".join(f"{i+1}. {x}" for i, x in enumerate(n))
                    return f"⭐ <b>NEWLY ADDED (Count: {len(n)})</b>\n{lines}"
                return "⭐ No new schemes added today yet."
            return "❌ SCADA data unavailable."

        return None

    def _read_live_data(self):
        try:
            path = os.path.join(self.watch_folder, "nexus_live_data.json")
            if os.path.exists(path):
                with open(path, "r") as f:
                    return json.load(f)
        except Exception as e:
            self.log(f"[SYS] Error reading live data JSON: {e}")
        return None

    def _jjm(self):
        data = self._read_live_data()
        if data and "jjm" in data:
            return data["jjm"]
        return None

    def _scada(self):
        data = self._read_live_data()
        if data and "scada" in data:
            return data["scada"]
        return None


if __name__ == "__main__":
    app = NexusBotApp()
    app.mainloop()
