import pyglet
from pyglet import shapes, text
import threading
import win32gui
import win32con
import win32api
from config import visuals

class ESPOverlay:
    def __init__(self, memory):
        self.memory = memory
        self.screen_w = win32api.GetSystemMetrics(0)
        self.screen_h = win32api.GetSystemMetrics(1)
        
        config = pyglet.gl.Config(double_buffer=True, sample_buffers=1, samples=4)
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
        self.cache_lock = threading.Lock()
        self.batch = pyglet.graphics.Batch()
        self.active_elements = [] 
        
        @self.window.event
        def on_draw():
            self.window.clear()
            self.render()
            
        pyglet.clock.schedule_interval(self.update_players, 0.05)
        pyglet.clock.schedule(self.update)

    def update_players(self, dt):
        try:
            data = self.memory.get_player_data()
            with self.cache_lock:
                self.player_cache = data
        except: pass

    def draw_line(self, x1, y1, x2, y2, width, color):
        line = shapes.Line(x1, y1, x2, y2, color=color, batch=self.batch)
        line.width = width
        self.active_elements.append(line)

    def draw_head_dot(self, x, y, radius, color):
        # Pyglet draws from bottom-left, but our Y is from top-left
        screen_y = self.screen_h - y
        circle = shapes.Circle(x, screen_y, radius, color=color, batch=self.batch)
        self.active_elements.append(circle)

    def draw_tracer(self, target_x, target_y, color):
        screen_y = self.screen_h - target_y
        start_x = self.screen_w / 2
        start_y = 0 
        
        if visuals.TRACER_ORIGIN == "Center":
            start_y = self.screen_h / 2
        elif visuals.TRACER_ORIGIN == "Mouse":
            mx, my = win32api.GetCursorPos()
            start_x, start_y = mx, self.screen_h - my 

        self.draw_line(start_x, start_y, target_x, screen_y, 1.5, color)

    def draw_text(self, x, y, content, color, size_index):
        # Convert top-down Y to Pyglet's bottom-up Y
        screen_y = self.screen_h - y
        actual_size = 7 + size_index 
        if len(color) == 3: color = (*color, 255)
        label = text.Label(content, font_name='Arial', font_size=actual_size, 
                           x=x, y=screen_y, anchor_x='center', color=color, batch=self.batch)
        label.bold = True
        self.active_elements.append(label)

    def get_health_color(self, hp):
        max_hp = float(visuals.MAX_HEALTH) 
        pct = (hp / max_hp) * 100
        if pct >= 80: return (0, 255, 0, 255)
        if pct >= 40: return (255, 255, 0, 255)
        return (255, 0, 0, 255)

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
            
            if visuals.ENABLE_DISTANCE_LIMIT and dist > visuals.MAX_DISTANCE:
                continue

            pos = self.memory.world_to_screen(p['center_pos'], matrix, win_x, win_y, win_w, win_h)
            
            if pos.x > 0:
                hp = p['health']

                if visuals.ENABLE_TRACERS:
                    self.draw_tracer(pos.x, pos.y, visuals.TRACER_COLOR)

                if visuals.ENABLE_DOT:
                    self.draw_head_dot(pos.x, pos.y, visuals.DOT_RADIUS, visuals.DOT_COLOR)
                
                # --- TEXT STACKING LOGIC ---
                text_stack = []
                info_line = []
                if visuals.ENABLE_NAME: info_line.append(p['name'])
                if visuals.ENABLE_DISTANCE: info_line.append(f"[{int(dist)}m]")
                if info_line: 
                    text_stack.append((" ".join(info_line), visuals.NAME_COLOR))
                
                if visuals.ENABLE_HEALTH:
                    hp_color = self.get_health_color(hp)
                    text_stack.append((f"HP: {hp:.1f}", hp_color))
                
                step_y = 12 + visuals.FONT_SIZE_INDEX
                
                if visuals.TEXT_POSITION == "Top":
                    # Move UP the screen (subtract from Y)
                    current_y = pos.y - 15 - visuals.DOT_RADIUS
                    
                    # We reverse the stack for Top mode so Name appears closest to the dot
                    for content, color in text_stack:
                        self.draw_text(pos.x, current_y, content, color, visuals.FONT_SIZE_INDEX)
                        current_y -= step_y 
                else:
                    # Move DOWN the screen (add to Y)
                    current_y = pos.y + 15 + visuals.DOT_RADIUS
                    
                    for content, color in text_stack:
                        self.draw_text(pos.x, current_y, content, color, visuals.FONT_SIZE_INDEX)
                        current_y += step_y 

        self.batch.draw()

    def update(self, dt): pass
    def run(self): pyglet.app.run()