import ctypes
import traceback
import threading
from memory import RobloxMemory
from overlay import ESPOverlay
from gui import run_gui # Import our new GUI function

# Force High DPI scaling (prevents blurriness on 4k screens)
ctypes.windll.user32.SetProcessDPIAware()

def main():
    print("Initializing Cheat...")
    try:
        # 1. Start the GUI in a separate thread so it doesn't block the overlay
        print("Starting GUI...")
        gui_thread = threading.Thread(target=run_gui, daemon=True)
        gui_thread.start()

        # 2. Initialize Memory
        memory = RobloxMemory()
        if not memory.pm:
            print("Could not attach to Roblox. Is it running?")
            return
            
        print(f"Attached to Process ID: {memory.process_id}")
        
        # 3. Start Overlay
        overlay = ESPOverlay(memory)
        print("Overlay started. Use the GUI to configure settings.")
        overlay.run()
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()