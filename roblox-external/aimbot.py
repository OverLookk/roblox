import time
import math
import win32api
import win32con
from config import visuals

class Aimbot:
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
            
            # Matrix math (Row-Major)
            w = x * view_matrix[12] + y * view_matrix[13] + z * view_matrix[14] + view_matrix[15]
            
            if w < 0.1: return None
            
            inv_w = 1.0 / w
            ndc_x = (x * view_matrix[0] + y * view_matrix[1] + z * view_matrix[2] + view_matrix[3]) * inv_w
            ndc_y = (x * view_matrix[4] + y * view_matrix[5] + z * view_matrix[6] + view_matrix[7]) * inv_w
            
            screen_x = (self.width / 2) * (1 + ndc_x)
            screen_y = (self.height / 2) * (1 - ndc_y)
            return int(screen_x), int(screen_y)
        except: return None

    def get_best_target(self, matrix, players):
        best_dist = visuals.AIMBOT_FOV
        target_offset = None
        
        for p in players:
            # 1. Alive Check
            if p['health'] <= 0: continue
            
            # 2. Team Check
            if visuals.ENABLE_TEAM_CHECK and p['team_match']: continue
            
            # 3. Distance Check (NEW)
            # If limit is ON and player is too far, skip them
            if visuals.ENABLE_DISTANCE_LIMIT and p['distance'] > visuals.MAX_DISTANCE:
                continue

            # 4. Screen Check
            screen = self.world_to_screen(matrix, p)
            if not screen: continue
            
            sx, sy = screen
            
            # 5. FOV Check (Distance to Crosshair)
            dx = sx - self.center_x
            dy = sy - self.center_y
            crosshair_dist = math.sqrt(dx**2 + dy**2)
            
            # Find closest to crosshair
            if crosshair_dist < best_dist:
                best_dist = crosshair_dist
                target_offset = (dx, dy)
                
        return target_offset

    def move_mouse(self, offset):
        dx, dy = offset
        
        # Apply Y-Offset (e.g. for aiming at neck instead of torso)
        dy += getattr(visuals, 'AIMBOT_OFFSET_Y', 0)
        
        # Get Smoothness and Sensitivity
        sens = getattr(visuals, 'AIMBOT_SENS', 0.5) 
        smooth = max(1.0, visuals.AIMBOT_SMOOTH)
        
        # Calculate move amount
        move_x = (dx * sens) / smooth
        move_y = (dy * sens) / smooth

        # Prevent 'stuck' mouse if move is less than 1 pixel but not 0
        if 0 < abs(move_x) < 1: move_x = 1 if move_x > 0 else -1
        if 0 < abs(move_y) < 1: move_y = 1 if move_y > 0 else -1
        
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(move_x), int(move_y), 0, 0)

    def run_loop(self):
        print("Aimbot running...")
        while True:
            if visuals.ENABLE_AIMBOT:
                try:
                    # Update Window Info (in case of resize)
                    _, _, w, h = self.memory.get_window_info()
                    self.width, self.height = w, h
                    self.center_x, self.center_y = w // 2, h // 2

                    # Check Key Bind
                    key_down = (win32api.GetAsyncKeyState(visuals.AIMBOT_KEY) & 0x8000) != 0
                    
                    should_aim = False
                    if visuals.AIMBOT_MODE == "Hold":
                        should_aim = key_down
                        self.active_toggle = False
                        
                    elif visuals.AIMBOT_MODE == "Toggle":
                        if key_down and not self.last_key_state:
                            self.active_toggle = not self.active_toggle
                        self.last_key_state = key_down
                        should_aim = self.active_toggle

                    # Aimbot Logic
                    if should_aim:
                        matrix, players = self.memory.read_fast()
                        if matrix:
                            target = self.get_best_target(matrix, players)
                            if target:
                                self.move_mouse(target)
                                time.sleep(0.005) # Super fast rate
                            else:
                                time.sleep(0.01)
                        else:
                            time.sleep(0.01)
                    else:
                        time.sleep(0.05)
                        
                except Exception as e:
                    print(f"Aimbot Error: {e}")
                    time.sleep(1)
            else:
                time.sleep(0.5)