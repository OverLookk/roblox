import pyglet
from pyglet import shapes, text
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
        
        # Anti-aliasing config for smoother dots/lines
        config = pyglet.gl.Config(double_buffer=True, sample_buffers=1, samples=4)
        
        self.window = pyglet.window.Window(
            width=self.screen_w, height=self.screen_h,
            style=pyglet.window.Window.WINDOW_STYLE_BORDERLESS,
            caption="ESP Overlay", vsync=True, config=config
        )
        
        # Set window as transparent and click-through
        hwnd = self.window._hwnd
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, 
                               ex_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_TOPMOST)
        win32gui.SetLayeredWindowAttributes(hwnd, 0, 0, win32con.LWA_COLORKEY)
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, self.screen_w, self.screen_h, win32con.SWP_SHOWWINDOW)
        
        self.player_cache = []
        self.cache_lock = threading.Lock()
        self.batch = pyglet.graphics.Batch()
        self.active_elements = [] 
        
        @self.window.event
        def on_draw():
            self.window.clear()
            self.render()
            
        # Refresh player data every 50ms
        pyglet.clock.schedule_interval(self.update_players, 0.05)
        pyglet.clock.schedule(self.update)

    def update_players(self, dt):
        try:
            data = self.memory.get_player_data()
            with self.cache_lock:
                self.player_cache = data
        except:
            pass

    def draw_line(self, x1, y1, x2, y2, width, color):
        line = shapes.Line(x1, y1, x2, y2, color=color, batch=self.batch)
        line.width = width
        self.active_elements.append(line)

    def draw_head_dot(self, x, y, radius, color):
        # Convert Y coordinate for Pyglet (bottom-up)
        screen_y = self.screen_h - y
        circle = shapes.Circle(x, screen_y, radius, color=color, batch=self.batch)
        self.active_elements.append(circle)

    def draw_tracer(self, target_x, target_y, color):
        screen_y = self.screen_h - target_y
        start_x = self.screen_w / 2
        start_y = 0 # Default: Bottom
        
        if visuals.TRACER_ORIGIN == "Center":
            start_y = self.screen_h / 2
        elif visuals.TRACER_ORIGIN == "Mouse":
            mx, my = win32api.GetCursorPos()
            start_x, start_y = mx, self.screen_h - my 

        self.draw_line(start_x, start_y, target_x, screen_y, 1.5, color)

    def draw_text(self, x, y, content, color, size_index):
        screen_y = self.screen_h - y
        actual_size = 7 + size_index 
        if len(color) == 3: color = (*color, 255)
            
        label = text.Label(content, font_name='Arial', font_size=actual_size, 
                           x=x, y=screen_y, anchor_x='center', color=color, batch=self.batch)
        label.bold = True
        self.active_elements.append(label)

    def get_health_color(self, hp):
        # Pulls current max health setting from GUI (100, 150, or 200)
        max_hp = float(visuals.MAX_HEALTH)
        if max_hp <= 0: max_hp = 150.0 # Default fallback
        
        pct = (hp / max_hp) * 100
        
        if pct >= 80: return (0, 255, 0, 255)    # Healthy (Green)
        if pct >= 40: return (255, 255, 0, 255)  # Damaged (Yellow)
        return (255, 0, 0, 255)                  # Critical (Red)

    def render(self):
        self.active_elements = [] 
        self.batch = pyglet.graphics.Batch()

        if not visuals.ENABLE_ESP:
            self.batch.draw()
            return

        matrix = self.memory.get_view_matrix()
        win_x, win_y, win_w, win_h = self.memory.get_window_info()
        
        if not matrix: return

        with self.cache_lock:
            snapshot = list(self.player_cache)

        for p in snapshot:
            dist = p['distance']
            
            # --- DISTANCE LIMIT FILTER ---
            if dist > visuals.MAX_DISTANCE:
                continue

            # Convert 3D world pos to 2D screen pos
            pos = self.memory.world_to_screen(p['center_pos'], matrix, win_x, win_y, win_w, win_h)
            
            if pos.x > 0:
                hp = p['health']

                # 1. Tracers
                if visuals.ENABLE_TRACERS:
                    self.draw_tracer(pos.x, pos.y, visuals.TRACER_COLOR)

                # 2. Head Dot
                if visuals.ENABLE_DOT:
                    self.draw_head_dot(pos.x, pos.y, visuals.DOT_RADIUS, visuals.DOT_COLOR)
                
                # 3. Dynamic Text Stack
                text_stack = []
                
                # Name & Distance
                info_line = []
                if visuals.ENABLE_NAME: info_line.append(p['name'])
                if visuals.ENABLE_DISTANCE: info_line.append(f"[{int(dist)}m]")
                if info_line: 
                    text_stack.append((" ".join(info_line), visuals.NAME_COLOR))
                
                # Health (Color calibrated to visuals.MAX_HEALTH)
                if visuals.ENABLE_HEALTH:
                    hp_color = self.get_health_color(hp)
                    text_stack.append((f"HP: {int(hp)}", hp_color))
                
                # Render the stack above the head
                base_y = pos.y + 15 + visuals.DOT_RADIUS
                for content, color in text_stack:
                    self.draw_text(pos.x, base_y, content, color, visuals.FONT_SIZE_INDEX)
                    # Shift up for the next line in the stack
                    base_y += (12 + visuals.FONT_SIZE_INDEX)

        self.batch.draw()

    def update(self, dt):
        pass

    def run(self):
        pyglet.app.run()