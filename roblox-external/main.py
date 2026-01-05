import ctypes
import traceback
import threading
import keyboard
from memory import RobloxMemory
from overlay import ESPOverlay
from gui import run_gui 
from triggerbot import Triggerbot 
from aimbot import Aimbot 

ctypes.windll.user32.SetProcessDPIAware()

def main():
    print("Initializing Cheat...")
    try:
        memory = RobloxMemory()
        
        print("Starting GUI...")
        gui_thread = threading.Thread(target=run_gui, args=(memory,), daemon=True)
        gui_thread.start()
        
        print("Starting Triggerbot...")
        trigger = Triggerbot(memory)
        # --- IMPORTANT: Start the thread ---
        threading.Thread(target=trigger.run_loop, daemon=True).start()
        
        print("Starting Aimbot...")
        aimbot = Aimbot(memory)
        threading.Thread(target=aimbot.run_loop, daemon=True).start()

        keyboard.add_hotkey('insert', memory.attach)
        print("Hotkeys: Press 'INSERT' to force re-attach.")

        if not memory.pm:
            print("Warning: Not attached to Roblox yet. Waiting for game...")
            
        print("Starting Overlay...")
        overlay = ESPOverlay(memory)
        overlay.run()
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()