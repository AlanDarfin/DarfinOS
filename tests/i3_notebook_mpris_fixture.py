"""Minimal disposable MPRIS player for the real playerctl/Polybar smoke test."""
from pathlib import Path
import sys

from gi.repository import Gio, GLib

state, event = map(Path, sys.argv[1:])
iface = "org.mpris.MediaPlayer2.Player"
xml = f"""
<node>
  <interface name="{iface}">
    <method name="PlayPause"/>
    <method name="Next"/>
    <method name="Previous"/>
    <property name="PlaybackStatus" type="s" access="read"/>
    <property name="CanControl" type="b" access="read"/>
    <property name="CanPlay" type="b" access="read"/>
    <property name="CanPause" type="b" access="read"/>
    <property name="CanGoNext" type="b" access="read"/>
    <property name="CanGoPrevious" type="b" access="read"/>
    <property name="Metadata" type="a{{sv}}" access="read"/>
  </interface>
</node>
"""


def call(conn, sender, path, interface, method, args, invocation):
    event.write_text(method + "\n")
    if method == "PlayPause":
        state.write_text("Paused" if state.read_text().strip() == "Playing" else "Playing")
    invocation.return_value(None)


def read(conn, sender, path, interface, name):
    if name == "PlaybackStatus":
        return GLib.Variant("s", state.read_text().strip())
    if name == "Metadata":
        return GLib.Variant("a{sv}", {"xesam:title": GLib.Variant("s", "DarfinOS Test Track")})
    if name.startswith("Can"):
        return GLib.Variant("b", True)
    return None


def acquired(conn, name):
    conn.register_object("/org/mpris/MediaPlayer2", Gio.DBusNodeInfo.new_for_xml(xml).interfaces[0],
                         call, read, None)


Gio.bus_own_name(Gio.BusType.SESSION, "org.mpris.MediaPlayer2.darfinos.test",
                 Gio.BusNameOwnerFlags.NONE, acquired, None, None)
GLib.MainLoop().run()
