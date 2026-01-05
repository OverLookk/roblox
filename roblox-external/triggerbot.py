import threading
import time
import ctypes
import win32api
import win32con
from config import visuals

# --- MOUSE HELPER FUNCTIONS ---
def mouse_click():
    """Simulates a quick left mouse click."""
    ctypes.windll.user32.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.01) # Short click
    ctypes.windll.user32.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def mouse_down():
    """Holds the left mouse button down."""
    ctypes.windll.user32.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)

def mouse_up():
    """Releases the left mouse button."""
    ctypes.windll.user32.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def is_key_held(vk_code):
    """Safely checks if a key is held down."""
    try:
        code = int(vk_code)
        return (win32api.GetAsyncKeyState(code) & 0x8000) != 0
    except:
        return False

class Triggerbot:
    def __init__(self, memory):
        self.memory = memory
        self.running = True
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def check_target(self, win_x, win_y, win_w, win_h, matrix, players):
        center_x = win_x + (win_w / 2)
        center_y = win_y + (win_h / 2)
        
        m0, m1, m2, m3 = matrix[0], matrix[1], matrix[2], matrix[3]
        m4, m5, m6, m7 = matrix[4], matrix[5], matrix[6], matrix[7]
        m12, m13, m14, m15 = matrix[12], matrix[13], matrix[14], matrix[15]

        for p in players:
            if visuals.ENABLE_TEAM_CHECK and p['team_match']: continue
            
            x, y, z = p['x'], p['y'], p['z']
            
            # World to Screen
            w = x*m12 + y*m13 + z*m14 + m15
            if w < 0.1: continue
            
            inv_w = 1.0 / w
            ndc_x = (x*m0 + y*m1 + z*m2 + m3) * inv_w
            ndc_y = (x*m4 + y*m5 + z*m6 + m7) * inv_w
            
            screen_x = ((win_w / 2) * (1 + ndc_x)) + win_x
            screen_y = ((win_h / 2) * (1 - ndc_y)) + win_y

            dist_from_crosshair = ((screen_x - center_x)**2 + (screen_y - center_y)**2)**0.5
            
            # Dynamic FOV
            dynamic_radius = (1500 / w) 
            if dynamic_radius > visuals.TRIGGER_FOV:
                dynamic_radius = visuals.TRIGGER_FOV 
            if dynamic_radius < 3: 
                dynamic_radius = 3 
            
            if dist_from_crosshair < dynamic_radius:
                return True
                
        return False

    def loop(self):
        last_debug_print = 0
        
        while self.running:
            if not visuals.ENABLE_TRIGGERBOT:
                time.sleep(0.5)
                continue

            if not is_key_held(visuals.TRIGGER_KEY):
                time.sleep(0.01)
                continue
            
            if time.time() - last_debug_print > 1.0:
                print(f"[DEBUG] Trigger Key Held. Scanning...")
                last_debug_print = time.time()

            matrix, players = self.memory.read_fast()
            if not matrix:
                time.sleep(0.02)
                continue
                
            win_x, win_y, win_w, win_h = self.memory.get_window_info()
            
            if self.check_target(win_x, win_y, win_w, win_h, matrix, players):
                print("[DEBUG] Target LOCKED -> SHOOTING")
                
                # Start Delay
                if visuals.TRIGGER_DELAY > 0:
                    time.sleep(visuals.TRIGGER_DELAY / 1000.0)

                # --- SHOOTING LOGIC ---
                if visuals.TRIGGER_MODE == "Hold":
                    
                    if visuals.RAPID_FIRE:
                        # RAPID FIRE LOOP
                        while visuals.ENABLE_TRIGGERBOT and is_key_held(visuals.TRIGGER_KEY):
                            # Re-check target every shot (optional, removes this if you want blind fire)
                            m, p = self.memory.read_fast()
                            if not m or not self.check_target(win_x, win_y, win_w, win_h, m, p):
                                break
                                
                            mouse_click()
                            
                            # Apply Rapid Delay (convert ms to seconds)
                            delay_sec = max(0.01, visuals.RAPID_DELAY / 1000.0)
                            time.sleep(delay_sec)
                            
                    else:
                        # STANDARD HOLD (SPRAY)
                        mouse_down()
                        while visuals.ENABLE_TRIGGERBOT and is_key_held(visuals.TRIGGER_KEY):
                            m, p = self.memory.read_fast()
                            if not m or not self.check_target(win_x, win_y, win_w, win_h, m, p):
                                break
                            time.sleep(0.03)
                        mouse_up()
                        
                else:
                    # CLICK MODE (Single Shot)
                    mouse_click()
                    time.sleep(0.15)
            
            time.sleep(0.01)