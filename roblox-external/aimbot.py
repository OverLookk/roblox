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
            w = x * view_matrix[12] + y * view_matrix[13] + z * view_matrix[14] + view_matrix[15]
            if w < 0.1: return None
            inv_w = 1.0 / w
            ndc_x = (x * view_matrix[0] + y * view_matrix[1] + z * view_matrix[2] + view_matrix[3]) * inv_w
            ndc_y = (x * view_matrix[4] + y * view_matrix[5] + z * view_matrix[6] + view_matrix[7]) * inv_w
            screen_x = (self.width / 2) * (1 + ndc_x)
            screen_y = (self.height / 2) * (1 - ndc_y)
            return int(screen_x), int(screen_y)
        except: return None

    def calculate_3d_distance(self, pos):
        # Simple Euclidean distance from origin (0,0,0) 
        # Assuming 'pos' is relative to local player. 
        # If 'pos' is absolute, you need local player pos. 
        # For most ESPs, read_fast returns relative coordinates or distance is pre-calculated.
        return math.sqrt(pos['x']**2 + pos['y']**2 + pos['z']**2)

    def get_best_target(self, matrix, players):
        best_target_offset = None
        best_metric = float('inf') 

        for p in players:
            if visuals.ENABLE_TEAM_CHECK and p['team_match']: continue
            if p['health'] <= 0: continue

            screen_pos = self.world_to_screen(matrix, p)
            if not screen_pos: continue
            
            sx, sy = screen_pos
            dx = sx - self.center_x
            dy = sy - self.center_y
            crosshair_dist = math.sqrt(dx**2 + dy**2)

            # --- PRIORITY LOGIC ---
            
            # 1. Check if valid based on FOV
            # Note: "Proximity" users might expect the bot to snap to the guy next to them
            # even if he is slightly outside the FOV ring. 
            # However, for safety, we usually still enforce FOV.
            if crosshair_dist > visuals.AIMBOT_FOV:
                continue

            # 2. Calculate Metric
            metric = 0
            if visuals.AIMBOT_PRIORITY == "Lowest HP":
                metric = p['health'] 
            
            elif visuals.AIMBOT_PRIORITY == "Proximity":
                # Ensure we use 3D distance
                # If 'distance' key exists in player dict, use it, else calc it
                dist_3d = p.get('distance', self.calculate_3d_distance(p))
                metric = dist_3d
                
            else: # "Crosshair"
                metric = crosshair_dist

            # 3. Compare
            if metric < best_metric:
                best_metric = metric
                best_target_offset = (dx, dy)

        return best_target_offset

    def update(self):
        _, _, w, h = self.memory.get_window_info()
        self.width, self.height = w, h
        self.center_x, self.center_y = w // 2, h // 2

        matrix, players = self.memory.read_fast()
        if not matrix: return

        target = self.get_best_target(matrix, players)
        
        if target:
            dx, dy = target
            dy += getattr(visuals, 'AIMBOT_OFFSET_Y', 0)
            sens = getattr(visuals, 'AIMBOT_SENS', 0.5) 
            smooth = max(1.0, visuals.AIMBOT_SMOOTH)
            
            move_x = (dx * sens) / smooth
            move_y = (dy * sens) / smooth

            if 0 < abs(move_x) < 1: move_x = 1 if move_x > 0 else -1
            if 0 < abs(move_y) < 1: move_y = 1 if move_y > 0 else -1
            
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(move_x), int(move_y), 0, 0)

    def run_loop(self):
        while True:
            if visuals.ENABLE_AIMBOT:
                try:
                    key_down = (win32api.GetAsyncKeyState(visuals.AIMBOT_KEY) & 0x8000) != 0
                    
                    should_aim = False
                    if visuals.AIMBOT_MODE == "Hold":
                        should_aim = key_down
                    elif visuals.AIMBOT_MODE == "Toggle":
                        if key_down and not self.last_key_state:
                            self.active_toggle = not self.active_toggle
                        self.last_key_state = key_down
                        should_aim = self.active_toggle

                    if should_aim:
                        self.update()
                        time.sleep(0.005)
                    else:
                        time.sleep(0.01)
                except: time.sleep(1)
            else:
                time.sleep(0.5)