import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from threading import Thread
import os
import sys
import platform
import subprocess
import queue
import time

from downloader import download_and_convert
from playsound import playsound
from config_manager import save_config, load_config

class YouTubeAudioDownloader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Audio Downloader")
        self.geometry("550x350")
        self.minsize(400, 300)

        self.dark_mode = False
        self.download_thread = None
        self.queue = queue.Queue()

        self.folder_path = load_config() or os.path.expanduser("~")
        self.filename = tk.StringVar(value="audio")

        self.create_widgets()
        self.setup_drag_and_drop()
        self.set_theme(dark=False)
        self.check_queue()

    def create_widgets(self):
        pad = 8

        tk.Label(self, text="Inserisci link YouTube:", font=("Segoe UI", 11)).pack(anchor="w", padx=pad, pady=(pad, 0))
        self.link_entry = tk.Entry(self, font=("Segoe UI", 11))
        self.link_entry.pack(fill="x", padx=pad)
        self.link_entry.focus()

        tk.Label(self, text="Nome file (senza estensione):", font=("Segoe UI", 11)).pack(anchor="w", padx=pad, pady=(pad,0))
        self.filename_entry = tk.Entry(self, textvariable=self.filename, font=("Segoe UI", 11))
        self.filename_entry.pack(fill="x", padx=pad)

        frame_folder = tk.Frame(self)
        frame_folder.pack(fill="x", padx=pad, pady=(pad,0))
        tk.Label(frame_folder, text="Cartella di salvataggio:", font=("Segoe UI", 11)).pack(side="left")
        self.folder_label = tk.Label(frame_folder, text=self.folder_path, font=("Segoe UI", 9), fg="blue", cursor="hand2")
        self.folder_label.pack(side="left", padx=5, fill="x", expand=True)
        self.folder_label.bind("<Button-1>", self.choose_folder)

        frame_btn = tk.Frame(self)
        frame_btn.pack(fill="x", padx=pad, pady=pad)
        self.download_btn = ttk.Button(frame_btn, text="Scarica e Converti", command=self.start_download)
        self.download_btn.pack(side="left", expand=True, fill="x")

        self.theme_btn = ttk.Button(frame_btn, text="Tema Scuro", command=self.toggle_theme)
        self.theme_btn.pack(side="left", expand=True, fill="x", padx=(5,0))

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=pad, pady=(0, pad))
        self.progress.pack_forget()

        self.status_box = ScrolledText(self, height=6, font=("Segoe UI", 10), state="disabled")
        self.status_box.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

        self.bind_all("<Control-t>", lambda e: self.toggle_theme())

    def setup_drag_and_drop(self):
        def drop(event):
            data = event.data
            if data.startswith("{") and data.endswith("}"):
                data = data[1:-1]
            self.link_entry.delete(0, "end")
            self.link_entry.insert(0, data)
            self.log(f"[DRAG&DROP] Link inserito: {data}")

        try:
            import tkinterdnd2
            self.dnd = tkinterdnd2.TkinterDnD.Tk()
            self.link_entry.drop_target_register(tkinterdnd2.DND_TEXT)
            self.link_entry.dnd_bind('<<Drop>>', drop)
        except ImportError:
            pass

    def choose_folder(self, event=None):
        path = filedialog.askdirectory(initialdir=self.folder_path, title="Seleziona cartella di salvataggio")
        if path:
            self.folder_path = path
            self.folder_label.config(text=path)
            self.log(f"[INFO] Cartella di salvataggio cambiata: {path}")
            save_config(path)

    def toggle_theme(self):
        self.set_theme(not self.dark_mode)

    def set_theme(self, dark: bool):
        self.dark_mode = dark
        if dark:
            bg = "#2e2e2e"
            fg = "white"
            entry_bg = "#454545"
            self.theme_btn.config(text="Tema Chiaro")
        else:
            bg = "white"
            fg = "black"
            entry_bg = "white"
            self.theme_btn.config(text="Tema Scuro")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", background=bg, foreground=fg)
        style.configure("TProgressbar", troughcolor=bg, background="#4a90e2")

        self.configure(bg=bg)
        for widget in self.winfo_children():
            try:
                widget.configure(bg=bg, fg=fg)
            except:
                pass

        self.link_entry.configure(bg=entry_bg, fg=fg, insertbackground=fg)
        self.filename_entry.configure(bg=entry_bg, fg=fg, insertbackground=fg)
        self.folder_label.configure(bg=bg, fg="lightblue" if dark else "blue")
        self.status_box.configure(bg=entry_bg, fg=fg, insertbackground=fg)

    def log(self, text: str):
        self.status_box.configure(state="normal")
        self.status_box.insert("end", text + "\n")
        self.status_box.see("end")
        self.status_box.configure(state="disabled")

    def start_download(self):
        url = self.link_entry.get().strip()
        filename = self.filename.get().strip()
        folder = self.folder_path

        if not url:
            messagebox.showerror("Errore", "Inserisci un link YouTube valido!")
            return
        if not filename:
            messagebox.showerror("Errore", "Inserisci un nome file valido!")
            return

        self.download_btn.config(state="disabled")
        self.progress.pack(fill="x", padx=8, pady=(0,8))
        self.progress.start(10)

        self.log(f"[INFO] Avvio download: {url}")
        self.download_thread = Thread(target=self.download_worker, args=(url, folder, filename), daemon=True)
        self.download_thread.start()

    def download_worker(self, url, folder, filename):
        try:
            for msg in download_and_convert(url, folder, filename):
                self.queue.put(msg)
            self.queue.put("[SUCCESS] Download e conversione completati!")
            sound_path = os.path.join(os.path.dirname(sys.argv[0]), "success.mp3")
            if os.path.isfile(sound_path):
                playsound(sound_path)
        except Exception as e:
            self.queue.put(f"[ERROR] {e}")
        finally:
            self.queue.put("DONE")

    def check_queue(self):
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg == "DONE":
                    self.download_btn.config(state="normal")
                    self.progress.stop()
                    self.progress.pack_forget()
                else:
                    self.log(msg)
        except queue.Empty:
            pass
        self.after(100, self.check_queue)


if __name__ == "__main__":
    app = YouTubeAudioDownloader()
    app.mainloop()
