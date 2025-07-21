import customtkinter as ctk
from tkinter import ttk, messagebox


class DatabaseEditorWindow(ctk.CTkToplevel):
    def __init__(self, master, tm_instance):
        super().__init__(master)
        self.tm = tm_instance

        self.title("Translation Memory Editor")
        self.geometry("900x600")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.master = master

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.selected_source_text = None

        self.setup_ui()
        self.load_entries()

    def setup_ui(self):
        controls_frame = ctk.CTkFrame(self)
        controls_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        controls_frame.grid_columnconfigure(0, weight=1)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.load_entries())
        search_entry = ctk.CTkEntry(controls_frame, textvariable=self.search_var,
                                    placeholder_text="Search Japanese or English text...")
        search_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        refresh_button = ctk.CTkButton(controls_frame, text="Refresh", command=self.load_entries)
        refresh_button.grid(row=0, column=1, padx=10, pady=10)

        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading", background="#565b5e", foreground="white", relief="flat",
                        font=('Calibri', 10, 'bold'))
        style.map("Treeview.Heading", background=[('active', '#3484ba')])
        style.configure("Treeview", borderwidth=0, relief="flat", rowheight=25)

        self.tree = ttk.Treeview(table_frame, columns=("id", "source", "translation"), show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("source", text="Original (Japanese)")
        self.tree.heading("translation", text="Translation (English)")
        self.tree.column("id", width=50, stretch=False, anchor="center")
        self.tree.column("source", width=350)
        self.tree.column("translation", width=350)

        self.tree.tag_configure("oddrow", background="#2a2d2e", foreground="white")
        self.tree.tag_configure("evenrow", background="#343638", foreground="white")

        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<Delete>", self.delete_on_key_press)
        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)

        edit_frame = ctk.CTkFrame(self)
        edit_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        edit_frame.grid_columnconfigure(0, weight=1)

        self.edit_entry = ctk.CTkEntry(edit_frame, placeholder_text="Select a row to edit its translation...")
        self.edit_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        save_button = ctk.CTkButton(edit_frame, text="Save Changes", command=self.save_changes, width=120)
        save_button.grid(row=0, column=1, padx=(0, 10), pady=10)

        delete_button = ctk.CTkButton(edit_frame, text="Delete Entry", fg_color="#c23434", hover_color="#992929",
                                      command=self.delete_selected, width=120)
        delete_button.grid(row=0, column=2, padx=(0, 10), pady=10)

        flush_button = ctk.CTkButton(edit_frame, text="Flush Database", fg_color="#8B0000", hover_color="#550000",
                                     command=self.flush_database, width=120)
        flush_button.grid(row=0, column=3, padx=0, pady=10)

    def delete_on_key_press(self, event):
        self.delete_selected()

    def flush_database(self):
        if messagebox.askyesno("Confirm Database Flush",
                               "Are you sure you want to permanently delete ALL entries from the Translation Memory?\n\nThis action cannot be undone.",
                               parent=self, icon='warning'):
            self.tm.flush_all()
            self.load_entries()
            messagebox.showinfo("Success", "The Translation Memory database has been flushed.", parent=self)

    def load_entries(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        search_term = self.search_var.get()
        entries = self.tm.fetch_all_entries(search_term)

        for i, entry in enumerate(entries):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=entry, tags=(tag,))

    def on_item_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return

        item = self.tree.item(selected_items[0])
        try:
            self.selected_source_text = item["values"][1]
            translation = item["values"][2]
            self.edit_entry.delete(0, "end")
            self.edit_entry.insert(0, translation)
        except IndexError:
            self.selected_source_text = None
            self.edit_entry.delete(0, "end")

    def save_changes(self):
        if not self.selected_source_text:
            messagebox.showwarning("No Selection", "Please select an entry from the table to update.", parent=self)
            return

        new_translation = self.edit_entry.get()
        if new_translation:
            self.tm.update_translation(self.selected_source_text, new_translation)
            messagebox.showinfo("Success", "Translation updated successfully.", parent=self)
            self.load_entries()
        else:
            messagebox.showwarning("Input Error", "Translation cannot be empty.", parent=self)

    def delete_selected(self):
        if not self.selected_source_text:
            messagebox.showwarning("No Selection", "Please select an entry from the table to delete.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete",
                               f"Are you sure you want to permanently delete the entry for:\n\n'{self.selected_source_text}'?",
                               parent=self):
            self.tm.delete_entry(self.selected_source_text)
            self.edit_entry.delete(0, "end")
            self.selected_source_text = None
            self.load_entries()

    def on_close(self):
        self.master.db_editor_window = None
        self.destroy()