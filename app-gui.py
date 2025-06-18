import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import os

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

        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.customize_style()

        self.create_widgets()

    def customize_style(self):
        self.style.configure("TFrame", background="#121212")
        self.style.configure("TLabel", background="#121212", foreground="#ffffff", font=("Segoe UI", 11))
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"))
        self.style.configure("TCombobox", font=("Segoe UI", 10))
        self.style.map("TButton", background=[("active", "#333333")])
        self.style.configure("RoundedButton.TButton", padding=6, relief="flat", background="#00b894", foreground="white")
        self.style.map("RoundedButton.TButton", background=[("active", "#00cec9")])

    def create_widgets(self):
        # Title
        title = tk.Label(self, text="Minecraft Server Launcher", fg="#00b894", bg="#121212",
                         font=("Segoe UI", 24, "bold"))
        title.pack(pady=15)

        # Server Selection Frame
        select_frame = ttk.Frame(self)
        select_frame.pack(padx=20, pady=10, fill="x")

        ttk.Label(select_frame, text="Select Server Type:").grid(row=0, column=0, sticky="w", pady=5)
        self.server_menu = ttk.Combobox(select_frame, textvariable=self.selected_server,
                                        values=list(self.server_types.keys()), state="readonly", width=40)
        self.server_menu.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.server_menu.bind("<<ComboboxSelected>>", self.toggle_custom)

        self.custom_entry = tk.Entry(select_frame, textvariable=self.custom_path, width=40, font=("Segoe UI", 10),
                                     state="disabled", bg="#1e1e1e", fg="#ffffff", insertbackground="white")
        self.custom_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        self.browse_button = ttk.Button(select_frame, text="Browse", command=self.browse_file, state="disabled")
        self.browse_button.grid(row=1, column=2, padx=5, sticky="w")

        # Launch Button
        self.launch_button = ttk.Button(self, text="🚀 Launch Server", style="RoundedButton.TButton", command=self.launch_server)
        self.launch_button.pack(pady=10)

        # Terminal Output
        self.log_text = tk.Text(self, height=20, bg="#1e1e1e", fg="#00ff00", insertbackground="white",
                                font=("Consolas", 10), wrap="word", relief="flat", borderwidth=5)
        self.log_text.pack(padx=20, pady=5, fill="both", expand=True)
        self.log_text.config(state="disabled")

        # Input command bar
        input_frame = ttk.Frame(self)
        input_frame.pack(fill="x", padx=20, pady=(5, 10))

        self.command_entry = tk.Entry(input_frame, font=("Consolas", 10), bg="#2d3436", fg="#ffffff",
                                      insertbackground="white", relief="flat", borderwidth=4)
        self.command_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.command_entry.bind("<Return>", self.send_command)

        self.send_button = ttk.Button(input_frame, text="📤 Send", style="RoundedButton.TButton", command=self.send_command)
        self.send_button.pack(side="right")

    def toggle_custom(self, event):
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
        server_type = self.selected_server.get()
        jar_file = self.server_types[server_type]

        if server_type == "Custom (Browse)":
            jar_file = self.custom_path.get()

        if not jar_file or not os.path.isfile(jar_file):
            messagebox.showerror("File Not Found", f"Cannot find file: {jar_file}")
            return

        self.append_log(f"Launching server: {jar_file}...\n")
        threading.Thread(target=self.run_server, args=(jar_file,), daemon=True).start()

    def run_server(self, jar_file):
        use_php = jar_file.endswith(".phar")
        cmd = ["php", jar_file] if use_php else ["java", "-jar", jar_file, "gui"]

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )

            for line in self.process.stdout:
                self.append_log(line)

            self.process.stdout.close()
            self.process.wait()
            self.append_log(f"\nServer stopped with exit code {self.process.returncode}\n")

        except Exception as e:
            self.append_log(f"Error: {str(e)}\n")

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

if __name__ == "__main__":
    MinecraftServerLauncher().mainloop()
