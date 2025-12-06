import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

# ==========================================
# 1. DATABASE MANAGER
# ==========================================
class DatabaseManager:
    def __init__(self, db_name='writers_notebook.db'):
        self.db_name = db_name
        self._init_tables() 

    def _execute(self, query, params=(), fetch=False):
        conn = None
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(query, params)
            if fetch == 'all':
                result = cursor.fetchall()
            elif fetch == 'one':
                result = cursor.fetchone()
            else:
                result = None
            conn.commit()
            return result
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            if conn: conn.close()

    def _init_tables(self):
        conn = sqlite3.connect(self.db_name)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.close()
        
        self._execute("CREATE TABLE IF NOT EXISTS Stories (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, genre TEXT, target_word_count INTEGER, summary TEXT)")
        self._execute("CREATE TABLE IF NOT EXISTS Characters (id INTEGER PRIMARY KEY AUTOINCREMENT, story_id INTEGER, name TEXT, role TEXT, bio TEXT, FOREIGN KEY (story_id) REFERENCES Stories(id) ON DELETE CASCADE)")
        self._execute("CREATE TABLE IF NOT EXISTS Settings (id INTEGER PRIMARY KEY AUTOINCREMENT, story_id INTEGER, name TEXT, type TEXT, history TEXT, FOREIGN KEY (story_id) REFERENCES Stories(id) ON DELETE CASCADE)")
        self._execute("CREATE TABLE IF NOT EXISTS PlotPoints (id INTEGER PRIMARY KEY AUTOINCREMENT, story_id INTEGER, chapter_number INTEGER, event_description TEXT, type TEXT, FOREIGN KEY (story_id) REFERENCES Stories(id) ON DELETE CASCADE)")
        self._execute("CREATE TABLE IF NOT EXISTS Themes (id INTEGER PRIMARY KEY AUTOINCREMENT, story_id INTEGER, name TEXT, notes TEXT, FOREIGN KEY (story_id) REFERENCES Stories(id) ON DELETE CASCADE)")
        self._execute("CREATE TABLE IF NOT EXISTS Chapters (id INTEGER PRIMARY KEY AUTOINCREMENT, story_id INTEGER, chapter_num INTEGER, title TEXT, content TEXT, FOREIGN KEY (story_id) REFERENCES Stories(id) ON DELETE CASCADE)")

    # --- CRUD METHODS ---
    def create_story(self, title, genre, word_count, summary):
        self._execute("INSERT INTO Stories (title, genre, target_word_count, summary) VALUES (?, ?, ?, ?)", (title, genre, int(word_count or 0), summary))
    def get_all_stories(self):
        return self._execute("SELECT id, title, genre, target_word_count FROM Stories ORDER BY id DESC", fetch='all') or []
    def get_story_details(self, story_id):
        return self._execute("SELECT id, title, genre, target_word_count, summary FROM Stories WHERE id = ?", (story_id,), fetch='one')
    def delete_story(self, story_id):
        self._execute("DELETE FROM Stories WHERE id = ?", (story_id,))

    def create_character(self, sid, name, role, bio):
        self._execute("INSERT INTO Characters (story_id, name, role, bio) VALUES (?, ?, ?, ?)", (sid, name, role, bio))
    def get_characters(self, sid):
        return self._execute("SELECT id, name, role, bio FROM Characters WHERE story_id = ? ORDER BY id", (sid,), fetch='all') or []
    def update_character(self, cid, name, role, bio):
        self._execute("UPDATE Characters SET name = ?, role = ?, bio = ? WHERE id = ?", (name, role, bio, cid))
    def delete_character(self, cid):
        self._execute("DELETE FROM Characters WHERE id = ?", (cid,))

    def create_setting(self, sid, name, type_, hist):
        self._execute("INSERT INTO Settings (story_id, name, type, history) VALUES (?, ?, ?, ?)", (sid, name, type_, hist))
    def get_settings(self, sid):
        return self._execute("SELECT id, name, type, history FROM Settings WHERE story_id = ? ORDER BY id", (sid,), fetch='all') or []
    def update_setting(self, sid, name, type_, hist):
        self._execute("UPDATE Settings SET name = ?, type = ?, history = ? WHERE id = ?", (name, type_, hist, sid))
    def delete_setting(self, sid):
        self._execute("DELETE FROM Settings WHERE id = ?", (sid,))

    def create_plotpoint(self, sid, ch, ev, ty):
        self._execute("INSERT INTO PlotPoints (story_id, chapter_number, event_description, type) VALUES (?, ?, ?, ?)", (sid, int(ch or 0), ev, ty))
    def get_plotpoints(self, sid):
        return self._execute("SELECT id, chapter_number, event_description, type FROM PlotPoints WHERE story_id = ? ORDER BY chapter_number, id", (sid,), fetch='all') or []
    def update_plotpoint(self, pid, ch, ev, ty):
        self._execute("UPDATE PlotPoints SET chapter_number = ?, event_description = ?, type = ? WHERE id = ?", (int(ch or 0), ev, ty, pid))
    def delete_plotpoint(self, pid):
        self._execute("DELETE FROM PlotPoints WHERE id = ?", (pid,))

    def create_theme(self, sid, name, notes):
        self._execute("INSERT INTO Themes (story_id, name, notes) VALUES (?, ?, ?)", (sid, name, notes))
    def get_themes(self, sid):
        return self._execute("SELECT id, name, notes FROM Themes WHERE story_id = ? ORDER BY id", (sid,), fetch='all') or []
    def update_theme(self, tid, name, notes):
        self._execute("UPDATE Themes SET name = ?, notes = ? WHERE id = ?", (name, notes, tid))
    def delete_theme(self, tid):
        self._execute("DELETE FROM Themes WHERE id = ?", (tid,))

    def create_chapter(self, sid, num, title, content):
        self._execute("INSERT INTO Chapters (story_id, chapter_num, title, content) VALUES (?, ?, ?, ?)", (sid, num, title, content))
    def get_chapters(self, sid):
        return self._execute("SELECT id, chapter_num, title, content FROM Chapters WHERE story_id = ? ORDER BY chapter_num", (sid,), fetch='all') or []
    def update_chapter(self, cid, num, title, content):
        self._execute("UPDATE Chapters SET chapter_num = ?, title = ?, content = ? WHERE id = ?", (num, title, content, cid))
    def delete_chapter(self, cid):
        self._execute("DELETE FROM Chapters WHERE id = ?", (cid,))


