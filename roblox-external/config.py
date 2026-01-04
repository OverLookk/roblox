import requests
import json

OFFSETS_URL = "https://robloxoffsets.com/offsets.json"
TIMEOUT = 5

try:
    OFFSETS = requests.get(OFFSETS_URL, timeout=TIMEOUT).json()
except:
    OFFSETS = {}

class VisualConfig:
    # Toggles
    ENABLE_ESP = True
    ENABLE_TRACERS = True
    ENABLE_DOT = True
    ENABLE_NAME = True
    ENABLE_DISTANCE = True
    ENABLE_HEALTH = True

    # Settings
    MAX_DISTANCE = 800  # Default render distance
    MAX_HEALTH = 150    # Default max HP
    
    DOT_RADIUS = 4.0
    FONT_SIZE_INDEX = 5
    TRACER_ORIGIN = "Bottom"
    
    # Colors
    TRACER_COLOR = (255, 255, 255)
    DOT_COLOR = (255, 0, 255)
    NAME_COLOR = (255, 255, 255, 255)

visuals = VisualConfig()