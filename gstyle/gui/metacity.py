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

import gconf

from functions import yesno
from functions import create_filechooser_open
from functions import make_metacity_preview
from config import _


class MetacityGui(object):
    def __init__(self,gladexml,metacity_dict):
        ## load buttons and attach signals
        self.metacity_dict = metacity_dict
        self.gclient = gconf.client_get_default()
        self.layout_model = None
        self.layout = self.gclient.get_string('/apps/metacity/general/button_layout')
        ## create main layout dic
        self.layout_dic = {'lucid':'close,minimize,maximize:','karmic':'menu:minimize,maximize,close','osx':'close,maximize,minimize:menu','custom':self.layout}
        
        self.metacity_addbtn = gladexml.get_widget("metacity_addbtn")
        self.metacity_applybtn = gladexml.get_widget("metacity_applybtn")
        self.metacity_delbtn = gladexml.get_widget("metacity_delbtn")
        self.metacity_gest_info = gladexml.get_widget("metacity_gest_info")
        self.metacity_dret_label = gladexml.get_widget("metacity_dret_label")
        self.decoration_page_img = gladexml.get_widget("decoration_page_img")
        self.decoration_page_desc = gladexml.get_widget("decoration_page_desc")
        
        ## buttons layout elements
        self.lucid_radio = gladexml.get_widget("lucid_radio")
        self.karmic_radio = gladexml.get_widget("karmic_radio")
        self.osx_radio = gladexml.get_widget("osx_radio")
        self.custom_radio = gladexml.get_widget("custom_radio")
        self.apply_layout_btn = gladexml.get_widget("metacity_apply_layout_btn")
        self.apply_layout_entry = gladexml.get_widget("metacity_apply_layout_entry")
        self.get_current_layout()
        self.apply_layout_entry.set_text(self.layout)
        
        self.statbar = gladexml.get_widget("statusbar")
        dic = {"on_metacity_addbtn_clicked" : self.on_metacity_addbtn_clicked,
               "on_metacity_applybtn_clicked" : self.apply_metacity_theme,
               "on_metacity_delbtn_clicked" : self.on_metacity_delbtn_clicked,
               "on_lucid_radio_toggled" : self.on_layout_changed,
               "on_karmic_radio_toggled" : self.on_layout_changed,
               "on_osx_radio_toggled" : self.on_layout_changed,
               "on_custom_radio_toggled" : self.on_layout_changed,
               "on_metacity_apply_layout_btn_clicked": self.apply_custom_layout,
               }
        gladexml.signal_autoconnect(dic)

        ## for threads
        self.progress_box = gladexml.get_widget("progress_box")
        self.progress_text = gladexml.get_widget("progress_box_text")
        self.main_progressbar = gladexml.get_widget("main_progressbar")
        self.metacity_scroll = gladexml.get_widget("metacity_list_scroll")
        self.metacity_container = gladexml.get_widget("metacity_container")
        ## setup the liststore model
        self.model = gtk.ListStore(str, str)

        self.metacityTree = gtk.TreeView()
        self.metacityTree.set_model(self.model)
        renderer = gtk.CellRendererText()
        titleColumn = gtk.TreeViewColumn(_("Name"), renderer, text=0)
        titleColumn.set_min_width(200)
        pathColumn = gtk.TreeViewColumn()

        self.metacityTree.append_column(titleColumn)
        self.metacityTree.append_column(pathColumn)

        ## setup the scrollview
        self.columns = self.metacityTree.get_columns()
        self.columns[0].set_sort_column_id(1)
        self.columns[1].set_visible(0)
        self.metacity_scroll.add(self.metacityTree)

        self.decoration_page_img.set_from_file(config.img_path+"/decoration.png")
        self.decoration_page_desc.set_text(_("Window decoration :\nManage and install your Metacity/Emerald themes"))
        self.metacity_gest_info.set_text(_("Available themes list"))

        ## start the listing
        ## iconview signal
        self.metacityTree.connect('cursor-changed',self.get_model)
        self.metacityTree.connect('button-press-event',self.check_double_click)
        self.list_metacity_themes()
        
    def get_current_layout(self):
        liste = ('osx','lucid','karmic')
        for key in liste:
            value = self.layout_dic[key]
            if value == self.layout:
                self.layout_model = key
            else:
                continue
        if not self.layout_model:
            self.layout_model = 'custom'
        active_radio = getattr(self,'%s_radio' % self.layout_model)
        active_radio.set_active(True)        
    
    def on_layout_changed(self,widget):
        name = widget.name.split('_')[0]
        for key,value in self.layout_dic.items():
            if key == name:
                self.layout = value
        layout = self.gclient.get_string('/apps/metacity/general/button_layout')
        self.apply_layout_entry.set_text(self.layout)
        return self.apply_layout()
    
    def apply_layout(self):
        self.gclient.set_string('/apps/metacity/general/button_layout', self.layout)
        
    def apply_custom_layout(self,widget):
        layout = self.apply_layout_entry.get_text()
        if layout == "":
            return
        self.layout = layout
        self.layout_model = 'custom'
        self.custom_radio.set_active(True)
        return self.apply_layout()
    
    def on_metacity_addbtn_clicked(self,widget):
        dialog = create_filechooser_open((_("Choose a tar/bz2/gz file")),["*.gz","*.bz2","*.tar","*.zip","*.rar"])
        result = dialog.run()
        if result != gtk.RESPONSE_OK:
            dialog.destroy()
            return
        ## if ok
        self.metacity_archive =  dialog.get_filename()
        dialog.destroy()
        if not os.path.exists(self.metacity_archive):
            print "metacity theme not exist or corrupted \n"
            return
        theme_list = self.metacity_dict.add_item_archive(self.metacity_archive)
        if theme_list:
            return self.action_add_todic(theme_list)

    def action_add_todic(self,theme_list):
        if theme_list and theme_list.has_key('metacity'):
            metacity_theme_list = theme_list['metacity']
            for destination in metacity_theme_list.values():
                if destination:
                    item = self.metacity_dict.add_item_system(destination)
                    if item:
                        self.add_metacity(item)
                        name = item.name
                if item:
                    self.metacity_dict.set_active_item(name)
                    make_metacity_preview(self.metacity_container, os.path.basename(item.path))
                    path = self.model[-1].path
                    self.metacityTree.set_cursor(path)
        else:
            "no metacity themes to install"
            return

    def list_metacity_themes(self):
        for item in self.metacity_dict.values():
            self.add_metacity(item)

    def add_metacity(self,item):
        ## add theme to the listStore
        self.model.append([item.name,item.path])

    def get_model(self,widget=None):
        """Action to get the information theme metacity"""
        selected = self.metacityTree.get_selection()
        self.iter = selected.get_selected()[1]
        ## else extract needed metacity's infos
        self.metacity_thname = self.model.get_value(self.iter, 0)
        ## return only theme name and description then extract infos from hash
        self.metacity_thdir = self.model.get_value(self.iter, 1)
        # print in the gui
        make_metacity_preview(self.metacity_container, os.path.basename(self.metacity_thdir))
        self.statbar.push(1,_("Selected metacity theme : %s") % self.metacity_thname)

    def apply_metacity_theme(self,widget=None,dir=None):
        if dir:
            self.metacity_thdir = dir
            self.metacity_thname = dir
        if not self.metacity_thdir:
            print "no theme selected..."
            return
        self.metacity_dict.set_active_item(self.metacity_thname)
        self.statbar.push(1,(_("Metacity theme  %s successfully activated") % self.metacity_thname))

    def on_metacity_delbtn_clicked(self,widget):
        confirm = yesno((_("Remove metacity theme")),(_("Are you sure you want to delete the metacity Theme \n%s ?") % self.metacity_thname))
        if confirm == "No":
            return
        self.metacity_dict.del_item(self.metacity_thname)
        self.model.remove(self.iter)
        self.statbar.push(1,(_("metacity theme %s removed successfully") % self.metacity_thname))

    def check_double_click(self, widget, event):
        if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            self.get_model()
            self.apply_metacity_theme()