# ==========================================
# 2. TABS LOGIC
# ==========================================
FONT_LABEL = ("Segoe UI", 11)
FONT_ENTRY = ("Segoe UI", 11)
BTN_UPDATE = "#ffb74d" 
BTN_ADD = "#81c784"    
BTN_CLEAR = "#e0e0e0"  
BTN_DEL = "#e57373"    

class BaseTab(tk.Frame):
    def __init__(self, parent, db, story_id):
        super().__init__(parent, bg="white")
        self.db = db
        self.story_id = story_id
        self.current_id = None
        self._setup_ui()
        self.refresh()

    def create_input_field(self, parent, label_text, row, col, width=25):
        tk.Label(parent, text=label_text, font=FONT_LABEL, bg="white").grid(row=row, column=col, sticky='w', pady=5)
        entry = tk.Entry(parent, font=FONT_ENTRY, width=width, relief="solid", bd=1)
        entry.grid(row=row, column=col+1, padx=(5, 20), pady=5)
        return entry
    
    def create_text_field(self, parent, label_text, row, col):
        tk.Label(parent, text=label_text, font=FONT_LABEL, bg="white").grid(row=row, column=col, sticky='nw', pady=5)
        text = tk.Text(parent, height=4, width=50, font=("Segoe UI", 10), relief="solid", bd=1)
        text.grid(row=row, column=col+1, columnspan=3, padx=5, pady=5, sticky="w")
        return text

    def create_buttons(self, parent, add_cmd, up_cmd, clr_cmd, row):
        f = tk.Frame(parent, bg="white")
        f.grid(row=row, column=1, columnspan=3, sticky='w', pady=15)
        self._btn(f, "SAVE NEW", add_cmd, BTN_ADD).pack(side='left', padx=5)
        self._btn(f, "UPDATE SELECTED", up_cmd, BTN_UPDATE).pack(side='left', padx=5)
        self._btn(f, "CLEAR FORM", clr_cmd, BTN_CLEAR, "black").pack(side='left', padx=5)

    def _btn(self, parent, text, cmd, bg, fg="white"):
        return tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg, font=("Segoe UI", 9, "bold"), relief="flat", padx=15, pady=5, cursor="hand2")

    def reselect_item(self, item_id):
        for i in range(self.listbox.size()):
            if self.listbox.get(i).startswith(f"[{item_id}]"):
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(i)
                self.listbox.activate(i)
                self.listbox.see(i)
                break

