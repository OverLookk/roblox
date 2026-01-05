import time
import math
import win32api
import win32con
from config import visuals

class Triggerbot:
    def __init__(self, memory_ref):
        self.memory = memory_ref
        self.width = 1920
        self.height = 1080
        self.center_x = 960
        self.center_y = 540
        self.active_toggle = False
        self.last_key_state = False

    def world_to_screen(self, view_matrix, pos):
        try:
            x, y, z = pos['x'], pos['y'], pos['z']
            w = x * view_matrix[12] + y * view_matrix[13] + z * view_matrix[14] + view_matrix[15]
            if w < 0.1: return None
            inv_w = 1.0 / w
            ndc_x = (x * view_matrix[0] + y * view_matrix[1] + z * view_matrix[2] + view_matrix[3]) * inv_w
            ndc_y = (x * view_matrix[4] + y * view_matrix[5] + z * view_matrix[6] + view_matrix[7]) * inv_w
            screen_x = (self.width / 2) * (1 + ndc_x)
            screen_y = (self.height / 2) * (1 - ndc_y)
            return int(screen_x), int(screen_y)
        except: return None

    def check_trigger(self):
        _, _, w, h = self.memory.get_window_info()
        self.width, self.height = w, h
        self.center_x, self.center_y = w // 2, h // 2

        matrix, players = self.memory.read_fast()
        if not matrix: return False

        # Check if ANY player is inside the "Trigger FOV" (Usually very small, e.g., 5-10 pixels)
        fov_sq = visuals.TRIGGER_FOV ** 2
        
        for p in players:
            if visuals.ENABLE_TEAM_CHECK and p['team_match']: continue
            if p['health'] <= 0: continue

            screen_pos = self.world_to_screen(matrix, p)
            if not screen_pos: continue
            
            sx, sy = screen_pos
            dx = sx - self.center_x
            dy = sy - self.center_y
            
            # Distance squared check is faster than sqrt
            if (dx*dx + dy*dy) < fov_sq:
                return True
        return False

    def shoot(self):
        # Click Mouse
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.01)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def run_loop(self):
        print("Triggerbot running...")
        while True:
            if visuals.ENABLE_TRIGGERBOT:
                try:
                    # Logic for Hold vs Toggle
                    key_down = (win32api.GetAsyncKeyState(visuals.TRIGGER_KEY) & 0x8000) != 0
                    
                    is_active = False
                    if visuals.TRIGGER_MODE == "Hold":
                        is_active = key_down
                    elif visuals.TRIGGER_MODE == "Toggle":
                        if key_down and not self.last_key_state:
                            self.active_toggle = not self.active_toggle
                            print(f"Triggerbot Toggle: {self.active_toggle}")
                        self.last_key_state = key_down
                        is_active = self.active_toggle

                    if is_active:
                        if self.check_trigger():
                            self.shoot()
                            time.sleep(visuals.TRIGGER_DELAY)
                        else:
                            time.sleep(0.01)
                    else:
                        time.sleep(0.05)
                        
                except Exception as e:
                    print(f"Trigger Error: {e}")
                    time.sleep(1)
            else:
                time.sleep(0.5)