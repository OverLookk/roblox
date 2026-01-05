import tkinter as tk
from tkinter import ttk, colorchooser
import os
import threading
import keyboard
import mouse
import win32api
import time
from config import visuals

BG_COLOR = "#1e1e1e"
FG_COLOR = "#ffffff"
ACCENT_COLOR = "#00e5ff"
FRAME_BG = "#2b2b2b"
BUTTON_BG = "#3c3c3c"

VK_MAP = {
    0x01: "L-CLICK", 0x02: "R-CLICK", 0x04: "M-CLICK",
    0x05: "MOUSE-X1", 0x06: "MOUSE-X2", 
    0xA0: "L-SHIFT", 0xA2: "L-CTRL", 0xA4: "L-ALT"
}

class ESP_GUI:
    def __init__(self, root, memory_ref):
        self.root = root
        self.memory = memory_ref
        
        # STOP UPDATE LOOP DURING STARTUP
        self.initialized = False 
        
        self.root.title("ovrhax - @OverLookk")
        self.root.geometry("400x850") # Adjusted height slightly
        self.root.configure(bg=BG_COLOR)
        self.root.attributes("-topmost", True) 
        self.root.resizable(False, False)

        self.root.option_add('*TCombobox*Listbox.background', FRAME_BG)
        self.root.option_add('*TCombobox*Listbox.foreground', FG_COLOR)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(".", background=BG_COLOR, foreground=FG_COLOR, borderwidth=0)
        style.configure("TLabel", background=FRAME_BG, foreground=FG_COLOR)
        style.configure("Header.TLabel", background=BG_COLOR, foreground=ACCENT_COLOR, font=("Segoe UI", 11, "bold"))
        style.configure("TCheckbutton", background=FRAME_BG, foreground=FG_COLOR)
        style.map("TCheckbutton", background=[('active', FRAME_BG)], indicatorcolor=[('selected', ACCENT_COLOR)])
        style.configure(
            "TCombobox",
            fieldbackground=FRAME_BG,
            background=FRAME_BG,
            foreground=FG_COLOR,
            arrowcolor=ACCENT_COLOR
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", FRAME_BG)],
            foreground=[("readonly", FG_COLOR)]
        )
        
        # 1. ESP Section
        self.create_section_header("ESP Visuals")
        esp_frame = self.create_panel()
        self.var_esp = self.create_checkbox(esp_frame, "Master ESP Switch", visuals.ENABLE_ESP)
        # REMOVED TEAM CHECK CHECKBOX HERE
        self.var_tracer = self.create_checkbox(esp_frame, "Show Tracers", visuals.ENABLE_TRACERS)
        self.var_dot = self.create_checkbox(esp_frame, "Show Head Dot", visuals.ENABLE_DOT)
        self.var_name = self.create_checkbox(esp_frame, "Show Names", visuals.ENABLE_NAME)
        self.var_dist = self.create_checkbox(esp_frame, "Show Distance", visuals.ENABLE_DISTANCE)
        self.var_hp = self.create_checkbox(esp_frame, "Show Health", visuals.ENABLE_HEALTH)

        # 2. Triggerbot Section
        self.create_section_header("Triggerbot")
        trig_frame = self.create_panel()
        self.var_trigger = self.create_checkbox(trig_frame, "Enable Triggerbot", visuals.ENABLE_TRIGGERBOT)
        
        key_row = tk.Frame(trig_frame, bg=FRAME_BG)
        key_row.pack(fill='x', padx=10, pady=5)
        tk.Label(key_row, text="Trigger Key:", bg=FRAME_BG, fg=FG_COLOR).pack(side='left')
        
        # Safe Key Name
        try:
            vk = int(visuals.TRIGGER_KEY)
            init_key_name = VK_MAP.get(vk, f"KEY {vk}")
        except:
            init_key_name = "UNK"

        self.btn_bind = tk.Button(key_row, text=init_key_name, bg=BUTTON_BG, fg=FG_COLOR, 
                                  width=12, relief="flat", command=self.start_binding)
        self.btn_bind.pack(side='right')

        # Mode
        tk.Label(trig_frame, text="Mode:", bg=FRAME_BG, fg="#aaaaaa").pack(anchor='w', padx=10, pady=(5,0))
        self.combo_trig_mode = ttk.Combobox(trig_frame, values=["Click", "Hold"], state="readonly")
        self.combo_trig_mode.set(visuals.TRIGGER_MODE)
        self.combo_trig_mode.pack(fill='x', padx=10, pady=2)
        self.combo_trig_mode.bind("<<ComboboxSelected>>", self.update_visuals)

        # Delays
        self.slider_delay, self.lbl_delay = self.create_labeled_slider(trig_frame, "Start Dly:", 0, 150, visuals.TRIGGER_DELAY)
        
        # NEW: Rapid Fire Section
        self.create_horizontal_line(trig_frame)
        self.var_rapid = self.create_checkbox(trig_frame, "Rapid Fire (Hold Mode)", visuals.RAPID_FIRE)
        self.slider_rapid, self.lbl_rapid = self.create_labeled_slider(trig_frame, "Rapid ms:", 10, 100, visuals.RAPID_DELAY)

        # 3. Settings
        self.create_section_header("ESP Settings")
        settings_frame = self.create_panel()
        
        self.var_dist_limit = self.create_checkbox(settings_frame, "Limit Render Distance", visuals.ENABLE_DISTANCE_LIMIT)
        self.slider_dist, self.lbl_dist = self.create_labeled_slider(settings_frame, "Max Dist:", 300, 3000, visuals.MAX_DISTANCE)
        self.slider_radius, self.lbl_radius = self.create_labeled_slider(settings_frame, "Dot Size:", 1, 15, visuals.DOT_RADIUS)
        self.slider_font, self.lbl_font = self.create_labeled_slider(settings_frame, "Text Size:", 1, 14, visuals.FONT_SIZE_INDEX)

        # 4. Colors
        self.create_section_header("Colors")
        color_frame = self.create_panel()
        self.create_color_btn(color_frame, "Tracer Color", visuals.TRACER_COLOR, "TRACER_COLOR")
        self.create_color_btn(color_frame, "Dot Color", visuals.DOT_COLOR, "DOT_COLOR")

        # 5. System
        self.create_section_header("System")
        action_frame = self.create_panel()
        
        tk.Button(action_frame, text="RE-ATTACH TO GAME", bg="#2979FF", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", command=self.reattach_game).pack(fill='x', padx=10, pady=5)
        tk.Button(action_frame, text="SAVE CONFIG", bg="#00C853", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", command=visuals.save).pack(fill='x', padx=10, pady=5)
        tk.Button(action_frame, text="EXIT", bg="#D50000", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", command=self.close_app).pack(fill='x', padx=10, pady=5)

        # START UPDATES NOW
        self.initialized = True
        self.update_visuals()

    def reattach_game(self):
        print("Force re-attaching via GUI...")
        threading.Thread(target=self.memory.attach, daemon=True).start()

    def start_binding(self):
        self.btn_bind.config(text="...", bg=ACCENT_COLOR, fg="black")
        self.binding_event = threading.Event()
        threading.Thread(target=self.wait_for_input, daemon=True).start()

    def wait_for_input(self):
        found_vk = None

        def on_key(e):
            nonlocal found_vk
            if e.event_type == 'down':
                try:
                    if e.name == 'alt': vk = 0xA4
                    elif e.name == 'ctrl': vk = 0xA2
                    elif e.name == 'shift': vk = 0xA0
                    else:
                        ret = win32api.VkKeyScan(e.name)
                        vk = ret & 0xFF if ret != -1 else e.scan_code
                    found_vk = vk
                    self.binding_event.set()
                except: pass

        def on_mouse(e):
            nonlocal found_vk
            if isinstance(e, mouse.ButtonEvent) and e.event_type == 'down':
                btn = str(e.button).lower()
                if btn == 'left': found_vk = 0x01
                elif btn == 'right': found_vk = 0x02
                elif btn == 'middle': found_vk = 0x04
                elif btn == 'x': found_vk = 0x05 
                elif btn == 'x2': found_vk = 0x06
                else: found_vk = 0x05
                self.binding_event.set()

        kb_hook = keyboard.hook(on_key)
        ms_hook = mouse.hook(on_mouse)
        self.binding_event.wait()
        keyboard.unhook(kb_hook)
        mouse.unhook(ms_hook)

        if found_vk:
            visuals.TRIGGER_KEY = int(found_vk) # FORCE INT
            name = VK_MAP.get(found_vk, f"KEY {found_vk}")
            if "KEY" in name and found_vk < 128:
                try: name = chr(found_vk).upper()
                except: pass
            self.root.after(0, lambda: self.btn_bind.config(text=name, bg=BUTTON_BG, fg=FG_COLOR))

    def create_section_header(self, text):
        ttk.Label(self.root, text=text, style="Header.TLabel").pack(anchor='w', padx=15, pady=(15, 2))

    def create_panel(self):
        frame = tk.Frame(self.root, bg=FRAME_BG)
        frame.pack(fill='x', padx=10, pady=0)
        return frame

    def create_checkbox(self, parent, text, val):
        var = tk.BooleanVar(value=val)
        ttk.Checkbutton(parent, text=text, variable=var, command=self.update_visuals).pack(anchor='w', padx=10, pady=2)
        return var

    def create_horizontal_line(self, parent):
        tk.Frame(parent, height=1, bg="#444444").pack(fill='x', padx=10, pady=5)

    def create_labeled_slider(self, parent, label_text, min_v, max_v, current):
        row = tk.Frame(parent, bg=FRAME_BG)
        row.pack(fill='x', padx=10, pady=5)
        tk.Label(row, text=label_text, bg=FRAME_BG, fg=FG_COLOR, width=10, anchor='w').pack(side='left')
        val_label = tk.Label(row, text=str(int(current)), bg=FRAME_BG, fg=ACCENT_COLOR, width=4, font=("Consolas", 10, "bold"))
        val_label.pack(side='right')
        scale = ttk.Scale(row, from_=min_v, to=max_v, command=lambda v: self.update_visuals())
        scale.set(current)
        scale.pack(side='left', fill='x', expand=True, padx=5)
        return scale, val_label

    def create_color_btn(self, parent, text, current_col, attr_name):
        try: hex_col = '#%02x%02x%02x' % (int(current_col[0]), int(current_col[1]), int(current_col[2]))
        except: hex_col = "#FFFFFF"
        row = tk.Frame(parent, bg=FRAME_BG)
        row.pack(fill='x', padx=10, pady=4)
        tk.Label(row, text=text, bg=FRAME_BG, fg=FG_COLOR).pack(side='left')
        btn = tk.Button(row, bg=hex_col, width=6, relief="flat", command=lambda: self.pick_color(btn, attr_name))
        btn.pack(side='right')

    def pick_color(self, btn, attr_name):
        color = colorchooser.askcolor(title="Choose Color")
        if color[0]:
            rgb = (int(color[0][0]), int(color[0][1]), int(color[0][2]))
            btn.config(bg=color[1])
            setattr(visuals, attr_name, rgb)

    def update_visuals(self, *args):
        # CRITICAL FIX: PREVENT STARTUP CRASH
        if not getattr(self, 'initialized', False): return

        visuals.ENABLE_ESP = self.var_esp.get()
        # REMOVED TEAM CHECK UPDATE LOGIC
        visuals.ENABLE_TRACERS = self.var_tracer.get()
        visuals.ENABLE_DOT = self.var_dot.get()
        visuals.ENABLE_NAME = self.var_name.get()
        visuals.ENABLE_DISTANCE = self.var_dist.get()
        visuals.ENABLE_HEALTH = self.var_hp.get()
        visuals.ENABLE_DISTANCE_LIMIT = self.var_dist_limit.get()
        visuals.ENABLE_TRIGGERBOT = self.var_trigger.get()
        visuals.RAPID_FIRE = self.var_rapid.get()
        
        visuals.MAX_DISTANCE = int(self.slider_dist.get())
        visuals.DOT_RADIUS = float(self.slider_radius.get())
        visuals.FONT_SIZE_INDEX = int(self.slider_font.get())
        visuals.TRIGGER_DELAY = int(self.slider_delay.get())
        visuals.RAPID_DELAY = int(self.slider_rapid.get())
        visuals.TRIGGER_MODE = self.combo_trig_mode.get()

        self.lbl_dist.config(text=str(visuals.MAX_DISTANCE))
        self.lbl_radius.config(text=f"{visuals.DOT_RADIUS:.1f}")
        self.lbl_font.config(text=str(visuals.FONT_SIZE_INDEX))
        self.lbl_delay.config(text=str(visuals.TRIGGER_DELAY))
        self.lbl_rapid.config(text=str(visuals.RAPID_DELAY))

    def close_app(self):
        os._exit(0)

def run_gui(memory_ref):
    root = tk.Tk()
    app = ESP_GUI(root, memory_ref)
    root.mainloop()