class CharactersTab(BaseTab):
    def _setup_ui(self):
        input_frame = tk.LabelFrame(self, text="Character Details", font=("Segoe UI", 12, "bold"), bg="white", padx=15, pady=10)
        input_frame.pack(fill='x', padx=20, pady=15)
        self.char_name = self.create_input_field(input_frame, "Name:", 0, 0)
        self.char_role = self.create_input_field(input_frame, "Role:", 0, 2)
        self.char_bio = self.create_text_field(input_frame, "Bio:", 1, 0)
        self.create_buttons(input_frame, self._add, self._update, self._clear, 2)
        
        list_frame = tk.Frame(self, bg="white")
        list_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        self.listbox = tk.Listbox(list_frame, font=FONT_ENTRY, height=12, bd=0, bg="#f9f9f9", highlightthickness=1, highlightbackground="#ccc", exportselection=False)
        self.listbox.pack(side='left', fill='both', expand=True)
        self.listbox.bind('<<ListboxSelect>>', self._on_select)
        sb = tk.Scrollbar(list_frame, command=self.listbox.yview)
        sb.pack(side='right', fill='y')
        self.listbox.config(yscrollcommand=sb.set)
        tk.Button(self, text="DELETE SELECTED", command=self._delete, bg=BTN_DEL, fg="white", font=("Segoe UI", 9, "bold"), relief="flat").pack(pady=5, anchor="e", padx=20)

    def _add(self):
        name = self.char_name.get().strip()
        if not name: return messagebox.showerror("Error", "Name is required.")
        self.db.create_character(self.story_id, name, self.char_role.get(), self.char_bio.get("1.0", tk.END))
        self.refresh(); self._clear()

    def _update(self):
        if not self.current_id: return messagebox.showwarning("Select", "Select a character first.")
        name = self.char_name.get().strip()
        if not name: return messagebox.showerror("Error", "Name is required.")
        self.db.update_character(self.current_id, name, self.char_role.get(), self.char_bio.get("1.0", tk.END))
        self.refresh(); self.reselect_item(self.current_id)

    def _delete(self):
        if self.current_id and messagebox.askyesno("Confirm", "Delete?"):
            self.db.delete_character(self.current_id)
            self.refresh(); self._clear()

    def _on_select(self, event):
        sel = self.listbox.curselection()
        if not sel: return
        try:
            self.current_id = int(self.listbox.get(sel[0]).split(']')[0].strip('['))
            for c in self.db.get_characters(self.story_id):
                if c[0] == self.current_id:
                    self.char_name.delete(0, tk.END); self.char_name.insert(0, c[1] or '')
                    self.char_role.delete(0, tk.END); self.char_role.insert(0, c[2] or '')
                    self.char_bio.delete("1.0", tk.END); self.char_bio.insert("1.0", c[3] or '')
                    break
        except: pass

    def _clear(self):
        self.char_name.delete(0, tk.END); self.char_role.delete(0, tk.END); self.char_bio.delete("1.0", tk.END)
        self.current_id = None; self.listbox.selection_clear(0, tk.END)

    def refresh(self):
        self.listbox.delete(0, tk.END)
        for c in self.db.get_characters(self.story_id): self.listbox.insert(tk.END, f"[{c[0]}]  {c[1]}  --  {c[2]}")

