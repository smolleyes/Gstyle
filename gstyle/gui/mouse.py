#!/usr/bin/python
#-*- coding: UTF-8 -*-
import os
from shutil import copytree,rmtree
import gtk
import config
import ConfigParser
import threading
import time
import re

from functions import yesno
from functions import create_filechooser_open
import config
from config import _

icons_dir = config.icons_home_srcdir

class MouseGui(object):
    def __init__(self,gladexml,gstyle_obj):
        ## load buttons and attach signals
        self.gstyle_obj = gstyle_obj
        self.mouse_dict = self.gstyle_obj.mouse_dict

        self.mouse_scroll = gladexml.get_widget("mouse_scroll")
        self.mouse_gest_label = gladexml.get_widget("mouse_gest_label")
        self.mouse_gest_label.set_text(_("Installed mouse themes list"))
        self.mouse_gest_colorbtn = gladexml.get_widget("mouse_gest_colorbtn")
        self.mouse_gest_welcomentry = gladexml.get_widget("mouse_gest_welcomentry")
        self.mouse_page_img = gladexml.get_widget("mouse_page_img")
        self.mouse_page_img.set_from_file("%s/mouse.png" % config.img_path)

        self.mouse_page_desc = gladexml.get_widget("mouse_page_desc")
        self.mouse_page_desc.set_text(_("\nmouse themes : \nOrganize your mouse themes...\n"))

        self.mouse_gest_applybtn = gladexml.get_widget('mouse_gest_applybtn')
        self.mouse_gest_delbtn = gladexml.get_widget('mouse_gest_delbtn')
        self.statbar = gladexml.get_widget("statusbar")

        dic = {"on_mouse_addbtn_clicked" : self.action_add,
               "on_mouse_applybtn_clicked" : self.action_apply,
               "on_mouse_delbtn_clicked" : self.action_del,
               }
        gladexml.signal_autoconnect(dic)

        ## gui
        self.model = gtk.ListStore(str,gtk.gdk.Pixbuf,str,str,str,str,str,str)
        self.mouse_iconview = gtk.IconView(model=self.model)

        # Setup GtkIconView
        self.mouse_iconview.set_pixbuf_column(1)
        self.mouse_iconview.set_text_column(0)
        ## options
        self.mouse_iconview.set_columns(0)
        self.mouse_iconview.set_selection_mode('single')
        self.mouse_iconview.set_reorderable(1)
        self.mouse_iconview.set_item_width(150);

        self.mouse_iconview.connect('selection_changed',self.get_model)
        self.mouse_iconview.connect('button-press-event',self.check_double_click)
        self.mouse_scroll.add(self.mouse_iconview)
        self.list_mouse_themes()

    def get_model(self,widget=None):
        selected = self.mouse_iconview.get_selected_items()
        ## check if path exist (or problems when clicking between rows..)
        try:
            row_index = selected[0]
        except:
             return
        self.item_comment = _("No_description")
        self.iter = self.model.get_iter(row_index)
        self.item_name = self.model.get_value(self.iter,0)
        self.item_comment = self.model.get_value(self.iter,2)
        self.item_path = self.model.get_value(self.iter,5)
        self.item_dirname = self.model.get_value(self.iter,6)
        self.mouse_gest_label.set_text(_("Description : %s") % self.item_comment)
        self.statbar.push(1,_("Selected mouse theme : %s") % self.item_name)

    def action_add(self,widget):
        filterlist = ["*.gz","*.bz2","*.tar","*.zip","*.rar"]
        dialog = create_filechooser_open(_("Choose a gz/bz2/tar file"),filterlist)
        result = dialog.run()
        if result != gtk.RESPONSE_OK:
            dialog.destroy()
            return
        ## if ok
        archive = dialog.get_filename()
        dialog.destroy()
        if not os.path.exists(archive):
            print "Mouse theme do not exist or corrupted \n"
            return
        theme_list = self.mouse_dict.add_item_archive(archive)
        if theme_list:
            return self.action_add_todic(theme_list)
        
    def action_add_todic(self,theme_list):
        if theme_list and theme_list.has_key('mouse'):
            mouse_theme_list = theme_list['mouse']
            for p in mouse_theme_list.items():
                destination = p[1]
                if destination:
                    item = self.mouse_dict.add_item_system(destination)
                    if item:
                        self.item = item
                        self.add_mouse_model(item)
            if item:
                self.mouse_dict.set_active_item(destination)
                path = self.model[-1].path
                self.mouse_iconview.select_path(path)
                self.mouse_iconview.set_cursor(path)
        else:
            "no mouse theme to install"
            return

    def action_apply(self,widget=None,item=None,name=None):
        if name:
            item = self.mouse_dict.get(name)
            if item:
                self.item_name = item.name
                self.item_path = item.path
            else:
                return
        self.mouse_dict.set_active_item(self.item_path)
        self.statbar.push(1,_("Mouse theme  %s successfully activated") % self.item_name)

    def action_del(self,widget):
        confirm = yesno((_("Remove mouse themes")),\
                _("Are you sure you want to delete the mouse Theme \n %s ?") % self.item_name)
        if confirm == "No":
            return
        ## remove the theme
        self.mouse_dict.del_item(self.item_dirname)
        self.model.remove(self.iter)
        self.statbar.push(1,_("Mouse theme %s removed successfully") % self.item_name)

    def list_mouse_themes(self):
        for item in self.mouse_dict.values():
            self.add_mouse_model(item)

    def add_mouse_model(self,item):
        img = gtk.gdk.pixbuf_new_from_file(item.pic)
        ## then add it to the iconview
        self.iter = self.model.append()
        self.model.set(self.iter,
        0, item.name,
        1, img,
        2, item.comment,
        3, item.example,
        4, item.inherit,
        5, item.path,
        6, item.dirname,
        )

    def check_double_click(self, widget, event):
        if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            self.get_model()
            self.action_apply()
    
    