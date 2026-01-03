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
        
        # 1. Determine Monitor Size (for the transparent overlay)
        self.screen_w = win32api.GetSystemMetrics(0)
        self.screen_h = win32api.GetSystemMetrics(1)
        
        # 2. Pyglet Config (Depth=0 fixes static, Samples=4 smooths lines)
        config = pyglet.gl.Config(
            double_buffer=True, 
            depth_size=0, 
            sample_buffers=1, 
            samples=4
        )
        
        # 3. Create Window (Fullscreen, Borderless)
        self.window = pyglet.window.Window(
            width=self.screen_w, height=self.screen_h,
            style=pyglet.window.Window.WINDOW_STYLE_BORDERLESS,
            caption="ESP Overlay", vsync=True, config=config
        )
        
        # 4. Make Window Transparent & Click-Through
        hwnd = self.window._hwnd
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                               ex_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_TOPMOST)
        win32gui.SetLayeredWindowAttributes(hwnd, 0, 0, win32con.LWA_COLORKEY)
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, self.screen_w, self.screen_h, win32con.SWP_SHOWWINDOW)

        # 5. Data Storage
        self.player_cache = []
        self.view_matrix = None
        self.game_window = {'x': 0, 'y': 0, 'w': 1920, 'h': 1080}
        self.cache_lock = threading.Lock()
        self.running = True

        # 6. Start Memory Thread
        self.thread = threading.Thread(target=self.memory_loop, daemon=True)
        self.thread.start()
        
        # 7. Start Render Loop (144 FPS)
        pyglet.clock.schedule_interval(self.update_screen, 1/144.0)

    def update_screen(self, dt):
        self.window.clear()
        self.render()

    def memory_loop(self):
        while self.running:
            try:
                # Fetch fresh data from memory
                new_data = self.memory.get_player_data()
                new_matrix = self.memory.get_view_matrix()
                # Fetch fresh window position (in case user moves the game window)
                win_info = self.memory.get_window_info()
                
                with self.cache_lock:
                    self.player_cache = new_data
                    self.view_matrix = new_matrix
                    self.game_window = win_info
            except: pass
            time.sleep(0.005) # Tiny sleep to prevent high CPU usage

    def render(self):
        with self.cache_lock:
            players = list(self.player_cache)
            matrix = self.view_matrix
            gw = self.game_window 
        
        if not matrix: return 

        for p in players:
            # 1. World to Screen (Returns px relative to Game Window Top-Left)
            rx, ry = self.memory.world_to_screen(p["center_pos"], matrix, gw['w'], gw['h'])
            
            # Check if player is behind us
            if rx <= 0 or ry <= 0: continue

            # 2. Calculate Screen Coordinates
            # Add Game Window Offset
            final_x = gw['x'] + rx
            raw_y   = gw['y'] + ry

            # 3. Y-Axis Flip (Pyglet counts Y from bottom, Windows from top)
            # Since 'ry' is now tracking the HEAD, this gives us the exact Head Y.
            head_y = self.screen_h - raw_y

            # --- DRAWING ---
            
            # 1. Tracer (From Bottom-Center of Game Window to Head)
            if visuals.ENABLE_TRACERS:
                try:
                    start_x = gw['x'] + (gw['w'] / 2)
                    start_y = self.screen_h - (gw['y'] + gw['h']) # Bottom of game window
                    
                    line = pyglet.shapes.Line(
                        start_x, start_y, 
                        final_x, head_y, 
                        color=visuals.TRACER_COLOR
                    )
                    if hasattr(line, 'width'): line.width = visuals.TRACER_THICKNESS
                    line.draw()
                except: pass

            # 2. Dot (Exactly on the Head)
            if visuals.ENABLE_DOT:
                try:
                    circle = pyglet.shapes.Circle(
                        final_x, head_y, 
                        radius=visuals.DOT_RADIUS, 
                        color=visuals.DOT_COLOR
                    )
                    circle.draw()
                except: pass

            # 3. Text Info (Slightly above Head)
            text_lines = []
            if visuals.ENABLE_NAME: text_lines.append(p['name'])
            if visuals.ENABLE_DISTANCE: text_lines.append(f"[{int(p['distance'])}m]")
            if visuals.ENABLE_HEALTH: text_lines.append(f"HP: {p['health']}")

            if text_lines:
                try:
                    lab = pyglet.text.Label(
                        " ".join(text_lines), 
                        font_size=visuals.FONT_SIZE,
                        x=final_x, 
                        y=head_y + 15, # Offset +15 to float above dot
                        anchor_x='center', 
                        color=visuals.NAME_COLOR
                    )
                    lab.bold = True
                    lab.draw()
                except: pass

    def run(self):
        gl.glClearColor(0, 0, 0, 0)
        pyglet.app.run()