class SettingsTab(BaseTab):
    def _setup_ui(self):
        input_frame = tk.LabelFrame(self, text="Setting Details", font=("Segoe UI", 12, "bold"), bg="white", padx=15, pady=10)
        input_frame.pack(fill='x', padx=20, pady=15)
        self.set_name = self.create_input_field(input_frame, "Name:", 0, 0)
        self.set_type = self.create_input_field(input_frame, "Type:", 0, 2)
        self.set_hist = self.create_text_field(input_frame, "History:", 1, 0)
        self.create_buttons(input_frame, self._add, self._update, self._clear, 2)
        
        list_frame = tk.Frame(self, bg="white")
        list_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        self.listbox = tk.Listbox(list_frame, font=FONT_ENTRY, height=12, bd=0, bg="#f9f9f9", highlightthickness=1, highlightbackground="#ccc", exportselection=False)
        self.listbox.pack(side='left', fill='both', expand=True)
        self.listbox.bind('<<ListboxSelect>>', self._on_select)
        sb = tk.Scrollbar(list_frame, command=self.listbox.yview)
        sb.pack(side='right', fill='y')
        self.listbox.config(yscrollcommand=sb.set)
        tk.Button(self, text="DELETE SELECTED", command=self._delete, bg=BTN_DEL, fg="white", font=("Segoe UI", 9, "bold"), relief="flat").pack(pady=5, anchor="e", padx=20)

    def _add(self):
        name = self.set_name.get().strip()
        if not name: return messagebox.showerror("Error", "Name required.")
        self.db.create_setting(self.story_id, name, self.set_type.get(), self.set_hist.get("1.0", tk.END))
        self.refresh(); self._clear()

    def _update(self):
        if not self.current_id: return messagebox.showwarning("Select", "Select a setting.")
        self.db.update_setting(self.current_id, self.set_name.get(), self.set_type.get(), self.set_hist.get("1.0", tk.END))
        self.refresh(); self.reselect_item(self.current_id)

    def _delete(self):
        if self.current_id and messagebox.askyesno("Confirm", "Delete?"):
            self.db.delete_setting(self.current_id); self.refresh(); self._clear()

    def _on_select(self, event):
        sel = self.listbox.curselection()
        if not sel: return
        try:
            self.current_id = int(self.listbox.get(sel[0]).split(']')[0].strip('['))
            for d in self.db.get_settings(self.story_id):
                if d[0] == self.current_id:
                    self.set_name.delete(0, tk.END); self.set_name.insert(0, d[1] or '')
                    self.set_type.delete(0, tk.END); self.set_type.insert(0, d[2] or '')
                    self.set_hist.delete("1.0", tk.END); self.set_hist.insert("1.0", d[3] or '')
                    break
        except: pass

    def _clear(self):
        self.set_name.delete(0, tk.END); self.set_type.delete(0, tk.END); self.set_hist.delete("1.0", tk.END)
        self.current_id = None; self.listbox.selection_clear(0, tk.END)

    def refresh(self):
        self.listbox.delete(0, tk.END)
        for s in self.db.get_settings(self.story_id): self.listbox.insert(tk.END, f"[{s[0]}]  {s[1]}  ({s[2]})")

