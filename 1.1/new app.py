# Add these two lines near top imports if not already
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess, threading, os, json
from PIL import Image, ImageDraw
import pystray

CONFIG_FILE = "log_config.json"

class MinecraftServerLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Minecraft Server Launcher by Om Prakash")
        self.geometry("800x600")
        self.configure(bg="#121212")
        self.minsize(700, 500)

        self.server_types = {
            "Vanilla": "server.jar",
            "Fabric": "fabric-server-launch.jar",
            "Forge": "forge-server.jar",
            "Pocket Edition (PHP)": "pocketmine-mp.phar",
            "Custom (Browse)": None
        }

        self.process = None
        self.selected_server = tk.StringVar(value="Vanilla")
        self.custom_path = tk.StringVar(value="")
        self.memory_xms = tk.IntVar(value=1024)  # Default 1024 MB
        self.memory_xmx = tk.IntVar(value=2048)  # Default 2048 MB

        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.customize_style()
        self.create_widgets()
        self.load_config()

        self.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.create_tray_icon()

    def customize_style(self):
        self.style.configure("TFrame", background="#121212")
        self.style.configure("TLabel", background="#121212", foreground="#ffffff", font=("Segoe UI", 11))
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"))
        self.style.configure("TCombobox", font=("Segoe UI", 10))
        self.style.map("TButton", background=[("active", "#333333")])
        self.style.configure("RoundedButton.TButton", padding=6, relief="flat", background="#00b894", foreground="white")
        self.style.map("RoundedButton.TButton", background=[("active", "#00cec9")])

    def create_widgets(self):
        title = tk.Label(self, text="Minecraft Server Launcher", fg="#00b894", bg="#121212",
                         font=("Segoe UI", 24, "bold"))
        title.pack(pady=15)

        select_frame = ttk.Frame(self)
        select_frame.pack(padx=20, pady=10, fill="x")

        ttk.Label(select_frame, text="Select Server Type:").grid(row=0, column=0, sticky="w", pady=5)
        self.server_menu = ttk.Combobox(select_frame, textvariable=self.selected_server,
                                        values=list(self.server_types.keys()), state="readonly", width=40)
        self.server_menu.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.server_menu.bind("<<ComboboxSelected>>", self.toggle_custom)

        self.profile_button = ttk.Button(select_frame, text="📁 Load Last Profile", style="RoundedButton.TButton", command=self.load_config)
        self.profile_button.grid(row=0, column=2, padx=5)

        self.custom_entry = tk.Entry(select_frame, textvariable=self.custom_path, width=40, font=("Segoe UI", 10),
                                     state="disabled", bg="#1e1e1e", fg="#ffffff", insertbackground="white")
        self.custom_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        self.browse_button = ttk.Button(select_frame, text="Browse", command=self.browse_file, state="disabled")
        self.browse_button.grid(row=1, column=2, padx=5, sticky="w")

        ttk.Label(select_frame, text="Initial RAM (MB):").grid(row=2, column=0, sticky="w", pady=5)
        xms_slider = tk.Scale(select_frame, from_=256, to=8192, resolution=128, orient="horizontal",
                            variable=self.memory_xms, bg="#1e1e1e", fg="white", highlightbackground="#1e1e1e",
                            troughcolor="#00b894", font=("Segoe UI", 9))
        xms_slider.grid(row=2, column=1, columnspan=2, sticky="ew", padx=10)

        ttk.Label(select_frame, text="Maximum RAM (MB):").grid(row=3, column=0, sticky="w", pady=5)
        xmx_slider = tk.Scale(select_frame, from_=512, to=16384, resolution=256, orient="horizontal",
                            variable=self.memory_xmx, bg="#1e1e1e", fg="white", highlightbackground="#1e1e1e",
                            troughcolor="#0984e3", font=("Segoe UI", 9))
        xmx_slider.grid(row=3, column=1, columnspan=2, sticky="ew", padx=10)

        self.launch_button = ttk.Button(self, text="🚀 Launch Server", style="RoundedButton.TButton", command=self.launch_server)
        self.launch_button.pack(pady=10)

        self.stop_button = ttk.Button(self, text="🚑 Stop Server", style="RoundedButton.TButton", command=self.stop_server)
        self.stop_button.pack(pady=(0, 10))

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

        self.send_button = ttk.Button(input_frame, text="📤 Send", style="RoundedButton.TButton", command=self.send_command)
        self.send_button.pack(side="right")

    def toggle_custom(self, event=None):
        server = self.selected_server.get()
        if server == "Custom (Browse)":
            self.custom_entry.config(state="normal")
            self.browse_button.config(state="normal")
        else:
            self.custom_entry.config(state="disabled")
            self.browse_button.config(state="disabled")

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("JAR/PHAR Files", "*.jar *.phar")])
        if file_path:
            self.custom_path.set(file_path)

    def launch_server(self):
        self.command_entry.config(state="normal")
        server_type = self.selected_server.get()
        jar_file = self.server_types[server_type]
        if server_type == "Custom (Browse)":
            jar_file = self.custom_path.get()

        if not jar_file or not os.path.isfile(jar_file):
            messagebox.showerror("File Not Found", f"Cannot find file: {jar_file}")
            return

        os.makedirs("server", exist_ok=True)
        self.save_config()
        self.append_log(f"Launching server: {jar_file} with {self.memory_xms.get()} initial and {self.memory_xmx.get()} max memory...\n")
        threading.Thread(target=self.run_server, args=(jar_file, "server"), daemon=True).start()

    def run_server(self, jar_file, server_dir_name):
        xms = self.memory_xms.get()
        xmx = self.memory_xmx.get()
        use_php = jar_file.endswith(".phar")
        cmd = ["php", jar_file] if use_php else ["java", f"-Xms{xms}M", f"-Xmx{xmx}M", "-jar", jar_file, "nogui"]
        self.append_log(f"\n▶ Starting server with command: {' '.join(cmd)}\n")
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1,
                cwd=os.path.join(os.path.dirname(__file__), server_dir_name)
            )
            for line in self.process.stdout:
                self.append_log(line)
            self.process.stdout.close()
            return_code = self.process.wait()
            if return_code == 0:
                self.append_log("\n✔ Server stopped gracefully.\n")
            else:
                self.append_log(f"\n⚠ Server crashed (exit code {return_code}).\n")
        except Exception as e:
            self.append_log(f"❌ Failed to start server: {str(e)}\n")

    def send_command(self, event=None):
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
                    self.append_log("✔ Profile loaded from config.json\n")
            except Exception as e:
                self.append_log(f"Failed to load profile: {str(e)}\n")

    def stop_server(self):
        if self.process and self.process.poll() is None:
            try:
                self.append_log("🛑 Stopping server...\n")
                self.process.terminate()
                self.process.wait(timeout=10)
                self.append_log("✔ Server terminated.\n")
                self.command_entry.config(state="disabled")
            except Exception as e:
                self.append_log(f"❌ Error stopping server: {str(e)}\n")
        else:
            self.append_log("⚠ No running server to stop.\n")

    def generate_icon_image(self):
        img = Image.new("RGB", (64, 64), color="#00b894")
        draw = ImageDraw.Draw(img)
        draw.rectangle((16, 16, 48, 48), fill="#2d3436")
        draw.text((20, 20), "M", fill="white")
        return img

    def create_tray_icon(self):
        def on_show(icon, item):
            self.deiconify()

        def on_hide(icon, item):
            self.withdraw()

        def on_stop_server(icon, item):
            self.stop_server()

        def on_quit(icon, item):
            icon.stop()
            self.stop_server()
            self.destroy()

        image = self.generate_icon_image()

        self.tray_icon = pystray.Icon("minecraft_launcher", image, "MC Launcher", menu=pystray.Menu(
            pystray.MenuItem("Show", on_show),
            pystray.MenuItem("Hide", on_hide),
            pystray.MenuItem("Stop Server", on_stop_server),
            pystray.MenuItem("Exit", on_quit)
        ))

        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def hide_window(self):
        self.withdraw()

if __name__ == "__main__":
    MinecraftServerLauncher().mainloop()