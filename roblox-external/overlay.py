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
        
        config = pyglet.gl.Config(double_buffer=True, sample_buffers=1, samples=4)
        self.window = pyglet.window.Window(
            width=self.screen_w, height=self.screen_h,
            style=pyglet.window.Window.WINDOW_STYLE_BORDERLESS,
            caption="ESP Overlay", vsync=False, config=config
        )
        
        hwnd = self.window._hwnd
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, 
                               ex_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_TOPMOST)
        win32gui.SetLayeredWindowAttributes(hwnd, 0, 0, win32con.LWA_COLORKEY)
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, self.screen_w, self.screen_h, win32con.SWP_SHOWWINDOW)
        
        self.batch = pyglet.graphics.Batch()
        self.active_elements = [] 
        self.running = True

        self.cache_thread = threading.Thread(target=self.cache_loop, daemon=True)
        self.cache_thread.start()

    def cache_loop(self):
        while self.running:
            self.memory.update_player_cache()
            time.sleep(0.5)

    def draw_line(self, x1, y1, x2, y2, width, color):
        line = shapes.Line(x1, y1, x2, y2, color=color, batch=self.batch)
        line.width = width
        self.active_elements.append(line)

    def draw_head_dot(self, x, y, radius, color):
        screen_y = self.screen_h - y
        circle = shapes.Circle(x, screen_y, radius, color=color, batch=self.batch)
        self.active_elements.append(circle)

    def draw_fov_ring(self, x, y, radius, color):
        screen_y = self.screen_h - y
        if len(color) == 3: color = (*color, 255)
        try:
            arc = shapes.Arc(x, screen_y, radius, angle=360, color=color, batch=self.batch)
            self.active_elements.append(arc)
        except AttributeError:
            pass

    def draw_tracer(self, target_x, target_y, color):
        screen_y = self.screen_h - target_y
        start_x = self.screen_w / 2
        start_y = 0 
        if visuals.TRACER_ORIGIN == "Center": start_y = self.screen_h / 2
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
        max_hp = float(visuals.MAX_HEALTH) 
        pct = (hp / max_hp) * 100
        if pct >= 80: return (0, 255, 0, 255)
        if pct >= 40: return (255, 255, 0, 255)
        return (255, 0, 0, 255)

    def render(self):
        self.active_elements = [] 
        self.batch = pyglet.graphics.Batch()

        win_x, win_y, win_w, win_h = self.memory.get_window_info()
        half_w = win_w / 2
        half_h = win_h / 2

        if visuals.ENABLE_AIMBOT and visuals.SHOW_FOV_RING:
            center_x = win_x + half_w
            center_y = win_y + half_h
            self.draw_fov_ring(center_x, center_y, visuals.AIMBOT_FOV, visuals.FOV_COLOR)

        if not visuals.ENABLE_ESP:
            self.batch.draw()
            return

        matrix, players = self.memory.read_fast()
        if not matrix: return

        m0, m1, m2, m3 = matrix[0], matrix[1], matrix[2], matrix[3]
        m4, m5, m6, m7 = matrix[4], matrix[5], matrix[6], matrix[7]
        m12, m13, m14, m15 = matrix[12], matrix[13], matrix[14], matrix[15]

        for p in players:
            if visuals.ENABLE_TEAM_CHECK and p['team_match']:
                continue

            dist = p['distance']
            if visuals.ENABLE_DISTANCE_LIMIT and dist > visuals.MAX_DISTANCE: continue

            x, y, z = p['x'], p['y'], p['z']
            w = x*m12 + y*m13 + z*m14 + m15
            if w < 0.1: continue

            inv_w = 1.0 / w
            ndc_x = (x*m0 + y*m1 + z*m2 + m3) * inv_w
            ndc_y = (x*m4 + y*m5 + z*m6 + m7) * inv_w
            
            screen_x = (half_w * (1 + ndc_x)) + win_x
            screen_y = (half_h * (1 - ndc_y)) + win_y

            hp = p['health']
            if visuals.ENABLE_TRACERS: self.draw_tracer(screen_x, screen_y, visuals.TRACER_COLOR)
            if visuals.ENABLE_DOT: self.draw_head_dot(screen_x, screen_y, visuals.DOT_RADIUS, visuals.DOT_COLOR)
            
            text_stack = []
            info_line = []
            
            if visuals.ENABLE_NAME: info_line.append(p['name'])
            
            # --- UPDATED: Use the correct config variable from GUI ---
            if getattr(visuals, "ENABLE_DISTANCE_TEXT", False): 
                info_line.append(f"[{int(dist)}m]")
            
            if info_line: text_stack.append((" ".join(info_line), visuals.NAME_COLOR))
            
            if visuals.ENABLE_HEALTH:
                text_stack.append((f"HP: {hp:.1f}", self.get_health_color(hp)))
            
            step_y = 12 + visuals.FONT_SIZE_INDEX
            current_y = screen_y - 15 - visuals.DOT_RADIUS if visuals.TEXT_POSITION == "Top" else screen_y + 15 + visuals.DOT_RADIUS
            direction = -1 if visuals.TEXT_POSITION == "Top" else 1

            for content, color in text_stack:
                self.draw_text(screen_x, current_y, content, color, visuals.FONT_SIZE_INDEX)
                current_y += (step_y * direction)

        self.batch.draw()

    def run(self):
        while self.running:
            self.window.dispatch_events()
            self.window.clear()
            self.render()
            self.window.flip()