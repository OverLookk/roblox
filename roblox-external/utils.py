import ctypes
from ctypes import wintypes
import math

# ⚠️ FIXED: _fields_ is properly indented inside the class
class MODULEENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("th32ModuleID", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("GlblcntUsage", wintypes.DWORD),
        ("ProccntUsage", wintypes.DWORD),
        ("modBaseAddr", ctypes.POINTER(wintypes.BYTE)),
        ("modBaseSize", wintypes.DWORD),
        ("hModule", wintypes.HMODULE),
        ("szModule", ctypes.c_char * 256),
        ("szExePath", ctypes.c_char * 260)
    ]

class Vec2:
    __slots__ = ('x', 'y')
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

class Vec3:
    __slots__ = ('x', 'y', 'z')
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

    def dist(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)