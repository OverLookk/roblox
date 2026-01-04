import pymem
import struct
import math
import time
import win32gui
from config import OFFSETS

class RobloxMemory:
    def __init__(self):
        self.pm = None
        self.process_id = 0
        self.base_addr = 0
        self.DataModel = None
        self.VisualEngine = None
        self.Players = None
        self.LocalPlayer = None
        self.offsets = OFFSETS
        self.last_check = 0
        
        self.attach()

    def attach(self):
        try:
            self.pm = pymem.Pymem("RobloxPlayerBeta.exe")
            self.process_id = self.pm.process_id
            self.base_addr = self.pm.process_base.lpBaseOfDll
            print(f"Attached to Process ID: {self.process_id}")
            self.init_pointers()
            return True
        except Exception as e:
            print(f"Attachment failed: {e}")
            return False

    def check_connection(self):
        # Runs every 2 seconds
        if time.time() - self.last_check < 2.0: return
        self.last_check = time.time()
        
        try:
            # Try to read the pointer to DataModel. If this fails, game closed or teleported.
            fake_dm = self.pm.read_longlong(self.base_addr + self.get_offset("FakeDataModelPointer"))
            if fake_dm == 0: raise Exception("Pointer Null")
        except:
            print("Connection lost. Re-attaching...")
            self.attach()

    def get_offset(self, key):
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
            raw = self.pm.read_bytes(address, 100)
            return raw.decode('utf-8', errors='ignore').split('\x00')[0].strip()
        except: return ""

    def get_children(self, instance_addr):
        if not instance_addr: return []
        try:
            children_ptr = self.pm.read_longlong(instance_addr + self.get_offset("Children"))
            if children_ptr == 0: return []
            start = self.pm.read_longlong(children_ptr)
            end = self.pm.read_longlong(children_ptr + self.get_offset("ChildrenEnd"))
            if start == 0 or end == 0 or end <= start: return []
            
            out = []
            cur = start
            while cur < end and len(out) < 2000:
                child = self.pm.read_longlong(cur)
                if child != 0: out.append(child)
                cur += 0x10
            return out
        except: return []

    def get_name(self, instance_addr):
        try: return self.read_string(self.pm.read_longlong(instance_addr + self.get_offset("Name")))
        except: return ""

    def init_pointers(self):
        found = False
        print("Scanning for DataModel...")
        for i in range(20):
            try:
                fake_dm = self.pm.read_longlong(self.base_addr + self.get_offset("FakeDataModelPointer"))
                if not fake_dm: time.sleep(0.5); continue
                dm_ptr = self.pm.read_longlong(fake_dm + self.get_offset("FakeDataModelToDataModel"))
                if not dm_ptr: time.sleep(0.5); continue
                if self.get_name(dm_ptr) == "Ugc":
                    self.DataModel = dm_ptr; found = True; break
            except: time.sleep(0.5)
        
        if not found: return

        try:
            self.VisualEngine = self.pm.read_longlong(self.base_addr + self.get_offset("VisualEnginePointer"))
            children = self.get_children(self.DataModel)
            for child in children:
                if self.get_name(child) == "Players": self.Players = child
            
            if self.Players:
                self.LocalPlayer = self.pm.read_longlong(self.Players + self.get_offset("LocalPlayer"))
        except: pass

    def get_view_matrix(self):
        try:
            mat_addr = self.VisualEngine + self.get_offset("viewmatrix")
            return list(struct.unpack("16f", self.pm.read_bytes(mat_addr, 64)))
        except: return None

    def get_window_info(self):
        try:
            hwnd = win32gui.FindWindow(None, "Roblox")
            if hwnd:
                pt = win32gui.ClientToScreen(hwnd, (0, 0))
                rect = win32gui.GetClientRect(hwnd)
                return pt[0], pt[1], rect[2], rect[3]
        except: pass
        return 0, 0, 1920, 1080

    def get_character_info(self, player_ptr):
        try:
            char_ptr = self.pm.read_longlong(player_ptr + self.get_offset("ModelInstance"))
            if char_ptr == 0: char_ptr = self.pm.read_longlong(player_ptr + self.offsets.get("Character", 0x298))
            if char_ptr == 0: return None, 100
            
            children = self.get_children(char_ptr)
            head_part = None
            humanoid = None
            
            for c in children:
                n = self.get_name(c)
                if n == "Head": head_part = c
                elif n == "Humanoid": humanoid = c
            
            if not head_part: return None, 100

            prim = self.pm.read_longlong(head_part + self.get_offset("Primitive"))
            pos = list(struct.unpack("3f", self.pm.read_bytes(prim + self.get_offset("Position"), 12)))
            
            hp = 100.0
            if humanoid:
                hp_val = self.pm.read_float(humanoid + self.get_offset("Health"))
                hp = round(hp_val, 1)

            return pos, hp
        except: return None, 100

    def get_player_data(self):
        self.check_connection()
        if not self.Players: return []
        
        data = []
        if self.Players: self.LocalPlayer = self.pm.read_longlong(self.Players + self.get_offset("LocalPlayer"))
        
        my_pos = None
        if self.LocalPlayer:
            pos, _ = self.get_character_info(self.LocalPlayer)
            my_pos = pos

        try:
            players = self.get_children(self.Players)
            for p_ptr in players:
                if p_ptr == self.LocalPlayer: continue 
                
                pos, hp = self.get_character_info(p_ptr)
                if not pos: continue
                
                dist = 0
                if my_pos: dist = math.sqrt((pos[0]-my_pos[0])**2 + (pos[1]-my_pos[1])**2 + (pos[2]-my_pos[2])**2)

                data.append({
                    'name': self.get_name(p_ptr),
                    'center_pos': type('Vec3', (), {'x': pos[0], 'y': pos[1], 'z': pos[2]})(),
                    'distance': dist,
                    'health': hp
                })
        except: pass
        return data

    def world_to_screen(self, pos, matrix, x_off, y_off, width, height):
        if not matrix: return type('Vec2', (), {'x': -1, 'y': -1})()
        
        x, y, z = pos.x, pos.y, pos.z
        w = x*matrix[12] + y*matrix[13] + z*matrix[14] + matrix[15]
        if w < 0.1: return type('Vec2', (), {'x': -1, 'y': -1})()
        
        ndc_x = (x*matrix[0] + y*matrix[1] + z*matrix[2] + matrix[3]) / w
        ndc_y = (x*matrix[4] + y*matrix[5] + z*matrix[6] + matrix[7]) / w
        
        screen_x = (width / 2 * (1 + ndc_x)) + x_off
        screen_y = (height / 2 * (1 - ndc_y)) + y_off
        
        return type('Vec2', (), {'x': screen_x, 'y': screen_y})()