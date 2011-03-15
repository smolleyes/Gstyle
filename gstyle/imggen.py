## function checked from epidermis
# Copyright 2009 David D Lowe
# released under the GPL v3

import gtk
import os
import sys
from functions import _

target_img = sys.argv[1]
gtkrc = sys.argv[2]

def gtk_generate(target_img, gtkrc):

    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.connect("destroy",  lambda widget: sys.exit(1))
    window.resize(100, 35)
    window.set_property("skip-pager-hint", True)
    window.set_property("skip-taskbar-hint",  True)

    hbox = gtk.HBox()
    window.add(hbox)
    button = gtk.Button()
    button.set_label(_("Button"))
    hbox.pack_start(button)
    chkbox = gtk.CheckButton()
    chkbox.set_active(True)
    hbox.pack_end(chkbox,  False)
    radiobox = gtk.RadioButton()
    hbox.pack_end(radiobox,  False)
    window.show_all()
    take_screenshot(hbox,  target_img)
    sys.exit(0)

def take_screenshot(widg,  target_img):
    pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,1,8,100,34)
    pm = widg.get_snapshot(None)
    pb = pb.get_from_drawable(pm,  pm.get_colormap(),  0, 0, 0, 0, 100,  34)
    if pb is not None:
        pb.save(target_img,  "png")
    else:
        print >> sys.stderr,  "Error getting image"
        sys.exit(3)

#################### end checked from epidermis

gtk_generate(target_img, gtkrc)
