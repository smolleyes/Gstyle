#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import os
import gtk
import config
import gconf

from functions import create_filechooser_open
from functions import yesno

from config import _

PREVIEW_GLADE = os.path.join(config.glade_path,'gtk-preview.glade')
APP_NAME = 'Gstyle'
gtkThemes_srcdir = config.gtkThemes_srcdir
gtkThemes_home_srcdir = config.gtkThemes_home_srcdir
gtkrcfile = config.gtkrcfile

class GtkGui(object):
    def __init__(self,gladexml,gtk_dict):
        self.gtk_dict = gtk_dict

        self.gclient = gconf.client_get_default()
        self.window = gladexml.get_widget("main_window")

        self.statbar = gladexml.get_widget("statusbar")

        self.gtk_img = gladexml.get_widget("gtk_img")
        self.gtk_label = gladexml.get_widget("gtk_label")
        self.gtk_img.set_from_file("%s/gtk-icon.png" % config.img_path)
        self.gtk_label.set_text(_("Gtk-themes:\nManage and install your Gtk themes..."))
        
        self.model = gtk.ListStore(str)

        ## glade widget for preview
        pgladexml = gtk.glade.XML(PREVIEW_GLADE,None,config.APP_NAME)
        self.gtkThemes_preview_cont = gladexml.get_widget('gtkpreview_container')

        self.preview = pgladexml.get_widget('gtk_preview')
        self.gtkpreview_infos = pgladexml.get_widget('gtkpreview_infos')
        self.gtkThemes_preview_cont.add(self.preview)
        self.gtkThemes_preview_cont.show()

        ## gui
        self.gtkThemes_previewer = gladexml.get_widget("gtkThemes_preview")
        self.gtkThemes_gest_label = gladexml.get_widget("gtkThemes_gest_label")
        self.gtkThemes_gest_colorbtn = gladexml.get_widget("gtkThemes_gest_colorbtn")
        self.gtkThemes_gest_welcomentry = gladexml.get_widget("gtkThemes_gest_welcomentry")
        self.gtkThemes_selector = gladexml.get_widget("gtkThemes_selector")
        self.gtkThemes_selector.set_model(self.model)
        self.gtkThemes_gest_applybtn = gladexml.get_widget('gtkThemes_gest_applybtn')
        self.gtkThemes_gest_delbtn = gladexml.get_widget('gtkThemes_gest_delbtn')

        ##load signal
        dic = {"on_gtk_addbtn_clicked" : self.action_add,
                "on_gtkThemes_gest_applybtn_clicked" : self.action_apply,
                "on_gtkThemes_gest_delbtn_clicked" : self.action_delete,
                "on_gtkThemes_selector_changed" : self.selector_changed,
            }
        gladexml.signal_autoconnect(dic)

        self.gtkThemes_preview = ""
        self.gtkThemes_save = self.gclient.get_string("/desktop/gnome/interface/gtk_theme")
        self.gtkThemes_thdir = "/usr/share/themes/Default" ## default gtk theme...
        self.gtkThemes_thname = "Default"

        if self.gtkThemes_save == "":
            ## set default gtk theme
            self.gtkThemes_save = "Default"
        print "Current gtk theme: %s" % self.gtkThemes_save

        self.list_gtk_themes()

    def selector_changed(self,widget):
        dirname = self.gtkThemes_selector.get_active_text()
        if self.gtk_dict.has_key(dirname):
            self.item = self.gtk_dict[dirname]
            self.gtkThemes_preview = self.item.name
            self.statbar.push(1,_("Gtk theme %s selected") % self.item.name)
            self.gtk_preview(self.item)

    def get_model(self):
        pass

    def action_add(self,widget):
        filterlist = ["*.gz","*.bz2","*.tar","*.zip","*.rar"]
        dialog = create_filechooser_open((_("Choose a tar/bz2 file")),filterlist)
        result = dialog.run()
        if result != gtk.RESPONSE_OK:
            dialog.destroy()
            return
        ## if ok
        self.gtk_archive =  dialog.get_filename()
        dialog.destroy()

        if not os.path.exists(self.gtk_archive):
            print "Gtk theme archive non-existent or corrupted \n"
            return
        theme_list = self.gtk_dict.add_item_archive(self.gtk_archive)
        if theme_list:
            return self.action_add_todic(theme_list)

    def action_add_todic(self,theme_list, fullpack=None):
        item=None
        if theme_list and theme_list.has_key('gtk'):
            gtk_list = theme_list['gtk'].values()
            for destination in gtk_list:
                if os.path.exists(destination):
                    item = self.gtk_dict.add_item_system(destination)
                    if item:
                        self.add_model(item)
                else:
                    continue
            if item:
                iter = self.gtkThemes_selector.get_model()[-1].iter
                self.gtkThemes_selector.set_active_iter(iter)
                if fullpack:
                    self.action_apply(item.dirname)
                else:
                    self.gtk_preview(item)
        else:
            "no gtk themes to install"
            return

    def action_apply(self,widget=None,name=None):
        if not name:
            name = self.gtkThemes_selector.get_active_text()
        self.gtk_dict.set_active_item(name)
        item = self.gtk_dict.get(name)
        if item:
            self.gtkThemes_save = item.dirname
            #Preview
            files = [item.rcfile]
            gtk.rc_set_default_files(files)
            settings = self.window.get_settings()
            gtk.rc_reparse_all_for_settings(settings, 1)

    def generate_previewbox(self):
        """Create a preview box like gnome apparence"""
        ## main vbox
        vbox = gtk.GtkVBox(gtk.FALSE, 5)
        ## open btn
        open_btn = gtk.Button
        open_btn.set_use_stock(True)
        open_btn.set_label("gtk-open")
        ## checkbox
        checkbox = gtk.CheckButton
        radio = gtk.RadioButton
        
        ## build
        vbox.add(open_btn)
        vbox.add(checkbox)
        vbox.add(radio)
        vbox.show_all
        

    def action_delete(self,widget):
        confirm = yesno((_("Remove Gtk themes")),\
                (_("Are you sure you want to delete the gtk Theme \n %s ?") % self.item.dirname))
        if confirm == "No":
            return
        ## remove the theme
        self.gtk_dict.action_delete(self.item.dirname)
        model = self.gtkThemes_selector.get_model()
        model.clear()
        self.list_gtk_themes()
        self.statbar.push(1,(_("Gtk theme %s removed successfully") % self.item.name))

    def list_gtk_themes(self):
        for item in self.gtk_dict.values():
            self.add_model(item)

    def add_model(self,item):
        ## then add it to the combobox
        self.iter = self.model.append()
        self.model.set(self.iter,
        0, item.dirname,
        )

    def gtk_preview(self,item):
        #self.gclient.set_string("/desktop/gnome/interface/gtk_theme", '')
        gtkThemes_index_rc = item.rcfile
        ## conteneur des informations du theme
        gtkThemes_index_metacity = item.metacity
        gtkThemes_index_gtk = item.name
        gtkThemes_dirname = item.path
        gtkThemes_comment = item.comment

        files=[]
        files.append(item.rcfile)
        gtk.rc_set_default_files(files)
        settings = gtk.settings_get_default()
        gtk.rc_reparse_all_for_settings(settings, 1)

        self.gtkpreview_infos.set_text("Theme : %(name)s \n\
Metacity : %(metacity)s \n\
Icones : %(gtk)s \n\
Comment : %(comment)s" % {'name' : gtkThemes_index_gtk,
                       'metacity' : gtkThemes_index_metacity ,
                       'gtk' : gtkThemes_index_gtk,
                       'comment': gtkThemes_comment
                       })

