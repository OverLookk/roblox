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
        self.has_shot = False 
        
        # Delay Timer Variables
        self.waiting_for_delay = False
        self.acquisition_time = 0.0

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
        # Update screen info
        _, _, w, h = self.memory.get_window_info()
        self.width, self.height = w, h
        self.center_x, self.center_y = w // 2, h // 2

        matrix, players = self.memory.read_fast()
        if not matrix: return False

        # Base FOV (e.g. 50px at 60 studs)
        base_fov = getattr(visuals, "TRIGGER_FOV", 50)
        # Tolerance Multiplier (e.g. 1.0 = normal, 2.0 = double size)
        tolerance = getattr(visuals, "TRIGGER_TOLERANCE", 1.0)
        
        for p in players:
            if visuals.ENABLE_TEAM_CHECK and p['team_match']: continue
            if p['health'] <= 0: continue

            screen_pos = self.world_to_screen(matrix, p)
            if not screen_pos: continue
            
            # --- DYNAMIC SCALING LOGIC ---
            dist = p.get('distance', 0)
            
            # Reference distance: 60 studs
            # If closer, use full Base FOV.
            # If further, shrink inversely.
            if dist < 60:
                # Close range: Full size * Tolerance
                dynamic_radius = base_fov
            else:
                # Long range: Shrink size * Tolerance
                dynamic_radius = base_fov * (60.0 / dist)
            
            # Apply User Tolerance Setting
            final_radius = dynamic_radius * tolerance
            
            # Clamp minimum size to 5px so it's not impossible to hit at max range
            final_radius = max(5.0, final_radius)
            radius_sq = final_radius ** 2
            # -----------------------------

            sx, sy = screen_pos
            dx = sx - self.center_x
            dy = sy - self.center_y
            
            # Check intersection
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
                    # --- 1. ACTIVATION LOGIC ---
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

                    # --- 2. ACTION & DELAY LOGIC ---
                    if is_active:
                        target_found = self.check_trigger()
                        
                        if target_found:
                            # START TIMER
                            if not self.waiting_for_delay:
                                self.acquisition_time = time.time()
                                self.waiting_for_delay = True
                            
                            # CHECK TIMER
                            reaction_delay = getattr(visuals, "TRIGGER_DELAY", 0.0)
                            
                            if (time.time() - self.acquisition_time) >= reaction_delay:
                                trigger_type = getattr(visuals, "TRIGGER_TYPE", "Click")

                                # -- TYPE: HOLD --
                                if trigger_type == "Hold":
                                    self.press_mouse()
                                    self.has_shot = False 
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
                                        self.has_shot = True 
                                    time.sleep(0.01) 
                            else:
                                time.sleep(0.001)
                        else:
                            # TARGET LOST
                            self.waiting_for_delay = False
                            self.release_mouse()
                            self.has_shot = False 
                            time.sleep(0.01)
                    else:
                        # MODULE INACTIVE
                        self.waiting_for_delay = False
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