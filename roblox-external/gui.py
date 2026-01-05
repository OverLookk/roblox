import tkinter as tk
from tkinter import ttk, colorchooser
import os
import threading
import keyboard
import mouse
import win32api
from config import visuals

def get_contrasting_text(hex_color):
    h = hex_color.lstrip('#')
    rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    luminance = (0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2])/255
    return "#000000" if luminance > 0.5 else "#ffffff"

class ESP_GUI:
    def __init__(self, root, memory_ref):
        self.root = root
        self.memory = memory_ref
        self.panels = [] 
        
        self.root.title("ovrhax - @OverLookk")
        self.root.geometry("750x570") 
        self.root.attributes("-topmost", True) 
        self.root.resizable(False, False)

        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill='both', expand=True, padx=10, pady=10)

        self.left_col = tk.Frame(self.main_container, width=350)
        self.left_col.pack(side='left', fill='both', expand=True, padx=(0, 5))

        self.right_col = tk.Frame(self.main_container, width=350)
        self.right_col.pack(side='right', fill='both', expand=True, padx=(5, 0))

        # Build Sections
        self.build_theme_section(self.left_col)
        self.build_esp_section(self.left_col)
        self.build_settings_section(self.left_col)
        self.build_colors_section(self.left_col)
        
        self.build_aimbot_section(self.right_col)
        self.build_trigger_section(self.right_col)

        self.footer = tk.Frame(self.root)
        self.footer.pack(fill='x', padx=10, pady=(0, 10))
        self.build_system_section(self.footer)

        self.initialized = True
        self.update_visuals() 
        self.apply_theme()    

    def apply_theme(self):
        bg = visuals.UI_BG_COLOR
        fg = get_contrasting_text(bg)
        accent = visuals.UI_ACCENT_COLOR
        panel_bg = visuals.UI_PANEL_COLOR 
        
        # Root & Columns
        self.root.configure(bg=bg)
        self.main_container.configure(bg=bg)
        self.left_col.configure(bg=bg)
        self.right_col.configure(bg=bg)

        # Style Configs
        self.style.configure(".", background=bg, foreground=fg, borderwidth=0)
        self.style.configure("TLabel", background=panel_bg, foreground=fg)
        self.style.configure("Header.TLabel", background=bg, foreground=accent, font=("Segoe UI", 12, "bold"))
        self.style.configure("TCheckbutton", background=panel_bg, foreground=fg)
        
        # Combobox styling
        self.style.configure(
            "TCombobox",
            fieldbackground=panel_bg,
            background=panel_bg,
            foreground=fg,
            arrowcolor=accent
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", panel_bg)],
            foreground=[("readonly", fg)]
        )
        self.root.option_add("*TCombobox*Listbox.background", panel_bg)
        self.root.option_add("*TCombobox*Listbox.foreground", fg)
        self.root.option_add("*TCombobox*Listbox.selectBackground", accent)
        self.root.option_add("*TCombobox*Listbox.selectForeground", bg)
        
        self.style.map("TCheckbutton", 
                       background=[('active', panel_bg)], 
                       indicatorcolor=[('selected', accent)])

        # Recursively update manual widgets
        self.update_widget_colors(self.root, bg, panel_bg, fg, accent)

    def update_widget_colors(self, widget, bg, panel_bg, fg, accent):
        try:
            w_type = widget.winfo_class()
            
            # Skip special buttons (Save, Exit, Reattach)
            if getattr(widget, "is_special_btn", False):
                return

            # Panels vs Background
            if getattr(widget, "is_panel", False):
                widget.configure(bg=panel_bg)
            
            elif w_type == 'Frame':
                widget.configure(bg=bg)
                
            elif w_type == 'Label':
                if getattr(widget, "is_header", False):
                    widget.configure(bg=bg, fg=accent)
                elif getattr(widget, "is_value_label", False):
                    widget.configure(bg=panel_bg, fg=accent)
                else:
                    widget.configure(bg=panel_bg, fg=fg)
                    
            elif w_type == 'Button':
                if getattr(widget, "is_color_btn", False):
                    widget.configure(
                        highlightbackground=accent,
                        highlightcolor=accent,
                        highlightthickness=1,
                        bd=1,
                        relief="solid"
                    )
                else:
                    widget.configure(bg="#3c3c3c", fg="#ffffff")
        except: pass
        
        for child in widget.winfo_children():
            self.update_widget_colors(child, bg, panel_bg, fg, accent)

    # --- BUILDERS ---
    def create_panel(self, parent):
        frame = tk.Frame(parent)
        frame.is_panel = True 
        frame.pack(fill='x', padx=5, pady=0)
        self.panels.append(frame)
        return frame

    def build_theme_section(self, parent):
        self.create_section_header(parent, "UI Theme")
        frame = self.create_panel(parent)
        
        # BG Row
        row_bg = tk.Frame(frame)
        row_bg.is_panel = True
        row_bg.pack(fill='x', padx=5, pady=(5, 2))
        tk.Label(row_bg, text="Background:", width=12, anchor='w').pack(side='left')
        self.btn_bg_col = tk.Button(row_bg, bg=visuals.UI_BG_COLOR, width=8, relief="flat",
                                    command=lambda: self.pick_ui_color("UI_BG_COLOR", self.btn_bg_col))
        self.btn_bg_col.pack(side='right', padx=2)
        self.btn_bg_col.is_color_btn = True

        # Accent Row
        row_acc = tk.Frame(frame)
        row_acc.is_panel = True
        row_acc.pack(fill='x', padx=5, pady=2)
        tk.Label(row_acc, text="Accent:", width=12, anchor='w').pack(side='left')
        self.btn_acc_col = tk.Button(row_acc, bg=visuals.UI_ACCENT_COLOR, width=8, relief="flat",
                                     command=lambda: self.pick_ui_color("UI_ACCENT_COLOR", self.btn_acc_col))
        self.btn_acc_col.pack(side='right', padx=2)
        self.btn_acc_col.is_color_btn = True

        # Panel Color Row
        row_pnl = tk.Frame(frame)
        row_pnl.is_panel = True
        row_pnl.pack(fill='x', padx=5, pady=(2, 5))
        tk.Label(row_pnl, text="Panel Color:", width=12, anchor='w').pack(side='left')
        self.btn_pnl_col = tk.Button(row_pnl, bg=visuals.UI_PANEL_COLOR, width=8, relief="flat",
                                     command=lambda: self.pick_ui_color("UI_PANEL_COLOR", self.btn_pnl_col))
        self.btn_pnl_col.pack(side='right', padx=2)
        self.btn_pnl_col.is_color_btn = True

    def build_esp_section(self, parent):
        self.create_section_header(parent, "ESP")
        frame = self.create_panel(parent)
        self.var_esp = self.create_checkbox(frame, "Master Switch", visuals.ENABLE_ESP)
        self.var_tracer = self.create_checkbox(frame, "Tracers", visuals.ENABLE_TRACERS)
        self.var_dot = self.create_checkbox(frame, "Head Dot", visuals.ENABLE_DOT)
        self.var_name = self.create_checkbox(frame, "Names", visuals.ENABLE_NAME)
        self.var_hp = self.create_checkbox(frame, "Health", visuals.ENABLE_HEALTH)

    def build_aimbot_section(self, parent):
        self.create_section_header(parent, "Aimbot")
        frame = self.create_panel(parent)

        row_enable = tk.Frame(frame)
        row_enable.is_panel = True
        row_enable.pack(fill='x', padx=5, pady=(4, 2))
        self.var_aimbot = tk.BooleanVar(value=visuals.ENABLE_AIMBOT)
        ttk.Checkbutton(row_enable, text="Enable", variable=self.var_aimbot, command=self.update_visuals).pack(side='left', padx=5)

        row_fov = tk.Frame(frame)
        row_fov.is_panel = True
        row_fov.pack(fill='x', padx=5, pady=2)
        self.var_fov_ring = tk.BooleanVar(value=visuals.SHOW_FOV_RING)
        ttk.Checkbutton(row_fov, text="FOV Ring", variable=self.var_fov_ring, command=self.update_visuals).pack(side='left', padx=5)

        row_fov_color = tk.Frame(frame)
        row_fov_color.is_panel = True
        row_fov_color.pack(fill='x', padx=5, pady=(2, 4))
        tk.Label(row_fov_color, text="FOV Color:", font=("Segoe UI", 8)).pack(side='left')
        self.btn_fov_col = tk.Button(row_fov_color, bg=self.rgb_to_hex(visuals.FOV_COLOR), width=8, relief="flat",
                                     command=lambda: self.pick_color(self.btn_fov_col, "FOV_COLOR"))
        self.btn_fov_col.pack(side='right', padx=5)
        self.btn_fov_col.is_color_btn = True

        row_pri = tk.Frame(frame)
        row_pri.is_panel = True
        row_pri.pack(fill='x', padx=10, pady=(2, 2))
        tk.Label(row_pri, text="Priority:", font=("Segoe UI", 8)).pack(anchor='w')
        self.combo_priority = ttk.Combobox(row_pri, values=["Crosshair", "Lowest HP", "Proximity"], state="readonly")
        self.combo_priority.set(visuals.AIMBOT_PRIORITY)
        self.combo_priority.pack(fill='x', expand=True, pady=(2, 0))

        row_mode = tk.Frame(frame)
        row_mode.is_panel = True
        row_mode.pack(fill='x', padx=10, pady=(2, 5))
        tk.Label(row_mode, text="Mode:", font=("Segoe UI", 8)).pack(anchor='w')
        self.combo_aim_mode = ttk.Combobox(row_mode, values=["Hold", "Toggle"], state="readonly")
        self.combo_aim_mode.set(visuals.AIMBOT_MODE)
        self.combo_aim_mode.pack(fill='x', expand=True, pady=(2, 0))

        key_row = tk.Frame(frame)
        key_row.is_panel = True
        key_row.pack(fill='x', padx=10, pady=5)
        tk.Label(key_row, text="Aim Key:").pack(side='left')
        self.btn_bind_aim = self.create_bind_btn(key_row, visuals.AIMBOT_KEY, "AIMBOT_KEY")
        self.btn_bind_aim.pack(side='right')

        self.slider_fov, self.lbl_fov = self.create_labeled_slider(frame, "FOV:", 10, 600, visuals.AIMBOT_FOV)
        self.slider_smooth, self.lbl_smooth = self.create_labeled_slider(frame, "Smooth:", 1, 20, visuals.AIMBOT_SMOOTH)
        self.slider_sens, self.lbl_sens = self.create_labeled_slider(frame, "Sens:", 0.1, 2.0, visuals.AIMBOT_SENS)

    def build_trigger_section(self, parent):
        self.create_section_header(parent, "Triggerbot")
        frame = self.create_panel(parent)
        self.var_trigger = self.create_checkbox(frame, "Enable", visuals.ENABLE_TRIGGERBOT)
        
        row_mode = tk.Frame(frame)
        row_mode.is_panel = True
        row_mode.pack(fill='x', padx=10, pady=(4, 2))
        tk.Label(row_mode, text="Mode:", font=("Segoe UI", 8)).pack(anchor='w')
        self.combo_trig_mode = ttk.Combobox(row_mode, values=["Hold", "Toggle"], state="readonly")
        self.combo_trig_mode.set(visuals.TRIGGER_MODE)
        self.combo_trig_mode.pack(fill='x', expand=True, pady=(2, 0))

        row_bind = tk.Frame(frame)
        row_bind.is_panel = True
        row_bind.pack(fill='x', padx=10, pady=(2, 5))
        tk.Label(row_bind, text="Trigger Key:", font=("Segoe UI", 8)).pack(side='left')
        self.btn_bind_trig = self.create_bind_btn(row_bind, visuals.TRIGGER_KEY, "TRIGGER_KEY")
        self.btn_bind_trig.pack(side='right')
        
        self.slider_trig_delay, self.lbl_trig_delay = self.create_labeled_slider(frame, "Delay (s):", 0.0, 1.0, visuals.TRIGGER_DELAY, is_float=True)
        self.slider_trig_fov, self.lbl_trig_fov = self.create_labeled_slider(frame, "FOV px:", 2, 50, visuals.TRIGGER_FOV)

    def build_settings_section(self, parent):
        self.create_section_header(parent, "Global Settings")
        frame = self.create_panel(parent)
        self.var_dist_limit = self.create_checkbox(frame, "Limit Distance", visuals.ENABLE_DISTANCE_LIMIT)
        self.slider_dist, self.lbl_dist = self.create_labeled_slider(frame, "Max Dist:", 300, 3000, visuals.MAX_DISTANCE)

    def build_colors_section(self, parent):
        self.create_section_header(parent, "ESP Colors")
        frame = self.create_panel(parent)

        row_tracer = tk.Frame(frame)
        row_tracer.is_panel = True
        row_tracer.pack(fill='x', padx=5, pady=2)
        tk.Label(row_tracer, text="Tracer Color:", font=("Segoe UI", 8)).pack(side='left')
        self.btn_tracer_col = tk.Button(row_tracer, bg=self.rgb_to_hex(visuals.TRACER_COLOR), width=8, relief="flat",
                                        command=lambda: self.pick_color(self.btn_tracer_col, "TRACER_COLOR"))
        self.btn_tracer_col.pack(side='right', padx=5)
        self.btn_tracer_col.is_color_btn = True

        row_dot = tk.Frame(frame)
        row_dot.is_panel = True
        row_dot.pack(fill='x', padx=5, pady=(2, 5))
        tk.Label(row_dot, text="Head Dot Color:", font=("Segoe UI", 8)).pack(side='left')
        self.btn_dot_col = tk.Button(row_dot, bg=self.rgb_to_hex(visuals.DOT_COLOR), width=8, relief="flat",
                                     command=lambda: self.pick_color(self.btn_dot_col, "DOT_COLOR"))
        self.btn_dot_col.pack(side='right', padx=5)
        self.btn_dot_col.is_color_btn = True

    def build_system_section(self, parent):
        frame = tk.Frame(parent)
        frame.pack(fill='x')
        
        btn_grid = tk.Frame(frame)
        btn_grid.pack(fill='x')
        btn_grid.columnconfigure(0, weight=1, uniform="sysbtn")
        btn_grid.columnconfigure(1, weight=1, uniform="sysbtn")
        btn_grid.columnconfigure(2, weight=1, uniform="sysbtn")

        # Re-attach Button (Blue)
        btn_att = tk.Button(btn_grid, text="RE-ATTACH", bg="#2979FF", fg="white", font=("Segoe UI", 8, "bold"), relief="flat",
                  command=self.reattach_game)
        btn_att.grid(row=0, column=0, padx=2, sticky="ew")
        btn_att.is_special_btn = True

        # Save Button (Green)
        btn_save = tk.Button(btn_grid, text="SAVE", bg="#00C853", fg="white", font=("Segoe UI", 8, "bold"), relief="flat",
                  command=visuals.save)
        btn_save.grid(row=0, column=1, padx=2, sticky="ew")
        btn_save.is_special_btn = True

        # Exit Button (Red)
        btn_exit = tk.Button(btn_grid, text="EXIT", bg="#D50000", fg="white", font=("Segoe UI", 8, "bold"), relief="flat",
                  command=self.close_app)
        btn_exit.grid(row=0, column=2, padx=2, sticky="ew")
        btn_exit.is_special_btn = True

    # --- HELPERS ---
    def create_section_header(self, parent, text):
        lbl = tk.Label(parent, text=text, font=("Segoe UI", 11, "bold"))
        lbl.pack(anchor='w', padx=5, pady=(10, 2))
        lbl.is_header = True

    def create_checkbox(self, parent, text, val):
        var = tk.BooleanVar(value=val)
        ttk.Checkbutton(parent, text=text, variable=var, command=self.update_visuals).pack(anchor='w', padx=10, pady=2)
        return var

    def create_labeled_slider(self, parent, label_text, min_v, max_v, current, is_float=False):
        row = tk.Frame(parent)
        row.is_panel = True
        row.pack(fill='x', padx=10, pady=2)
        tk.Label(row, text=label_text, width=10, anchor='w', font=("Segoe UI", 8)).pack(side='left')
        
        display_val = f"{current:.2f}" if is_float else str(int(current))
        val_label = tk.Label(row, text=display_val, width=5, font=("Consolas", 9, "bold"))
        val_label.pack(side='right')
        val_label.is_value_label = True
        
        scale = ttk.Scale(row, from_=min_v, to=max_v, command=lambda v: self.update_visuals())
        scale.set(current)
        scale.pack(side='left', fill='x', expand=True, padx=5)
        return scale, val_label

    def create_bind_btn(self, parent, key_code, attr_name):
        text = self.format_key_name(key_code)
        btn = tk.Button(parent, text=text, bg="#3c3c3c", fg="white", width=10, relief="flat")
        btn.config(command=lambda: self.start_binding(attr_name, btn))
        return btn

    def rgb_to_hex(self, rgb):
        return '#%02x%02x%02x' % (int(rgb[0]), int(rgb[1]), int(rgb[2]))

    def pick_color(self, btn, attr_name):
        color = colorchooser.askcolor(title="Choose Color")
        if color[0]:
            rgb = (int(color[0][0]), int(color[0][1]), int(color[0][2]))
            btn.config(bg=color[1])
            setattr(visuals, attr_name, rgb)

    def pick_ui_color(self, attr_name, btn):
        color = colorchooser.askcolor(title="Choose UI Color")
        if color[1]:
            setattr(visuals, attr_name, color[1])
            btn.config(bg=color[1])
            self.apply_theme()

    def start_binding(self, config_key_name, btn_widget):
        btn_widget.config(text="...", bg=visuals.UI_ACCENT_COLOR, fg="black")
        self.binding_event = threading.Event()
        threading.Thread(target=lambda: self.wait_for_input(config_key_name, btn_widget), daemon=True).start()

    def wait_for_input(self, config_key_name, btn_widget):
        found_vk = None
        def on_key(e):
            nonlocal found_vk
            if e.event_type == 'down':
                found_vk = e.scan_code if e.scan_code else 0
                self.binding_event.set()
        def on_mouse(e):
            nonlocal found_vk
            if isinstance(e, mouse.ButtonEvent) and e.event_type == 'down':
                btn = str(e.button).lower()
                found_vk = { 'left':0x01, 'right':0x02, 'middle':0x04, 'x':0x05, 'x2':0x06 }.get(btn, 0x05)
                self.binding_event.set()
        
        kb = keyboard.hook(on_key)
        ms = mouse.hook(on_mouse)
        self.binding_event.wait()
        keyboard.unhook(kb)
        mouse.unhook(ms)

        if found_vk:
            setattr(visuals, config_key_name, int(found_vk))
            self.root.after(0, lambda: btn_widget.config(text=self.format_key_name(found_vk), bg="#3c3c3c", fg="white"))

    def format_key_name(self, key_code):
        mouse_map = {
            0x01: "L-CLICK",
            0x02: "R-CLICK",
            0x04: "M-CLICK",
            0x05: "X1",
            0x06: "X2",
        }
        return mouse_map.get(int(key_code), f"KEY {int(key_code)}")

    def update_visuals(self, *args):
        if not getattr(self, 'initialized', False): return

        visuals.ENABLE_ESP = self.var_esp.get()
        visuals.ENABLE_TRACERS = self.var_tracer.get()
        visuals.ENABLE_DOT = self.var_dot.get()
        visuals.ENABLE_NAME = self.var_name.get()
        visuals.ENABLE_HEALTH = self.var_hp.get()
        visuals.ENABLE_DISTANCE_LIMIT = self.var_dist_limit.get()
        
        visuals.ENABLE_AIMBOT = self.var_aimbot.get()
        visuals.SHOW_FOV_RING = self.var_fov_ring.get()
        visuals.AIMBOT_FOV = int(self.slider_fov.get())
        visuals.AIMBOT_SMOOTH = float(self.slider_smooth.get())
        visuals.AIMBOT_SENS = float(self.slider_sens.get())
        
        visuals.AIMBOT_PRIORITY = self.combo_priority.get()
        visuals.AIMBOT_MODE = self.combo_aim_mode.get()

        visuals.ENABLE_TRIGGERBOT = self.var_trigger.get()
        visuals.TRIGGER_MODE = self.combo_trig_mode.get()
        visuals.TRIGGER_DELAY = float(self.slider_trig_delay.get())
        visuals.TRIGGER_FOV = int(self.slider_trig_fov.get())
        
        visuals.MAX_DISTANCE = int(self.slider_dist.get())

        self.lbl_dist.config(text=str(visuals.MAX_DISTANCE))
        self.lbl_fov.config(text=str(visuals.AIMBOT_FOV))
        self.lbl_smooth.config(text=f"{visuals.AIMBOT_SMOOTH:.1f}")
        self.lbl_sens.config(text=f"{visuals.AIMBOT_SENS:.1f}")
        self.lbl_trig_delay.config(text=f"{visuals.TRIGGER_DELAY:.2f}")
        self.lbl_trig_fov.config(text=str(visuals.TRIGGER_FOV))

    def reattach_game(self):
        threading.Thread(target=self.memory.attach, daemon=True).start()

    def close_app(self):
        os._exit(0)

def run_gui(memory_ref):
    root = tk.Tk()
    app = ESP_GUI(root, memory_ref)
    root.mainloop()
