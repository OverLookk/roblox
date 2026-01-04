import tkinter as tk
from tkinter import ttk, colorchooser
import os
from config import visuals

# --- THEME COLORS ---
BG_COLOR = "#1e1e1e"       # Dark Grey
FG_COLOR = "#ffffff"       # White Text
ACCENT_COLOR = "#00e5ff"   # Cyan Accent
FRAME_BG = "#2b2b2b"       # Slightly lighter grey for panels
BUTTON_BG = "#3c3c3c"
BUTTON_ACTIVE = "#505050"

class ESP_GUI:
    def __init__(self, root, memory_ref):
        self.root = root
        self.memory = memory_ref
        self.root.title("Nexus ESP")
        self.root.geometry("400x820")
        self.root.configure(bg=BG_COLOR)
        self.root.attributes("-topmost", True) 
        self.root.resizable(False, False)

        # --- Dropdown Color Fix ---
        # This forces the popup listbox of Comboboxes to be Dark Grey with White Text
        self.root.option_add('*TCombobox*Listbox.background', FRAME_BG)
        self.root.option_add('*TCombobox*Listbox.foreground', FG_COLOR)
        self.root.option_add('*TCombobox*Listbox.selectBackground', ACCENT_COLOR)
        self.root.option_add('*TCombobox*Listbox.selectForeground', 'black')

        # --- Custom Style Configuration ---
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure(".", background=BG_COLOR, foreground=FG_COLOR, borderwidth=0)
        style.configure("TLabel", background=FRAME_BG, foreground=FG_COLOR, font=("Segoe UI", 10))
        style.configure("Header.TLabel", background=BG_COLOR, foreground=ACCENT_COLOR, font=("Segoe UI", 11, "bold"))
        style.configure("TCheckbutton", background=FRAME_BG, foreground=FG_COLOR, font=("Segoe UI", 10))
        style.map("TCheckbutton", background=[('active', FRAME_BG)], indicatorcolor=[('selected', ACCENT_COLOR)])
        
        # Style for the Entry/Combobox field itself
        style.configure("TCombobox", fieldbackground=BUTTON_BG, background=BUTTON_BG, foreground=FG_COLOR, arrowcolor=FG_COLOR, borderwidth=0)
        style.map("TCombobox", fieldbackground=[('readonly', BUTTON_BG)], selectbackground=[('readonly', BUTTON_BG)], selectforeground=[('readonly', FG_COLOR)])

        # --- Main Layout ---
        
        # 1. Master Toggle Section
        self.create_section_header("Main Control")
        main_frame = self.create_panel()
        self.var_esp = self.create_checkbox(main_frame, "Master ESP Switch", visuals.ENABLE_ESP)

        # 2. Visual Elements Section
        self.create_section_header("Visual Elements")
        elem_frame = self.create_panel()
        self.var_tracer = self.create_checkbox(elem_frame, "Show Tracers", visuals.ENABLE_TRACERS)
        self.var_dot = self.create_checkbox(elem_frame, "Show Head Dot", visuals.ENABLE_DOT)
        self.var_name = self.create_checkbox(elem_frame, "Show Names", visuals.ENABLE_NAME)
        self.var_dist = self.create_checkbox(elem_frame, "Show Distance", visuals.ENABLE_DISTANCE)
        self.var_hp = self.create_checkbox(elem_frame, "Show Health", visuals.ENABLE_HEALTH)

        # 3. Settings & Sliders Section
        self.create_section_header("Configuration")
        settings_frame = self.create_panel()
        
        # Distance Limit
        self.var_dist_limit = self.create_checkbox(settings_frame, "Limit Render Distance", visuals.ENABLE_DISTANCE_LIMIT)
        self.slider_dist, self.lbl_dist = self.create_labeled_slider(settings_frame, "Max Dist:", 300, 3000, visuals.MAX_DISTANCE)
        
        # Dot Radius
        self.slider_radius, self.lbl_radius = self.create_labeled_slider(settings_frame, "Dot Size:", 1, 15, visuals.DOT_RADIUS)
        
        # Text Size
        self.slider_font, self.lbl_font = self.create_labeled_slider(settings_frame, "Text Size:", 1, 14, visuals.FONT_SIZE_INDEX)

        # Tracer Origin
        tk.Label(settings_frame, text="Tracer Origin:", bg=FRAME_BG, fg="#aaaaaa", font=("Segoe UI", 9)).pack(anchor='w', padx=10, pady=(8, 0))
        self.combo_origin = ttk.Combobox(settings_frame, values=["Bottom", "Center", "Mouse"], state="readonly")
        self.combo_origin.set(visuals.TRACER_ORIGIN)
        self.combo_origin.pack(fill='x', padx=10, pady=5)
        self.combo_origin.bind("<<ComboboxSelected>>", self.update_visuals)

        # Text Position (New)
        tk.Label(settings_frame, text="Info Position:", bg=FRAME_BG, fg="#aaaaaa", font=("Segoe UI", 9)).pack(anchor='w', padx=10, pady=(8, 0))
        self.combo_text_pos = ttk.Combobox(settings_frame, values=["Top", "Bottom"], state="readonly")
        self.combo_text_pos.set(visuals.TEXT_POSITION)
        self.combo_text_pos.pack(fill='x', padx=10, pady=5)
        self.combo_text_pos.bind("<<ComboboxSelected>>", self.update_visuals)

        # 4. Colors Section
        self.create_section_header("Color Theme")
        color_frame = self.create_panel()
        self.create_color_btn(color_frame, "Tracer Color", visuals.TRACER_COLOR, "TRACER_COLOR")
        self.create_color_btn(color_frame, "Dot Color", visuals.DOT_COLOR, "DOT_COLOR")

        # 5. Actions
        self.create_section_header("System")
        action_frame = self.create_panel()
        
        btn_save = tk.Button(action_frame, text="SAVE CONFIG", bg="#00C853", fg="white", 
                             font=("Segoe UI", 9, "bold"), relief="flat", command=visuals.save)
        btn_save.pack(fill='x', padx=10, pady=5)

        btn_reattach = tk.Button(action_frame, text="FORCE RE-ATTACH", bg="#2962FF", fg="white", 
                                 font=("Segoe UI", 9, "bold"), relief="flat", command=self.memory.attach)
        btn_reattach.pack(fill='x', padx=10, pady=5)

        # Close Button
        btn_close = tk.Button(action_frame, text="EXIT CHEAT", bg="#D50000", fg="white", 
                              font=("Segoe UI", 9, "bold"), relief="flat", command=self.close_app)
        btn_close.pack(fill='x', padx=10, pady=(15, 5))

        self.update_visuals()

    def close_app(self):
        # Force kill the process
        os._exit(0)

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
        visuals.ENABLE_ESP = self.var_esp.get()
        visuals.ENABLE_TRACERS = self.var_tracer.get()
        visuals.ENABLE_DOT = self.var_dot.get()
        visuals.ENABLE_NAME = self.var_name.get()
        visuals.ENABLE_DISTANCE = self.var_dist.get()
        visuals.ENABLE_HEALTH = self.var_hp.get()
        visuals.ENABLE_DISTANCE_LIMIT = self.var_dist_limit.get()
        
        visuals.MAX_DISTANCE = int(self.slider_dist.get())
        visuals.DOT_RADIUS = float(self.slider_radius.get())
        visuals.FONT_SIZE_INDEX = int(self.slider_font.get())
        visuals.TRACER_ORIGIN = self.combo_origin.get()
        visuals.TEXT_POSITION = self.combo_text_pos.get()

        self.lbl_dist.config(text=str(visuals.MAX_DISTANCE))
        self.lbl_radius.config(text=f"{visuals.DOT_RADIUS:.1f}")
        self.lbl_font.config(text=str(visuals.FONT_SIZE_INDEX))

def run_gui(memory_ref):
    root = tk.Tk()
    app = ESP_GUI(root, memory_ref)
    root.mainloop()