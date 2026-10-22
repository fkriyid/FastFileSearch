

import json
import os

import subprocess

import threading

import tkinter as tk

from tkinter import filedialog, messagebox, ttk



try:

    import customtkinter as ctk

except ImportError:

    raise SystemExit(

        "Module belum terpasang. Jalankan dulu:  pip install customtkinter")
# =========================
# CONFIG
# =========================
DEFAULT_FOLDER = ""  # User selects a folder; avoid scanning private folders automatically.

# Store cache outside the source/repository folder and keep it local to this user.
APP_DATA_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "FastSearchFile",
)
os.makedirs(APP_DATA_DIR, exist_ok=True)
CACHE_FILE = os.path.join(APP_DATA_DIR, "file_index.json")

MAX_RESULTS = 500

DEBOUNCE_MS = 200

ACCENT, ACCENT_HOVER = "#3b82f6", "#2563eb"



LIGHT = dict(win="#eef1f6", card="#ffffff", fg="#1f2937",

             muted="#6b7280", head="#eef1f6", alt="#f6f8fb")

DARK = dict(win="#12151c", card="#1b1f2a", fg="#e6e9f0",

            muted="#9aa3b5", head="#262c3a", alt="#202534")

PALETTE = {"Light": LIGHT, "Dark": DARK}





def pair(key):

    return (LIGHT[key], DARK[key])





TYPES = {

    "Semua tipe": None,

    "PDF": (".pdf",),

    "Excel / CSV": (".xlsx", ".xls", ".xlsm", ".csv"),

    "Word": (".docx", ".doc"),

    "PowerPoint": (".pptx", ".ppt"),

    "Gambar": (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"),

    "Arsip": (".zip", ".rar", ".7z"),

}

ICONS = {

    ".pdf": "📕", ".xlsx": "📗", ".xls": "📗", ".xlsm": "📗", ".csv": "📗",

    ".docx": "📘", ".doc": "📘", ".pptx": "📙", ".ppt": "📙",

    ".png": "🖼️", ".jpg": "🖼️", ".jpeg": "🖼️", ".gif": "🖼️", ".webp": "🖼️",

    ".zip": "🗜️", ".rar": "🗜️", ".7z": "🗜️", ".txt": "📝", ".py": "🐍",

}
# =========================
# INDEX (background scan + cache)
# =========================
index = []  # (name_lower, name, path)

scan_state = None

row_paths = {}





def scan_folder(folder, state):

    result = []

    stack = [folder]

    while stack:

        if state["cancel"]:

            return None

        current = stack.pop()

        try:

            with os.scandir(current) as it:

                for entry in it:

                    try:

                        if entry.is_dir(follow_symlinks=False):

                            stack.append(entry.path)

                        else:

                            result.append(

                                (entry.name.lower(), entry.name, entry.path))

                    except OSError:

                        pass

        except OSError:

            pass

        state["count"] = len(result)

    return result





def load_cache(folder):
    """Load this user's local JSON index cache, if it is valid."""
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        files = data.get(folder)
        if not isinstance(files, list):
            return None
        # Validate the cache shape before using it in the search UI.
        if all(
            isinstance(item, list)
            and len(item) == 3
            and all(isinstance(part, str) for part in item)
            for item in files
        ):
            return [tuple(item) for item in files]
    except (OSError, json.JSONDecodeError, AttributeError, TypeError):
        return None
    return None


def save_cache(folder, files):
    """Save the file index as JSON; avoid executable pickle deserialization."""
    try:
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                data = {}
        except (OSError, json.JSONDecodeError):
            data = {}

        data[folder] = files
        temporary_file = CACHE_FILE + ".tmp"
        with open(temporary_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(temporary_file, CACHE_FILE)
    except (OSError, TypeError, ValueError):
        # Caching is optional; search should still work if it cannot be saved.
        pass


def worker(folder, state):

    files = scan_folder(folder, state)

    if files is None:

        return

    save_cache(folder, files)

    state["result"] = files

    state["done"] = True





def start_scan(folder):

    global scan_state

    folder = os.path.normpath(folder)

    if not os.path.isdir(folder):

        messagebox.showwarning("Folder tidak ditemukan", folder)

        return

    if scan_state:

        scan_state["cancel"] = True

    state = {"count": 0, "done": False, "cancel": False, "result": None}

    scan_state = state

    progress.start()

    threading.Thread(target=worker, args=(folder, state), daemon=True).start()

    poll_scan(state)





def poll_scan(state):

    global index

    if state is not scan_state:

        return

    if state["done"]:

        index = state["result"]

        progress.stop()

        progress.set(0)

        status_var.set(f"●  {len(index):,} file ter-index")

        do_search()

    else:

        status_var.set(f"⟳  Scanning... {state['count']:,} file")

        root.after(150, poll_scan, state)





def load_folder(folder):

    global index

    folder = os.path.normpath(folder)

    cached = load_cache(folder)

    if cached:

        index = cached

        status_var.set(f"●  {len(index):,} file (cache), memperbarui...")

        do_search()

    else:

        index = []

    start_scan(folder)
# =========================
# SEARCH
# =========================
def do_search(*_):

    keywords = entry_search.get().lower().split()

    exts = TYPES.get(type_var.get())

    tree.delete(*tree.get_children())

    row_paths.clear()



    if not keywords:

        result_var.set("Ketik untuk mulai mencari")

        return



    total = shown = 0

    for name_lower, name, path in index:

        if exts and not name_lower.endswith(exts):

            continue

        if all(k in name_lower for k in keywords):

            total += 1

            if shown < MAX_RESULTS:

                ext = os.path.splitext(name_lower)[1]

                iid = str(shown)

                row_paths[iid] = path

                tree.insert(

                    "", "end", iid=iid,

                    values=(f"{ICONS.get(ext, '📄')}  {name}",

                            ext[1:].upper() or "-", path),

                    tags=("odd" if shown % 2 else "even",),

                )

                shown += 1



    if total == 0:

        result_var.set("Tidak ada file yang cocok")

    elif total > shown:

        result_var.set(

            f"{total:,} hasil  •  menampilkan {shown} teratas, perjelas keyword")

    else:

        result_var.set(f"{total:,} hasil")





debounce_id = None





def on_key(_event=None):

    global debounce_id

    if debounce_id:

        root.after_cancel(debounce_id)

    debounce_id = root.after(DEBOUNCE_MS, do_search)





def clear_search(_event=None):

    entry_search.delete(0, "end")

    do_search()
# =========================
# ACTIONS
# =========================
def selected_path():

    sel = tree.selection()

    return row_paths.get(sel[0]) if sel else None





def open_file(_event=None):

    path = selected_path()

    if path and os.path.exists(path):

        os.startfile(path)





def open_folder():

    path = selected_path()

    if path and os.path.exists(path):

        subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])





