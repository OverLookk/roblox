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
            # ESP
            "ENABLE_ESP": True,
            "ENABLE_TRACERS": True,
            "ENABLE_DOT": True,
            "ENABLE_NAME": True,
            "ENABLE_DISTANCE": True,
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
            "TRIGGER_MODE": "Hold", 
            "TRIGGER_DELAY": 0,
            "TRIGGER_FOV": 30,
            "TRIGGER_KEY": 6,
            
            # RAPID FIRE SETTINGS (NEW)
            "RAPID_FIRE": False,
            "RAPID_DELAY": 50, # ms
            
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
                        # FORCE INTEGERS for Keys
                        if k == "TRIGGER_KEY":
                            val = data.get(k, v)
                            setattr(self, k, int(val) if str(val).isdigit() else 6)
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