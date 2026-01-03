import requests

# --- CONSTANTS ---
OFFSETS_URL = "https://robloxoffsets.com/offsets.json"
PLAYER_CACHE_INTERVAL = 0.005  # <--- This was missing
TIMEOUT = 5

# --- FETCH OFFSETS ---
try:
    OFFSETS = requests.get(OFFSETS_URL, timeout=TIMEOUT).json()
except:
    print("Failed to fetch offsets from URL, ensure internet connection or valid URL.")
    OFFSETS = {}

# --- VISUAL CONFIGURATION ---
class VisualConfig:
    # Toggles
    ENABLE_ESP = True
    ENABLE_DOT = True
    ENABLE_TRACERS = True
    ENABLE_NAME = True
    ENABLE_DISTANCE = True
    ENABLE_HEALTH = True

    # Visual Settings
    DOT_COLOR = (255, 0, 255)         # Purple
    TRACER_COLOR = (255, 255, 255)    # White
    NAME_COLOR = (255, 255, 255, 255) # White Text
    DIST_COLOR = (200, 200, 200, 255) # Light Gray Text
    HEALTH_COLOR = (0, 255, 0, 255)   # Green Text
    
    DOT_RADIUS = 4
    TRACER_THICKNESS = 1.5
    FONT_SIZE = 10
    
    # Health Scaling
    # If the player has 100/100 HP, it will display as this number.
    MAX_HEALTH_DISPLAY_VALUE = 100 

    # Manual Offsets (Common defaults)
    HUMANOID_HEALTH_OFFSET = 0x100 
    HUMANOID_MAX_HEALTH_OFFSET = 0x110

visuals = VisualConfig()

# --- INTERPOLATION CONFIG ---
class GlobalConfig:
    def __init__(self):
        self.offset_map = {
            0: -200.0, 10: -70.0, 20: -30.0, 30: -15.0, 40: 0.0,
            50: 2.0, 60: 6.0, 70: 8.0, 80: 10.0, 90: 12.0,
            100: 11.8, 110: 12.0, 120: 15.0, 130: 16.0, 140: 16.0,
            150: 17.5, 160: 15.8, 170: 17.8, 180: 17.0, 190: 18.2,
            200: 20.0, 210: 18.0, 220: 18.7, 230: 18.7, 240: 17.9,
            250: 20.0, 260: 19.5, 270: 19.3, 280: 19.4, 290: 19.3,
            300: 19.5, 310: 20.5, 320: 20.1, 330: 20.5, 340: 20.3,
            350: 19.5
        }

    def get_interpolated_offset(self, distance):
        if distance <= 0: return self.offset_map[0]
        if distance >= 350: return self.offset_map[350]

        lower_dist = (int(distance) // 10) * 10
        upper_dist = lower_dist + 10

        val_low = self.offset_map.get(lower_dist, 0.0)
        val_high = self.offset_map.get(upper_dist, 0.0)

        ratio = (distance - lower_dist) / 10.0
        return val_low + (val_high - val_low) * ratio

game_config = GlobalConfig()