def copy_path():

    path = selected_path()

    if path:

        root.clipboard_clear()

        root.clipboard_append(path)

        result_var.set("Path disalin ke clipboard")





def show_menu(event):

    row = tree.identify_row(event.y)

    if row:

        tree.selection_set(row)

        menu.tk_popup(event.x_root, event.y_root)





def choose_folder():

    folder = filedialog.askdirectory()

    if folder:

        folder_var.set(os.path.normpath(folder))

        load_folder(folder)





def apply_style(mode):

    c = PALETTE[mode]

    style = ttk.Style()

    style.theme_use("clam")

    style.configure("Treeview", background=c["card"], fieldbackground=c["card"], foreground=c["fg"],

                    rowheight=36, borderwidth=0, font=("Segoe UI", 10))

    style.configure("Treeview.Heading", background=c["head"], foreground=c["muted"], relief="flat",

                    borderwidth=0, padding=(10, 8), font=("Segoe UI", 9, "bold"))

    style.map("Treeview", background=[("selected", ACCENT)], foreground=[

              ("selected", "#ffffff")])

    style.map("Treeview.Heading", background=[("active", c["head"])])

    style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

    tree.tag_configure("even", background=c["card"])

    tree.tag_configure("odd", background=c["alt"])

    menu.configure(bg=c["card"], fg=c["fg"],

                   activebackground=ACCENT, activeforeground="#ffffff", bd=0)





def toggle_theme():

    mode = "Dark" if theme_switch.get() else "Light"

    ctk.set_appearance_mode(mode)

    apply_style(mode)
# =========================
# GUI
# =========================
ctk.set_appearance_mode("Dark")

ctk.set_default_color_theme("blue")



root = ctk.CTk(fg_color=pair("win"))

root.title("Fast File Search")

root.geometry("1100x720")

root.minsize(860, 560)



folder_var = tk.StringVar(value=DEFAULT_FOLDER)

type_var = tk.StringVar(value="Semua tipe")

status_var = tk.StringVar(value="Belum load folder")

result_var = tk.StringVar(value="Ketik untuk mulai mencari")



root.grid_columnconfigure(0, weight=1)

root.grid_rowconfigure(3, weight=1)
# --- header
header = ctk.CTkFrame(root, fg_color="transparent")

header.grid(row=0, column=0, sticky="ew", padx=28, pady=(22, 8))

header.grid_columnconfigure(0, weight=1)

ctk.CTkLabel(header, text="Fast File Search", font=ctk.CTkFont("Segoe UI", 26, "bold"),

             text_color=pair("fg")).grid(row=0, column=0, sticky="w")

ctk.CTkLabel(header, text="Cari file di folder kerja kamu secara instan",

             font=ctk.CTkFont("Segoe UI", 12), text_color=pair("muted")).grid(row=1, column=0, sticky="w")

theme_switch = ctk.CTkSwitch(header, text="Dark mode", command=toggle_theme, progress_color=ACCENT,

                             text_color=pair("muted"))

theme_switch.select()

theme_switch.grid(row=0, column=1, rowspan=2, sticky="e")
# --- folder card
folder_card = ctk.CTkFrame(root, corner_radius=16, fg_color=pair("card"))

