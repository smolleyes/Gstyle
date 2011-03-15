#!/usr/bin/env python
#-*- coding: UTF-8 -*-
import os
import config
from glob import glob
import ConfigParser
import re
import gtk
from shutil import rmtree,copytree
import urllib2

#Module gstyle
from functions import theme_downloader
from functions import refresh_themes_download
from functions import get_theme_from_html
from functions import yesno
from functions import create_filechooser_open
from config import _

import config
from functions import geturl

compiz_config = config.compizConfig
cubemodels_home_srcdir = config.cubemodels_srcdir
cubemodels_index_url = config.cubemodels_index_url
cubemodels_url_dir = config.cubemodels_url_dir
compiz_config = config.compizConfig

class CubemodelsGui(object):
    def __init__(self,gladexml,cubemodels_dict):
        ## load buttons and attach signals
        self.cubemodels_dict = cubemodels_dict

        self.cubemodels_manage_scroll = gladexml.get_widget("cubemodels_manage_scroll")
        self.cubemodels_manage_info = gladexml.get_widget("cubemodels_manage_info")
        self.cubemodels_manage_info.set_text(_("Installed cubemodels theme list"))
        ## cubemodels notebook page image
        self.cubemodels_page_img = gladexml.get_widget("cubemodels_page_img")
        self.cubemodels_page_img.set_from_file("%s/cubemodels.png" % config.img_path)
        ## cubemodels top description
        self.cubemodels_page_label = gladexml.get_widget("cubemodels_page_label")
        self.cubemodels_page_label.set_text(_("cubemodels : \nOrganize, create or download cubemodels themes...\n"))

        self.cubemodels_applybtn = gladexml.get_widget('cubemodels_applybtn')
        self.cubemodels_delbtn = gladexml.get_widget('cubemodels_delbtn')
        self.cubemodels_download_scroll = gladexml.get_widget('cubemodels_download_scroll')
        self.cubemodels_download_info = gladexml.get_widget('cubemodels_download_info')
        self.cubemodels_download_info.set_text(_("Click the refresh button to update the theme list"))

        ## creation
        self.cubemodel_create_name = gladexml.get_widget('cubemodel_create_name')
        self.cubemodel_create_imgpath = gladexml.get_widget('cubemodel_create_imgpath')
        self.cubemodels_chooseimg_btn = gladexml.get_widget('cubemodels_chooseimg_btn')
        self.create_cubemodel_btn = gladexml.get_widget('create_cubemodel_btn')

        self.statbar = gladexml.get_widget("statusbar")
        self.progress = gladexml.get_widget("cubemodels_down_progress")
        dic = {"on_cubemodels_addbtn_clicked" : self.action_add,
               "on_cubemodels_applybtn_clicked" : self.action_apply,
               "on_cubemodels_delbtn_clicked" : self.action_del,
               "on_cubemodels_refreshbtn_clicked" : self.action_refresh,
               "on_cubemodels_downbtn_clicked" : self.action_download,
               "on_cubemodels_chooseimg_btn_clicked" : self.action_chooseimg,
               "on_create_cubemodel_btn_clicked" : self.action_create,
               }
        gladexml.signal_autoconnect(dic)

        ## gui
        self.model = gtk.ListStore(str,gtk.gdk.Pixbuf,str,str)
        self.cubemodels_iconview = gtk.IconView(model=self.model)
        self.cubemodels_notebook = gladexml.get_widget("cubemodel_notebook")

        # Setup cubemodel iconview
        self.cubemodels_iconview.set_pixbuf_column(1)
        self.cubemodels_iconview.set_text_column(0)
        ## options
        self.cubemodels_iconview.set_columns(0)
        self.cubemodels_iconview.set_selection_mode('single')
        self.cubemodels_iconview.set_reorderable(1)


        self.cubemodels_iconview.connect('selection_changed',self.get_model)
        self.cubemodels_iconview.connect('button-press-event',self.check_double_click)
        self.cubemodels_manage_scroll.add(self.cubemodels_iconview)

        ############################################
        # download model
         ## gui
        self.cubemodels_down_model = gtk.ListStore(gtk.gdk.Pixbuf,str,str)
        self.cubemodels_down_iconview = gtk.IconView(model=self.cubemodels_down_model)

        # Setup cubemodel iconview
        self.cubemodels_down_iconview.set_pixbuf_column(0)
        self.cubemodels_down_iconview.set_text_column(1)
        ## options
        self.cubemodels_down_iconview.set_columns(0)
        self.cubemodels_down_iconview.set_selection_mode('single')
        self.cubemodels_down_iconview.set_reorderable(1)

        self.cubemodels_down_iconview.connect('selection_changed', self.get_down_model)
        self.cubemodels_download_scroll.add(self.cubemodels_down_iconview)

        self.check_conf()

    def add_model(self,item):
        picture = item.picture
        if not os.path.exists(picture):
            return
        gtk.ACCEL_LOCKED
        img = gtk.gdk.pixbuf_new_from_file_at_scale(picture,  100, 100, 1)

        self.iter = self.model.append()
        self.model.set(self.iter,
                       0, item.name,
                       1, img,
                       2, item.path,
                       3, item.ini,
                       )

    def get_model(self,widget=None):
        selected = self.cubemodels_iconview.get_selected_items()
        ## check if path exist (or problems when clicking between rows..)
        try:
            row_index = selected[0]
        except:
             return
        self.iter = self.model.get_iter(row_index)
        self.item_name = self.model.get_value(self.iter,0)
        self.item_path = self.model.get_value(self.iter,2)
        self.item_ini = self.model.get_value(self.iter,3)
        self.statbar.push(1,(_("Selected cubemodels theme : %s") % self.item_name))

    def get_down_model(self,widget):
        selected = self.cubemodels_down_iconview.get_selected_items()
        ## check if path exist (or problems when clicking between rows..)
        try:
            row_index = selected[0]
        except:
             return
        self.down_iter = self.cubemodels_down_model.get_iter(row_index)
        self.down_name = self.cubemodels_down_model.get_value(self.down_iter,1)
        self.down_link = self.cubemodels_down_model.get_value(self.down_iter,2)
        self.statbar.push(1,(_("Selected cubemodels download : %s") % self.down_name))

    def action_add(self,widget):
        filterlist = ["*.tar.lzma"]
        dialog = create_filechooser_open((_("Choose a tar.lzma file")),filterlist)
        result = dialog.run()
        if result != gtk.RESPONSE_OK:
            dialog.destroy()
            return
        ## if ok
        archive =  dialog.get_filename()
        dialog.destroy()
        if not os.path.exists(archive):
            print "cubemodel theme non-existent or corrupt \n"
            return
        return self.get_theme_list(archive)
        
    def get_theme_list(self,archive):
        theme_list = self.cubemodels_dict.add_item_archive(archive)
        if theme_list and theme_list.has_key('cubemodels'):
            return self.action_add_todic(theme_list)
        else:
            print "no cubemodel theme in this file... %s " % archive
            return
        
    def action_add_todic(self,theme_list):
        if theme_list and theme_list.has_key('cubemodels'):
            cubemodels_themes_list = theme_list['cubemodels']
            if cubemodels_themes_list:
                for p in cubemodels_themes_list.items():
                    name = p[0]
                    if name:
                        item = self.cubemodels_dict.add_item_system(name)
                        if item:
                            self.cubemodels_dict.edit_theme_ini(item)
                            self.add_model(item)
                if item:
                    self.cubemodels_dict.active_item(item.name)
                    path = self.model[-1].path
                    self.cubemodels_iconview.select_path(path)
                    self.cubemodels_iconview.set_cursor(path)
            else:
                return

    def action_apply(self,widget=None,name=None):
        if name:
            self.item_name = name
        print "activating cubemodel : %s " % name
        self.cubemodels_dict.active_item(self.item_name)
        self.statbar.push(1,_("Cubemodel theme %s successfully activated" % self.item_name))

    def action_del(self,widget):
        confirm = yesno((_("Remove cubemodels themes")),\
                (_("Are you sure you want to delete the cubemodels Theme \n %s ?") % self.item_name))
        if confirm == "No":
            return
        self.cubemodels_dict.del_item(self.item_name)
        self.statbar.push(1,_("Cubemodel theme %s successfully removed" % self.item_name))
        self.model.remove(self.iter)

    def list_cubemodels_themes(self):
        for item in self.cubemodels_dict.values():
            self.add_model(item)

    def action_chooseimg(self,widget):
        dialog = create_filechooser_open((_("Choose a thumbnail file")),["*.png","*.jpeg","*.jpg"])
        result = dialog.run()
        if result != gtk.RESPONSE_OK:
            dialog.destroy()
            return
        ## if ok
        img =  dialog.get_filename()
        dialog.destroy()
        if not os.path.exists(img):
            print "thumbnail image do not exist %s \n" % img
            return

        self.cubemodel_create_imgpath.set_text(img)

    def action_create(self,widget):
        """ Retrieve cubemodel name and img path then start cubemodel
        theme creation"""

        ## check name and img path
        name = self.cubemodel_create_name.get_text()
        img_path = self.cubemodel_create_imgpath.get_text()
        if name:
            print "Selected cubemodel name : "+name+""
        else:
            print "Please, select a name for your theme"
            return
        if img_path:
            print "cubemodel img path : "+img_path+""
            if not os.path.exists(img_path):
                print "Selected cubemodel path is wrong : "+img_path+""
                return
        else:
             print "Please, select an image for your theme"
             return
        ## check all elements before creation
        self.cubemodels_dict.create_theme(name, img_path)
        item = self.cubemodels_dict.get(name)
        self.add_model(item)
        self.cubemodels_dict.active_item(item.name)

    def action_download(self,widget):
        archive = geturl(self.down_link, '/tmp/'+self.down_name+'.tar.lzma', self.progress)
        if archive:
            install = self.get_theme_list(archive)
            if install:
                self.action_refresh()
        else:
            print "can't download archive %s" % self.down_link
            return

    def action_refresh(self,widget=None):
        theme_list = get_theme_from_html(cubemodels_index_url)
        self.cubemodels_down_model.clear()
        count = refresh_themes_download(theme_list, self.cubemodels_down_model, cubemodels_home_srcdir)
        self.cubemodels_download_info.set_text(_("%d available themes") % count)

    def check_conf(self):
        if not os.path.exists("/usr/local/lib/compiz/libcubemodel.so") and not os.path.exists(config.homedir+"/.compiz/plugins/libcubemodel.so") or not os.path.exists(config.compizConfig):
            self.cubemodels_notebook.set_sensitive(0)
            self.cubemodels_page_label.set_text("""Page desactivated !

The cubemodel plugin and/or compiz are not installed, you can build it from Git sources or with the following script :

http://forum.ubuntu-fr.org/viewtopic.php?id=259077&p=1 \n""")
        else:
            ## check activation et presence du plugin cube et cubemodel
            if compiz_config:
                self.cubemodels_dict.check_plugins()
            else:
                print "Impossible d'ouvrir le fichier %s, compiz pas installe ?" % compiz_config
                return
            ## start listing
            self.list_cubemodels_themes()
            
    def check_double_click(self, widget, event):
        if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            self.get_model()
            self.action_apply()
