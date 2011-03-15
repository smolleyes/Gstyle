#!/usr/bin/python
#-*- coding: UTF-8 -*-
import os
from shutil import copytree,rmtree
import gtk
import config

from functions import yesno
from functions import create_filechooser_open
from config import _


class EmeraldGui(object):
    def __init__(self,gladexml,emerald_dict):
        ## load buttons and attach signals
        self.emerald_dict = emerald_dict

        self.emerald_addbtn = gladexml.get_widget("emerald_addbtn")
        self.emerald_applybtn = gladexml.get_widget("emerald_applybtn")
        self.emerald_delbtn = gladexml.get_widget("emerald_delbtn")
        self.statbar = gladexml.get_widget("statusbar")
        dic = {"on_emerald_addbtn_clicked" : self.on_emerald_addbtn_clicked,
               "on_emerald_applybtn_clicked" : self.apply_emerald_theme,
               "on_emerald_delbtn_clicked" : self.on_emerald_delbtn_clicked,
               }
        gladexml.signal_autoconnect(dic)

        ## for threads
        self.progress_box = gladexml.get_widget("progress_box")
        self.progress_text = gladexml.get_widget("progress_box_text")
        self.main_progressbar = gladexml.get_widget("main_progressbar")

        ## setup the liststore model
        self.model = gtk.ListStore(str,gtk.gdk.Pixbuf, str, str, str, str, str, str)

        ## setup the iconview
        self.emerald_iconview = gtk.IconView(model=self.model)
        self.emerald_iconview.set_pixbuf_column(1)
        self.emerald_iconview.set_text_column(0)
        self.emerald_iconview.set_item_width(225);
        self.emerald_iconview.set_selection_mode('single')
        self.emerald_iconview.set_reorderable(1)
        ## iconview signal
        self.emerald_iconview.connect('selection_changed',self.get_model)
        self.emerald_iconview.connect('button-press-event',self.check_double_click)

        self.emerald_gest_info = gladexml.get_widget("emerald_gest_info")
        self.emerald_gest_viewer = gladexml.get_widget("emerald_gest_viewer")
        self.emerald_dret_label = gladexml.get_widget("emerald_dret_label")
        self.emerald_applybtn =  gladexml.get_widget("emerald_applybtn")
        self.emerald_addbtn =  gladexml.get_widget("emerald_addbtn")
        self.emerald_delbtn =  gladexml.get_widget("emerald_delbtn")
        self.decoration_page_img = gladexml.get_widget("decoration_page_img")
        self.decoration_page_desc = gladexml.get_widget("decoration_page_desc")

        self.decoration_page_img.set_from_file(config.img_path+"//decoration.png")
        self.decoration_page_desc.set_text(_("Window decoration :\nManage and install your metacity/emerald themes"))
        self.emerald_gest_info.set_text(_("Available themes list"))

        ## add the iconview
        self.emerald_gest_viewer.add(self.emerald_iconview)
        self.list_emerald_themes()

    def on_emerald_addbtn_clicked(self,widget):
        dialog = create_filechooser_open((_("Choose a .emerald file")),["*.emerald"])
        result = dialog.run()
        if result != gtk.RESPONSE_OK:
            dialog.destroy()
            return
        ## if ok
        archive =  dialog.get_filename()
        dialog.destroy()
        if not os.path.exists(archive):
            print "Emerald theme not exist or corrupted \n"
            return
        return self.get_theme_list(archive)
        
    def get_theme_list(self,archive):
        theme_list = self.emerald_dict.add_item_archive(archive)
        if theme_list and theme_list.has_key('emerald'):
            return self.action_add_todic(theme_list)
        else:
            print "no emerald theme in this file... %s " % archive
            return
    
    def action_add_todic(self,theme_list):
        if theme_list and theme_list.has_key('emerald'):
            emerald_themes_list = theme_list['emerald']
            for p in emerald_themes_list.items():
                destination = p[1]
                if destination:
                    item = self.emerald_dict.add_item_system(destination)
                    if item:
                        self.add_emerald(item)
                        name = item.name
                else:
                    "no emerald themes to install"
            path = self.model[-1].path
            self.emerald_iconview.select_path(path)
            self.emerald_iconview.set_cursor(path)
            self.emerald_dict.active_item(name)

    def list_emerald_themes(self):
        for item in self.emerald_dict.values():
            self.add_emerald(item)

    def add_emerald(self,item):
        img = gtk.gdk.pixbuf_new_from_file_at_scale(item.img_path, 150, 150 , 1)

        ## then add it to the iconview
        self.iter = self.model.append()
        self.model.set(self.iter,
        0, item.name,
        1, img,
        2, item.path,
        3, item.creator,
        4, item.description,
        5, item.theme_version,
        6, item.suggested,
        7, item.version,
        )


    def get_model(self,widget=None):
        """Action to get the information theme emerald"""
        selected = self.emerald_iconview.get_selected_items()
        ## check if path exist (or problems when clicking between rows..)
        try:
            row_index = selected[0]
        except:
             return

        ## else extract needed emerald's infos
        self.iter = self.model.get_iter(row_index)
        self.emerald_thname = self.model.get_value(self.iter, 0)
        ## return only theme name and description
        ## then extract infos from hash
        self.emerald_thdir = self.model.get_value(self.iter, 2)
        self.emerald_creator = self.model.get_value(self.iter, 3)
        self.emerald_description = self.model.get_value(self.iter, 4)
        self.emerald_theme_version = self.model.get_value(self.iter, 5)
        self.emerald_suggested = self.model.get_value(self.iter, 6)
        self.emerald_version = self.model.get_value(self.iter, 7)

        # print in the gui
        self.emerald_gest_info.set_text(_('Author : %(author)s \n\
Version : %(version)s \n\
Suggested gtk/Qt theme : %(suggested)s \n\
Description : %(description)s') % {"author":self.emerald_creator,
                                 "version":self.emerald_theme_version,
                                 "suggested":self.emerald_suggested,
                                 "description":self.emerald_description })

        self.statbar.push(1,(_("Selected emerald theme : %s") % self.emerald_thname))

    def apply_emerald_theme(self,widget=None,dir=None):
        if dir:
            self.emerald_thname = dir
        print "Activating emerald theme : "+self.emerald_thname
        self.emerald_dict.active_item(self.emerald_thname)
        self.statbar.push(1, _("Emerald theme \"%s\" successfully activated") % self.emerald_thname)

    def on_emerald_delbtn_clicked(self,widget):
        confirm = yesno((_("Remove emerald theme")),(_("Are you sure you want to delete the Emerald Theme \n%s ?") % self.emerald_thname))
        if confirm == "No":
            return
        print
        self.emerald_dict.del_item(self.emerald_thname)
        self.model.remove(self.iter)
        self.statbar.push(1,(_("Emerald theme %s removed successfully") % self.emerald_thname))
        
    def check_double_click(self, widget, event):
        if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            self.get_model()
            self.apply_emerald_theme()

