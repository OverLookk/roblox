import tkinter as tk
from tkinter import ttk, colorchooser
from config import visuals

class ESP_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP Config")
        self.root.geometry("360x780")
        self.root.attributes("-topmost", True) 
        self.root.resizable(False, False)

        style = ttk.Style()
        style.theme_use('clam')

        # --- Master Toggle ---
        self.create_header("Main Switch")
        self.var_esp = self.create_checkbox("Enable Master ESP", visuals.ENABLE_ESP)
        
        ttk.Separator(root, orient='horizontal').pack(fill='x', pady=10)

        # --- Element Toggles ---
        self.create_header("Elements")
        self.var_tracer = self.create_checkbox("Tracers", visuals.ENABLE_TRACERS)
        self.var_dot = self.create_checkbox("Head Dot", visuals.ENABLE_DOT)
        self.var_name = self.create_checkbox("Names", visuals.ENABLE_NAME)
        self.var_dist = self.create_checkbox("Distance Text", visuals.ENABLE_DISTANCE)
        self.var_hp = self.create_checkbox("Health Text", visuals.ENABLE_HEALTH)

        # --- Range Limit with Value Label ---
        self.create_header("Render Distance")
        self.slider_dist, self.lbl_dist = self.create_slider_with_label(300, 1300, visuals.MAX_DISTANCE)

        # --- Tracer Origin ---
        self.create_header("Tracer Origin")
        self.combo_origin = ttk.Combobox(self.root, values=["Bottom", "Center", "Mouse"], state="readonly")
        self.combo_origin.set(visuals.TRACER_ORIGIN)
        self.combo_origin.pack(fill='x', padx=20)
        self.combo_origin.bind("<<ComboboxSelected>>", self.update_visuals)

        # --- Dot Radius ---
        self.create_header("Dot Radius")
        self.slider_radius, self.lbl_radius = self.create_slider_with_label(1, 10, visuals.DOT_RADIUS)
        
        # --- Font Size ---
        self.create_header("Font Size")
        self.slider_font, self.lbl_font = self.create_slider_with_label(1, 10, visuals.FONT_SIZE_INDEX)

        # --- Max HP Dropdown (100, 150, 200) ---
        self.create_header("Max HP (Calibration)")
        # Ensuring 150 is the default if not already set
        if visuals.MAX_HEALTH not in [100, 150, 200]:
            visuals.MAX_HEALTH = 150
            
        self.combo_hp = ttk.Combobox(self.root, values=["100", "150", "200"], state="readonly")
        self.combo_hp.set(str(visuals.MAX_HEALTH))
        self.combo_hp.pack(fill='x', padx=20)
        self.combo_hp.bind("<<ComboboxSelected>>", self.update_visuals)

        # --- Colors ---
        self.create_header("Colors")
        self.create_color_btn("Tracer Color", visuals.TRACER_COLOR, "TRACER_COLOR")
        self.create_color_btn("Dot Color", visuals.DOT_COLOR, "DOT_COLOR")
        
        # Initial call to sync labels and settings
        self.update_visuals()

    def create_header(self, text):
        ttk.Label(self.root, text=text, font=("Segoe UI", 9, "bold")).pack(anchor='w', padx=10, pady=(10, 2))

    def create_checkbox(self, text, val):
        var = tk.BooleanVar(value=val)
        ttk.Checkbutton(self.root, text=text, variable=var, command=self.update_visuals).pack(anchor='w', padx=20)
        return var

    def create_slider_with_label(self, min_v, max_v, current):
        frame = ttk.Frame(self.root)
        frame.pack(fill='x', padx=20)
        
        # This label shows the actual number beside the slider
        val_label = ttk.Label(frame, text=str(int(current)), width=5)
        val_label.pack(side='right')
        
        scale = ttk.Scale(frame, from_=min_v, to=max_v, command=lambda v: self.update_visuals())
        scale.set(current)
        scale.pack(side='left', fill='x', expand=True)
        
        return scale, val_label

    def create_color_btn(self, text, current_col, attr_name):
        # Convert RGB to Hex for the button background
        hex_col = '#%02x%02x%02x' % (int(current_col[0]), int(current_col[1]), int(current_col[2]))
        frame = ttk.Frame(self.root)
        frame.pack(fill='x', padx=20, pady=2)
        ttk.Label(frame, text=text).pack(side='left')
        btn = tk.Button(frame, bg=hex_col, width=4, command=lambda: self.pick_color(btn, attr_name))
        btn.pack(side='right')

    def pick_color(self, btn, attr_name):
        color = colorchooser.askcolor(title="Choose Color")
        if color[0]:
            rgb = (int(color[0][0]), int(color[0][1]), int(color[0][2]))
            btn.config(bg=color[1])
            setattr(visuals, attr_name, rgb)

    def update_visuals(self, *args):
        # 1. Update the shared config object
        visuals.ENABLE_ESP = self.var_esp.get()
        visuals.ENABLE_TRACERS = self.var_tracer.get()
        visuals.ENABLE_DOT = self.var_dot.get()
        visuals.ENABLE_NAME = self.var_name.get()
        visuals.ENABLE_DISTANCE = self.var_dist.get()
        visuals.ENABLE_HEALTH = self.var_hp.get()
        
        visuals.MAX_DISTANCE = int(self.slider_dist.get())
        visuals.DOT_RADIUS = float(self.slider_radius.get())
        visuals.FONT_SIZE_INDEX = int(self.slider_font.get())
        visuals.TRACER_ORIGIN = self.combo_origin.get()
        visuals.MAX_HEALTH = int(self.combo_hp.get())

        # 2. Update GUI Value Labels to match sliders
        self.lbl_dist.config(text=str(visuals.MAX_DISTANCE))
        self.lbl_radius.config(text=f"{visuals.DOT_RADIUS:.1f}")
        self.lbl_font.config(text=str(visuals.FONT_SIZE_INDEX))

def run_gui():
    root = tk.Tk()
    app = ESP_GUI(root)
    root.mainloop()