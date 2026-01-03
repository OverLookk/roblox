import pymem
import pymem.process
import struct
import math
import win32gui
import win32api
from config import OFFSETS

class RobloxMemory:
    def __init__(self):
        try:
            self.pm = pymem.Pymem("RobloxPlayerBeta.exe")
            self.process_id = self.pm.process_id
            self.base_addr = self.pm.process_base.lpBaseOfDll
            print(f"Attached to Roblox: {hex(self.base_addr)}")
        except Exception as e:
            print(f"Failed to attach: {e}")
            self.pm = None
            return

        self.offsets = OFFSETS
        self.DataModel = None
        self.VisualEngine = None
        self.Players = None
        self.LocalPlayer = None 
        self.Workspace = None
        
        self.init_pointers()

    def get_offset(self, key):
        val = self.offsets.get(key, "0x0")
        return int(val, 16) if isinstance(val, str) else val

    def read_string(self, address):
        try:
            length = self.pm.read_int(address + 0x10) 
            if length >= 16:
                address = self.pm.read_longlong(address)
            if address == 0: return ""
            raw = self.pm.read_bytes(address, 100)
            return raw.decode('utf-8', errors='ignore').split('\x00')[0]
        except:
            return ""

    def get_children(self, instance_addr):
        children = []
        try:
            children_ptr = self.pm.read_longlong(instance_addr + self.get_offset("Children"))
            if children_ptr == 0: return []
            top = self.pm.read_longlong(children_ptr)
            end = self.pm.read_longlong(children_ptr + 8)
            current = top
            while current < end and len(children) < 1000:
                child = self.pm.read_longlong(current)
                if child != 0: children.append(child)
                current += 16 
        except: pass
        return children

    def get_name(self, instance_addr):
        try:
            name_ptr = self.pm.read_longlong(instance_addr + self.get_offset("Name"))
            return self.read_string(name_ptr)
        except: return ""

    def get_class_name(self, instance_addr):
        try:
            class_desc = self.pm.read_longlong(instance_addr + self.get_offset("ClassDescriptor"))
            if class_desc == 0: return ""
            name_ptr = self.pm.read_longlong(class_desc + self.get_offset("ClassDescriptorToClassName"))
            return self.read_string(name_ptr)
        except: return ""

    def init_pointers(self):
        try:
            fake_dm = self.pm.read_longlong(self.base_addr + self.get_offset("FakeDataModelPointer"))
            self.DataModel = self.pm.read_longlong(fake_dm + self.get_offset("FakeDataModelToDataModel"))
            self.VisualEngine = self.pm.read_longlong(self.base_addr + self.get_offset("VisualEnginePointer"))
            
            children = self.get_children(self.DataModel)
            for child in children:
                name = self.get_name(child)
                if name == "Players": self.Players = child
                elif name == "Workspace": self.Workspace = child
            
            if self.Players:
                self.LocalPlayer = self.pm.read_longlong(self.Players + self.get_offset("LocalPlayer"))
        except Exception as e: print(f"Pointer Init Error: {e}")

    def get_view_matrix(self):
        if not self.VisualEngine: return None
        try:
            mat_addr = self.VisualEngine + self.get_offset("viewmatrix")
            mat_bytes = self.pm.read_bytes(mat_addr, 64)
            return list(struct.unpack("16f", mat_bytes))
        except: return None

    def get_window_info(self):
        try:
            hwnd = win32gui.FindWindow(None, "Roblox")
            if hwnd:
                point = win32gui.ClientToScreen(hwnd, (0, 0))
                rect = win32gui.GetClientRect(hwnd)
                return {'x': point[0], 'y': point[1], 'w': rect[2], 'h': rect[3]}
        except: pass
        return {'x': 0, 'y': 0, 'w': 1920, 'h': 1080}

    def get_position(self, player_ptr):
        try:
            char_ptr = self.pm.read_longlong(player_ptr + self.get_offset("ModelInstance"))
            if char_ptr == 0: return None
            
            children = self.get_children(char_ptr)
            target_part = None
            
            # --- UPDATED: Look for "Head" instead of RootPart ---
            for child in children: 
                name = self.get_name(child)
                if name == "Head":
                    target_part = child
                    break
            
            # Fallback to HumanoidRootPart if Head is missing (rare)
            if not target_part:
                for child in children:
                    if self.get_name(child) == "HumanoidRootPart":
                        target_part = child
                        break
            
            if not target_part: return None

            primitive = self.pm.read_longlong(target_part + self.get_offset("Primitive"))
            if primitive == 0: return None
            pos_bytes = self.pm.read_bytes(primitive + self.get_offset("Position"), 12)
            return list(struct.unpack("3f", pos_bytes)) 
        except: return None

    def get_player_data(self):
        if not self.Players: return []
        data = []
        my_pos = None
        if self.LocalPlayer: my_pos = self.get_position(self.LocalPlayer)

        try:
            players = self.get_children(self.Players)
            for p_ptr in players:
                if p_ptr == self.LocalPlayer: continue 
                if self.get_class_name(p_ptr) != "Player": continue
                pos = self.get_position(p_ptr)
                if not pos: continue
                
                dist = 0
                if my_pos:
                    dist = math.sqrt((pos[0]-my_pos[0])**2 + (pos[1]-my_pos[1])**2 + (pos[2]-my_pos[2])**2)

                data.append({
                    'name': self.get_name(p_ptr),
                    'center_pos': pos,
                    'distance': dist,
                    'health': 100
                })
        except: pass
        return data

    def world_to_screen(self, pos, matrix, width, height):
        if not matrix: return -100, -100
        x, y, z = pos
        w = x*matrix[12] + y*matrix[13] + z*matrix[14] + matrix[15]
        if w < 0.1: return -100, -100
        
        ndc_x = (x*matrix[0] + y*matrix[1] + z*matrix[2] + matrix[3]) / w
        ndc_y = (x*matrix[4] + y*matrix[5] + z*matrix[6] + matrix[7]) / w
        
        screen_x = (width / 2 * (1 + ndc_x))
        screen_y = (height / 2 * (1 - ndc_y))
        
        return screen_x, screen_y