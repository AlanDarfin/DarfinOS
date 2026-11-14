"""Helper for the disposable X11 integration test."""
import ctypes
from ctypes.util import find_library
import hashlib
from pathlib import Path
import sys


def cursor_hash():
    class CursorImage(ctypes.Structure):
        _fields_ = [("x", ctypes.c_short), ("y", ctypes.c_short),
                    ("width", ctypes.c_ushort), ("height", ctypes.c_ushort),
                    ("xhot", ctypes.c_ushort), ("yhot", ctypes.c_ushort),
                    ("serial", ctypes.c_ulong), ("pixels", ctypes.POINTER(ctypes.c_ulong))]

    x11 = ctypes.CDLL(find_library("X11"))
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    x11.XFree.argtypes = [ctypes.c_void_p]
    fixes = ctypes.CDLL(find_library("Xfixes"))
    fixes.XFixesGetCursorImage.argtypes = [ctypes.c_void_p]
    fixes.XFixesGetCursorImage.restype = ctypes.POINTER(CursorImage)
    conn = x11.XOpenDisplay(None)
    if not conn:
        return 1
    image = fixes.XFixesGetCursorImage(conn)
    try:
        data = image.contents
        pixels = ctypes.string_at(data.pixels, data.width * data.height * ctypes.sizeof(ctypes.c_ulong))
        print(f"{data.width}x{data.height}+{data.xhot}+{data.yhot} {hashlib.sha256(pixels).hexdigest()}")
    finally:
        x11.XFree(image)
        x11.XCloseDisplay(conn)
    return 0


def app(path):
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, Gtk
    window = Gtk.Window(title="DarfinOS mouse fixture")
    window.set_default_size(240, 200)
    window.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

    def button(_, event):
        if event.button == 3:
            Path(path).touch()
        return True

    window.connect("button-press-event", button)
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()
    return 0


if __name__ == "__main__":
    sys.exit(cursor_hash() if sys.argv[1] == "cursor" else app(sys.argv[1]))
