import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
import os
import sys
import time
import shutil
import pyautogui
import keyboard
from PIL import Image, ImageTk
# Here is the code to prove it doesn't really do anything and is very harmless, also why it doesn't require you to use admin permissions to use it. (won't work if you only download this unless you want to build it custom yourself with your own pictures.) -pasted just in case you didn't see the download description 
# This is lined with ai overview for any bugs and also to let you kinda know what sections everything is in but it's pretty self explanatory.
CONFIG_FILE = "clicker_config_slots.json"

# The 7 original core files that cannot be deleted
DEFAULT_TEMPLATES = [
    'Token_small.png',
    'Token_shine.png',
    'Token_shine1.png',
    'Token_grid.png',
    'Token_plane.png',
    'Token_shine2.png',
    'Token_shine3.png'
]

class FlashOverlay(tk.Toplevel):
    """Semi-transparent frameless overlay window to display real-time tracking points."""
    def __init__(self, x, y, radius=25):
        super().__init__()
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-transparentcolor", "#111111")
        self.config(bg="#111111")
        
        width = radius * 2
        height = radius * 2
        self.geometry(f"{width}x{height}+{int(x - radius)}+{int(y - radius)}")
        
        canvas = tk.Canvas(self, width=width, height=height, bg="#111111", highlightthickness=0)
        canvas.pack()
        
        canvas.create_oval(2, 2, width - 2, height - 2, outline="#00cc66", width=3)
        self.update()

