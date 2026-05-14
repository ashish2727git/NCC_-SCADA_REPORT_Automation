import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
import time
import requests
import urllib.request
import json

# --- GoDaddy API Credentials ---
GODADDY_AUTH = "sso-key hkHs3BfsbBKB_UmgfR9K9eSZGpkxVa8DLwB:M1cfoukoEQavEJUdpmXHgn"
DOMAIN = "devash.in"
CLUSTER = "nexus-cluster"
SERVICE = "nexus-control-tower-service"
REGION = "ap-south-1"

ADMIN_PWD = "nexus-admin-2026"

class NexusAdminControl(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Nexus Admin Control & Dashboard")
        self.geometry("600x650")
        self.configure(fg_color="#0f172a")
        
        # Center Window
        self.eval('tk::PlaceWindow . center')
        
        self.header = ctk.CTkLabel(self, text="⚡ NEXUS CONTROL TOWER", font=("Segoe UI", 24, "bold"), text_color="#3b82f6")
        self.header.pack(pady=(20, 10))

        # Tabs
        self.tabview = ctk.CTkTabview(self, width=550, height=550, fg_color="#1e293b", segmented_button_fg_color="#0f172a", segmented_button_selected_color="#3b82f6", segmented_button_selected_hover_color="#2563eb")
        self.tabview.pack(padx=20, pady=10)
        
        self.tab_infra = self.tabview.add("Infrastructure")
        self.tab_license = self.tabview.add("License Manager")
        self.tab_remote = self.tabview.add("Remote Control")
        self.tab_logs = self.tabview.add("Live Logs")

        self.setup_infra_tab()
        self.setup_license_tab()
        self.setup_remote_tab()
        self.setup_logs_tab()

        self.current_state = "UNKNOWN"
        self.active_ip = None
        self.polling_logs = False
        
        threading.Thread(target=self.check_status, daemon=True).start()

    # ================= INFRASTRUCTURE TAB =================
    def setup_infra_tab(self):
        self.status_frame = ctk.CTkFrame(self.tab_infra, fg_color="#0f172a", corner_radius=10)
        self.status_frame.pack(fill="x", padx=20, pady=20)

        self.status_lbl = ctk.CTkLabel(self.status_frame, text="Checking Status...", font=("Segoe UI", 18, "bold"), text_color="#cbd5e1")
        self.status_lbl.pack(pady=15)

        self.ip_lbl = ctk.CTkLabel(self.status_frame, text="IP: Unknown", font=("Consolas", 14), text_color="#64748b")
        self.ip_lbl.pack(pady=(0, 15))

        self.btn_toggle = ctk.CTkButton(self.tab_infra, text="...", font=("Segoe UI", 16, "bold"), height=50, command=self.toggle_server)
        self.btn_toggle.pack(fill="x", padx=20, pady=10)
        
        self.log_box = ctk.CTkTextbox(self.tab_infra, fg_color="#000000", text_color="#10b981", font=("Consolas", 11), height=150)
        self.log_box.pack(fill="both", expand=True, padx=20, pady=20)

    def log(self, msg):
        self.log_box.insert("end", f"> {msg}\n")
        self.log_box.see("end")

    def run_cmd(self, cmd):
        try:
            result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return result.stdout.strip()
        except Exception as e:
            return str(e)

    def update_dns(self, ip):
        self.log(f"Updating GoDaddy DNS to {ip}...")
        cmd = f"""
        $headers = @{{ "Authorization" = "{GODADDY_AUTH}"; "Content-Type" = "application/json" }};
        $body = '[{{"data":"{ip}","ttl":600}}]';
        Invoke-RestMethod -Method Put -Uri "https://api.godaddy.com/v1/domains/{DOMAIN}/records/A/@" -Headers $headers -Body $body
        """
        self.run_cmd(cmd)
        self.log("✅ DNS successfully mapped!")

    def check_status(self):
        self.btn_toggle.configure(state="disabled", text="Checking AWS...")
        self.log("Fetching ECS container status...")
        count = self.run_cmd(f"aws ecs describe-services --cluster {CLUSTER} --services {SERVICE} --region {REGION} --query 'services[0].runningCount' --output text")
        
        if count == "1":
            self.current_state = "RUNNING"
            self.status_lbl.configure(text="● SERVER IS LIVE", text_color="#10b981")
            self.btn_toggle.configure(text="🛑 STOP SERVER", fg_color="#ef4444", hover_color="#dc2626", state="normal")
            
            task_arn = self.run_cmd(f"aws ecs list-tasks --cluster {CLUSTER} --service-name {SERVICE} --region {REGION} --query 'taskArns[0]' --output text")
            if task_arn and task_arn != "None":
                eni = self.run_cmd(f"aws ecs describe-tasks --cluster {CLUSTER} --tasks {task_arn} --region {REGION} --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text")
                ip = self.run_cmd(f"aws ec2 describe-network-interfaces --network-interface-ids {eni} --query 'NetworkInterfaces[0].Association.PublicIp' --output text --region {REGION}")
                self.active_ip = ip
                self.ip_lbl.configure(text=f"IP: {ip}")
                self.log(f"Found active IP: {ip}")
        else:
            self.current_state = "STOPPED"
            self.active_ip = None
            self.status_lbl.configure(text="○ SERVER IS OFFLINE", text_color="#ef4444")
            self.ip_lbl.configure(text="IP: None (AWS Zero Cost)")
            self.btn_toggle.configure(text="🚀 START SERVER", fg_color="#10b981", hover_color="#059669", state="normal")
            self.log("Server is currently stopped.")

    def toggle_server(self):
        if self.current_state == "RUNNING":
            threading.Thread(target=self.stop_server_task, daemon=True).start()
        elif self.current_state == "STOPPED":
            threading.Thread(target=self.start_server_task, daemon=True).start()

    def stop_server_task(self):
        self.btn_toggle.configure(state="disabled", text="Stopping AWS...")
        self.log("Sending shutdown command to AWS ECS...")
        self.run_cmd(f"aws ecs update-service --cluster {CLUSTER} --service {SERVICE} --desired-count 0 --region {REGION}")
        self.log("Instances terminated. Billing paused.")
        self.check_status()

    def start_server_task(self):
        self.btn_toggle.configure(state="disabled", text="Booting AWS...")
        self.log("Requesting new container from AWS...")
        self.run_cmd(f"aws ecs update-service --cluster {CLUSTER} --service {SERVICE} --desired-count 1 --region {REGION}")
        self.log("Waiting 30 seconds for boot sequence...")
        time.sleep(30)
        
        for _ in range(10):
            task_arn = self.run_cmd(f"aws ecs list-tasks --cluster {CLUSTER} --service-name {SERVICE} --region {REGION} --query 'taskArns[0]' --output text")
            if task_arn and task_arn != "None":
                eni = self.run_cmd(f"aws ecs describe-tasks --cluster {CLUSTER} --tasks {task_arn} --region {REGION} --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text")
                ip = self.run_cmd(f"aws ec2 describe-network-interfaces --network-interface-ids {eni} --query 'NetworkInterfaces[0].Association.PublicIp' --output text --region {REGION}")
                if ip and ip.strip() and "None" not in ip:
                    self.active_ip = ip
                    self.ip_lbl.configure(text=f"IP: {ip}")
                    self.log(f"New container launched at {ip}")
                    self.update_dns(ip)
                    self.check_status()
                    return
            self.log("Waiting for IP allocation...")
            time.sleep(10)
        self.check_status()

    # ================= LICENSE MANAGER TAB =================
    def setup_license_tab(self):
        ctk.CTkLabel(self.tab_license, text="Generate New License", font=("Segoe UI", 16, "bold"), text_color="#3b82f6").pack(pady=(15,5))
        
        self.client_entry = ctk.CTkEntry(self.tab_license, placeholder_text="Client Name (e.g. Ravi Kumar)", width=300)
        self.client_entry.pack(pady=10)
        
        self.custom_key_entry = ctk.CTkEntry(self.tab_license, placeholder_text="Custom Key (Optional)", width=300)
        self.custom_key_entry.pack(pady=10)

        ctk.CTkButton(self.tab_license, text="⚡ Generate Key", command=self.generate_key, fg_color="#10b981", hover_color="#059669").pack(pady=10)
        
        self.result_key_lbl = ctk.CTkLabel(self.tab_license, text="", font=("Consolas", 18, "bold"), text_color="#f59e0b")
        self.result_key_lbl.pack(pady=10)

        ctk.CTkLabel(self.tab_license, text="Revoke License", font=("Segoe UI", 16, "bold"), text_color="#ef4444").pack(pady=(30,5))
        self.revoke_entry = ctk.CTkEntry(self.tab_license, placeholder_text="License Key to Block", width=300)
        self.revoke_entry.pack(pady=10)
        ctk.CTkButton(self.tab_license, text="🚫 Revoke Key", command=self.revoke_key, fg_color="#ef4444", hover_color="#dc2626").pack(pady=10)

    def generate_key(self):
        if self.current_state != "RUNNING":
            messagebox.showerror("Error", "Server must be ONLINE to generate keys.")
            return
        
        client = self.client_entry.get().strip()
        if not client:
            messagebox.showwarning("Warning", "Please enter a client name.")
            return

        key = self.custom_key_entry.get().strip()
        if not key:
            import random, string
            part = lambda: ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            key = f"NEXUS-{part()}-{part()}-{part()}"

        try:
            r = requests.post(
                f"http://{self.active_ip}/api/admin/add_license", 
                json={"key": key, "client_name": client, "admin_secret": ADMIN_PWD},
                timeout=5
            )
            if r.status_code == 200:
                self.result_key_lbl.configure(text=key)
                self.client_entry.delete(0, "end")
                self.custom_key_entry.delete(0, "end")
                # Automatically copy to clipboard
                self.clipboard_clear()
                self.clipboard_append(key)
                messagebox.showinfo("Success", f"Key registered and copied to clipboard!\n\n{key}")
            else:
                messagebox.showerror("Server Error", r.text)
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to server: {e}")

    def revoke_key(self):
        if self.current_state != "RUNNING":
            messagebox.showerror("Error", "Server must be ONLINE to revoke keys.")
            return
        
        key = self.revoke_entry.get().strip()
        if not key:
            messagebox.showwarning("Warning", "Enter a key to revoke.")
            return
        
        if not messagebox.askyesno("Confirm", f"Are you sure you want to permanently block this key?\n\n{key}"):
            return

        try:
            r = requests.post(
                f"http://{self.active_ip}/api/admin/revoke_license", 
                json={"key": key, "admin_secret": ADMIN_PWD},
                timeout=5
            )
            if r.status_code == 200:
                messagebox.showinfo("Success", f"Key {key} successfully revoked.")
                self.revoke_entry.delete(0, "end")
            else:
                messagebox.showerror("Server Error", r.text)
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to server: {e}")

    # ================= REMOTE CONTROL TAB =================
    def setup_remote_tab(self):
        ctk.CTkLabel(self.tab_remote, text="Target Client System", font=("Segoe UI", 16, "bold"), text_color="#3b82f6").pack(pady=(20,5))
        
        # Dropdown to select client HWID
        self.client_dropdown = ctk.CTkComboBox(self.tab_remote, values=["Refresh to load clients..."], width=350, font=("Segoe UI", 14))
        self.client_dropdown.pack(pady=10)
        
        ctk.CTkButton(self.tab_remote, text="🔄 Refresh Clients", width=200, command=self.load_active_clients, fg_color="#475569", hover_color="#334155").pack(pady=5)
        
        ctk.CTkLabel(self.tab_remote, text="Remote Actions", font=("Segoe UI", 16, "bold"), text_color="#f59e0b").pack(pady=(40,10))
        
        action_frame = ctk.CTkFrame(self.tab_remote, fg_color="transparent")
        action_frame.pack(pady=10)
        
        ctk.CTkButton(action_frame, text="📥 Trigger PULL DATA", width=160, height=50, font=("Segoe UI", 13, "bold"), fg_color="#10b981", hover_color="#059669", command=lambda: self.issue_remote_cmd("PULL_DATA")).pack(side="left", padx=10)
        ctk.CTkButton(action_frame, text="📤 Trigger BROADCAST", width=160, height=50, font=("Segoe UI", 13, "bold"), fg_color="#8b5cf6", hover_color="#7c3aed", command=lambda: self.issue_remote_cmd("BROADCAST")).pack(side="left", padx=10)

    def load_active_clients(self):
        if self.current_state != "RUNNING" or not self.active_ip:
            messagebox.showerror("Error", "Server must be ONLINE.")
            return
        try:
            r = requests.get(f"http://{self.active_ip}/api/admin/list_licenses", timeout=5)
            if r.status_code == 200:
                clients = [f"{c['client_name']} ({c['hwid']})" for c in r.json() if c['is_active'] and c['hwid']]
                if clients:
                    self.client_dropdown.configure(values=clients)
                    self.client_dropdown.set(clients[0])
                else:
                    self.client_dropdown.configure(values=["No bound clients found."])
                    self.client_dropdown.set("No bound clients found.")
            else:
                messagebox.showerror("Server Error", r.text)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def issue_remote_cmd(self, cmd):
        if self.current_state != "RUNNING" or not self.active_ip:
            messagebox.showerror("Error", "Server must be ONLINE.")
            return
        
        selection = self.client_dropdown.get()
        if not selection or "(" not in selection:
            messagebox.showwarning("Warning", "Please select a valid client first.")
            return
            
        hwid = selection.split("(")[-1].replace(")", "")
        
        if not messagebox.askyesno("Confirm", f"Are you sure you want to send '{cmd}' to {selection.split('(')[0].strip()}?"):
            return
            
        try:
            r = requests.post(f"http://{self.active_ip}/api/admin/issue_command", 
                json={"hwid": hwid, "command": cmd, "admin_secret": ADMIN_PWD}, timeout=5)
            if r.status_code == 200:
                messagebox.showinfo("Success", f"Command '{cmd}' successfully queued for {selection.split('(')[0].strip()}!")
            else:
                messagebox.showerror("Error", r.text)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= LOGS TAB =================
    def setup_logs_tab(self):
        self.server_log_box = ctk.CTkTextbox(self.tab_logs, fg_color="#000000", text_color="#22c55e", font=("Consolas", 12))
        self.server_log_box.pack(fill="both", expand=True, padx=10, pady=10)
        
        btn_frame = ctk.CTkFrame(self.tab_logs, fg_color="transparent")
        btn_frame.pack(fill="x", pady=5, padx=10)
        
        self.log_btn = ctk.CTkButton(btn_frame, text="▶ Start Live Polling", command=self.toggle_log_polling)
        self.log_btn.pack(side="left")

    def toggle_log_polling(self):
        self.polling_logs = not self.polling_logs
        if self.polling_logs:
            self.log_btn.configure(text="⏹ Stop Polling", fg_color="#ef4444", hover_color="#dc2626")
            threading.Thread(target=self.poll_logs_loop, daemon=True).start()
        else:
            self.log_btn.configure(text="▶ Start Live Polling", fg_color="#3b82f6", hover_color="#2563eb")

    def poll_logs_loop(self):
        while self.polling_logs:
            if self.current_state == "RUNNING":
                try:
                    r = requests.post(
                        f"http://{self.active_ip}/api/admin/logs", 
                        json={"key": "", "admin_secret": ADMIN_PWD},
                        timeout=3
                    )
                    if r.status_code == 200:
                        logs = r.json().get("logs", "")
                        self.server_log_box.delete("0.0", "end")
                        self.server_log_box.insert("end", logs)
                        self.server_log_box.see("end")
                except Exception:
                    pass
            time.sleep(3)

if __name__ == "__main__":
    app = NexusAdminControl()
    app.mainloop()