class PlotPointsTab(BaseTab):
    def _setup_ui(self):
        input_frame = tk.LabelFrame(self, text="Plot Point Details", font=("Segoe UI", 12, "bold"), bg="white", padx=15, pady=10)
        input_frame.pack(fill='x', padx=20, pady=15)
        self.plot_chapter = self.create_input_field(input_frame, "Chapter:", 0, 0, width=10)
        self.plot_type = self.create_input_field(input_frame, "Type:", 0, 2)
        self.plot_event = self.create_text_field(input_frame, "Event:", 1, 0)
        self.create_buttons(input_frame, self._add, self._update, self._clear, 2)
        
        list_frame = tk.Frame(self, bg="white")
        list_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        self.listbox = tk.Listbox(list_frame, font=FONT_ENTRY, height=12, bd=0, bg="#f9f9f9", highlightthickness=1, highlightbackground="#ccc", exportselection=False)
        self.listbox.pack(side='left', fill='both', expand=True)
        self.listbox.bind('<<ListboxSelect>>', self._on_select)
        sb = tk.Scrollbar(list_frame, command=self.listbox.yview)
        sb.pack(side='right', fill='y')
        self.listbox.config(yscrollcommand=sb.set)
        tk.Button(self, text="DELETE SELECTED", command=self._delete, bg=BTN_DEL, fg="white", font=("Segoe UI", 9, "bold"), relief="flat").pack(pady=5, anchor="e", padx=20)

    def _add(self):
        event = self.plot_event.get("1.0", tk.END).strip()
        if not event: return messagebox.showerror("Error", "Event required.")
        self.db.create_plotpoint(self.story_id, self.plot_chapter.get(), event, self.plot_type.get())
        self.refresh(); self._clear()

    def _update(self):
        if not self.current_id: return messagebox.showwarning("Select", "Select a plot point.")
        event = self.plot_event.get("1.0", tk.END).strip()
        if not event: return messagebox.showerror("Error", "Event required.")
        self.db.update_plotpoint(self.current_id, self.plot_chapter.get(), event, self.plot_type.get())
        self.refresh(); self.reselect_item(self.current_id)

    def _delete(self):
        if self.current_id and messagebox.askyesno("Confirm", "Delete?"):
            self.db.delete_plotpoint(self.current_id); self.refresh(); self._clear()

    def _on_select(self, event):
        sel = self.listbox.curselection()
        if not sel: return
        try:
            self.current_id = int(self.listbox.get(sel[0]).split(']')[0].strip('['))
            for d in self.db.get_plotpoints(self.story_id):
                if d[0] == self.current_id:
                    self.plot_chapter.delete(0, tk.END); self.plot_chapter.insert(0, str(d[1]) if d[1] else '')
                    self.plot_event.delete("1.0", tk.END); self.plot_event.insert("1.0", d[2] or '')
                    self.plot_type.delete(0, tk.END); self.plot_type.insert(0, d[3] or '')
                    break
        except: pass

    def _clear(self):
        self.plot_chapter.delete(0, tk.END); self.plot_type.delete(0, tk.END); self.plot_event.delete("1.0", tk.END)
        self.current_id = None; self.listbox.selection_clear(0, tk.END)

    def refresh(self):
        self.listbox.delete(0, tk.END)
        for p in self.db.get_plotpoints(self.story_id):
            self.listbox.insert(tk.END, f"[{p[0]}]  Ch.{p[1] or '--'} :  {p[2][:60]}...")

class ThemesTab(BaseTab):
    def _setup_ui(self):
        input_frame = tk.LabelFrame(self, text="Theme Details", font=("Segoe UI", 12, "bold"), bg="white", padx=15, pady=10)
        input_frame.pack(fill='x', padx=20, pady=15)
        self.theme_name = self.create_input_field(input_frame, "Theme:", 0, 0, width=40)
        self.theme_notes = self.create_text_field(input_frame, "Notes:", 1, 0)
        self.create_buttons(input_frame, self._add, self._update, self._clear, 2)
        
        list_frame = tk.Frame(self, bg="white")
        list_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        self.listbox = tk.Listbox(list_frame, font=FONT_ENTRY, height=12, bd=0, bg="#f9f9f9", highlightthickness=1, highlightbackground="#ccc", exportselection=False)
        self.listbox.pack(side='left', fill='both', expand=True)
        self.listbox.bind('<<ListboxSelect>>', self._on_select)
        sb = tk.Scrollbar(list_frame, command=self.listbox.yview)
        sb.pack(side='right', fill='y')
        self.listbox.config(yscrollcommand=sb.set)
        tk.Button(self, text="DELETE SELECTED", command=self._delete, bg=BTN_DEL, fg="white", font=("Segoe UI", 9, "bold"), relief="flat").pack(pady=5, anchor="e", padx=20)

    def _add(self):
        name = self.theme_name.get().strip()
        if not name: return messagebox.showerror("Error", "Name required.")
        self.db.create_theme(self.story_id, name, self.theme_notes.get("1.0", tk.END))
        self.refresh(); self._clear()

    def _update(self):
        if not self.current_id: return messagebox.showwarning("Select", "Select a theme.")
        name = self.theme_name.get().strip()
        if not name: return messagebox.showerror("Error", "Name required.")
        self.db.update_theme(self.current_id, name, self.theme_notes.get("1.0", tk.END))
        self.refresh(); self.reselect_item(self.current_id)

    def _delete(self):
        if self.current_id and messagebox.askyesno("Confirm", "Delete?"):
            self.db.delete_theme(self.current_id); self.refresh(); self._clear()

    def _on_select(self, event):
        sel = self.listbox.curselection()
        if not sel: return
        try:
            self.current_id = int(self.listbox.get(sel[0]).split(']')[0].strip('['))
            for d in self.db.get_themes(self.story_id):
                if d[0] == self.current_id:
                    self.theme_name.delete(0, tk.END); self.theme_name.insert(0, d[1] or '')
                    self.theme_notes.delete("1.0", tk.END); self.theme_notes.insert("1.0", d[2] or '')
                    break
        except: pass

    def _clear(self):
        self.theme_name.delete(0, tk.END); self.theme_notes.delete("1.0", tk.END)
        self.current_id = None; self.listbox.selection_clear(0, tk.END)

    def refresh(self):
        self.listbox.delete(0, tk.END)
        for t in self.db.get_themes(self.story_id): self.listbox.insert(tk.END, f"[{t[0]}]  {t[1]}")


