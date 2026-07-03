import tkinter as tk
from tkinter import ttk
import threading
import json
import os
import sys
import time
import pyautogui
import keyboard

CONFIG_FILE = "clicker_config_slots.json"

ALL_TEMPLATES = [
    'Token_small.png',
    'Token_shine.png',
    'Token_shine1.png',
    'Token_grid.png',
    'Token_plane.png',
    'Token_shine2.png',
    'Token_shine3.png'
]

class CheatMenuApp:
    def __init__(self, root):
        self.root = root
        self.root.title("UL Token Assistant Pro")
        self.root.geometry("480x880")
        self.root.configure(bg="#1e1e24")
        
        # Core configuration states
        self.running = False
        self.active_slot = "Slot 1"
        self.is_binding = False
        
        # Profile Data Storage Dictionary
        self.slots_data = {
            "Slot 1": {"confidence": 0.91, "scan_delay": 0.14, "stop_key": "esc", "failsafe": True, "enabled_files": list(ALL_TEMPLATES)},
            "Slot 2": {"confidence": 0.70, "scan_delay": 0.30, "stop_key": "esc", "failsafe": True, "enabled_files": list(ALL_TEMPLATES)},
            "Slot 3": {"confidence": 0.70, "scan_delay": 0.30, "stop_key": "esc", "failsafe": True, "enabled_files": list(ALL_TEMPLATES)}
        }
        
        self.load_all_slots_from_disk()
        
        # Current active variables mapped to the engine
        self.confidence = self.slots_data[self.active_slot]["confidence"]
        self.scan_delay = self.slots_data[self.active_slot]["scan_delay"]
        self.stop_key = self.slots_data[self.active_slot]["stop_key"]
        self.failsafe_enabled = self.slots_data[self.active_slot]["failsafe"]
        
        self.file_vars = {}
        for filename in ALL_TEMPLATES:
            is_enabled = filename in self.slots_data[self.active_slot]["enabled_files"]
            self.file_vars[filename] = tk.BooleanVar(value=is_enabled)
            
        self.build_ui()
        
        self.current_hotkey_hook = None
        self.bind_global_hotkey()
        self.root.bind("<Key>", self.handle_window_key_press)

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
        
        desc_conf = tk.Label(self.root, text="Lower values (0.50 - 0.70) match tokens over changing UI backdrops.", font=("Arial", 8, "italic"), bg="#1e1e24", fg="#aaaaaa")
        desc_conf.pack()

        # ---------------- SLIDER 2: SCAN DELAY ----------------
        tk.Label(self.root, text="SCAN FREQUENCY DELAY", font=("Arial", 10, "bold"), bg="#1e1e24", fg="#ffffff").pack(pady=(10,0))
        
        self.slider_delay = ttk.Scale(self.root, from_=0.05, to=1.50, value=self.scan_delay, command=self.on_delay_change)
        self.slider_delay.pack(fill='x', padx=30, pady=2)
        
        self.lbl_delay = tk.Label(self.root, text=f"Value: {self.scan_delay:.2f}s", bg="#1e1e24", fg="#ff8c00", font=("Arial", 9, "bold"))
        self.lbl_delay.pack()
        
        desc_delay = tk.Label(self.root, text="Sleep step cycle timeline between screenshot analysis ticks.", font=("Arial", 8, "italic"), bg="#1e1e24", fg="#aaaaaa")
        desc_delay.pack()

        # ---------------- SUB MENU: FILE SELECTION CHECKLIST ----------------
        files_frame = tk.LabelFrame(self.root, text=" TARGET ENGINE ACTIVE FILES ", font=("Arial", 9, "bold"), bg="#1e1e24", fg="#ffffff", padx=10, pady=10)
        files_frame.pack(fill="x", padx=25, pady=10)

        for filename in ALL_TEMPLATES:
            cb = tk.Checkbutton(
                files_frame, 
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
            cb.pack(anchor="w")

        # ---------------- HARDWARE FAILSAFE TOGGLE ----------------
        self.chk_var = tk.BooleanVar(value=self.failsafe_enabled)
        self.chk_failsafe = tk.Checkbutton(self.root, text="Enable Mouse-Corner Failsafe", variable=self.chk_var, command=self.on_failsafe_toggle, bg="#1e1e24", fg="#ffffff", selectcolor="#1e1e24", activebackground="#1e1e24", activeforeground="#ff8c00", font=("Arial", 9, "bold"))
        self.chk_failsafe.pack(pady=(5, 0))
        
        desc_fail = tk.Label(self.root, text="Emergency Stop: Forcing mouse to corners instantly cuts engine execution.", font=("Arial", 8, "italic"), bg="#1e1e24", fg="#aaaaaa")
        desc_fail.pack()

        # ---------------- GAME MOD MENU HOTKEY SELECTOR ----------------
        tk.Label(self.root, text="GLOBAL STOP HOTKEY", font=("Arial", 10, "bold"), bg="#1e1e24", fg="#ffffff").pack(pady=(10,0))
        
        hotkey_container = tk.Frame(self.root, bg="#1e1e24")
        hotkey_container.pack(pady=5)
        
        self.btn_bind = tk.Button(hotkey_container, text=f"Key: {self.stop_key.upper()}", width=16, bg="#2d2d34", fg="#ffffff", font=("Arial", 10, "bold"), command=self.start_listening_for_bind, activebackground="#3d3d44", activeforeground="#ffffff")
        self.btn_bind.pack(side="left", padx=5)
        
        btn_reset_esc = tk.Button(hotkey_container, text="RESET ESC", bg="#cc3333", fg="#ffffff", font=("Arial", 9, "bold"), command=self.reset_hotkey_to_esc, activebackground="#aa2222")
        btn_reset_esc.pack(side="left", padx=5)
        
        self.lbl_bind_hint = tk.Label(self.root, text="Click button above, then strike any key on your keyboard.", font=("Arial", 8, "italic"), bg="#1e1e24", fg="#ff8c00")
        self.lbl_bind_hint.pack()

        # ---------------- MAIN RUN BOARD ----------------
        self.btn_toggle = tk.Button(self.root, text="START ENGINE", bg="#00cc66", fg="#ffffff", font=("Arial", 12, "bold"), height=2, width=18, command=self.toggle_execution, activebackground="#00994d")
        self.btn_toggle.pack(pady=(15, 5))
        
        self.lbl_status = tk.Label(self.root, text=f"ACTIVE CONFIG: {self.active_slot}", fg="#aaaaaa", bg="#1e1e24", font=("Courier New", 10, "bold"))
        self.lbl_status.pack()

        # New Interactive Help Engine Call Hook Button
        self.btn_help = tk.Button(self.root, text="VIEW DOCUMENTATION / HELP", bg="#2d2d34", fg="#ff8c00", font=("Arial", 9, "bold"), command=self.show_documentation_view)
        self.btn_help.pack(pady=10)

    def show_documentation_view(self):
        # Stop execution thread instantly if help menu is invoked
        if self.running:
            self.toggle_execution()

        for widget in self.root.winfo_children():
            widget.destroy()

        header = tk.Label(self.root, text="⚙️ SYSTEM DOCUMENTATION ⚙️", font=("Courier New", 14, "bold"), bg="#1e1e24", fg="#ff8c00")
        header.pack(pady=15)

        # Scannable, scrollable textbox element frame containers
        text_frame = tk.Frame(self.root, bg="#1e1e24")
        text_frame.pack(fill="both", expand=True, padx=20, pady=5)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        help_txt = tk.Text(text_frame, bg="#17171c", fg="#dddddd", insertbackground="white", wrap="word", font=("Arial", 10), yscrollcommand=scrollbar.set, padx=10, pady=10)
        help_txt.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=help_txt.yview)

        # Documentation content body
        docs = """=========================================
WELCOME TO TOKENS ASSISTANT PRO
=========================================

1. MACRO SLOT PROFILES
• Supports 3 separate independent layout presets.
• Swapping profiles instantly updates active configs.
• Click "MANUAL SAVE" to completely write your modifications permanently into disk memory (clicker_config_slots.json).

2. MATCH SENSITIVITY (CONFIDENCE)
• Configures the precision requirements of target matching.
• High Values (0.85 - 0.95): Demands near pixel-perfect shape and color uniformity. Great for filtering out false positives (like UI stars or folders).
• Low Values (0.50 - 0.70): Forgiving tracking framework. Helps capture elements even when hidden beneath changing UI backdrops, texts, and grids.

3. SCAN FREQUENCY DELAY
• Adjusts response loop timing intervals.
• Low delay values provide faster click cycles, but utilize more processing overhead. Keep it balanced to match application limits.

4. ACTIVE FILE CHECKLIST MATRIX
• Toggles template visibility. 
• If an asset file (e.g., Token_grid.png) begins misclicking or snapping onto static background text icons, uncheck its matrix box. The engine loop will skip it instantly.

5. FAILSAFES & EMERGENCY STOPS
• Mouse-Corner Failsafe: When active, slamming your mouse physical cursor hard into any of the 4 monitor corners breaks engine logic.
• Global Stop Hotkey: Striking your custom mapped button cuts processes mid-tick. Click the mapping key to rebind to any custom layout.
"""
        help_txt.insert(tk.END, docs)
        help_txt.config(state="disabled") # Set to read-only mode

        btn_back = tk.Button(self.root, text="BACK TO CONTROLS", bg="#ff8c00", fg="#000000", font=("Arial", 11, "bold"), height=2, width=20, command=self.build_ui)
        btn_back.pack(pady=15)

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
        self.btn_bind.config(text="PRESS ANY KEY...", bg="#ff3333")
        self.root.focus_set()

    def handle_window_key_press(self, event):
        if not self.is_binding:
            return
        
        key_pressed = event.keysym.lower()
        if key_pressed == "delete":
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
        self.root.focus_set()

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
        
        for filename in ALL_TEMPLATES:
            is_enabled = filename in self.slots_data[self.active_slot].get("enabled_files", ALL_TEMPLATES)
            self.file_vars[filename].set(is_enabled)
        
        self.build_ui()
        self.bind_global_hotkey()
        self.lbl_status.config(text=f"LOADED MAPPED CONTEXT: {self.active_slot}", fg="#ff8c00")

    def manual_save_current_slot(self):
        self.slots_data[self.active_slot] = {
            "confidence": self.confidence,
            "scan_delay": self.scan_delay,
            "stop_key": self.stop_key,
            "failsafe": self.failsafe_enabled,
            "enabled_files": self.slots_data[self.active_slot]["enabled_files"]
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.slots_data, f, indent=4)
        
        self.lbl_status.config(text=f"SAVED PROFILE DATA TO {self.active_slot.upper()}!", fg="#00cc66")

    def load_all_slots_from_disk(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    disk_data = json.load(f)
                for slot in ["Slot 1", "Slot 2", "Slot 3"]:
                    if slot in disk_data:
                        self.slots_data[slot] = disk_data[slot]
                        if "enabled_files" not in self.slots_data[slot]:
                            self.slots_data[slot]["enabled_files"] = list(ALL_TEMPLATES)
                print("[File I/O] Configured slots loaded successfully.")
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
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except:
            pass

        while self.running:
            found_and_clicked = False
            active_templates = self.slots_data[self.active_slot].get("enabled_files", ALL_TEMPLATES)
            
            if not active_templates:
                time.sleep(1.0)
                continue

            for file_name in active_templates:
                if not self.running: 
                    break
                
                full_template_path = os.path.join(base_dir, file_name)
                
                if not os.path.exists(full_template_path):
                    continue
                
                try:
                    location = pyautogui.locateOnScreen(full_template_path, confidence=self.confidence)
                    
                    if location is not None:
                        cx, cy = pyautogui.center(location)
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