"""Render the controls from the GTK appearance dialog in both supported toolkits."""
import sys

import gi

major = int(sys.argv[1])
gi.require_version("Gtk", f"{major}.0")
from gi.repository import Gtk, GLib

window = Gtk.Window(title=f"Notebook GTK{major} swatches")
window.set_default_size(460, 360)
box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=8, margin_bottom=8,
              margin_start=12, margin_end=12)
tabs = Gtk.Notebook()
tabs.append_page(Gtk.Label(label="Primeira página"), Gtk.Label(label="Aba ativa"))
tabs.append_page(Gtk.Label(label="Segunda página"), Gtk.Label(label="Outra aba"))
progress = Gtk.ProgressBar(fraction=0.65, show_text=True)
scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
scale.set_value(65)
checked = Gtk.CheckButton(label="Marcado", active=True)
radio = (Gtk.RadioButton.new_with_label_from_widget(None, "Rádio")
         if major == 3 else Gtk.CheckButton(label="Rádio", active=True))
if major == 4:
    radio.set_group(Gtk.CheckButton())
    radio.set_active(True)
choose = Gtk.ListBox()
choose.append(Gtk.Label(label="Linha selecionada")) if major == 4 else choose.add(Gtk.Label(label="Linha selecionada"))
choose.select_row(choose.get_row_at_index(0))
button = Gtk.Button(label="Ação sugerida")
button.get_style_context().add_class("suggested-action")
for widget in (tabs, progress, scale, checked, radio, choose, button):
    box.append(widget) if major == 4 else box.pack_start(widget, False, False, 0)

loop = GLib.MainLoop()
if major == 4:
    window.set_child(box)
    window.connect("close-request", lambda *_: loop.quit() or False)
    window.present()
else:
    window.add(box)
    window.connect("destroy", lambda *_: loop.quit())
    window.show_all()
loop.run()
