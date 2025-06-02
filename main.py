import customtkinter as ctk
import subprocess
import threading
import json
import os
import sys
from pathlib import Path
import tempfile
import signal
import psutil
from tkinter import messagebox, filedialog, simpledialog
import webbrowser
from ss_parser import decode_ss_link

class SocksicleApp:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        self.base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        theme_path = os.path.join(self.base_dir, "dark-violet.json")
        ctk.set_default_color_theme(theme_path)
        self.root = ctk.CTk()
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)
        self.root.title("Socksicle")
        self.root.geometry("480x550")
        icon_path = os.path.join(os.path.dirname(sys.argv[0]), "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass
        self.root.resizable(False, False)
        self.ss_process = None
        self.ss_config_file = None
        self.is_connected = False
        self.settings = {
            "server": "",
            "server_port": 8388,
            "local_address": "127.0.0.1",
            "local_port": 1080,
            "password": "",
            "method": "aes-256-gcm",
            "timeout": 300,
            "ss_local_path": "ss-local.exe",
            "servers": []
        }
        self.load_settings()
        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        title_label = ctk.CTkLabel(
            self.root, 
            text="🧊 Socksicle", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=15)
        main_frame = ctk.CTkScrollableFrame(self.root, width=430, height=350)
        main_frame.pack(pady=10, padx=25, fill="both", expand=True)
        import_frame = ctk.CTkFrame(main_frame)
        import_frame.pack(pady=5, padx=10, fill="x")
        ctk.CTkLabel(import_frame, text="Server Management", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=8)
        import_button_frame = ctk.CTkFrame(import_frame, fg_color="transparent")
        import_button_frame.pack(pady=(0, 8), padx=15, fill="x")
        self.import_button = ctk.CTkButton(
            import_button_frame, 
            text="📥 Add server (ss://)", 
            height=32,
            command=self.import_ss_server
        )
        self.import_button.pack(side="left", fill="x", expand=True)
        self.manage_button = ctk.CTkButton(
            import_button_frame, 
            text="📋 Manage", 
            width=100,
            height=32,
            command=self.manage_servers
        )
        self.manage_button.pack(side="right", padx=(8, 0))
        server_frame = ctk.CTkFrame(main_frame)
        server_frame.pack(pady=5, padx=10, fill="x")
        ctk.CTkLabel(server_frame, text="Server Settings", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=8)
        fields_frame = ctk.CTkFrame(server_frame, fg_color="transparent")
        fields_frame.pack(pady=(0, 8), padx=15, fill="x")
        left_col = ctk.CTkFrame(fields_frame, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 5))
        ctk.CTkLabel(left_col, text="Server:", anchor="w").pack(fill="x")
        self.server_entry = ctk.CTkEntry(left_col, height=28, placeholder_text="example.com")
        self.server_entry.pack(fill="x", pady=(0, 8))
        self.server_entry.insert(0, self.settings["server"])
        ctk.CTkLabel(left_col, text="Password:", anchor="w").pack(fill="x")
        self.password_entry = ctk.CTkEntry(left_col, height=28, show="*", placeholder_text="password")
        self.password_entry.pack(fill="x", pady=(0, 8))
        self.password_entry.insert(0, self.settings["password"])
        ctk.CTkLabel(left_col, text="Local port:", anchor="w").pack(fill="x")
        self.local_port_entry = ctk.CTkEntry(left_col, height=28, placeholder_text="1080")
        self.local_port_entry.pack(fill="x")
        self.local_port_entry.insert(0, str(self.settings["local_port"]))
        right_col = ctk.CTkFrame(fields_frame, fg_color="transparent")
        right_col.pack(side="right", fill="both", expand=True, padx=(5, 0))
        ctk.CTkLabel(right_col, text="Port:", anchor="w").pack(fill="x")
        self.server_port_entry = ctk.CTkEntry(right_col, height=28, placeholder_text="8388")
        self.server_port_entry.pack(fill="x", pady=(0, 8))
        self.server_port_entry.insert(0, str(self.settings["server_port"]))
        ctk.CTkLabel(right_col, text="Method:", anchor="w").pack(fill="x")
        self.method_combobox = ctk.CTkComboBox(
            right_col, 
            height=28,
            values=["aes-256-gcm", "aes-192-gcm", "aes-128-gcm", "chacha20-ietf-poly1305"]
        )
        self.method_combobox.pack(fill="x", pady=(0, 8))
        self.method_combobox.set(self.settings["method"])
        ctk.CTkLabel(right_col, text="Path to ss-local:", anchor="w").pack(fill="x")
        path_frame = ctk.CTkFrame(right_col, fg_color="transparent")
        path_frame.pack(fill="x")
        self.ss_path_entry = ctk.CTkEntry(path_frame, height=28, placeholder_text="ss-local.exe")
        self.ss_path_entry.pack(side="left", fill="x", expand=True)
        self.ss_path_entry.insert(0, self.settings["ss_local_path"])
        browse_btn = ctk.CTkButton(path_frame, text="...", width=28, height=28, command=self.browse_ss_local)
        browse_btn.pack(side="right", padx=(5, 0))
        self.status_frame = ctk.CTkFrame(self.root)
        self.status_frame.pack(pady=8, padx=25, fill="x")
        self.status_label = ctk.CTkLabel(
            self.status_frame, 
            text="● Disconnected", 
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="red"
        )
        self.status_label.pack(pady=8)
        button_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        button_frame.pack(pady=8, padx=25, fill="x")
        self.connect_button = ctk.CTkButton(
            button_frame, 
            text="🔌 Connect", 
            font=ctk.CTkFont(size=13, weight="bold"),
            height=35,
            command=self.toggle_connection
        )
        self.connect_button.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.test_button = ctk.CTkButton(
            button_frame, 
            text="🧪 Test", 
            width=80,
            height=35,
            command=self.test_connection
        )
        self.test_button.pack(side="right", padx=(5, 0))
    
    def import_ss_server(self):
        ss_link = simpledialog.askstring(
            "Import server", 
            "Paste ss:// link:",
            parent=self.root
        )
        if not ss_link:
            return
        server_config = decode_ss_link(ss_link.strip())
        if not server_config:
            messagebox.showerror("Error", "Invalid ss:// link format")
            return
        self.server_entry.delete(0, "end")
        self.server_entry.insert(0, server_config['server'])
        self.server_port_entry.delete(0, "end")
        self.server_port_entry.insert(0, str(server_config['port']))
        self.password_entry.delete(0, "end")
        self.password_entry.insert(0, server_config['password'])
        self.method_combobox.set(server_config['method'])
        server_name = server_config.get('tag', f"{server_config['server']}:{server_config['port']}")
        server_data = {
            "name": server_name,
            "server": server_config['server'],
            "port": server_config['port'],
            "password": server_config['password'],
            "method": server_config['method']
        }
        existing = next((s for s in self.settings["servers"] if s["server"] == server_config['server'] and s["port"] == server_config['port']), None)
        if not existing:
            self.settings["servers"].append(server_data)
            self.save_settings()
        messagebox.showinfo("Success", f"Server '{server_name}' added and set")
    
    def manage_servers(self):
        if not self.settings["servers"]:
            messagebox.showinfo("Info", "No saved servers")
            return
        manage_window = ctk.CTkToplevel(self.root)
        manage_window.title("Manage servers")
        manage_window.geometry("400x300")
        manage_window.resizable(False, False)
        manage_window.transient(self.root)
        manage_window.grab_set()
        list_frame = ctk.CTkScrollableFrame(manage_window, width=360, height=200)
        list_frame.pack(pady=10, padx=20, fill="both", expand=True)
        for i, server in enumerate(self.settings["servers"]):
            server_frame = ctk.CTkFrame(list_frame)
            server_frame.pack(pady=2, padx=5, fill="x")
            info_label = ctk.CTkLabel(
                server_frame, 
                text=f"{server['name']}\n{server['server']}:{server['port']} ({server['method']})",
                anchor="w"
            )
            info_label.pack(side="left", padx=10, pady=5, fill="x", expand=True)
            btn_frame = ctk.CTkFrame(server_frame, fg_color="transparent")
            btn_frame.pack(side="right", padx=5, pady=5)
            use_btn = ctk.CTkButton(
                btn_frame, 
                text="Use", 
                width=80, 
                height=25,
                command=lambda idx=i: self.use_server(idx, manage_window)
            )
            use_btn.pack(side="left", padx=2)
            del_btn = ctk.CTkButton(
                btn_frame, 
                text="❌", 
                width=30, 
                height=25,
                fg_color="red",
                command=lambda idx=i: self.delete_server(idx, manage_window)
            )
            del_btn.pack(side="left", padx=2)
        close_btn = ctk.CTkButton(manage_window, text="Close", command=manage_window.destroy)
        close_btn.pack(pady=10)
    
    def use_server(self, server_index, manage_window):
        if server_index < len(self.settings["servers"]):
            server = self.settings["servers"][server_index]
            self.server_entry.delete(0, "end")
            self.server_entry.insert(0, server['server'])
            self.server_port_entry.delete(0, "end")
            self.server_port_entry.insert(0, str(server['port']))
            self.password_entry.delete(0, "end")
            self.password_entry.insert(0, server['password'])
            self.method_combobox.set(server['method'])
            manage_window.destroy()
            messagebox.showinfo("Success", f"Server '{server['name']}' loaded")
    
    def delete_server(self, server_index, manage_window):
        if server_index < len(self.settings["servers"]):
            server_name = self.settings["servers"][server_index]['name']
            if messagebox.askyesno("Confirm", f"Delete server '{server_name}'?"):
                del self.settings["servers"][server_index]
                self.save_settings()
                manage_window.destroy()
                self.manage_servers()
    
    def browse_ss_local(self):
        filename = filedialog.askopenfilename(
            title="Select ss-local.exe",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if filename:
            self.ss_path_entry.delete(0, "end")
            self.ss_path_entry.insert(0, filename)
    
    def get_current_settings(self):
        try:
            return {
                "server": self.server_entry.get().strip(),
                "server_port": int(self.server_port_entry.get()),
                "local_address": "127.0.0.1",
                "local_port": int(self.local_port_entry.get()),
                "password": self.password_entry.get(),
                "method": self.method_combobox.get(),
                "timeout": 300,
                "ss_local_path": self.ss_path_entry.get().strip()
            }
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid data format: {e}")
            return None
    
    def validate_settings(self, settings):
        if not settings["server"]:
            messagebox.showerror("Error", "Server not specified")
            return False
        if not settings["password"]:
            messagebox.showerror("Error", "Password not specified")
            return False
        if not os.path.exists(settings["ss_local_path"]):
            messagebox.showerror("Error", f"ss-local.exe not found: {settings['ss_local_path']}")
            return False
        if not (1 <= settings["server_port"] <= 65535):
            messagebox.showerror("Error", "Invalid server port (1-65535)")
            return False
        if not (1 <= settings["local_port"] <= 65535):
            messagebox.showerror("Error", "Invalid local port (1-65535)")
            return False
        return True
    
    def create_config_file(self, settings):
        config = {
            "server": settings["server"],
            "server_port": settings["server_port"],
            "local_address": settings["local_address"],
            "local_port": settings["local_port"],
            "password": settings["password"],
            "method": settings["method"],
            "timeout": settings["timeout"]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f, indent=2)
            return f.name
    
    def toggle_connection(self):
        if self.is_connected:
            self.disconnect()
        else:
            self.connect()
    
    def connect(self):
        settings = self.get_current_settings()
        if not settings or not self.validate_settings(settings):
            return
        try:
            self.ss_config_file = self.create_config_file(settings)
            self.ss_process = subprocess.Popen(
                [settings["ss_local_path"], "-c", self.ss_config_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.is_connected = True
            self.update_ui_state()
            threading.Thread(target=self.monitor_connection, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Connection error", str(e))
            self.cleanup_connection()
    
    def disconnect(self):
        self.cleanup_connection()
        self.is_connected = False
        self.update_ui_state()
    
    def cleanup_connection(self):
        if self.ss_process:
            try:
                self.ss_process.terminate()
                self.ss_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ss_process.kill()
            except:
                pass
            finally:
                self.ss_process = None
        if self.ss_config_file and os.path.exists(self.ss_config_file):
            try:
                os.unlink(self.ss_config_file)
            except:
                pass
            self.ss_config_file = None
    
    def monitor_connection(self):
        while self.is_connected and self.ss_process:
            if self.ss_process.poll() is not None:
                self.is_connected = False
                self.root.after(0, self.update_ui_state)
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", "Connection lost. Check server settings."
                ))
                break
            threading.Event().wait(1)
    
    def update_ui_state(self):
        if self.is_connected:
            self.status_label.configure(text="● Connected", text_color="green")
            self.connect_button.configure(text="🔌 Disconnect")
        else:
            self.status_label.configure(text="● Disconnected", text_color="red")
            self.connect_button.configure(text="🔌 Connect")
    
    def test_connection(self):
        if not self.is_connected:
            messagebox.showwarning("Warning", "Connect to the server first")
            return

        def test_thread():
            import time
            results = []
            try:
                import socket
                server = self.server_entry.get().strip()
                port = int(self.server_port_entry.get())
                start = time.time()
                sock = socket.create_connection((server, port), timeout=3)
                latency = (time.time() - start) * 1000
                sock.close()
                results.append(f"Ping to {server}:{port}: {latency:.1f} ms")
            except Exception as e:
                results.append(f"Ping to {server}:{port}: failed ({e})")

            try:
                import requests
                proxies = {
                    'http': f'socks5://127.0.0.1:{self.local_port_entry.get()}',
                    'https': f'socks5://127.0.0.1:{self.local_port_entry.get()}'
                }
                start = time.time()
                response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    results.append(f"Your IP: {result.get('origin', 'unknown')}")
                else:
                    results.append("Proxy test: failed (bad response)")
            except Exception as e:
                results.append(f"Proxy test: failed ({e})")

            msg = "\n\n".join(results)
            self.root.after(0, lambda: messagebox.showinfo("Test result", msg))

        threading.Thread(target=test_thread, daemon=True).start()
    
    def save_settings(self):
        current_settings = self.get_current_settings()
        if current_settings:
            self.settings.update(current_settings)
        try:
            settings_file = Path.home() / ".socksicle_settings.json"
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Error", f"Could not save settings: {e}")
    
    def load_settings(self):
        try:
            settings_file = Path.home() / ".socksicle_settings.json"
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
        except Exception:
            pass
    
    def on_closing(self):
        self.save_settings()
        if self.is_connected:
            self.disconnect()
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()

def main():
    try:
        app = SocksicleApp()
        app.run()
    except Exception as e:
        messagebox.showerror("Critical error", f"Could not start application: {e}")

if __name__ == "__main__":
    main()
