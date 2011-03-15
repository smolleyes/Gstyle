#!/usr/bin/env python
#-*- coding: UTF-8 -*-
#Standard library
import os
import new
import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
import dbus
from urlparse import urlparse
from urllib import unquote
from functions import *
#Gstyle library

#import gtkui
from emerald import EmeraldGui
from icon import IconGui
from mouse import MouseGui
from wallpapers import WallpaperGui
from metacity import MetacityGui
from xsplash import XsplashGui
from cubemodels import CubemodelsGui
from fullpacks import FullpackGui
from gtk_gui import GtkGui
from lib.theme_scaner import ThemeScaner

import config
import gettext

GLADE_FILE = os.path.join(config.glade_path,'Gstyle.glade')
vfile=config.data_path+"/version"
f = open(vfile)
VERSION=f.read()
f.close()

class MainWindow(object):   
    def initialisation_gui(self, gstyle_obj):
        #Build interface
        self.gstyle_obj = gstyle_obj
        self.wTree = gtk.glade.XML(GLADE_FILE, None, config.APP_NAME)
        #icon
        self.icon_obj = IconGui(self.wTree,self.gstyle_obj.icon_dict)
        #emerald
        self.emerald_obj = EmeraldGui(self.wTree,self.gstyle_obj.emerald_dict)
        #metacity
        self.metacity_obj = MetacityGui(self.wTree,self.gstyle_obj.metacity_dict)
        #mouse
        self.mouse_obj = MouseGui(self.wTree,self.gstyle_obj)
        #gtk
        self.gtk_obj = GtkGui(self.wTree,self.gstyle_obj.gtk_dict)
        #wallpaper
        self.wallpaper_obj = WallpaperGui(self.wTree,self.gstyle_obj.wallpapers_dict)
        #xsplash
        self.xsplash_obj = XsplashGui(self.wTree,self.gstyle_obj)
        #cubemodel
        self.cubemodel_obj = CubemodelsGui(self.wTree,self.gstyle_obj.cubemodels_dict)
        #fullpack
        self.fullpack_obj = FullpackGui(self.wTree,self.gstyle_obj)

        self.check_dbus_configuration()
        self.setup_widgets()
    
    def setup_widgets(self):

        self.window = self.wTree.get_widget("main_window")
        self.window.set_title("Gstyle")
        self.window.set_resizable(1)
        self.window.set_position("center")
        width = gtk.gdk.screen_width()
        height = gtk.gdk.screen_height()
        self.window.set_default_size((width - 260), (height - 250))
        self.window.set_icon_from_file(os.path.join(config.img_path,'puzzle.png'))

        self.main_notebook = self.wTree.get_widget("main_notebook")

        self.aboutdialog_btn= self.wTree.get_widget("aboutdialog_btn")
        self.statbar = self.wTree.get_widget("statusbar")

        ## menu elements
        self.toggleb_menu_icons = self.wTree.get_widget("menu_icons_btn")
        self.toggleb_menu_gtkThemes = self.wTree.get_widget("menu_gtk_btn")
        self.toggleb_menu_cubemodel = self.wTree.get_widget("menu_cubemodel_btn")
        self.toggleb_menu_wallpapers = self.wTree.get_widget("menu_wallpapers_btn")
        self.toggleb_menu_gdm = self.wTree.get_widget("menu_gdm_btn")
        self.toggleb_menu_mouse = self.wTree.get_widget("menu_mouse_btn")
        self.toggleb_menu_fullpack = self.wTree.get_widget("menu_fullpack_btn")
        self.toggleb_menu_decoration = self.wTree.get_widget("menu_decoration_btn")
        self.list_widget = (self.toggleb_menu_icons, self.toggleb_menu_gtkThemes,\
        self.toggleb_menu_wallpapers, self.toggleb_menu_gdm, self.toggleb_menu_mouse,\
        self.toggleb_menu_cubemodel,self.toggleb_menu_fullpack, self.toggleb_menu_decoration)
        self.ddbox = self.wTree.get_widget("dragndrop_box")
        self.ddbox.drag_dest_set(0, [], 0)
       #Create our dictionary and connect it
        dic = {"on_main_window_destroy" : gtk.main_quit,
        "on_toggleb_menu_cubemodel" : self.get_func_menu_pressed(0),
        "on_toggleb_menu_wallpapers" :  self.get_func_menu_pressed(1),
        "on_toggleb_menu_gdm" :  self.get_func_menu_pressed(2),
        "on_toggleb_menu_gtkThemes" :  self.get_func_menu_pressed(3),
        "on_toggleb_menu_icons" :  self.get_func_menu_pressed(4),
        "on_toggleb_menu_fullpack" :   self.get_func_menu_pressed(5),
        "on_toggleb_menu_mouse" :  self.get_func_menu_pressed(6),
        "on_toggleb_menu_decoration" :  self.get_func_menu_pressed(7),
        "on_aboutdialog" : self.on_aboutdialog_pressed,
        "on_dragndrop_box_drag_data_received" : self.got_data_cb,
        "on_dragndrop_box_drag_motion" : self.motion_cb,
        "on_dragndrop_box_drag_drop" : self.drop_cb,
        }
        
        self.window.connect("destroy",gtk.main_quit)
        self.window.connect("delete_event",gtk.main_quit)
        self.wTree.signal_autoconnect(dic)
        
        self.window.show_all()
        self.wTree.get_widget('cubemodels_down_progress').hide()
        self.wTree.get_widget('fullpack_download_pbar').hide()
        self.wTree.get_widget('progress_box').hide()
        self.wTree.get_widget("walldyn_editor_options").hide()
        self.wTree.get_widget("walldyns_edit_btn").hide()
        ## start page
        self.main_notebook.set_current_page(5)
        ## gdm check
        self.gdm_check=None

    def inactive_widgets(self,widget):
        fonc_inact = lambda x : x.set_active(False)
        [fonc_inact(item) for item in self.list_widget if item != widget]

    def on_aboutdialog_pressed(self, widget):
        dlg = self.wTree.get_widget("aboutdialog")
        dlg.set_version(VERSION)
        response = dlg.run()
        if response == gtk.RESPONSE_DELETE_EVENT or response == gtk.RESPONSE_CANCEL:
            self.wTree.get_widget("aboutdialog").hide()

    ## defini menu
    def get_func_menu_pressed(self,num_page):
        def toggleb_menu_func_pressed(self,widget):
            gtk_check = self.toggleb_menu_gtkThemes.get_active()
            gdm_check = self.toggleb_menu_gdm.get_active()
            appgtk = self.gtk_obj.gtkThemes_preview
            if gtk_check :
                sysgtk = self.gtk_obj.gtkThemes_save
                if appgtk and sysgtk != appgtk and sysgtk != "Default" :
                    item = self.gtk_obj.gtk_dict[sysgtk]
                    path = item.path
                    rc = os.path.join(path,'gtk-2.0/gtkrc')
                    if not(os.path.exists(rc)):
                        return
                    gtk.rc_set_default_files(rc)
                    settings = self.window.get_settings()
                    gtk.rc_reparse_all_for_settings(settings, 1)
                    self.gtk_obj.gtkThemes_preview = ""
            ## if gdm btn clicked for first time and authentication not applied yet
            ## start the admin dialog
            if widget.name == "menu_gdm_btn" and not gdm_check and not self.gdm_check:
                run_as_root('Gstyle')
                self.xsplash_obj.autosetup_gdm()
                self.xsplash_obj.check_gdm_options()
                self.gdm_check=True

            self.inactive_widgets(widget)
            self.main_notebook.set_current_page(num_page)
        return new.instancemethod(toggleb_menu_func_pressed,self,MainWindow)
        
    def motion_cb(self,wid, context, x, y, time):
        print '\n'.join([str(t) for t in context.targets])
        context.drag_status(gtk.gdk.ACTION_COPY, time)
        # Returning True which means "I accept this data".
        return True

    def drop_cb(self,wid, context, x, y, time):
        # Some data was dropped, get the data
        wid.drag_get_data(context, context.targets[-1], time)
        return True
    
    def got_data_cb(self,wid, context, x, y, data, info, time):
        # Got data.
        file = urlparse(data.get_text().encode('utf-8'))
        archive = unquote(file.path)
        context.finish(True, False, time)
        self.add_item_archive(archive)
        
    def add_item_archive(self,archive):
        """Ajouter un element dans le dictionnaire"""
        scaner = ThemeScaner(archive,self.gstyle_obj)
        theme_list = scaner.theme_loader(archive)
        
    def check_dbus_configuration(self):
        same_content = True
        if not with_same_content('/etc/dbus-1/system.d/cn.gstyle.conf', '/usr/share/gstyle/support/cn.gstyle.conf'):
            same_content = False
        if not with_same_content('/usr/share/dbus-1/system-services/cn.gstyle.service', '/usr/share/gstyle/support/cn.gstyle.service'):
            same_content = False
        dbus_ok = True
        try:
            get_authentication_method()
        except:
            dbus_ok = False
        if same_content and dbus_ok: return
        import StringIO
        message = StringIO.StringIO()
        print >>message, _('Error happened. Dbus problem. :(')
        print >>message, ''
        if not same_content:
            print >>message, _('System configuration file should be updated.')
            print >>message, _('Please run these commands using <b>su</b> or <b>sudo</b>:')
            print >>message, ''
            print >>message, '<span color="blue">', 'cp /usr/share/gstyle/support/cn.gstyle.conf /etc/dbus-1/system.d/cn.gstyle.conf', '</span>'
            print >>message, '<span color="blue">', 'cp /usr/share/gstyle/support/cn.gstyle.service /usr/share/dbus-1/system-services/cn.gstyle.service', '</span>'
            print >>message, ''
        if not dbus_ok:
            print >>message, _("gstyle' D-Bus daemon exited with error.")
            print >>message, _("Please restart your computer, or start daemon using <b>su</b> or <b>sudo</b>:")
            print >>message, ''
            print >>message, '<span color="blue">', '/usr/share/gstyle/support/gstyle-daemon &amp;', '</span>'
        dialog = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
        dialog.set_title('gstyle')
        dialog.set_markup(message.getvalue())
        dialog.run()
        dialog.destroy()
