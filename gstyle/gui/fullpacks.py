#!/usr/bin/env python
#-*- coding: UTF-8 -*-
import os
import config
import gtk
import subprocess
from xml.dom import minidom
import gobject
import re
import subprocess

#Module gstyle
from functions import refresh_themes_download
from functions import get_theme_from_html
from functions import yesno
from functions import error_dialog
from functions import create_filechooser_open
from functions import make_metacity_preview
from functions import ComboBox
from functions import create_archive
from config import _
from functions import geturl
from functions import gthread
from shutil import copyfile,rmtree
import tempfile

fullpack_home_srcdir = config.fullpacks_srcdir
fullpack_index_url = config.fullpacks_index_url
fullpack_url_dir = config.fullpacks_url_dir
main_path = config.exec_path

class FullpackGui(object):
    def __init__(self,gladexml,gstyle_obj):
        ## load buttons and attach signals
        self.gstyle_obj = gstyle_obj
        self.fullpack_dict = gstyle_obj.fullpack_dict
        self.gtk_dict = self.gstyle_obj.gtk_dict
        self.wallstat_dict = self.gstyle_obj.wallpapers_dict.get_dict_static_w()
        self.walldyn_dict = self.gstyle_obj.wallpapers_dict.get_dict_dynamique_w()
        self.icons_dict = self.gstyle_obj.icon_dict
        self.emerald_dict = self.gstyle_obj.emerald_dict
        self.mouse_dict = self.gstyle_obj.mouse_dict
        self.cubemodel_dict = self.gstyle_obj.cubemodels_dict
        self.metacity_dict = self.gstyle_obj.metacity_dict
        
        self.icon_obj = self.gstyle_obj.gtk_gui.icon_obj
        self.gtk_obj = self.gstyle_obj.gtk_gui.gtk_obj
        self.wallpaper_obj = self.gstyle_obj.gtk_gui.wallpaper_obj
        self.mouse_obj = self.gstyle_obj.gtk_gui.mouse_obj
        self.metacity_obj = self.gstyle_obj.gtk_gui.metacity_obj
        self.emerald_obj = self.gstyle_obj.gtk_gui.emerald_obj
        self.cubemodel_obj = self.gstyle_obj.gtk_gui.cubemodel_obj
        
        self.fpack_dic = {}
        self.fpack_dic_copy = {}

        self.fullpack_save_btn = gladexml.get_widget("fullpack_save_btn")
        self.fullpack_create_btn = gladexml.get_widget("fpack_create_btn")
        self.fullpack_manage_scroll = gladexml.get_widget("fullpack_gest_viewer")
        self.fullpack_manage_info = gladexml.get_widget("fullpack_gest_label")
        self.fullpack_manage_info.set_text(_("Installed fullpack theme list"))
        ## fullpack notebook page image
        self.fullpack_page_img = gladexml.get_widget("fullpack_page_img")
        self.fullpack_page_img.set_from_file("%s/fullpack-icon.png" % config.img_path)
        ## fullpack top description
        self.fullpack_page_label = gladexml.get_widget("fullpack_page_label")
        self.fullpack_page_label.set_text(_("Fullpacks : \nOrganize, create or download fullpack themes...\n"))

        self.fullpack_download_scroll = gladexml.get_widget('fullpack_download_scroll')
        self.fullpack_download_info = gladexml.get_widget('fullpack_download_info')
        self.fullpack_download_info.set_text(_("Click the refresh button to update the theme list"))
        
        ## progress
        self.progress_box = gladexml.get_widget("progress_box")
        self.progress_text = gladexml.get_widget("progress_box_text")
        self.main_progressbar = gladexml.get_widget("main_progressbar")

        self.statbar = gladexml.get_widget("statusbar")
        self.progress = gladexml.get_widget("fullpack_download_pbar")

        ## gui
        self.fullpack_name_scroll = gladexml.get_widget("fullpack_gest_txtlist")
        self.fullpack_name_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        self.model = gtk.ListStore(gtk.gdk.Pixbuf,str,str,str)
        self.fullpack_name_tree = gtk.TreeView()
        self.fullpack_name_tree.set_model(self.model)
        renderer = gtk.CellRendererText()
        img_renderer = gtk.CellRendererPixbuf()
        pixColumn = gtk.TreeViewColumn(_("Preview"), img_renderer)
        pixColumn.set_fixed_width(200)
        self.fullpack_name_tree.append_column(pixColumn)
        pixColumn.add_attribute(img_renderer, 'pixbuf', 0)
        titleColumn = gtk.TreeViewColumn(_("Fullpack name"),renderer, text=1)
        titleColumn.set_min_width(200)
        pathColumn = gtk.TreeViewColumn()
        iniColumn = gtk.TreeViewColumn()

        self.fullpack_name_tree.append_column(titleColumn)
        self.fullpack_name_tree.append_column(pathColumn)
        self.fullpack_name_tree.append_column(iniColumn)

        ## setup the scrollview
        self.name_list_columns = self.fullpack_name_tree.get_columns()
        self.name_list_columns[1].set_visible(0)
        self.name_list_columns[2].set_visible(0)
        self.name_list_columns[3].set_visible(0)
        self.fullpack_name_scroll.add_with_viewport(self.fullpack_name_tree)
        self.fullpack_name_scroll.show()

        self.fullpack_name_tree.connect('cursor-changed',self.get_model)
        self.fullpack_name_tree.connect('button-press-event',self.check_double_click)

        ## the fullpack editor
        self.fpack_gtk_selector = gladexml.get_widget('fpack_gtk_selector')
        self.fpack_gtk_selector.set_model(self.gtk_obj.model)
        self.fpack_icon_selector = gladexml.get_widget('fpack_icon_selector')
        self.fpack_icon_selector.set_model(self.icon_obj.model)
        self.fpack_metacity_selector = gladexml.get_widget('fpack_metacity_selector')
        self.fpack_metacity_selector.set_model(self.metacity_obj.model)
        self.fpack_emerald_selector = gladexml.get_widget('fpack_emerald_selector')
        self.fpack_emerald_selector.set_model(self.emerald_obj.model)
        self.fpack_wallstat_selector = gladexml.get_widget('fpack_wallstat_selector')
        self.fpack_wallstat_selector.set_model(self.wallpaper_obj.wallstats_model)
        self.fpack_walldyn_selector = gladexml.get_widget('fpack_walldyn_selector')
        self.fpack_walldyn_selector.set_model(self.wallpaper_obj.walldyns_model)
        self.fpack_mouse_selector = gladexml.get_widget('fpack_mouse_selector')
        self.fpack_mouse_selector.set_model(self.mouse_obj.model)
        self.fpack_cubemodel_selector = gladexml.get_widget('fpack_cubemodel_selector')
        self.fpack_cubemodel_selector.set_model(self.cubemodel_obj.model)

        ## preview images
        self.fpack_gtk_img = gladexml.get_widget('fpack_gtk_img')
        self.fpack_gtk_preview = gladexml.get_widget('fpack_gtk_preview')
        self.fpack_icon_img = gladexml.get_widget('fpack_icon_img')
        self.metacity_previewbox = gladexml.get_widget('metacity_previewbox')
        self.fpack_emerald_img = gladexml.get_widget('fpack_emerald_img')
        self.fpack_wallstat_img = gladexml.get_widget('fpack_wallstat_img')
        self.fpack_walldyn_img = gladexml.get_widget('fpack_walldyn_img')
        self.fpack_mouse_img = gladexml.get_widget('fpack_mouse_img')
        self.fpack_cubemodel_img = gladexml.get_widget('fpack_cubemodel_img')

        ## entry
        self.fpack_name_entry = gladexml.get_widget('fpack_name_entry')
        self.fpack_author_entry = gladexml.get_widget('fpack_author_entry')
        self.fpack_licence_entry = gladexml.get_widget('fpack_licence_entry')
        self.fpack_website_entry = gladexml.get_widget('fpack_website_entry')

        ## create
        self.fpack_create_imgpath = gladexml.get_widget('fpack_create_imgpath')
        self.fpack_chooseimg_btn = gladexml.get_widget('fpack_chooseimg_btn')
        
        ############################################
        # download model
         ## gui
        self.fullpack_down_model = gtk.ListStore(gtk.gdk.Pixbuf,str,str)
        self.fullpack_down_iconview = gtk.IconView(model=self.fullpack_down_model)

        # Setup cubemodel iconview
        self.fullpack_down_iconview.set_pixbuf_column(0)
        self.fullpack_down_iconview.set_text_column(1)
        ## options
        self.fullpack_down_iconview.set_columns(0)
        self.fullpack_down_iconview.set_selection_mode('single')
        self.fullpack_down_iconview.set_reorderable(1)

        self.fullpack_down_iconview.connect('selection_changed', self.get_down_model)
        self.fullpack_download_scroll.add(self.fullpack_down_iconview)
        ## start listing
        self.fullpack_save_btn.set_sensitive(0)
        ## active comboboxes
        self.gtk_combo = ComboBox(self.fpack_gtk_selector)
        self.icons_combo = ComboBox(self.fpack_icon_selector)
        self.metacity_combo = ComboBox(self.fpack_metacity_selector)
        self.emerald_combo = ComboBox(self.fpack_emerald_selector)
        self.wallstat_combo = ComboBox(self.fpack_wallstat_selector)
        self.walldyn_combo = ComboBox(self.fpack_walldyn_selector)
        self.mouse_combo = ComboBox(self.fpack_mouse_selector)
        self.cubemodel_combo = ComboBox(self.fpack_cubemodel_selector)

        dic = {"on_fullpack_add_btn_clicked" : self.action_add,
               "on_fullpack_apply_btn_clicked" : self.action_apply,
               "on_fullpack_del_btn_clicked" : self.action_del,
               "on_fullpack_refresh_btn_clicked" : self.action_refresh,
               "on_fullpack_down_btn_clicked" : self.action_download,
               "on_fullpack_save_btn_clicked" : self.action_save,
               "on_fpack_gtk_selector_changed" : self.on_select_gtk,
               "on_fpack_metacity_selector_changed" : self.on_select_metacity,
               "on_fpack_icon_selector_changed" : self.on_select_icon,
               "on_fpack_emerald_selector_changed" : self.on_select_emerald,
               "on_fpack_wallstat_selector_changed" : self.on_select_wallstat,
               "on_fpack_walldyn_selector_changed" : self.on_select_walldyn,
               "on_fpack_mouse_selector_changed" : self.on_select_mouse,
               "on_fpack_cubemodel_selector_changed" : self.on_select_cubemodel,
               "on_fpack_create_btn_clicked": self.action_create,
               "on_fpack_chooseimg_btn_clicked": self.action_chooseimg,
               "on_fpack_gtk_reset_clicked": self.reset_combobox,
               "on_fpack_icons_reset_clicked": self.reset_combobox,
               "on_fpack_metacity_reset_clicked": self.reset_combobox,
               "on_fpack_wallstat_reset_clicked": self.reset_combobox,
               "on_fpack_walldyn_reset_clicked": self.reset_combobox,
               "on_fpack_mouse_reset_clicked": self.reset_combobox,
               "on_fpack_cubemodel_reset_clicked": self.reset_combobox,
               "on_fpack_emerald_reset_clicked": self.reset_combobox,
               "on_fpack_export_btn_clicked": self.export_fullpack,
               }
        gladexml.signal_autoconnect(dic)

        self.list_fullpack_themes()

    def add_model(self,item):
        picture = item.picture
        if not os.path.exists(picture):
            return
        img = gtk.gdk.pixbuf_new_from_file_at_scale(picture,  100, 100, 1)

        self.iter = self.model.append()
        self.model.set(self.iter,
                       0, img,
                       1, item.name,
                       2, item.srcdir,
                       3, item.ini,
                       )

    def action_add(self,widget):
        filterlist = ["*.tar.lzma"]
        dialog = create_filechooser_open((_("Choose a fullpack archive file")),filterlist)
        result = dialog.run()
        if result != gtk.RESPONSE_OK:
            dialog.destroy()
            return
        ## if ok
        archive =  dialog.get_filename()
        dialog.destroy()
        if not os.path.exists(archive):
            print "Fullpack theme non-existent or corrupted \n"
        return self.get_theme_list(archive)

    def get_theme_list(self,archive):
        theme_list = self.fullpack_dict.add_item_archive(archive)
        if theme_list:
            return self.action_add_todic(theme_list)

    def action_apply(self,widget=None):
        self.fullpack_dict.active_item(self.item_name,self.gstyle_obj)
        self.statbar.push(1,_("Fullpack %s successfully activated" % self.item_name))

    def action_del(self,widget):
        confirm = yesno((_("Remove fullpack themes")),\
                (_("Are you sure you want to delete the fullpack Theme \n %s ?") % self.item_name))
        if confirm == "No":
            return
        self.fullpack_dict.del_item(self.item_name)
        self.statbar.push(1,_("Fullpack theme %s successfully removed" % self.item_name))
        self.model.remove(self.iter)

    def list_fullpack_themes(self):
        for item in self.fullpack_dict.values():
            self.add_model(item)

    def action_download(self,widget=None):
        archive = geturl(self.down_link, '/tmp/'+self.down_name+'.tar.lzma', self.progress)
        if archive:
            theme_list = self.get_theme_list(archive)
            if theme_list:
                self.action_refresh()
        else:
            print "can't download archive %s" % self.down_link
            return

    def action_refresh(self,widget=None):
        theme_list = get_theme_from_html(fullpack_index_url)
        self.fullpack_down_model.clear()
        count = refresh_themes_download(theme_list, self.fullpack_down_model, fullpack_home_srcdir)
        self.fullpack_download_info.set_text(_("%d available themes") % count)

    def get_model(self,widget=None):
        selected = self.fullpack_name_tree.get_selection()
        ## check if path exist (or problems when clicking between rows..)
        try:
            self.iter = selected.get_selected()[1]
        except:
            return
        self.item_name = self.model.get_value(self.iter,1)
        self.item_srcdir = self.model.get_value(self.iter,2)
        self.item_ini = self.model.get_value(self.iter,3)
        self.statbar.push(1,_("Selected fullpack theme : %s") % self.item_name)
        ## start fullpack preview
        self.fpack_dic = self.make_fullpack_dic()
        self.fpack_dic_copy = self.make_fullpack_dic()
        self.make_fullpack_preview()
        self.fullpack_save_btn.set_sensitive(0)

    def set_savebtn_state(self):
        new = self.fpack_dic_copy
        old = self.fpack_dic
        result = None
        for (key, value) in new.iteritems():
            try:
                if old[key] != value:
                    result = True
            except KeyError:
                ## corrupted file?
                return
        state = self.fullpack_save_btn.state
        if result:
            if state == gtk.STATE_INSENSITIVE:
                self.fullpack_save_btn.set_sensitive(1)
        else:
            if state == gtk.STATE_NORMAL:
                self.fullpack_save_btn.set_sensitive(0)

    def get_down_model(self,widget):
        selected = self.fullpack_down_iconview.get_selected_items()
        ## check if path exist (or problems when clicking between rows..)
        try:
            row_index = selected[0]
        except:
             return
        self.down_iter = self.fullpack_down_model.get_iter(row_index)
        self.down_name = self.fullpack_down_model.get_value(self.down_iter,1)
        self.down_link = self.fullpack_down_model.get_value(self.down_iter,2)
        self.statbar.push(1,(_("Selected fullpack download : %s") % self.down_name))

    def action_add_todic(self,theme_list):
        if theme_list and theme_list.has_key('fullpacks'):
            fpack_list = theme_list['fullpacks'].keys()
            for name in fpack_list:
                item = self.fullpack_dict.add_item_system(name)
                if item:
                    self.add_model(item)
                    ## Wallpaper
                    self.wallpaper_obj.action_add_todic(theme_list)
                    ## gtk
                    self.gtk_obj.action_add_todic(theme_list,1)
                    ## icons
                    self.icon_obj.action_add_todic(theme_list)
                    ## mouse
                    self.gstyle_obj.gtk_gui.mouse_obj.action_add_todic(theme_list)
                    ## metacity
                    self.gstyle_obj.gtk_gui.metacity_obj.action_add_todic(theme_list)
                    ## cubemodel
                    self.gstyle_obj.gtk_gui.cubemodel_obj.action_add_todic(theme_list)
                    ## emerald
                    self.gstyle_obj.gtk_gui.emerald_obj.action_add_todic(theme_list)

        self.action_refresh()

    def action_create(self,widget):
        #icon_theme = self.gstyle_obj.icon_dict.get_active_item()
        #mouse_theme = self.gstyle_obj.mouse_dict.get_active_item()
        #wallpaper = self.gstyle_obj.wallpapers_dict.get_active_item()
        #metacity = self.gstyle_obj.metacity_dict.get_active_item()
        pass
        
    def on_select_gtk(self,widget):
        gtk_name = self.fpack_gtk_selector.get_active_text()
        if gtk_name == "":
            return
        theme = self.gtk_dict.get(gtk_name)
        if not theme:
            self.fpack_dic_copy["gtk"] = ""
            self.fpack_gtk_img.set_from_stock("gtk-missing-image", gtk.ICON_SIZE_BUTTON)
            self.set_savebtn_state()
            return
        env = os.environ
        env["GTK2_RC_FILES"] = theme.rcfile
        subprocess.call(["python", main_path+"/imggen.py","/tmp/gtk-preview.png",theme.rcfile])
        try:
            pb = gtk.gdk.pixbuf_new_from_file("/tmp/gtk-preview.png")
        except Exception, ee:
            import traceback
            traceback.print_exc()
            return None
        if not pb is None:
            self.preview = pb
            self.fpack_gtk_img.set_from_pixbuf(pb)
        else:
            return None
        if not self.gtk_combo.getSelected() == 0:
            self.fpack_dic_copy["gtk"] = gtk_name
        else:
            self.fpack_dic_copy["gtk"] = ""
        self.set_savebtn_state()

    def on_select_metacity(self,widget):
        metacity_name = self.fpack_metacity_selector.get_active_text()
        if metacity_name == "":
            return
        theme = self.metacity_dict.get(metacity_name)
        if not theme:
            self.fpack_dic_copy["metacity"] = ""
            for item in self.metacity_previewbox.get_children():
                self.metacity_previewbox.remove(item)
            self.set_savebtn_state()
            return
        make_metacity_preview(self.metacity_previewbox, os.path.basename(theme.path))
        if not self.metacity_combo.getSelected() == 0:
            self.fpack_dic_copy["metacity"] = metacity_name
        else:
            self.fpack_dic_copy["metacity"] = ""
        self.set_savebtn_state()

    def on_select_icon(self,widget):
        icon_name = self.fpack_icon_selector.get_active_text()
        if icon_name == "":
            return
        theme = self.icons_dict.get(icon_name)
        if not theme:
            self.fpack_dic_copy["icons"] = ""
            self.fpack_icon_img.set_from_stock("gtk-missing-image", gtk.ICON_SIZE_BUTTON)
            self.set_savebtn_state()
            return
        extension = os.path.splitext(theme.picture)[1]
        if extension == '.svg':
            img = gtk.gdk.pixbuf_new_from_file_at_size(theme.picture, 60, 60)
        elif extension == '.png':
            gtk.ACCEL_LOCKED
            img = gtk.gdk.pixbuf_new_from_file_at_size(theme.picture, 60, 60 )
        else:
            return
        self.fpack_icon_img.set_from_pixbuf(img)
        if not self.icons_combo.getSelected() == 0:
            self.fpack_dic_copy["icons"] = icon_name
        else:
            self.fpack_dic_copy["icons"] = ""
        self.set_savebtn_state()

    def on_select_emerald(self,widget):
        emerald_name = self.fpack_emerald_selector.get_active_text()
        if emerald_name == "":
            return
        theme = self.emerald_dict.get(emerald_name)
        if not theme:
            self.fpack_dic_copy["emerald"] = ""
            self.fpack_emerald_img.set_from_stock("gtk-missing-image", gtk.ICON_SIZE_BUTTON)
            self.set_savebtn_state()
            return
        img = gtk.gdk.pixbuf_new_from_file_at_scale(theme.img_path, 100, 100, 1 )
        self.fpack_emerald_img.set_from_pixbuf(img)
        if not self.emerald_combo.getSelected() == 0:
            self.fpack_dic_copy["emerald"] = emerald_name
        else:
            self.fpack_dic_copy["emerald"] = ""
        self.set_savebtn_state()

    def on_select_wallstat(self,widget):
        name = self.fpack_wallstat_selector.get_active_text()
        if name == "":
            return
        wallpaper = None
        for item in self.wallstat_dict.values():
            if item.name == name:
                wallpaper = self.wallstat_dict[item.filename]
            else:
                continue
        if not wallpaper:
            self.fpack_dic_copy["wallstat"] = ""
            self.fpack_wallstat_img.set_from_stock("gtk-missing-image", gtk.ICON_SIZE_BUTTON)
            self.set_savebtn_state()
            return
        img = gtk.gdk.pixbuf_new_from_file_at_scale(wallpaper.filename, 100, 100, 1 )
        self.fpack_wallstat_img.set_from_pixbuf(img)
        self.set_savebtn_state()
        if not self.wallstat_combo.getSelected() == 0:
            self.fpack_dic_copy["wallstat"] = os.path.basename(wallpaper.filename)
        else:
            self.fpack_dic_copy["wallstat"] = ""
        self.set_savebtn_state()

    def on_select_walldyn(self,widget):
        name = self.fpack_walldyn_selector.get_active_text()
        if name == "":
            return
        wallpaper = None
        for item in self.walldyn_dict.values():
            if item.name == name:
                wallpaper = self.walldyn_dict[item.filename]
            else:
                continue
        if not wallpaper:
            self.fpack_dic_copy["walldyn"] = ""
            self.fpack_walldyn_img.set_from_stock("gtk-missing-image", gtk.ICON_SIZE_BUTTON)
            self.set_savebtn_state()
            return
        file = wallpaper.get_path_img()
        img = gtk.gdk.pixbuf_new_from_file_at_scale(file, 100, 100, 1 )
        self.fpack_walldyn_img.set_from_pixbuf(img)
        if not self.walldyn_combo.getSelected() == 0:
            self.fpack_dic_copy["walldyn"] = name
        else:
            self.fpack_dic_copy["walldyn"] = ""
        self.set_savebtn_state()


    def on_select_mouse(self,widget):
        name = self.fpack_mouse_selector.get_active_text()
        if name == "":
            return
        item = self.mouse_dict.get(name)
        if item:
            img = gtk.gdk.pixbuf_new_from_file(item.pic)
            self.fpack_mouse_img.set_from_pixbuf(img)
            self.fpack_dic_copy["mouse"] = item.name
            if self.mouse_combo.getSelectedIndex() >= 1:
                self.fpack_dic_copy["mouse"] = item.name
            else:
                self.fpack_dic_copy["mouse"] = ""
            self.set_savebtn_state()
        else:
            self.fpack_dic_copy["mouse"] = ""
            self.fpack_mouse_img.set_from_stock("gtk-missing-image", gtk.ICON_SIZE_BUTTON)
            self.set_savebtn_state()

    def on_select_cubemodel(self,widget):
        name = self.fpack_cubemodel_selector.get_active_text()
        if name == "":
            return
        item = self.cubemodel_dict.get(name)
        if item:
            img = gtk.gdk.pixbuf_new_from_file_at_scale(item.picture, 100, 100, 1)
            self.fpack_cubemodel_img.set_from_pixbuf(img)
            if not self.cubemodel_combo.getSelected() == 0:
                self.fpack_dic_copy["cubemodel"] = item.name
            else:
                self.fpack_dic_copy["cubemodel"] = ""
            self.set_savebtn_state()
        else:
            self.fpack_dic_copy["cubemodel"] = ""
            self.fpack_cubemodel_img.set_from_stock("gtk-missing-image", gtk.ICON_SIZE_BUTTON)
            self.set_savebtn_state()

    def make_fullpack_dic(self):
        file_obj = open(self.item_ini)
        xml_obj = minidom.parse(file_obj)
        file_obj.close()
        fpack_xmldic = {}

        types_element = ("packname","licence","author","link","gtk","metacity","icons","wallstat","walldyn",
                         "emerald","cubemodel","mouse")
        for type in types_element:
            fpack_xmldic[type] = ""
            try:
                value = self.get_value_tag("%s" % type,xml_obj)
            except:
                value =""
            fpack_xmldic[type] = value
        return fpack_xmldic

    def make_fullpack_preview(self):
        if self.fpack_dic:
            self.fpack_name_entry.set_text(self.fpack_dic["packname"])
            self.fpack_author_entry.set_text(self.fpack_dic["author"])
            self.fpack_website_entry.set_text(self.fpack_dic["link"])
            self.fpack_licence_entry.set_text(self.fpack_dic["licence"])
            self.active_combobox_items()

    def get_value_tag(self,name_tag,root_tag):
        tag = root_tag.getElementsByTagName(name_tag)
        if tag:
            tag = tag[0]
            return tag.firstChild.data
        else:
            return ""

    def active_combobox_items(self):
        self.fpack_create_imgpath.set_text('')
        ## search theme name and select the good path in combobox
        for key,value in self.fpack_dic_copy.items():
            if re.match('packname|link|licence|author|img',key):
                continue
            combo = getattr(self,'%s_combo' % key)
            if key == "wallstat":
                combo.setIndexFromString(os.path.splitext(value)[0])
            else:
                combo.setIndexFromString(value)

    def check_double_click(self, widget, event):
        if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            self.get_model()
            self.action_apply()

    def action_save(self,widget=None):
        name = self.fpack_name_entry.get_text()
        if name == "":
            error_dialog(_("Please enter a name for your theme"))
            return False
        self.new_theme = False
        licence = self.fpack_licence_entry.get_text()
        author = self.fpack_author_entry.get_text()
        link = self.fpack_website_entry.get_text()
        img = self.fpack_create_imgpath.get_text()
        ## check pack dir 
        fpack_srcdir = os.path.join(fullpack_home_srcdir,name)
        if self.fpack_dic.has_key('packname'):
            if self.fpack_dic['packname'] != name:
                ret = yesno("Save fullpack","The fullpack's name was changed, a new fullpack will be created")
                if ret == "No":
                    return False
                self.new_theme=True
        else:
            self.fpack_dic['packname'] = name
        
        if not os.path.exists(fpack_srcdir):
            self.new_theme=True
            if img == "":
                error_dialog(_("Please select a preview image for your theme"))
                return False
        
        self.fpack_dic_copy['packname'] = name
        self.fpack_dic_copy['link'] = link
        self.fpack_dic_copy['licence'] = licence
        self.fpack_dic_copy['author'] = author
        self.fpack_dic_copy['img'] = img
        
        item = self.fullpack_dict.gen_xml(self.fpack_dic_copy,self.new_theme)
        if self.new_theme:
            if item:
                self.add_model(item)
                self.statbar.push(1,(_("fullpack %s successfully created") % item.name))
                
        self.statbar.push(1,(_("fullpack %s successfully saved") % name))
        self.fpack_dic = {}
        for (key, value) in self.fpack_dic_copy.iteritems():
            self.fpack_dic[key] = value
        self.fullpack_save_btn.set_sensitive(0)
        return True
        
    def action_create(self,widget):
        self.new_theme = True
        self.fpack_dic = {}
        self.fpack_dic_copy = {}
        self.fpack_name_entry.set_text('')
        self.fpack_licence_entry.set_text('')
        self.fpack_author_entry.set_text('')
        self.fpack_website_entry.set_text('')
        self.fpack_create_imgpath.set_text('')
        self.gtk_combo.select(-1)
        self.icons_combo.select(-1)
        self.metacity_combo.select(-1)
        self.emerald_combo.select(-1)
        self.wallstat_combo.select(-1)
        self.walldyn_combo.select(-1)
        self.mouse_combo.select(-1)
        self.cubemodel_combo.select(-1)
        self.fullpack_save_btn.set_sensitive(1)
        
        ## detect active themes
        icon = self.gstyle_obj.icon_dict.get_active_item()
        if icon:
            self.fpack_dic_copy['icons'] = icon.dirname
        wallstat = self.gstyle_obj.wallpapers_dict.get_active_item()
        if wallstat:
            self.fpack_dic_copy['wallstat'] = wallstat.name
        gtk = self.gstyle_obj.gtk_dict.get_active_item()
        if gtk:
            self.fpack_dic_copy['gtk'] = gtk.dirname
        metacity = self.gstyle_obj.metacity_dict.get_active_item()
        if metacity:
            self.fpack_dic_copy['metacity'] = metacity.name
        walldyn = self.gstyle_obj.wallpapers_dict.get_active_item()
        if walldyn:
            self.fpack_dic_copy['walldyn'] = walldyn.name
        mouse = self.gstyle_obj.mouse_dict.get_active_item()
        if mouse:
            self.fpack_dic_copy['mouse'] = mouse.name
        cubemodel = self.gstyle_obj.cubemodels_dict.get_active_item()
        if cubemodel:
            self.fpack_dic_copy['cubemodel'] = cubemodel.name
        emerald = self.gstyle_obj.emerald_dict.get_active_item()
        if emerald:
            self.fpack_dic_copy['emerald'] = emerald.name
        ## activate items
        self.active_combobox_items()

    def action_chooseimg(self,widget):
        dialog = create_filechooser_open(_("Choose a thumbnail file"),["*.png"])
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
        self.fpack_create_imgpath.set_text(img)
        
    def reset_combobox(self,widget):
        type =  widget.name.split('_')[1]
        if type:
            combo = getattr(self,'%s_combo' %  type)
            combo.select(-1)

    def export_fullpack(self,widget):
        ## detect srcdirs for active themes
        saved = self.action_save()
        if not saved:
            return
        fpack_name = self.fpack_dic_copy['packname']
        basedir = tempfile.mkdtemp()
        themedir = os.path.join(basedir,fpack_name)
        os.mkdir(themedir)
        tar_elements = ("gtk","metacity","icons","mouse","emerald")
        licence = self.fpack_dic_copy['licence']
        author = self.fpack_dic_copy['author']
        link = self.fpack_dic_copy['link']
        img = self.fpack_dic_copy['img']
        
        for key,value in self.fpack_dic_copy.items():
            if re.match('packname|link|licence|author|img',key):
                continue
            target = os.path.join(themedir,key)
            if not os.path.exists(target):
                os.makedirs(target)
            ext = ".tar.gz"
            for type in tar_elements:
                item = None
                ## generate a tar.gz if match
                if key == type:
                    item = getattr(self,'%s_dict' % key).get(value)
                    if item:
                        if key == "emerald":
                            ext = ".emerald"
                        self.fullpack_dict.create_archive(item.name, item.path, key, target, ext)
            ## now others elements
            if key == "wallstat":
                name = os.path.splitext(value)[0]            
                for item in self.wallstat_dict.values():
                    if item.name == name:
                        wallpaper = self.wallstat_dict[item.filename]
                        target_file = os.path.join(target,value)
                        copyfile(wallpaper.filename, target_file)
                    else:
                        continue
            elif key == "walldyn":
                for item in self.walldyn_dict.values():
                    if item.name == value:
                        walldyn = self.walldyn_dict[item.filename]
                        self.fullpack_dict.create_archive(item.name, item.path, key, target, ext)
                    else:
                        continue 
            
            elif key == "cubemodel":
                theme = self.cubemodel_dict.get(value)
                if theme:
                    path = os.path.dirname(theme.path)
                    os.chdir(path)
                    target_file = os.path.join(target,value+".tar.lzma")
                    os.system("tar cv \""+value+"\" | lzma -z --best > \""+target_file+"\"")

        ## generate final lzma with thumb
        thumb = fullpack_home_srcdir+'/'+fpack_name+'/thumb.png'
        xml = fullpack_home_srcdir+'/'+fpack_name+'/elements.xml'
        if not os.path.exists(thumb):
            print "no thumb file in your theme folder..."
            return
        copyfile(thumb,basedir+'/thumb.png')
        copyfile(thumb,themedir+'/thumb.png')
        copyfile(xml,themedir+'/elements.xml')
        
        os.chdir(basedir)
        target_file = os.path.join(config.homedir,fpack_name+".tar.lzma")
        os.system("tar cv * | lzma -z --best > \""+target_file+"\"")
        os.chdir(config.homedir)
        ## cleanos.system wait
        rmtree(basedir)
        if os.path.exists(target_file):
            self.statbar.push(1,_("Fullpack %s successfully exported!" % target_file))
        