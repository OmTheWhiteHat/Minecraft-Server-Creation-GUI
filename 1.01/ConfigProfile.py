import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os

class ConfigEditor(tk.Tk):
    def __init__(self, config_path="config.json"):
        super().__init__()
        self.title("Config Editor - Minecraft Profile")
        self.geometry("600x500")
        self.configure(bg="#2d3436")
        self.config_path = config_path
        self.config_data = {}

        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("Treeview", font=("Segoe UI", 10), rowheight=25, background="#2d3436", fieldbackground="#2d3436", foreground="white")
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#00b894", foreground="white")

        self.create_widgets()
        self.load_config()

    def create_widgets(self):
        # Treeview
        self.tree = ttk.Treeview(self, columns=("Key", "Value"), show="headings", selectmode="browse")
        self.tree.heading("Key", text="Key")
        self.tree.heading("Value", text="Value")
        self.tree.pack(fill="both", expand=True, pady=10, padx=10)

        # Buttons
        btn_frame = tk.Frame(self, bg="#2d3436")
        btn_frame.pack(pady=5)

        ttk.Button(btn_frame, text="➕ Add", command=self.add_entry).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Edit", command=self.edit_entry).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Delete", command=self.delete_entry).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="💾 Save", command=self.save_config).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="📂 Open File", command=self.browse_file).pack(side="left", padx=5)

    def load_config(self):
        if os.path.isfile(self.config_path):
            with open(self.config_path, "r") as f:
                self.config_data = json.load(f)
        else:
            self.config_data = {}

        self.refresh_tree()

    def save_config(self):
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config_data, f, indent=4)
            self.load_config()  # 🔁 Auto-reload after save
            messagebox.showinfo("Saved", "Configuration saved and reloaded.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config:\n{e}")


    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())

        for section, values in self.config_data.items():
            if isinstance(values, dict):
                parent = self.tree.insert("", "end", text=section, values=(section, ""), open=True)
                for key, val in values.items():
                    self.tree.insert(parent, "end", values=(f"{section}.{key}", val))
            else:
                self.tree.insert("", "end", values=(section, values))  # Flat key


    def add_entry(self):
        self.open_editor("Add Entry")

    def edit_entry(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select an item to edit.")
            return

        key, value = self.tree.item(selected[0], "values")
        if "." in key:
            section, subkey = key.split(".", 1)
        else:
            section, subkey = None, key

        self.open_editor("Edit Entry", key=subkey, value=value, section=section)

    def delete_entry(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select an item to delete.")
            return
        key, _ = self.tree.item(selected[0], "values")
        if "." in key:
            section, subkey = key.split(".", 1)
            if section in self.config_data and subkey in self.config_data[section]:
                del self.config_data[section][subkey]
        else:
            if key in self.config_data:
                del self.config_data[key]

        self.refresh_tree()


    def open_editor(self, title, key="", value="", section=None):
        def save_entry():
            new_key = key_entry.get()
            new_value = value_entry.get()
            if not new_key:
                messagebox.showerror("Invalid", "Key cannot be empty.")
                return

            if section:
                self.config_data.setdefault(section, {})[new_key] = new_value
            else:
                self.config_data[new_key] = new_value

            self.refresh_tree()
            editor.destroy()

        editor = tk.Toplevel(self)
        editor.title(title)
        editor.geometry("300x150")
        editor.configure(bg="#2d3436")

        tk.Label(editor, text="Key:", bg="#2d3436", fg="white").pack(pady=5)
        key_entry = tk.Entry(editor)
        key_entry.insert(0, key)
        key_entry.pack(pady=5)

        tk.Label(editor, text="Value:", bg="#2d3436", fg="white").pack(pady=5)
        value_entry = tk.Entry(editor)
        value_entry.insert(0, value)
        value_entry.pack(pady=5)

        ttk.Button(editor, text="Save", command=save_entry).pack(pady=10)


    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if path:
            self.config_path = path
            self.load_config()

if __name__ == "__main__":
    ConfigEditor().mainloop()
