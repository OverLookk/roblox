import json
import os
import requests

# --- GLOBAL OFFSETS ---
OFFSETS_URL = "https://robloxoffsets.com/offsets.json"

try:
    response = requests.get(OFFSETS_URL, timeout=3)
    OFFSETS = response.json()
except:
    OFFSETS = {
        "viewmatrix": 0x111111,
        "LocalPlayer": 0x222222,
        "Team": 0x1F0,
        "ModelInstance": 0x298,
        "Primitive": 0x160,
        "Position": 0x140,
        "Children": 0x50,
        "ChildrenEnd": 0x8,
        "Name": 0x48,
        "Health": 0x100
    }

CONFIG_FILE = "config.json"

class VisualConfig:
    def __init__(self):
        self.defaults = {
            # UI THEME
            "UI_BG_COLOR": "#1e1e1e",
            "UI_PANEL_COLOR": "#2b2b2b",
            "UI_ACCENT_COLOR": "#00e5ff",

            # ESP
            "ENABLE_ESP": True,
            "ENABLE_TRACERS": True,
            "ENABLE_DOT": True,
            "ENABLE_NAME": True,
            "ENABLE_DISTANCE_TEXT": False,
            "ENABLE_HEALTH": True,
            "ENABLE_DISTANCE_LIMIT": False,
            "ENABLE_TEAM_CHECK": False,
            
            "MAX_DISTANCE": 1000,
            "DOT_RADIUS": 4.0,
            "FONT_SIZE_INDEX": 5,
            
            "TRACER_ORIGIN": "Bottom",
            "TEXT_POSITION": "Top",
            "TRACER_COLOR": [255, 255, 255],
            "DOT_COLOR": [255, 0, 255],
            "NAME_COLOR": [255, 255, 255, 255],
            
            # TRIGGERBOT
            "ENABLE_TRIGGERBOT": False,
            "TRIGGER_KEY": 6,
            "TRIGGER_MODE": "Hold",       # Activation: Hold or Toggle
            "TRIGGER_TYPE": "Click",      # Action: Click, Hold, or Spam
            "TRIGGER_DELAY": 0.05,        # Delay for 'Click'
            "TRIGGER_SPAM_DELAY": 100,    # Delay for 'Spam' (ms)
            "TRIGGER_FOV": 50,            # Larger detection range (50px)
            
            # AIMBOT
            "ENABLE_AIMBOT": True,
            "SHOW_FOV_RING": True,
            "FOV_COLOR": [255, 255, 255],
            "AIMBOT_KEY": 5,          
            "AIMBOT_MODE": "Hold",      
            "AIMBOT_PRIORITY": "Crosshair", 
            "AIMBOT_FOV": 100,        
            "AIMBOT_SMOOTH": 5.0,     
            "AIMBOT_SENS": 0.5,       
            "AIMBOT_OFFSET_Y": 0,     
            
            # MISC
            "MAX_HEALTH": 100.0
        }
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    for k, v in self.defaults.items():
                        if "KEY" in k:
                            val = data.get(k, v)
                            setattr(self, k, int(val) if str(val).isdigit() else v)
                        else:
                            setattr(self, k, data.get(k, v))
            except:
                self.restore_defaults()
        else:
            self.restore_defaults()

    def restore_defaults(self):
        for k, v in self.defaults.items():
            setattr(self, k, v)
        self.save()

    def save(self):
        data = {k: getattr(self, k) for k in self.defaults.keys()}
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)
        print("Configuration saved.")

visuals = VisualConfig()