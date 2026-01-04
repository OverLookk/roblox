import pyglet
from pyglet import gl
import threading
import time
import win32gui
import win32con
import win32api
from config import visuals

class ESPOverlay:
    def __init__(self, memory):
        self.memory = memory
        self.screen_w = win32api.GetSystemMetrics(0)
        self.screen_h = win32api.GetSystemMetrics(1)
        
        config = pyglet.gl.Config(
            double_buffer=True, 
            depth_size=0, 
            sample_buffers=1, 
            samples=4
        )
        
        self.window = pyglet.window.Window(
            width=self.screen_w, height=self.screen_h,
            style=pyglet.window.Window.WINDOW_STYLE_BORDERLESS,
            caption="ESP Overlay", vsync=True, config=config
        )
        
        hwnd = self.window._hwnd
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                               ex_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_TOPMOST)
        win32gui.SetLayeredWindowAttributes(hwnd, 0, 0, win32con.LWA_COLORKEY)
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, self.screen_w, self.screen_h, win32con.SWP_SHOWWINDOW)

        self.player_cache = []
        self.view_matrix = None
        self.game_window = {'x': 0, 'y': 0, 'w': 1920, 'h': 1080}
        self.cache_lock = threading.Lock()
        self.running = True

        self.thread = threading.Thread(target=self.memory_loop, daemon=True)
        self.thread.start()
        
        pyglet.clock.schedule_interval(self.update_screen, 1/144.0)

    def update_screen(self, dt):
        self.window.clear()
        self.render()

    def memory_loop(self):
        while self.running:
            try:
                new_data = self.memory.get_player_data()
                new_matrix = self.memory.get_view_matrix()
                win_info = self.memory.get_window_info()
                
                with self.cache_lock:
                    self.player_cache = new_data
                    self.view_matrix = new_matrix
                    self.game_window = win_info
            except: pass
            time.sleep(0.005)

    def get_health_color(self, scaled_hp):
        # We use the SCALED health to determine color based on the Custom Max
        max_hp = visuals.MAX_HEALTH if visuals.MAX_HEALTH > 0 else 100
        hp = max(0, min(scaled_hp, max_hp))
        ratio = hp / max_hp
        
        # Gradient: Red (low) -> Green (high)
        r = int(255 * (1 - ratio))
        g = int(255 * ratio)
        b = 0
        return (r, g, b, 255)

    def render(self):
        if not visuals.ENABLE_ESP:
            return

        with self.cache_lock:
            players = list(self.player_cache)
            matrix = self.view_matrix
            gw = self.game_window 
        
        if not matrix: return 

        real_font_size = 7 + visuals.FONT_SIZE_INDEX

        for p in players:
            rx, ry = self.memory.world_to_screen(p["center_pos"], matrix, gw['w'], gw['h'])
            
            if rx <= 0 or ry <= 0: continue

            final_x = gw['x'] + rx
            raw_y   = gw['y'] + ry
            head_y = self.screen_h - raw_y

            # --- CALCULATE SCALED HEALTH ---
            # Standard Roblox HP is 100. We normalize raw HP to 0.0-1.0
            # Then we multiply by your Custom MAX_HEALTH.
            raw_hp = p['health']
            normalized = raw_hp / 100.0 
            scaled_hp = normalized * visuals.MAX_HEALTH
            
            # 1. TRACERS
            if visuals.ENABLE_TRACERS:
                try:
                    if visuals.TRACER_ORIGIN == "Mouse":
                        mx, my = win32api.GetCursorPos()
                        start_x = mx
                        start_y = self.screen_h - my 
                    elif visuals.TRACER_ORIGIN == "Center":
                        start_x = gw['x'] + (gw['w'] / 2)
                        start_y = self.screen_h - (gw['y'] + (gw['h'] / 2))
                    else: # Bottom
                        start_x = gw['x'] + (gw['w'] / 2)
                        start_y = self.screen_h - (gw['y'] + gw['h']) 

                    line = pyglet.shapes.Line(
                        start_x, start_y, 
                        final_x, head_y, 
                        color=visuals.TRACER_COLOR
                    )
                    line.draw()
                except: pass

            # 2. DOT
            if visuals.ENABLE_DOT:
                try:
                    circle = pyglet.shapes.Circle(
                        final_x, head_y, 
                        radius=visuals.DOT_RADIUS, 
                        color=visuals.DOT_COLOR
                    )
                    circle.draw()
                except: pass

            # 3. TEXT INFO
            text_lines = []
            
            if visuals.ENABLE_NAME: 
                text_lines.append((p['name'], visuals.NAME_COLOR))
            
            if visuals.ENABLE_DISTANCE: 
                dist_str = f"[{int(p['distance'])}m]"
                text_lines.append((dist_str, (200, 200, 200, 255))) 
            
            if visuals.ENABLE_HEALTH: 
                # Use the Scaled HP for display and color
                hp_color = self.get_health_color(scaled_hp)
                text_lines.append((f"HP: {int(scaled_hp)}", hp_color))

            if text_lines:
                current_y_offset = 15 + visuals.DOT_RADIUS 
                
                for text, color in text_lines:
                    try:
                        lab = pyglet.text.Label(
                            text, 
                            font_name="Segoe UI",
                            font_size=real_font_size,
                            x=final_x, 
                            y=head_y + current_y_offset, 
                            anchor_x='center', 
                            color=color
                        )
                        lab.bold = True
                        lab.draw()
                        current_y_offset += (real_font_size + 4)
                    except: pass

    def run(self):
        gl.glClearColor(0, 0, 0, 0)
        pyglet.app.run()