import pymem
import ctypes
from ctypes import wintypes
import struct
import math
import time
import win32gui
from config import OFFSETS

# --- DIRECT KERNEL DEFINITIONS ---
kernel32 = ctypes.windll.kernel32
ReadProcessMemory = kernel32.ReadProcessMemory
ReadProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, wintypes.LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
ReadProcessMemory.restype = wintypes.BOOL

class RobloxMemory:
    def __init__(self):
        self.pm = None
        self.process_handle = None
        self.base_addr = 0
        self.offsets = OFFSETS
        self.position_cache = {} 
        self.player_info_cache = {}
        
        # Buffers
        self.matrix_buffer = (ctypes.c_float * 16)()
        self.vec3_buffer = (ctypes.c_float * 3)()
        self.bytes_read = ctypes.c_size_t()
        
        self.attach()

    def attach(self):
        try:
            self.pm = pymem.Pymem("RobloxPlayerBeta.exe")
            self.process_handle = self.pm.process_handle
            self.base_addr = self.pm.process_base.lpBaseOfDll
            self.init_pointers()
            return True
        except:
            return False

    def get_offset(self, key):
        # Default fallbacks if offset file is missing keys
        if key == "Team" and key not in self.offsets: return 0x1F0 
        if key == "ModelInstance" and key not in self.offsets: return 0x298
        if key == "Primitive" and key not in self.offsets: return 0x160 
        if key == "Position" and key not in self.offsets: return 0x140
        if key == "ChildrenEnd" and key not in self.offsets: return 8
        if key == "Health" and key not in self.offsets: return 0x100
        val = self.offsets.get(key, "0x0")
        return int(val, 16) if isinstance(val, str) else val

    def read_string(self, address):
        try:
            length = self.pm.read_int(address + 0x18) 
            if length >= 16: address = self.pm.read_longlong(address)
            if address == 0: return ""
            raw = self.pm.read_bytes(address, 64)
            return raw.decode('utf-8', errors='ignore').split('\x00')[0].strip()
        except: return ""

    def get_children(self, instance_addr):
        if not instance_addr: return []
        try:
            children_ptr = self.pm.read_longlong(instance_addr + self.get_offset("Children"))
            if children_ptr == 0: return []
            start = self.pm.read_longlong(children_ptr)
            end = self.pm.read_longlong(children_ptr + self.get_offset("ChildrenEnd"))
            size = end - start
            if size > 500 * 0x10: return [] 
            out = []
            cur = start
            limit = 0
            while cur < end and limit < 150:
                child = self.pm.read_longlong(cur)
                if child != 0: out.append(child)
                cur += 0x10
                limit += 1
            return out
        except: return []

    def get_name(self, instance_addr):
        try: return self.read_string(self.pm.read_longlong(instance_addr + self.get_offset("Name")))
        except: return ""

    def init_pointers(self):
        try:
            fake_dm = self.pm.read_longlong(self.base_addr + self.get_offset("FakeDataModelPointer"))
            dm_ptr = self.pm.read_longlong(fake_dm + self.get_offset("FakeDataModelToDataModel"))
            self.DataModel = dm_ptr
            self.VisualEngine = self.pm.read_longlong(self.base_addr + self.get_offset("VisualEnginePointer"))
            children = self.get_children(self.DataModel)
            for child in children:
                if self.get_name(child) == "Players": self.Players = child
        except: pass

    def update_player_cache(self):
        if not getattr(self, "Players", None): 
            self.init_pointers()
            return
        try:
            self.LocalPlayer = self.pm.read_longlong(self.Players + self.get_offset("LocalPlayer"))
            players = self.get_children(self.Players)
            new_pos_cache = {}
            new_info_cache = {}

            for p_ptr in players:
                # Basic Info
                p_name = self.get_name(p_ptr)
                
                # Team Check Pointer
                team_ptr = self.pm.read_longlong(p_ptr + self.get_offset("Team"))
                
                char_ptr = self.pm.read_longlong(p_ptr + self.get_offset("ModelInstance"))
                if char_ptr == 0: continue
                
                children = self.get_children(char_ptr)
                head_part = None
                humanoid = None

                for c in children:
                    n = self.get_name(c)
                    if n == "Head": head_part = c
                    elif n == "Humanoid": humanoid = c
                
                if head_part:
                    prim = self.pm.read_longlong(head_part + self.get_offset("Primitive"))
                    if prim:
                        new_pos_cache[p_ptr] = prim + self.get_offset("Position")
                        new_info_cache[p_ptr] = {
                            'name': p_name, 
                            'hp_ptr': 0,
                            'team_ptr': team_ptr # Store Team Address
                        }
                        if humanoid:
                            new_info_cache[p_ptr]['hp_ptr'] = humanoid + self.get_offset("Health")

            self.position_cache = new_pos_cache
            self.player_info_cache = new_info_cache
        except: pass

    def read_fast(self):
        data = []
        try:
            mat_addr = self.VisualEngine + self.get_offset("viewmatrix")
            if not ReadProcessMemory(self.process_handle, mat_addr, self.matrix_buffer, 64, ctypes.byref(self.bytes_read)):
                return None, []
        except: return None, []

        matrix = self.matrix_buffer[:]

        my_pos = None
        my_team = 0
        
        # Get LocalPlayer Info
        if getattr(self, "LocalPlayer", None):
            # Read My Team
            try: my_team = self.pm.read_longlong(self.LocalPlayer + self.get_offset("Team"))
            except: pass
            
            if self.LocalPlayer in self.position_cache:
                if ReadProcessMemory(self.process_handle, self.position_cache[self.LocalPlayer], self.vec3_buffer, 12, ctypes.byref(self.bytes_read)):
                    my_pos = (self.vec3_buffer[0], self.vec3_buffer[1], self.vec3_buffer[2])

        for p_ptr, pos_addr in self.position_cache.items():
            if p_ptr == self.LocalPlayer: continue

            if ReadProcessMemory(self.process_handle, pos_addr, self.vec3_buffer, 12, ctypes.byref(self.bytes_read)):
                x, y, z = self.vec3_buffer[0], self.vec3_buffer[1], self.vec3_buffer[2]
                
                info = self.player_info_cache.get(p_ptr, {'name': '?', 'hp_ptr': 0, 'team_ptr': 0})
                
                hp = 100.0
                if info['hp_ptr']:
                    if ReadProcessMemory(self.process_handle, info['hp_ptr'], self.vec3_buffer, 4, ctypes.byref(self.bytes_read)):
                        hp = self.vec3_buffer[0]

                # --- NEW: IGNORE DEAD PLAYERS ---
                if hp <= 0:
                    continue 

                dist = 0
                if my_pos:
                    dist = math.sqrt((x-my_pos[0])**2 + (y-my_pos[1])**2 + (z-my_pos[2])**2)

                data.append({
                    'name': info['name'],
                    'x': x, 'y': y, 'z': z,
                    'distance': dist,
                    'health': hp,
                    'team_match': (my_team != 0 and my_team == info['team_ptr']) 
                })
                
        return matrix, data

    def get_window_info(self):
        try:
            hwnd = win32gui.FindWindow(None, "Roblox")
            if hwnd:
                rect = win32gui.GetClientRect(hwnd)
                pt = win32gui.ClientToScreen(hwnd, (0, 0))
                return pt[0], pt[1], rect[2], rect[3]
        except: pass
        return 0, 0, 1920, 1080