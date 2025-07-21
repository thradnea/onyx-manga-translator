import os
import shutil
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox, Tk, Label
from tkinter import PhotoImage
from natsort import natsorted
import sys
from datetime import datetime

from manga_translator.translator import MangaTranslator
from manga_translator.memory import TranslationMemory
from db_editor import DatabaseEditorWindow
import config_manager

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DEB_LOG_FILE = os.path.join(APP_DIR, "deb.log")


def log_to_deb_file(message):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(DEB_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"LOGGING FAILED: {e}")


if os.path.exists(DEB_LOG_FILE):
    os.remove(DEB_LOG_FILE)
log_to_deb_file("=== NEW SESSION STARTED ===")


def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def show_splash(duration_ms=1500):
    splash = Tk()
    splash.overrideredirect(True)
    img = PhotoImage(file=resource_path("splash.png"))
    Label(splash, image=img).pack()
    w, h = img.width(), img.height()
    x = (splash.winfo_screenwidth()  - w) // 2
    y = (splash.winfo_screenheight() - h) // 2
    splash.geometry(f"{w}x{h}+{x}+{y}")
    splash.update()
    splash.after(duration_ms, splash.destroy)
    splash.mainloop()


class App(ctk.CTk):
    def __init__(self):
        log_to_deb_file("=== App.__init__ STARTED ===")
        super().__init__()

        self.set_window_icon()

        self.title("Onyx")
        self.geometry("800x650")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.input_folder = ctk.StringVar()
        self.output_folder = ctk.StringVar(value=os.path.abspath("output"))
        self.api_key_path = ctk.StringVar()
        self.is_translating = False
        self.db_editor_window = None
        self.translator_instance = None

        self.create_widgets()
        self.load_initial_config()
        log_to_deb_file("=== App.__init__ FINISHED ===")

    def set_window_icon(self):
        try:
            png_path = r"C:\Users\airon\Desktop\Stuff\Scagg\.venv - Copy (2)\icon.png"
            if os.path.exists(png_path):
                self._app_icon = PhotoImage(file=png_path)
                self.iconphoto(True, self._app_icon)
            else:
                log_to_deb_file(f"Icon not found at hardcoded path: {png_path}")
        except Exception as e:
            log_to_deb_file(f"FAILED to set PNG icon with hardcoded path: {e}")

    def create_widgets(self):
        log_to_deb_file("--- create_widgets started ---")
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        top_frame.grid_columnconfigure(1, weight=1)
        title_label = ctk.CTkLabel(top_frame, text="Onyx Manga & Comic Translator",
                                   font=ctk.CTkFont(size=28, weight="bold"))
        title_label.grid(row=0, column=0, sticky="w")
        theme_switch = ctk.CTkSwitch(top_frame, text="Light/Dark Mode",
                                     command=lambda: ctk.set_appearance_mode("light" if theme_switch.get() else "dark"))
        theme_switch.grid(row=0, column=2, sticky="e")
        tab_view = ctk.CTkTabview(self, anchor="w")
        tab_view.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        tab_view.add("Translate")
        tab_view.add("Manage Data")
        translate_tab = tab_view.tab("Translate")
        translate_tab.grid_columnconfigure(0, weight=1)
        config_frame = ctk.CTkFrame(translate_tab)
        config_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        config_frame.grid_columnconfigure(1, weight=1)
        api_label = ctk.CTkLabel(config_frame, text="Google API Key (.json):")
        api_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.api_entry = ctk.CTkEntry(config_frame, textvariable=self.api_key_path)
        self.api_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        api_button = ctk.CTkButton(config_frame, text="Browse...", command=self.browse_api_key, width=100)
        api_button.grid(row=0, column=2, padx=10, pady=10)
        folder_frame = ctk.CTkFrame(translate_tab)
        folder_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        folder_frame.grid_columnconfigure(1, weight=1)
        in_label = ctk.CTkLabel(folder_frame, text="Input Folder:")
        in_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        in_entry = ctk.CTkEntry(folder_frame, textvariable=self.input_folder)
        in_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        in_button = ctk.CTkButton(folder_frame, text="Select...", command=self.browse_input_folder, width=100)
        in_button.grid(row=0, column=2, padx=10, pady=10)
        out_label = ctk.CTkLabel(folder_frame, text="Output Folder:")
        out_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        out_entry = ctk.CTkEntry(folder_frame, textvariable=self.output_folder)
        out_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        out_button = ctk.CTkButton(folder_frame, text="Select...", command=self.browse_output_folder, width=100)
        out_button.grid(row=1, column=2, padx=10, pady=10)
        self.start_button = ctk.CTkButton(translate_tab, text="Start Translation", font=ctk.CTkFont(size=18),
                                          command=self.start_translation_thread)
        self.start_button.grid(row=2, column=0, padx=10, pady=20, sticky="ew", ipady=10)
        manage_tab = tab_view.tab("Manage Data")
        manage_tab.grid_columnconfigure(0, weight=1)
        manage_tab.grid_columnconfigure(1, weight=1)
        db_button = ctk.CTkButton(manage_tab, text="Open Translation Editor", font=ctk.CTkFont(size=14),
                                  command=self.open_db_editor)
        db_button.grid(row=0, column=0, columnspan=2, padx=10, pady=20, sticky="ew", ipady=6)
        clear_input_button = ctk.CTkButton(manage_tab, text="Wipe Input Folder", fg_color="#c23434",
                                           hover_color="#992929", command=self.clear_input_folder)
        clear_input_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        clear_output_button = ctk.CTkButton(manage_tab, text="Wipe Output Folder", fg_color="#c23434",
                                            hover_color="#992929", command=self.clear_output_folder)
        clear_output_button.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        status_frame = ctk.CTkFrame(self)
        status_frame.grid(row=2, column=0, padx=20, pady=(5, 20), sticky="ewns")
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.progress_bar = ctk.CTkProgressBar(status_frame, mode='determinate')
        self.progress_bar.set(0)
        self.progress_bar.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        self.status_box = ctk.CTkTextbox(status_frame, state="disabled", font=ctk.CTkFont(family="monospace"))
        self.status_box.grid(row=1, column=0, padx=10, pady=(5, 10), sticky="nsew")
        log_to_deb_file("--- create_widgets finished ---")

    def log_status(self, message):
        log_to_deb_file(f"STATUS: {message}")
        if hasattr(self, 'status_box') and self.status_box.winfo_exists():
            self.status_box.configure(state="normal")
            self.status_box.insert("end", message + "\n")
            self.status_box.see("end")
            self.status_box.configure(state="disabled")
        else:
            print(message)

    def update_progress(self, value):
        self.progress_bar.set(value)

    def load_initial_config(self):
        log_to_deb_file("--- load_initial_config started ---")
        config = config_manager.load_config()
        self.api_key_path.set(config.get("google_api_key_path", ""))
        self.input_folder.set(config.get("input_folder", ""))
        self.output_folder.set(config.get("output_folder", os.path.abspath("output")))
        self.log_status("Welcome! Please configure your settings and start a translation.")
        os.makedirs(self.output_folder.get(), exist_ok=True)
        log_to_deb_file("--- load_initial_config finished ---")

    def save_current_config(self):
        config = {"google_api_key_path": self.api_key_path.get(), "input_folder": self.input_folder.get(),
                  "output_folder": self.output_folder.get()}
        config_manager.save_config(config)

    def browse_api_key(self):
        path = filedialog.askopenfilename(title="Select Google API Key File", filetypes=[("JSON files", "*.json")])
        if path:
            self.api_key_path.set(path)
            self.save_current_config()
            self.log_status("API Key path set and saved.")

    def browse_input_folder(self):
        path = filedialog.askdirectory(title="Select Input Folder")
        if path:
            self.input_folder.set(path)
            self.save_current_config()

    def browse_output_folder(self):
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            self.output_folder.set(path)
            self.save_current_config()

    def set_ui_state(self, is_enabled: bool):
        state = "normal" if is_enabled else "disabled"
        self.start_button.configure(state=state)

    def start_translation_thread(self):
        if self.is_translating: return
        if not all([self.input_folder.get(), self.output_folder.get(), self.api_key_path.get()]):
            self.log_status("❌ Error: Please specify API Key, Input, and Output folders.")
            return
        self.is_translating = True
        self.set_ui_state(False)
        self.log_status("🚀 Starting translation process...")
        self.progress_bar.set(0)
        thread = threading.Thread(target=self.translation_worker)
        thread.daemon = True
        thread.start()

    def translation_worker(self):
        try:
            self.log_status("Initializing translation engine...")
            if not self.translator_instance or self.translator_instance.google_api_key_path != self.api_key_path.get():
                self.translator_instance = MangaTranslator(google_api_key_path=self.api_key_path.get())
            input_dir = self.input_folder.get()
            output_dir = self.output_folder.get()
            image_files = natsorted([f for f in os.listdir(input_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))])
            if not image_files:
                self.log_status("⚠️ No image files found in the input directory.")
                self.after(0, self.translation_finished)
                return
            total_files = len(image_files)
            for i, filename in enumerate(image_files):
                if not self.is_translating:
                    self.log_status("Translation cancelled.")
                    break
                self.log_status(f"Processing page {i + 1}/{total_files}: {filename}")
                self.translator_instance.process_page(os.path.join(input_dir, filename),
                                                      os.path.join(output_dir, filename))
                self.log_status(f"   -> TM has {self.translator_instance.tm.count_entries()} unique entries.")
                self.after(0, self.update_progress, (i + 1) / total_files)
            self.log_status("\n🎉 Translation complete! Check the output folder.")
        except Exception as e:
            import traceback
            self.log_status(f"\n❌ An error occurred: {e}\n{traceback.format_exc()}")
        finally:
            self.after(0, self.translation_finished)

    def translation_finished(self):
        self.is_translating = False
        self.set_ui_state(True)
        self.progress_bar.set(0)

    def clear_folder_contents(self, folder_path, folder_name):
        if not folder_path or not os.path.isdir(folder_path):
            self.log_status(f"⚠️ Cannot clear '{folder_name}': Folder path is not set or invalid.")
            return
        if messagebox.askyesno("Confirm Action",
                               f"Are you sure you want to permanently delete all files in the '{folder_name}' folder?\n\n({folder_path})"):
            self.log_status(f"Clearing contents of {folder_name} folder...")
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    self.log_status(f"❌ Failed to delete {file_path}. Reason: {e}")
            self.log_status(f"✅ {folder_name} folder has been cleared.")

    def clear_input_folder(self):
        self.clear_folder_contents(self.input_folder.get(), "Input")

    def clear_output_folder(self):
        self.clear_folder_contents(self.output_folder.get(), "Output")

    def open_db_editor(self):
        if self.db_editor_window is None or not self.db_editor_window.winfo_exists():
            tm = self.translator_instance.tm if self.translator_instance else TranslationMemory()
            self.db_editor_window = DatabaseEditorWindow(self, tm)
            self.db_editor_window.grab_set()
        else:
            self.db_editor_window.focus()