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
        
        # State variables
        self.active_toggle = False
        self.last_key_state = False
        self.holding_mouse = False 
        self.has_shot = False # New: Tracks if we already took the single shot

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

        # Use GUI FOV setting or default to 35
        detect_radius = getattr(visuals, "TRIGGER_FOV", 35)
        radius_sq = detect_radius ** 2
        
        for p in players:
            if visuals.ENABLE_TEAM_CHECK and p['team_match']: continue
            if p['health'] <= 0: continue

            screen_pos = self.world_to_screen(matrix, p)
            if not screen_pos: continue
            
            sx, sy = screen_pos
            dx = sx - self.center_x
            dy = sy - self.center_y
            
            if (dx*dx + dy*dy) < radius_sq:
                return True
        return False

    def press_mouse(self):
        if not self.holding_mouse:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            self.holding_mouse = True

    def release_mouse(self):
        if self.holding_mouse:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            self.holding_mouse = False

    def click_mouse(self):
        self.release_mouse()
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.01)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def run_loop(self):
        print("Triggerbot logic started.")
        while True:
            if visuals.ENABLE_TRIGGERBOT:
                try:
                    # --- 1. ACTIVATION LOGIC (Hold vs Toggle) ---
                    key_down = (win32api.GetAsyncKeyState(visuals.TRIGGER_KEY) & 0x8000) != 0
                    activation_mode = getattr(visuals, "TRIGGER_MODE", "Hold")
                    
                    is_active = False
                    
                    if activation_mode == "Hold":
                        is_active = key_down
                        self.active_toggle = False 
                        
                    elif activation_mode == "Toggle":
                        if key_down and not self.last_key_state:
                            self.active_toggle = not self.active_toggle
                            print(f"Triggerbot Active: {self.active_toggle}")
                        self.last_key_state = key_down
                        is_active = self.active_toggle

                    # --- 2. ACTION LOGIC (Click vs Hold vs Spam) ---
                    if is_active:
                        target_found = self.check_trigger()
                        trigger_type = getattr(visuals, "TRIGGER_TYPE", "Click")

                        if target_found:
                            # -- TYPE: HOLD --
                            if trigger_type == "Hold":
                                self.press_mouse()
                                self.has_shot = False # Reset flag (not used in hold, but good practice)
                                time.sleep(0.01)
                                
                            # -- TYPE: SPAM --
                            elif trigger_type == "Spam":
                                self.click_mouse()
                                self.has_shot = False
                                delay_ms = getattr(visuals, "TRIGGER_SPAM_DELAY", 100)
                                time.sleep(max(0.01, delay_ms / 1000.0))
                                
                            # -- TYPE: CLICK (Single Shot) --
                            else: 
                                if not self.has_shot:
                                    self.click_mouse()
                                    self.has_shot = True # Mark as shot so we don't shoot again
                                
                                # Wait small amount to prevent CPU spam, but don't shoot again
                                time.sleep(0.01) 
                        else:
                            # Target Lost: Reset everything
                            self.release_mouse()
                            self.has_shot = False # Allow shooting again next time we find a target
                            time.sleep(0.01)
                    else:
                        # Module Inactive: Reset everything
                        self.release_mouse()
                        self.has_shot = False
                        time.sleep(0.05)

                except Exception as e:
                    print(f"Trigger Loop Error: {e}")
                    self.release_mouse()
                    time.sleep(1)
            else:
                self.release_mouse()
                time.sleep(0.5)