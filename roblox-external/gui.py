import tkinter as tk
from tkinter import ttk, colorchooser
import json
from config import visuals, OFFSETS 

class ESP_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP Config")
        self.root.geometry("320x650")
        self.root.attributes("-topmost", True) 
        self.root.resizable(False, False)

        style = ttk.Style()
        style.theme_use('clam')

        # Initialize placeholders to None
        self.slider_radius = None
        self.slider_font = None
        self.combo_origin = None
        self.entry_hp = None

        # --- Master Toggle ---
        self.create_header("Main Switch")
        self.var_esp = self.create_checkbox("Enable Master ESP", visuals.ENABLE_ESP, self.update_visuals)
        
        ttk.Separator(root, orient='horizontal').pack(fill='x', pady=10)

        # --- Element Toggles ---
        self.create_header("Elements")
        self.var_tracer = self.create_checkbox("Tracers", visuals.ENABLE_TRACERS, self.update_visuals)
        self.var_dot = self.create_checkbox("Head Dot", visuals.ENABLE_DOT, self.update_visuals)
        self.var_name = self.create_checkbox("Names", visuals.ENABLE_NAME, self.update_visuals)
        self.var_dist = self.create_checkbox("Distance", visuals.ENABLE_DISTANCE, self.update_visuals)
        self.var_hp = self.create_checkbox("Health", visuals.ENABLE_HEALTH, self.update_visuals)

        # --- Tracer Origin ---
        self.create_header("Tracer Origin")
        frame_origin = ttk.Frame(self.root)
        frame_origin.pack(fill='x', padx=20, pady=2)
        
        self.combo_origin = ttk.Combobox(frame_origin, values=["Bottom", "Center", "Mouse"], state="readonly")
        self.combo_origin.set(visuals.TRACER_ORIGIN)
        self.combo_origin.pack(fill='x')
        self.combo_origin.bind("<<ComboboxSelected>>", lambda e: self.update_visuals())

        # --- Numeric Settings ---
        self.create_header("Sizing")
        self.slider_radius = self.create_slider("Dot Radius (1-50)", 1, 50, visuals.DOT_RADIUS)
        self.slider_font = self.create_slider("Font Size (1-10)", 1, 10, visuals.FONT_SIZE_INDEX)

        # --- Health Calibration ---
        self.create_header("Health Calibration")
        frame_hp = ttk.Frame(self.root)
        frame_hp.pack(fill='x', padx=20, pady=2)
        
        lbl_hp = ttk.Label(frame_hp, text="Max HP Value:", font=("Segoe UI", 8))
        lbl_hp.pack(side='left')
        
        self.entry_hp = ttk.Entry(frame_hp, width=8)
        self.entry_hp.insert(0, str(visuals.MAX_HEALTH))
        self.entry_hp.pack(side='right')
        
        # Trigger updates on Enter key and Focus Out
        self.entry_hp.bind('<Return>', lambda event: self.update_visuals())
        self.entry_hp.bind('<FocusOut>', lambda event: self.update_visuals())

        # --- Colors ---
        self.create_header("Colors")
        self.btn_tracer_col = self.create_color_btn("Tracer Color", visuals.TRACER_COLOR, "TRACER_COLOR")
        self.btn_dot_col = self.create_color_btn("Dot Color", visuals.DOT_COLOR, "DOT_COLOR")
        
        # --- Save ---
        ttk.Separator(root, orient='horizontal').pack(fill='x', pady=15)
        btn_save = ttk.Button(root, text="Save Config", command=self.save_to_file)
        btn_save.pack(fill='x', padx=10, pady=5)

    def create_header(self, text):
        lbl = ttk.Label(self.root, text=text, font=("Segoe UI", 9, "bold"))
        lbl.pack(anchor='w', padx=10, pady=(15, 2))

    def create_checkbox(self, text, val, callback):
        var = tk.BooleanVar(value=val)
        chk = ttk.Checkbutton(self.root, text=text, variable=var, command=callback)
        chk.pack(anchor='w', padx=20)
        return var

    def create_slider(self, text, min_v, max_v, current):
        frame = ttk.Frame(self.root)
        frame.pack(fill='x', padx=20, pady=2)
        
        lbl = ttk.Label(frame, text=text, font=("Segoe UI", 8))
        lbl.pack(anchor='w')
        
        scale = ttk.Scale(frame, from_=min_v, to=max_v, command=lambda v: self.update_visuals())
        scale.set(current)
        scale.pack(fill='x')
        return scale

    def create_color_btn(self, text, current_col, attr_name):
        try:
            hex_col = '#%02x%02x%02x' % (int(current_col[0]), int(current_col[1]), int(current_col[2]))
        except: hex_col = "#FFFFFF"

        frame = ttk.Frame(self.root)
        frame.pack(fill='x', padx=20, pady=2)
        
        lbl = ttk.Label(frame, text=text)
        lbl.pack(side='left')
        
        btn = tk.Button(frame, bg=hex_col, width=4, command=lambda: self.pick_color(btn, attr_name))
        btn.pack(side='right')
        return btn

    def pick_color(self, btn, attr_name):
        color = colorchooser.askcolor(title="Choose Color")
        if color[0]:
            rgb = (int(color[0][0]), int(color[0][1]), int(color[0][2]))
            btn.config(bg=color[1])
            setattr(visuals, attr_name, rgb)

    def update_visuals(self, *args):
        # --- CRITICAL FIX: Check ALL widgets before running ---
        if self.slider_radius is None or self.slider_font is None or self.combo_origin is None:
            return

        # Toggles
        visuals.ENABLE_ESP = self.var_esp.get()
        visuals.ENABLE_TRACERS = self.var_tracer.get()
        visuals.ENABLE_DOT = self.var_dot.get()
        visuals.ENABLE_NAME = self.var_name.get()
        visuals.ENABLE_DISTANCE = self.var_dist.get()
        visuals.ENABLE_HEALTH = self.var_hp.get()
        
        # Controls
        visuals.DOT_RADIUS = float(self.slider_radius.get())
        visuals.FONT_SIZE_INDEX = int(self.slider_font.get())
        visuals.TRACER_ORIGIN = self.combo_origin.get()

        # Update HP Variable immediately
        try:
            val = int(self.entry_hp.get())
            if val > 0:
                visuals.MAX_HEALTH = val
        except:
            pass

    def save_to_file(self):
        content = f"""
import requests
import json

OFFSETS_URL = "https://robloxoffsets.com/offsets.json"
TIMEOUT = 5

try:
    OFFSETS = requests.get(OFFSETS_URL, timeout=TIMEOUT).json()
except:
    OFFSETS = {{}}

# Saved Offsets Snapshot
OFFSETS = {json.dumps(OFFSETS, indent=4)}

class VisualConfig:
    ENABLE_ESP = {visuals.ENABLE_ESP}
    ENABLE_TRACERS = {visuals.ENABLE_TRACERS}
    ENABLE_DOT = {visuals.ENABLE_DOT}
    ENABLE_NAME = {visuals.ENABLE_NAME}
    ENABLE_DISTANCE = {visuals.ENABLE_DISTANCE}
    ENABLE_HEALTH = {visuals.ENABLE_HEALTH}

    DOT_RADIUS = {visuals.DOT_RADIUS}
    FONT_SIZE_INDEX = {visuals.FONT_SIZE_INDEX}
    TRACER_ORIGIN = "{visuals.TRACER_ORIGIN}"
    
    TRACER_COLOR = {visuals.TRACER_COLOR}
    DOT_COLOR = {visuals.DOT_COLOR}
    NAME_COLOR = {visuals.NAME_COLOR}
    
    MAX_HEALTH = {visuals.MAX_HEALTH}

visuals = VisualConfig()

class GlobalConfig:
    def __init__(self):
        self.offset_map = {{
            0: -200.0, 10: -70.0, 20: -30.0, 30: -15.0, 40: 0.0,
            50: 2.0, 60: 6.0, 70: 8.0, 80: 10.0, 90: 12.0,
            100: 11.8, 110: 12.0, 120: 15.0, 130: 16.0, 140: 16.0,
            150: 17.5, 160: 15.8, 170: 17.8, 180: 17.0, 190: 18.2,
            200: 20.0, 210: 18.0, 220: 18.7, 230: 18.7, 240: 17.9,
            250: 20.0, 260: 19.5, 270: 19.3, 280: 19.4, 290: 19.3,
            300: 19.5, 310: 20.5, 320: 20.1, 330: 20.5, 340: 20.3,
            350: 19.5
        }}

    def get_interpolated_offset(self, distance):
        if distance <= 0: return self.offset_map[0]
        if distance >= 350: return self.offset_map[350]
        lower_dist = (int(distance) // 10) * 10
        upper_dist = lower_dist + 10
        val_low = self.offset_map.get(lower_dist, 0.0)
        val_high = self.offset_map.get(upper_dist, 0.0)
        ratio = (distance - lower_dist) / 10.0
        return val_low + (val_high - val_low) * ratio

game_config = GlobalConfig()
"""
        try:
            with open("config.py", "w") as f:
                f.write(content.strip())
            print("Configuration Saved!")
        except Exception as e:
            print(f"Error saving config: {e}")

def run_gui():
    root = tk.Tk()
    app = ESP_GUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()