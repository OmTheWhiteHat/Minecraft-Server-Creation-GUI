# Add these two lines near top imports if not already
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess, threading, os, json

CONFIG_FILE = "log_config.json"

class MinecraftServerLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        server_dir_path = os.path.join(os.path.dirname(__file__), "server_run")
        os.makedirs(server_dir_path, exist_ok=True)

        self.title("Minecraft Server Launcher by Om Prakash")
        self.geometry("800x600")
        self.configure(bg="#121212")
        self.minsize(700, 500)

        self.server_types = {
            "Vanilla": "server.jar",
            "Fabric": "fabric-server-launch.jar",
            "Forge": "forge-server.jar",
            "Pocket Edition (PHP)": os.path.join("bedrock", "bedrock_server.exe"),
            "Custom (Browse)": None
        }

        self.process = None
        self.selected_server = tk.StringVar(value="Vanilla")
        self.custom_path = tk.StringVar()
        self.memory_xms = tk.IntVar(value=1024)
        self.memory_xmx = tk.IntVar(value=2048)

        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.customize_style()
        self.create_widgets()
        self.load_config()

    def customize_style(self):
        style = self.style
        style.configure("TFrame", background="#121212")
        style.configure("TLabel", background="#121212", foreground="#ffffff", font=("Segoe UI", 11))
        style.configure("TButton", font=("Segoe UI", 10, "bold"))
        style.configure("TCombobox", font=("Segoe UI", 10))
        style.map("TButton", background=[("active", "#333333")])
        style.configure("RoundedButton.TButton", padding=6, relief="flat", background="#00b894", foreground="white")
        style.map("RoundedButton.TButton", background=[("active", "#00cec9")])

    def create_widgets(self):
        tk.Label(self, text="Minecraft Server Launcher", fg="#00b894", bg="#121212",
                 font=("Segoe UI", 24, "bold")).pack(pady=15)

        select_frame = ttk.Frame(self)
        select_frame.pack(padx=20, pady=10, fill="x")

        ttk.Label(select_frame, text="Select Server Type:").grid(row=0, column=0, sticky="w", pady=5)
        self.server_menu = ttk.Combobox(select_frame, textvariable=self.selected_server,
                                        values=list(self.server_types.keys()), state="readonly", width=40)
        self.server_menu.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.server_menu.bind("<<ComboboxSelected>>", self.toggle_custom)

        ttk.Button(select_frame, text="📁 Load Last Profile", style="RoundedButton.TButton",
                   command=self.load_config).grid(row=0, column=2, padx=5)

        self.custom_entry = tk.Entry(select_frame, textvariable=self.custom_path, width=40, font=("Segoe UI", 10),
                                     state="disabled", bg="#1e1e1e", fg="#ffffff", insertbackground="white")
        self.custom_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        self.browse_button = ttk.Button(select_frame, text="Browse", command=self.browse_file, state="disabled")
        self.browse_button.grid(row=1, column=2, padx=5, sticky="w")

        ttk.Label(select_frame, text="Initial RAM (MB):").grid(row=2, column=0, sticky="w", pady=5)
        tk.Scale(select_frame, from_=256, to=8192, resolution=128, orient="horizontal",
                 variable=self.memory_xms, bg="#1e1e1e", fg="white", highlightbackground="#1e1e1e",
                 troughcolor="#00b894", font=("Segoe UI", 9)).grid(row=2, column=1, columnspan=2, sticky="ew", padx=10)

        ttk.Label(select_frame, text="Maximum RAM (MB):").grid(row=3, column=0, sticky="w", pady=5)
        tk.Scale(select_frame, from_=512, to=16384, resolution=256, orient="horizontal",
                 variable=self.memory_xmx, bg="#1e1e1e", fg="white", highlightbackground="#1e1e1e",
                 troughcolor="#0984e3", font=("Segoe UI", 9)).grid(row=3, column=1, columnspan=2, sticky="ew", padx=10)

        for text, command in [
            ("🚀 Launch Server", self.launch_server),
            ("🛑 Stop Server", self.stop_server),
            ("🔄 Restart Server", self.restart_server)
        ]:
            ttk.Button(self, text=text, style="RoundedButton.TButton", command=command).pack(pady=(0, 10))

        self.log_text = tk.Text(self, height=20, bg="#1e1e1e", fg="#00ff00", insertbackground="white",
                                font=("Consolas", 10), wrap="word", relief="flat", borderwidth=5)
        self.log_text.pack(padx=20, pady=5, fill="both", expand=True)
        self.log_text.config(state="disabled")

        input_frame = ttk.Frame(self)
        input_frame.pack(fill="x", padx=20, pady=(5, 10))

        self.command_entry = tk.Entry(input_frame, font=("Consolas", 10), bg="#2d3436", fg="#ffffff",
                                      insertbackground="white", relief="flat", borderwidth=4)
        self.command_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.command_entry.bind("<Return>", self.send_command)

        ttk.Button(input_frame, text="📤 Send", style="RoundedButton.TButton",
                   command=self.send_command).pack(side="right")

    def toggle_custom(self, event=None):
        custom_selected = self.selected_server.get() == "Custom (Browse)"
        state = "normal" if custom_selected else "disabled"
        self.custom_entry.config(state=state)
        self.browse_button.config(state=state)
        self.toggle_memory_sliders()


    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("JAR/PHAR Files", "*.jar *.phar")])
        if file_path:
            self.custom_path.set(file_path)

    def launch_server(self):
        self.command_entry.config(state="normal")
        server_type = self.selected_server.get()
        jar_file = self.server_types.get(server_type)

        # Handle missing server file
        if server_type == "Custom (Browse)":
            jar_path = self.custom_path.get()
        elif jar_file:
            jar_path = os.path.join(os.path.dirname(__file__), "server_run", jar_file)
        else:
            messagebox.showerror("Error", f"Server type '{server_type}' is not supported or file missing.")
            return

        if not os.path.isfile(jar_path):
            messagebox.showerror("File Not Found", f"Cannot find server file:\n{jar_path}")
            return

        self.save_config()
        self.append_log(f"🚀 Launching server: {jar_path} with {self.memory_xms.get()}MB - {self.memory_xmx.get()}MB RAM\n")
        threading.Thread(target=self.run_server, args=(jar_path,), daemon=True).start()


    def run_server(self, jar_path):
        xms, xmx = self.memory_xms.get(), self.memory_xmx.get()
        
        if jar_path.endswith(".phar"):
            cmd = ["php", jar_path]
        elif jar_path.endswith(".exe"):
            cmd = [jar_path]  # Pocket Edition Bedrock
        else:
            cmd = ["java", f"-Xms{xms}M", f"-Xmx{xmx}M", "-jar", jar_path, "nogui"]

        server_dir = os.path.join(os.path.dirname(__file__), "server_run")

        try:
            self.append_log(f"\n▶ Starting server with command: {' '.join(cmd)}\n")
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                            stdin=subprocess.PIPE if not jar_path.endswith(".exe") else None,
                                            universal_newlines=True, bufsize=1, cwd=server_dir)
            if self.process.stdout:
                for line in self.process.stdout:
                    self.append_log(line)
            self.process.wait()
            self.append_log("\n✔ Server stopped.\n")
        except Exception as e:
            self.append_log(f"❌ Failed to start server: {str(e)}\n")


    def send_command(self, event=None):
        if self.selected_server.get() == "Pocket Edition (PHP)":
            self.append_log("⚠ Bedrock server does not support console input.\n")
            return

        cmd = self.command_entry.get().strip()
        if self.process and self.process.stdin and cmd:
            try:
                self.process.stdin.write(cmd + "\n")
                self.process.stdin.flush()
                self.append_log(f"> {cmd}\n")
                self.command_entry.delete(0, tk.END)
            except Exception as e:
                self.append_log(f"Failed to send command: {str(e)}\n")
        else:
            self.append_log("Server not running or command is empty.\n")

    def append_log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", message)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def save_config(self):
        config = {
            "server_type": self.selected_server.get(),
            "custom_path": self.custom_path.get(),
            "xms": self.memory_xms.get(),
            "xmx": self.memory_xmx.get()
        }
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f)
        except Exception as e:
            self.append_log(f"Failed to save profile: {str(e)}\n")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    self.selected_server.set(config.get("server_type", "Vanilla"))
                    self.custom_path.set(config.get("custom_path", ""))
                    self.memory_xms.set(config.get("xms", 1024))
                    self.memory_xmx.set(config.get("xmx", 2048))
                    self.toggle_custom()
                    self.toggle_memory_sliders()
                    self.append_log("✔ Profile loaded from config.json\n")
            except Exception as e:
                self.append_log(f"Failed to load profile: {str(e)}\n")


    def stop_server(self):
        if self.process and self.process.poll() is None:
            try:
                self.append_log("🛑 Sending 'stop' command to server...\n")
                self.process.stdin.write("stop\n")
                self.process.stdin.flush()

                # Wait for process to exit gracefully
                self.process.wait(timeout=15)
                self.append_log("✔ Server stopped gracefully.\n")
                self.command_entry.config(state="disabled")
            except Exception as e:
                self.append_log(f"❌ Error stopping server: {str(e)}\n")
        else:
            self.append_log("⚠ No running server to stop.\n")

        # Clean up lock files after server stops
        lock_paths = [
            os.path.join("server_run", "world", "session.lock"),
            os.path.join("server_run", "world_nether", "session.lock"),
            os.path.join("server_run", "world_the_end", "session.lock")
        ]
        for path in lock_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    self.append_log(f"🧹 Deleted lock file: {path}\n")
            except Exception as e:
                self.append_log(f"⚠ Failed to delete lock file {path}: {str(e)}\n")

    def restart_server(self):
        if self.process and self.process.poll() is None:
            self.append_log("🔁 Restarting server...\n")
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
            except Exception as e:
                self.append_log(f"⚠ Error while stopping server: {str(e)}\n")
        self.launch_server()

    def toggle_memory_sliders(self):
        server_type = self.selected_server.get()
        if server_type == "Pocket Edition (PHP)":
            # Disable RAM sliders for Bedrock
            for widget in self.children.values():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Scale):
                            child.config(state="disabled")
        else:
            for widget in self.children.values():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Scale):
                            child.config(state="normal")

if __name__ == "__main__":
    MinecraftServerLauncher().mainloop()