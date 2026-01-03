import ctypes  # <--- NEW
ctypes.windll.user32.SetProcessDPIAware() # <--- NEW: Forces 1:1 pixel mapping

import traceback
from memory import RobloxMemory
from overlay import ESPOverlay

def main():
    print("Initializing...")
    try:
        memory = RobloxMemory()
        print(f"Attached to Process ID: {memory.process_id}")
        
        overlay = ESPOverlay(memory)
        print("Overlay started. Press ESC to exit.")
        overlay.run()
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()