class CheatMenuApp:
    def __init__(self, root):
        self.root = root
        self.root.title("UL Token Assistant v2.0")
        self.root.geometry("520x920")
        self.root.configure(bg="#1e1e24")
        
        if getattr(sys, 'frozen', False):
            self.base_dir = sys._MEIPASS
            self.working_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
            self.working_dir = self.base_dir

        self.running = False
        self.active_slot = "Slot 1"
        self.is_binding = False
        self.all_templates = list(DEFAULT_TEMPLATES)
        
        self.slots_data = {
            "Slot 1": {"confidence": 0.91, "scan_delay": 0.14, "stop_key": "esc", "failsafe": True, "enabled_files": list(self.all_templates)},
            "Slot 2": {"confidence": 0.70, "scan_delay": 0.30, "stop_key": "esc", "failsafe": True, "enabled_files": list(self.all_templates)},
            "Slot 3": {"confidence": 0.70, "scan_delay": 0.30, "stop_key": "esc", "failsafe": True, "enabled_files": list(self.all_templates)}
        }
        
        self.load_all_slots_from_disk()
        
        self.confidence = self.slots_data[self.active_slot]["confidence"]
        self.scan_delay = self.slots_data[self.active_slot]["scan_delay"]
        self.stop_key = self.slots_data[self.active_slot]["stop_key"]
        self.failsafe_enabled = self.slots_data[self.active_slot]["failsafe"]
        
        self.file_vars = {}
        self.thumbnail_images = {}  
        self.update_file_variables()
            
        self.build_ui()
        
        self.current_hotkey_hook = None
        self.bind_global_hotkey()
        self.root.bind("<Key>", self.handle_window_key_press)

    def find_file_path(self, filename):
        path_working = os.path.join(self.working_dir, filename)
        if os.path.exists(path_working):
            return path_working
        path_base = os.path.join(self.base_dir, filename)
        if os.path.exists(path_base):
            return path_base
        return None

    def update_file_variables(self):
        for filename in self.all_templates:
            if filename not in self.file_vars:
                is_enabled = filename in self.slots_data[self.active_slot].get("enabled_files", self.all_templates)
                self.file_vars[filename] = tk.BooleanVar(value=is_enabled)

    def get_thumbnail(self, filename):
        full_path = self.find_file_path(filename)
        if full_path:
            try:
                img = Image.open(full_path)
                img = img.resize((20, 20), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Error loading thumb {filename}: {e}")
        return None

    def build_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        header = tk.Label(self.root, text="★ TOKENS ASSISTANT ★", font=("Courier New", 16, "bold"), bg="#1e1e24", fg="#ff8c00")
        header.pack(pady=10)

        # ---------------- PROFILE MANAGEMENT SLOTS ----------------
        slot_frame = tk.LabelFrame(self.root, text=" MACRO PROFILE PROFILE (MAX 3) ", font=("Arial", 9, "bold"), bg="#1e1e24", fg="#ffffff", padx=10, pady=10)
        slot_frame.pack(fill="x", padx=25, pady=5)
        
        self.slot_var = tk.StringVar(value=self.active_slot)
        for slot_name in ["Slot 1", "Slot 2", "Slot 3"]:
            rb = tk.Radiobutton(slot_frame, text=slot_name, variable=self.slot_var, value=slot_name, command=self.change_active_slot_view, bg="#1e1e24", fg="#ffffff", selectcolor="#1e1e24", activebackground="#1e1e24", activeforeground="#ff8c00", font=("Arial", 10))
            rb.pack(side="left", expand=True)
            
        btn_save = tk.Button(slot_frame, text="MANUAL SAVE", command=self.manual_save_current_slot, bg="#ff8c00", fg="#000000", font=("Arial", 8, "bold"))
        btn_save.pack(side="right", padx=5)

        # ---------------- SLIDER 1: SENSITIVITY ----------------
        tk.Label(self.root, text="MATCH SENSITIVITY (CONFIDENCE)", font=("Arial", 10, "bold"), bg="#1e1e24", fg="#ffffff").pack(pady=(5,0))
        
        self.slider_conf = ttk.Scale(self.root, from_=0.40, to=1.00, value=self.confidence, command=self.on_confidence_change)
        self.slider_conf.pack(fill='x', padx=30, pady=2)
        
        self.lbl_conf = tk.Label(self.root, text=f"Value: {self.confidence:.2f}", bg="#1e1e24", fg="#ff8c00", font=("Arial", 9, "bold"))
        self.lbl_conf.pack()

        # ---------------- SLIDER 2: SCAN DELAY ----------------
        tk.Label(self.root, text="SCAN FREQUENCY DELAY", font=("Arial", 10, "bold"), bg="#1e1e24", fg="#ffffff").pack(pady=(5,0))
        
        self.slider_delay = ttk.Scale(self.root, from_=0.05, to=1.50, value=self.scan_delay, command=self.on_delay_change)
        self.slider_delay.pack(fill='x', padx=30, pady=2)
        
        self.lbl_delay = tk.Label(self.root, text=f"Value: {self.scan_delay:.2f}s", bg="#1e1e24", fg="#ff8c00", font=("Arial", 9, "bold"))
        self.lbl_delay.pack()

        # ---------------- SUB MENU: FILE SELECTION MATRIX WITH THUMBNAILS & DELETION ----------------
        files_frame = tk.LabelFrame(self.root, text=" TARGET ENGINE ACTIVE FILES ", font=("Arial", 9, "bold"), bg="#1e1e24", fg="#ffffff", padx=10, pady=5)
        files_frame.pack(fill="both", expand=True, padx=25, pady=5)

        canvas_files = tk.Canvas(files_frame, bg="#1e1e24", highlightthickness=0)
        scrollbar_files = tk.Scrollbar(files_frame, orient="vertical", command=canvas_files.yview)
        scroll_content = tk.Frame(canvas_files, bg="#1e1e24")

        scroll_content.bind("<Configure>", lambda e: canvas_files.configure(scrollregion=canvas_files.bbox("all")))
        canvas_files.create_window((0, 0), window=scroll_content, anchor="nw")
        canvas_files.configure(yscrollcommand=scrollbar_files.set)

        canvas_files.pack(side="left", fill="both", expand=True)
        scrollbar_files.pack(side="right", fill="y")

        for filename in self.all_templates:
            row_frame = tk.Frame(scroll_content, bg="#1e1e24")
            row_frame.pack(anchor="w", fill="x", pady=2)

            thumb_img = self.get_thumbnail(filename)
            if thumb_img:
                self.thumbnail_images[filename] = thumb_img
                lbl_thumb = tk.Label(row_frame, image=thumb_img, bg="#1e1e24")
            else:
                lbl_thumb = tk.Label(row_frame, text="[?]", fg="#aaaaaa", bg="#1e1e24", font=("Courier New", 9, "bold"), width=3)
            
            lbl_thumb.pack(side="left", padx=(0, 5))

            cb = tk.Checkbutton(
                row_frame, 
                text=filename, 
                variable=self.file_vars[filename],
                command=self.on_file_toggle,
                bg="#1e1e24", 
                fg="#ffffff", 
                selectcolor="#1e1e24",
                activebackground="#1e1e24",
                activeforeground="#ff8c00",
                font=("Courier New", 9)
            )
            cb.pack(side="left")

            # ONLY add a delete button if it is NOT one of the 7 original core files
            if filename not in DEFAULT_TEMPLATES:
                btn_delete = tk.Button(
                    row_frame, 
                    text="✕", 
                    font=("Arial", 8, "bold"), 
                    bg="#1e1e24", 
                    fg="#cc3333", 
                    activebackground="#cc3333", 
                    activeforeground="#ffffff", 
                    bd=0, 
                    padx=5, 
                    command=lambda f=filename: self.delete_custom_token_file(f)
                )
                btn_delete.pack(side="right", padx=(10, 0))

        btn_upload = tk.Button(self.root, text="+ ADD CUSTOM TOKEN IMAGE", command=self.upload_custom_token_file, bg="#2d2d34", fg="#ff8c00", font=("Arial", 9, "bold"))
        btn_upload.pack(pady=5)

        # ---------------- HARDWARE FAILSAFE TOGGLE ----------------
        self.chk_var = tk.BooleanVar(value=self.failsafe_enabled)
        self.chk_failsafe = tk.Checkbutton(self.root, text="Enable Mouse-Corner Failsafe", variable=self.chk_var, command=self.on_failsafe_toggle, bg="#1e1e24", fg="#ffffff", selectcolor="#1e1e24", activebackground="#1e1e24", activeforeground="#ff8c00", font=("Arial", 9, "bold"))
        self.chk_failsafe.pack(pady=2)
        
        # ---------------- GLOBAL STOP HOTKEY ----------------
        hotkey_container = tk.Frame(self.root, bg="#1e1e24")
        hotkey_container.pack(pady=2)
        
        self.btn_bind = tk.Button(hotkey_container, text=f"Key: {self.stop_key.upper()}", width=14, bg="#2d2d34", fg="#ffffff", font=("Arial", 9, "bold"), command=self.start_listening_for_bind)
        self.btn_bind.pack(side="left", padx=5)
        
        btn_reset_esc = tk.Button(hotkey_container, text="RESET ESC", bg="#cc3333", fg="#ffffff", font=("Arial", 8, "bold"), command=self.reset_hotkey_to_esc)
        btn_reset_esc.pack(side="left", padx=5)

        # ---------------- ACTION PLATFORM RUN HOOK BOARD ----------------
        action_frame = tk.Frame(self.root, bg="#1e1e24")
        action_frame.pack(pady=5)

        self.btn_toggle = tk.Button(action_frame, text="START ENGINE", bg="#00cc66", fg="#ffffff", font=("Arial", 11, "bold"), height=2, width=15, command=self.toggle_execution)
        self.btn_toggle.pack(side="left", padx=5)

        btn_preview = tk.Button(action_frame, text="TEST SCAN\n(PREVIEW)", bg="#ff8c00", fg="#000000", font=("Arial", 9, "bold"), height=2, width=15, command=self.execute_single_preview_scan)
        btn_preview.pack(side="left", padx=5)
        
        self.lbl_status = tk.Label(self.root, text=f"ACTIVE CONFIG: {self.active_slot}", fg="#aaaaaa", bg="#1e1e24", font=("Courier New", 10, "bold"))
        self.lbl_status.pack()

        self.btn_help = tk.Button(self.root, text="VIEW DOCUMENTATION / HELP", bg="#2d2d34", fg="#ff8c00", font=("Arial", 9, "bold"), command=self.show_documentation_view)
        self.btn_help.pack(pady=5)

    def show_documentation_view(self):
        if self.running:
            self.toggle_execution()

        for widget in self.root.winfo_children():
            widget.destroy()

        header = tk.Label(self.root, text="⚙️ SYSTEM DOCUMENTATION ⚙️", font=("Courier New", 14, "bold"), bg="#1e1e24", fg="#ff8c00")
        header.pack(pady=15)

        text_frame = tk.Frame(self.root, bg="#1e1e24")
        text_frame.pack(fill="both", expand=True, padx=20, pady=5)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        help_txt = tk.Text(text_frame, bg="#17171c", fg="#dddddd", wrap="word", font=("Arial", 10), yscrollcommand=scrollbar.set, padx=10, pady=10)
        help_txt.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=help_txt.yview)

        docs = """=========================================
WELCOME TO TOKENS ASSISTANT v2.0
=========================================
1. VISUAL IMAGE PREVIEWS 
• Image previews display target files directly in the menu list context layout frames. 
• Unchecked file parameters automatically bypass target checking execution sweeps entirely. 

2. PREVIEW SCANS 
• The "TEST SCAN" utility maps your screen configuration matrix boundaries once without driving mouse actions. Use it to dial in tracking sensitivity configurations on targets securely. 

3. GRAPHICAL CANVAS HUD OVERLAYS 
• Active engine runs project a high-visibility neon overlay indicator path right before generating native mouse executions. 

4. REALTIME FILE INGESTION UPLOADER 
• Use "+ ADD CUSTOM TOKEN IMAGE" to drop image clips natively straight into active layout slots arrays on runtime cycles. 

5. MACRO SLOT PROFILES 
• Supports 3 separate independent layout presets. 
• Swapping profiles instantly updates active configs. 
• Click "MANUAL SAVE" to completely write your modifications permanently into disk memory (clicker_config_slots.json). 

6. MATCH SENSITIVITY (CONFIDENCE) 
• Configures the precision requirements of target matching. 
• High Values (0.85 - 0.95): Demands near pixel-perfect shape and color uniformity. Great for filtering out false positives (like UI stars or folders). 
• Low Values (0.50 - 0.70): Forgiving tracking framework. Helps capture elements even when hidden beneath changing UI backdrops, texts, and grids. 

7. SCAN FREQUENCY DELAY 
• Adjusts response loop timing intervals. 
• Low delay values provide faster click cycles, but utilize more processing overhead. Keep it balanced to match application limits. 

8. ACTIVE FILE CHECKLIST MATRIX 
• Toggles template visibility. 
• If an asset file (e.g., Token_grid.png) begins misclicking or snapping onto static background text icons, uncheck its matrix box. The engine loop will skip it instantly. 

9. FAILSAFES & EMERGENCY STOPS 
• Mouse-Corner Failsafe: When active, slamming your mouse physical cursor hard into any of the 4 monitor corners breaks engine logic. 
• Global Stop Hotkey: Striking your custom mapped button cuts processes mid-tick. Click the mapping key to rebind to any custom layout.
"""
        help_txt.insert(tk.END, docs)
        help_txt.config(state="disabled")

        btn_back = tk.Button(self.root, text="BACK TO CONTROLS", bg="#ff8c00", fg="#000000", font=("Arial", 11, "bold"), height=2, width=20, command=self.build_ui)
        btn_back.pack(pady=15)

    def upload_custom_token_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Custom Token Image Asset",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
        )
        if file_path:
            filename = os.path.basename(file_path)
            destination_path = os.path.join(self.working_dir, filename)
            
            try:
                shutil.copy(file_path, destination_path)
                
                if filename not in self.all_templates:
                    self.all_templates.append(filename)
                
                self.slots_data[self.active_slot]["enabled_files"] = self.slots_data[self.active_slot].get("enabled_files", [])
                if filename not in self.slots_data[self.active_slot]["enabled_files"]:
                    self.slots_data[self.active_slot]["enabled_files"].append(filename)
                
                self.update_file_variables()
                self.auto_save_to_disk() # Instantly lock and persist changes to disk memory
                self.build_ui()
                messagebox.showinfo("Success", f"Ingested asset '{filename}' successfully mapped into tracking array slots matrix!")
            except Exception as e:
                messagebox.showerror("IO Error Mapping File", f"Could not copy file element: {e}")

    def delete_custom_token_file(self, filename):
        """Purges custom added images from all runtime states, variables, and disk tracking slots."""
        if filename in DEFAULT_TEMPLATES:
            return  # Safety lock boundary bypass safeguard

        if messagebox.askyesno("Confirm Removal", f"Are you sure you want to completely remove '{filename}' from all profile configurations?"):
            try:
                # 1. Clean out memory template lists references
                if filename in self.all_templates:
                    self.all_templates.remove(filename)

                # 2. Scrub target lists references out of ALL profile slots data objects safely
                for slot in ["Slot 1", "Slot 2", "Slot 3"]:
                    if "enabled_files" in self.slots_data[slot] and filename in self.slots_data[slot]["enabled_files"]:
                        self.slots_data[slot]["enabled_files"].remove(filename)
                    if "all_known_templates_matrix" in self.slots_data[slot] and filename in self.slots_data[slot]["all_known_templates_matrix"]:
                        self.slots_data[slot]["all_known_templates_matrix"].remove(filename)

                # 3. Drop internal tracking variables and image pointers
                if filename in self.file_vars:
                    del self.file_vars[filename]
                if filename in self.thumbnail_images:
                    del self.thumbnail_images[filename]

                # 4. Remove the physical file asset from your local folder
                local_path = os.path.join(self.working_dir, filename)
                if os.path.exists(local_path):
                    os.remove(local_path)

                # 5. Flush state changes directly straight to JSON disk blocks
                self.auto_save_to_disk()
                self.build_ui()
                self.lbl_status.config(text=f"PURGED CUSTOM ASSET: {filename}", fg="#ff3333")
            except Exception as e:
                messagebox.showerror("Deletion Error", f"Failed to completely remove asset cleanly: {e}")

    def execute_single_preview_scan(self):
        active_templates = self.slots_data[self.active_slot].get("enabled_files", self.all_templates)
        target_found = False
        
        for file_name in active_templates:
            full_template_path = self.find_file_path(file_name)
            if not full_template_path:
                continue
                
            try:
                location = pyautogui.locateOnScreen(full_template_path, confidence=self.confidence)
                if location is not None:
                    cx, cy = pyautogui.center(location)
                    
                    overlay = FlashOverlay(cx, cy, radius=30)
                    self.root.after(800, overlay.destroy)
                    
                    messagebox.showinfo("Preview Match Trace Found", f"Asset Success: '{file_name}' verified active at X: {cx}, Y: {cy}!\n(A green ring flashed on target position point)")
                    target_found = True
                    break
            except pyautogui.ImageNotFoundException:
                pass
            except Exception as e:
                print(f"Error scanning element preview asset: {e}")
                
        if not target_found:
            messagebox.showwarning("Scan Matrix Finished", "Matrix sweep completed: No items found with current confidence settings.")

    def on_confidence_change(self, val):
        self.confidence = round(float(val), 2)
        self.lbl_conf.config(text=f"Value: {self.confidence:.2f}")
        self.slots_data[self.active_slot]["confidence"] = self.confidence

    def on_delay_change(self, val):
        self.scan_delay = round(float(val), 2)
        self.lbl_delay.config(text=f"Value: {self.scan_delay:.2f}s")
        self.slots_data[self.active_slot]["scan_delay"] = self.scan_delay

    def on_failsafe_toggle(self):
        self.failsafe_enabled = self.chk_var.get()
        pyautogui.FAILSAFE = self.failsafe_enabled
        self.slots_data[self.active_slot]["failsafe"] = self.failsafe_enabled

    def on_file_toggle(self):
        enabled_list = []
        for filename, var in self.file_vars.items():
            if var.get():
                enabled_list.append(filename)
        self.slots_data[self.active_slot]["enabled_files"] = enabled_list

    def start_listening_for_bind(self):
        self.is_binding = True
        self.btn_bind.config(text="PRESS KEY...", bg="#ff3333")
        self.root.focus_set()

    def handle_window_key_press(self, event):
        if not self.is_binding:
            return
        key_pressed = event.keysym.lower()
        if key_pressed in ["delete", "backspace"]:
            return
        if key_pressed == "space":
            key_pressed = "space"
        elif key_pressed == "escape":
            key_pressed = "esc"
            
        self.stop_key = key_pressed
        self.slots_data[self.active_slot]["stop_key"] = self.stop_key
        
        self.is_binding = False
        self.btn_bind.config(text=f"Key: {self.stop_key.upper()}", bg="#2d2d34")
        self.bind_global_hotkey()

    def reset_hotkey_to_esc(self):
        self.stop_key = "esc"
        self.slots_data[self.active_slot]["stop_key"] = "esc"
        self.btn_bind.config(text="Key: ESC", bg="#2d2d34")
        self.is_binding = False
        self.bind_global_hotkey()

    def bind_global_hotkey(self):
        try:
            if self.current_hotkey_hook:
                keyboard.remove_hotkey(self.current_hotkey_hook)
        except:
            pass
        self.current_hotkey_hook = keyboard.add_hotkey(self.stop_key, self.emergency_hotkey_trigger)

    def emergency_hotkey_trigger(self):
        if self.running:
            self.root.after(0, self.toggle_execution)

    def change_active_slot_view(self):
        if self.running:
            self.toggle_execution()
            
        self.active_slot = self.slot_var.get()
        
        self.confidence = self.slots_data[self.active_slot]["confidence"]
        self.scan_delay = self.slots_data[self.active_slot]["scan_delay"]
        self.stop_key = self.slots_data[self.active_slot]["stop_key"]
        self.failsafe_enabled = self.slots_data[self.active_slot]["failsafe"]
        
        saved_files = self.slots_data[self.active_slot].get("enabled_files", self.all_templates)
        for filename in self.all_templates:
            if filename in self.file_vars:
                self.file_vars[filename].set(filename in saved_files)
        
        self.build_ui()
        self.bind_global_hotkey()
        self.lbl_status.config(text=f"LOADED MAPPED CONTEXT: {self.active_slot}", fg="#ff8c00")

    def auto_save_to_disk(self):
        """Silently handles backend disk persistence across modification actions."""
        for slot in ["Slot 1", "Slot 2", "Slot 3"]:
            if slot == self.active_slot:
                self.slots_data[slot] = {
                    "confidence": self.confidence,
                    "scan_delay": self.scan_delay,
                    "stop_key": self.stop_key,
                    "failsafe": self.failsafe_enabled,
                    "enabled_files": [f for f in self.all_templates if f in self.file_vars and self.file_vars[f].get()],
                    "all_known_templates_matrix": list(self.all_templates)
                }
            else:
                # Update known master tracks for non-active configurations too
                self.slots_data[slot]["all_known_templates_matrix"] = list(self.all_templates)

        disk_save_path = os.path.join(self.working_dir, CONFIG_FILE)
        with open(disk_save_path, "w") as f:
            json.dump(self.slots_data, f, indent=4)

    def manual_save_current_slot(self):
        self.auto_save_to_disk()
        self.lbl_status.config(text=f"SAVED PROFILE DATA TO {self.active_slot.upper()}!", fg="#00cc66")

    def load_all_slots_from_disk(self):
        disk_load_path = os.path.join(self.working_dir, CONFIG_FILE)
        if os.path.exists(disk_load_path):
            try:
                with open(disk_load_path, "r") as f:
                    disk_data = json.load(f)
                for slot in ["Slot 1", "Slot 2", "Slot 3"]:
                    if slot in disk_data:
                        self.slots_data[slot] = disk_data[slot]
                        
                        known_matrix = disk_data[slot].get("all_known_templates_matrix", [])
                        for target_file in known_matrix:
                            if target_file not in self.all_templates:
                                self.all_templates.append(target_file)
                                
                        if "enabled_files" not in self.slots_data[slot]:
                            self.slots_data[slot]["enabled_files"] = list(self.all_templates)
                print("[File I/O] Extended multi-slots system presets initialized successfully.")
            except Exception as e:
                print(f"Error loading config: {e}")

    def toggle_execution(self):
        if not self.running:
            self.running = True
            self.btn_toggle.config(text="STOP ENGINE", bg="#ff3333", activebackground="#cc2424")
            self.lbl_status.config(text="STATUS: BOT IS MONITORING ACTIVE", fg="#00cc66")
            pyautogui.FAILSAFE = self.failsafe_enabled
            
            threading.Thread(target=self.bot_loop, daemon=True).start()
        else:
            self.running = False
            self.btn_toggle.config(text="START ENGINE", bg="#00cc66", activebackground="#00994d")
            self.lbl_status.config(text=f"STATUS: PAUSED ({self.active_slot})", fg="#ff3333")

    def bot_loop(self):
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except:
            pass

        while self.running:
            found_and_clicked = False
            active_templates = self.slots_data[self.active_slot].get("enabled_files", self.all_templates)
            
            if not active_templates:
                time.sleep(1.0)
                continue

            for file_name in active_templates:
                if not self.running: 
                    break
                
                full_template_path = self.find_file_path(file_name)
                if not full_template_path:
                    continue
                
                try:
                    location = pyautogui.locateOnScreen(full_template_path, confidence=self.confidence)
                    
                    if location is not None:
                        cx, cy = pyautogui.center(location)
                        
                        self.root.after(0, lambda x=cx, y=cy: FlashOverlay(x, y, radius=25))
                        time.sleep(0.3)  
                        
                        if not self.running:
                            break
                            
                        pyautogui.moveTo(cx, cy, duration=0.1)
                        pyautogui.click()
                        
                        print(f"[Core Engine] Target Clicked via file -> '{file_name}' at X: {cx}, Y: {cy}")
                        found_and_clicked = True
                        break
                except pyautogui.ImageNotFoundException:
                    pass
                except Exception as e:
                    print(f"Loop error tracking: {e}")
            
            if found_and_clicked:
                time.sleep(1.8)
            else:
                time.sleep(self.scan_delay)

if __name__ == "__main__":
    root = tk.Tk()
    app = CheatMenuApp(root)
    root.mainloop()