folder_card.grid(row=1, column=0, sticky="ew", padx=28, pady=6)

folder_card.grid_columnconfigure(1, weight=1)

ctk.CTkLabel(folder_card, text="📁  Folder", font=ctk.CTkFont("Segoe UI", 13, "bold"),

             text_color=pair("fg")).grid(row=0, column=0, padx=(18, 10), pady=14)

ctk.CTkEntry(folder_card, textvariable=folder_var, height=38, corner_radius=10, border_width=0,

             fg_color=pair("win"), text_color=pair("fg")).grid(row=0, column=1, sticky="ew", pady=14)

ctk.CTkButton(folder_card, text="Pilih folder", width=110, height=38, corner_radius=10, fg_color=ACCENT,

              hover_color=ACCENT_HOVER, command=choose_folder).grid(row=0, column=2, padx=(10, 6))

ctk.CTkButton(folder_card, text="⟳  Rescan", width=100, height=38, corner_radius=10, fg_color="transparent",

              border_width=1, border_color=ACCENT, text_color=ACCENT, hover_color=pair("win"),

              command=lambda: load_folder(folder_var.get())).grid(row=0, column=3, padx=(0, 18))
# --- search card
search_card = ctk.CTkFrame(root, corner_radius=16, fg_color=pair("card"))

search_card.grid(row=2, column=0, sticky="ew", padx=28, pady=6)

search_card.grid_columnconfigure(0, weight=1)

entry_search = ctk.CTkEntry(search_card, height=50, corner_radius=12, border_width=0, fg_color=pair("win"),

                            text_color=pair("fg"), font=ctk.CTkFont("Segoe UI", 15),

                            placeholder_text="🔍  Cari nama file... (boleh lebih dari satu kata)")

entry_search.grid(row=0, column=0, sticky="ew", padx=(18, 10), pady=(18, 8))

entry_search.bind("<KeyRelease>", on_key)

entry_search.bind("<Escape>", clear_search)

ctk.CTkOptionMenu(search_card, values=list(TYPES), variable=type_var, width=150, height=50, corner_radius=12,

                  fg_color=pair("win"), button_color=ACCENT, button_hover_color=ACCENT_HOVER,

                  text_color=pair("fg"), command=lambda _v: do_search()).grid(row=0, column=1, padx=(0, 18), pady=(18, 8))



info = ctk.CTkFrame(search_card, fg_color="transparent")

info.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 8))

info.grid_columnconfigure(1, weight=1)

ctk.CTkLabel(info, textvariable=status_var, text_color=ACCENT,

             font=ctk.CTkFont("Segoe UI", 12)).grid(row=0, column=0, sticky="w")

ctk.CTkLabel(info, textvariable=result_var, text_color=pair(

    "muted"), font=ctk.CTkFont("Segoe UI", 12)).grid(row=0, column=1, sticky="e")

progress = ctk.CTkProgressBar(

    search_card, height=4, mode="indeterminate", progress_color=ACCENT, fg_color=pair("win"))

progress.grid(row=2, column=0, columnspan=2,

              sticky="ew", padx=20, pady=(0, 14))

progress.set(0)
# --- results card
results_card = ctk.CTkFrame(root, corner_radius=16, fg_color=pair("card"))

results_card.grid(row=3, column=0, sticky="nsew", padx=28, pady=6)

results_card.grid_columnconfigure(0, weight=1)

results_card.grid_rowconfigure(0, weight=1)



tree = ttk.Treeview(results_card, columns=(

    "name", "type", "path"), show="headings", selectmode="browse")

tree.heading("name", text="NAMA FILE", anchor="w")

tree.heading("type", text="TIPE", anchor="center")

tree.heading("path", text="LOKASI", anchor="w")

tree.column("name", width=380, anchor="w")

tree.column("type", width=80, anchor="center", stretch=False)

tree.column("path", width=560, anchor="w")

tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)

scroll = ctk.CTkScrollbar(

    results_card, command=tree.yview, button_color=pair("muted"))

scroll.grid(row=0, column=1, sticky="ns", padx=(4, 8), pady=10)

tree.configure(yscrollcommand=scroll.set)



tree.bind("<Double-Button-1>", open_file)

tree.bind("<Return>", open_file)

tree.bind("<Button-3>", show_menu)



menu = tk.Menu(root, tearoff=0)

menu.add_command(label="  Buka file", command=open_file)

menu.add_command(label="  Buka lokasi folder", command=open_folder)

menu.add_command(label="  Copy path", command=copy_path)
# --- footer
ctk.CTkLabel(root, text="Double click / Enter: buka file   •   Klik kanan: menu   •   Esc: hapus pencarian",

             font=ctk.CTkFont("Segoe UI", 11), text_color=pair("muted")).grid(row=4, column=0, pady=(4, 14))



apply_style("Dark")

entry_search.focus()



if os.path.isdir(DEFAULT_FOLDER):

    load_folder(DEFAULT_FOLDER)



root.mainloop()