# ==========================================
# 3. SPLIT-SCREEN WORKSTATION
# ==========================================
class StoryWorkstationWindow:
    def __init__(self, parent, db, story_id):
        self.window = tk.Toplevel(parent)
        self.db = db
        self.story_id = story_id
        
        self.window.configure(bg="#f4f4f9")
        details = self.db.get_story_details(story_id)
        title = details[1] if details else "Story Editor"
        self.window.title(f"Workstation: {title}")
        self.window.geometry("1400x800") 

        # --- PANED WINDOW (Split Screen) ---
        self.paned_window = tk.PanedWindow(self.window, orient=tk.HORIZONTAL, sashwidth=6, bg="#ddd")
        self.paned_window.pack(fill='both', expand=True)

        # --- LEFT SIDE: WRITING STATION ---
        self.writing_frame = tk.Frame(self.paned_window, bg="white", padx=10, pady=10)
        self.paned_window.add(self.writing_frame, minsize=500)
        self._setup_writing_area()

        # --- RIGHT SIDE: REFERENCE TABS ---
        self.tabs_frame = tk.Frame(self.paned_window, bg="#f4f4f9", padx=10, pady=10)
        self.paned_window.add(self.tabs_frame, minsize=450)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background="#f4f4f9", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 10), padding=[10, 5])
        
        self.notebook = ttk.Notebook(self.tabs_frame)
        self.notebook.pack(fill='both', expand=True)
        self.notebook.add(CharactersTab(self.notebook, db, story_id), text="Characters")
        self.notebook.add(SettingsTab(self.notebook, db, story_id), text="Settings")
        self.notebook.add(PlotPointsTab(self.notebook, db, story_id), text="Plot Points")
        self.notebook.add(ThemesTab(self.notebook, db, story_id), text="Themes")

    def _setup_writing_area(self):
        # Header
        header = tk.Frame(self.writing_frame, bg="white")
        header.pack(fill='x', pady=(0, 10))
        tk.Label(header, text="Chapter List", font=("Segoe UI", 11, "bold"), bg="white").pack(side='left')
        
        # Chapter List
        self.chap_list = tk.Listbox(self.writing_frame, height=5, font=("Segoe UI", 10), exportselection=False, bd=1, relief="solid")
        self.chap_list.pack(fill='x', pady=(0, 10))
        self.chap_list.bind('<<ListboxSelect>>', self._load_chapter)

        # Inputs
        info_frame = tk.Frame(self.writing_frame, bg="white")
        info_frame.pack(fill='x', pady=(0, 10))
        tk.Label(info_frame, text="#:", bg="white").pack(side='left')
        self.chap_num = tk.Entry(info_frame, width=5)
        self.chap_num.pack(side='left', padx=5)
        tk.Label(info_frame, text="Title:", bg="white").pack(side='left')
        self.chap_title = tk.Entry(info_frame, width=30)
        self.chap_title.pack(side='left', padx=5)
        
        tk.Button(info_frame, text="Save Chapter", command=self._save_chapter, bg="#4caf50", fg="white", relief="flat").pack(side='right', padx=5)
        tk.Button(info_frame, text="New", command=self._new_chapter, bg="#2196f3", fg="white", relief="flat").pack(side='right', padx=5)
        tk.Button(info_frame, text="Del", command=self._delete_chapter, bg="#ef5350", fg="white", relief="flat").pack(side='right', padx=5)

        # Editor
        tk.Label(self.writing_frame, text="Writing Area:", font=("Segoe UI", 11, "bold"), bg="white", anchor="w").pack(fill='x')
        txt_frame = tk.Frame(self.writing_frame, bd=1, relief="solid")
        txt_frame.pack(fill='both', expand=True)
        self.editor = tk.Text(txt_frame, font=("Georgia", 12), wrap="word", padx=15, pady=15, undo=True)
        self.editor.pack(side='left', fill='both', expand=True)
        scrolly = tk.Scrollbar(txt_frame, command=self.editor.yview)
        scrolly.pack(side='right', fill='y')
        self.editor.config(yscrollcommand=scrolly.set)
        
        self.current_chap_id = None
        self._refresh_chap_list()

    def _refresh_chap_list(self):
        self.chap_list.delete(0, tk.END)
        self.chapters = self.db.get_chapters(self.story_id)
        for c in self.chapters:
            self.chap_list.insert(tk.END, f"Ch {c[1]}: {c[2]}")

    def _load_chapter(self, event):
        sel = self.chap_list.curselection()
        if not sel: return
        idx = sel[0]
        chap_data = self.chapters[idx]
        self.current_chap_id = chap_data[0]
        self.chap_num.delete(0, tk.END); self.chap_num.insert(0, str(chap_data[1]))
        self.chap_title.delete(0, tk.END); self.chap_title.insert(0, chap_data[2])
        self.editor.delete("1.0", tk.END); self.editor.insert("1.0", chap_data[3])

    def _save_chapter(self):
        num = self.chap_num.get().strip()
        title = self.chap_title.get().strip()
        content = self.editor.get("1.0", tk.END).strip()
        if not num or not title: return messagebox.showerror("Error", "Chapter Number and Title are required.")
        if self.current_chap_id:
            self.db.update_chapter(self.current_chap_id, num, title, content)
        else:
            self.db.create_chapter(self.story_id, num, title, content)
        self._refresh_chap_list()
        messagebox.showinfo("Saved", "Chapter saved!")

    def _new_chapter(self):
        self.current_chap_id = None
        self.chap_num.delete(0, tk.END); self.chap_title.delete(0, tk.END)
        self.editor.delete("1.0", tk.END); self.chap_list.selection_clear(0, tk.END)

    def _delete_chapter(self):
        if not self.current_chap_id: return
        if messagebox.askyesno("Delete", "Delete this chapter?"):
            self.db.delete_chapter(self.current_chap_id); self._new_chapter(); self._refresh_chap_list()


