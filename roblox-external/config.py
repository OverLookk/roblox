import json
import os
import requests

# Try to fetch latest offsets, fallback to hardcoded if offline
OFFSETS_URL = "https://robloxoffsets.com/offsets.json"
try:
    OFFSETS = requests.get(OFFSETS_URL, timeout=3).json()
except:
    OFFSETS = {}

CONFIG_FILE = "config.json"

class VisualConfig:
    def __init__(self):
        # Default Settings
        self.defaults = {
            "ENABLE_ESP": True,
            "ENABLE_TRACERS": True,
            "ENABLE_DOT": True,
            "ENABLE_NAME": True,
            "ENABLE_DISTANCE": True,
            "ENABLE_HEALTH": True,
            "ENABLE_DISTANCE_LIMIT": False,
            "MAX_DISTANCE": 1000,
            "DOT_RADIUS": 4.0,
            "FONT_SIZE_INDEX": 5,
            "TRACER_ORIGIN": "Bottom",
            "TEXT_POSITION": "Top",  # New Setting: "Top" or "Bottom"
            "TRACER_COLOR": [255, 255, 255],
            "DOT_COLOR": [255, 0, 255],
            "NAME_COLOR": [255, 255, 255, 255]
        }
        
        # Hardcoded variable
        self.MAX_HEALTH = 150
        
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    for k, v in self.defaults.items():
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