# ==========================================
# 4. MAIN DASHBOARD
# ==========================================
FONT_HEADER = ("Segoe UI", 16, "bold")
FONT_BODY = ("Segoe UI", 11)
BG_COLOR = "#f4f4f9"
BTN_PRIMARY = "#5c6bc0" 
BTN_DANGER = "#ef5350"
BTN_TEXT = "white"

class WriterApp:
    def __init__(self, master, db):
        self.master = master
        self.db = db
        self._setup_ui()
        self._refresh_list()

    def _setup_ui(self):
        self.master.title("Writer's Idea Notebook")
        self.master.geometry("800x650")
        self.master.configure(bg=BG_COLOR)

        header_frame = tk.Frame(self.master, bg=BG_COLOR)
        header_frame.pack(fill='x', padx=20, pady=(20, 10))
        tk.Label(header_frame, text="My Stories", font=FONT_HEADER, bg=BG_COLOR, fg="#333").pack(side='left')

        input_frame = tk.Frame(self.master, bg="white", padx=20, pady=20, relief=tk.RIDGE, bd=1)
        input_frame.pack(fill='x', padx=20, pady=5)

        tk.Label(input_frame, text="Story Title:", font=FONT_BODY, bg="white").grid(row=0, column=0, sticky='w')
        self.title = tk.Entry(input_frame, font=FONT_BODY, width=35, relief="solid", bd=1)
        self.title.grid(row=0, column=1, padx=(5, 20), pady=5)
        
        tk.Label(input_frame, text="Genre:", font=FONT_BODY, bg="white").grid(row=0, column=2, sticky='w')
        self.genre = tk.Entry(input_frame, font=FONT_BODY, width=20, relief="solid", bd=1)
        self.genre.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(input_frame, text="Summary:", font=FONT_BODY, bg="white").grid(row=1, column=0, sticky='nw', pady=10)
        self.summary = tk.Text(input_frame, height=3, width=60, font=("Segoe UI", 10), relief="solid", bd=1)
        self.summary.grid(row=1, column=1, columnspan=3, pady=10, sticky='w')

        self.btn_save = tk.Button(input_frame, text="CREATE NEW STORY", command=self._save, font=("Segoe UI", 10, "bold"), bg=BTN_PRIMARY, fg=BTN_TEXT, relief="flat", padx=15, pady=5, cursor="hand2")
        self.btn_save.grid(row=2, column=1, sticky='w', pady=(10, 0))

        list_frame = tk.Frame(self.master, bg=BG_COLOR)
        list_frame.pack(fill='both', expand=True, padx=20, pady=20)
        tk.Label(list_frame, text="Select a story to open the Workstation", font=("Segoe UI", 9, "italic"), bg=BG_COLOR, fg="#666").pack(anchor='w')

        self.listbox = tk.Listbox(list_frame, font=FONT_BODY, selectmode=tk.SINGLE, bg="white", relief="flat", bd=0, highlightthickness=1, highlightbackground="#ccc")
        self.listbox.pack(side='left', fill='both', expand=True)
        self.listbox.bind('<Double-Button-1>', lambda e: self._open_details())

        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.listbox.config(yscrollcommand=scrollbar.set)

        ctrl_frame = tk.Frame(self.master, bg=BG_COLOR)
        ctrl_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        # --- NEW BUTTON LABEL HERE ---
        tk.Button(ctrl_frame, text="OPEN WORKSTATION", command=self._open_details, font=FONT_BODY, bg="#4db6ac", fg="white", relief="flat", padx=10).pack(side='left', padx=(0, 10))
        tk.Button(ctrl_frame, text="DELETE STORY", command=self._delete, font=FONT_BODY, bg=BTN_DANGER, fg="white", relief="flat", padx=10).pack(side='right')

    def _save(self):
        t = self.title.get().strip()
        if not t: return messagebox.showerror("Required", "Please enter a Story Title.")
        self.db.create_story(t, self.genre.get(), 0, self.summary.get("1.0", tk.END))
        self._refresh_list(); self.title.delete(0, tk.END); self.genre.delete(0, tk.END); self.summary.delete("1.0", tk.END)

    def _open_details(self):
        sel = self.listbox.curselection()
        if not sel: return messagebox.showwarning("Select Story", "Please click a story to select it first.")
        try:
            # FIX: Replace '[' with nothing, then strip whitespace
            text_item = self.listbox.get(sel[0])
            s_id = int(text_item.split(']')[0].replace('[', '').strip())
            
            StoryWorkstationWindow(self.master, self.db, s_id)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open story: {e}")

    def _delete(self):
        sel = self.listbox.curselection()
        if not sel: return messagebox.showwarning("Select Story", "Please click a story to delete it.")
        try:
            # FIX: Apply the same fix here
            text_item = self.listbox.get(sel[0])
            s_id = int(text_item.split(']')[0].replace('[', '').strip())
            
            if messagebox.askyesno("Confirm Delete", "Are you sure?"):
                self.db.delete_story(s_id); self._refresh_list()
        except: pass

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        for s in self.db.get_all_stories(): self.listbox.insert(tk.END, f"  [{s[0]}]  {s[1]}  ({s[2]})")

if __name__ == "__main__":
    db = DatabaseManager()
    root = tk.Tk()
    app = WriterApp(root, db)
    root.mainloop()