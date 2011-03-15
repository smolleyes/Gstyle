#-*- coding: UTF-8 -*-

import os
import gtk
from glob import glob
import config
import gconf
from shutil import copyfile

from functions import create_filechooser_open
from functions import yesno
from config import _
from functions import ComboBox
from functions import gconf_get
from functions import run_as_root
import ConfigParser

gstyle_conf_file = config.gstyle_conf_file
panel_icon_dir = config.icon_panel_dir+"/img"

class IconGui(object):
    def __init__(self,gladexml,icon_dict):
        #Load api icon
        self.icon_dict = icon_dict
        self.gclient = gconf.client_get_default()
        self.iconsTheme_save = gconf_get("/desktop/gnome/interface/icon_theme")
        ## load widget
        self.w_status_bar = gladexml.get_widget("statusbar")

        self.icons_page_img = gladexml.get_widget("icons_page_img")
        self.icons_page_img.set_from_file(config.img_path+"/iconspack.png")
        self.icons_page_label = gladexml.get_widget("icons_page_label")
        self.icons_page_label.set_text(_("Icons:\nManage and install your icons themes"))

        self.wl_icon_gest = gladexml.get_widget("icons_gest_label")
        self.wl_icon_gest.set_text(_("Available themes list"))

        self.progress_box = gladexml.get_widget("progress_box")
        self.progress_text = gladexml.get_widget("progress_box_text")

        self.main_progressbar = gladexml.get_widget("main_progressbar")

        self.statbar = gladexml.get_widget("statusbar")

        ## setup the iconview
        self.model = gtk.ListStore(str,gtk.gdk.Pixbuf, str, str, str, str, str, str)
        self.w_iconview = gtk.IconView(model=self.model)
        self.w_iconview.set_pixbuf_column(1)
        self.w_iconview.set_text_column(0)
        self.w_iconview.set_columns(0)
        self.w_iconview.set_item_width(150)
        self.w_iconview.set_selection_mode('single')
        self.w_iconview.set_reorderable(1)
        ## add the iconview
        self.w_viewer = gladexml.get_widget("icons_viewer")
        self.w_viewer.add(self.w_iconview)
        self.list_icon_themes()

        self.w_applybtn =  gladexml.get_widget("icons_gest_applybtn")


        #Mettre ça dans un objet fenétre principal
        self.decoration_page_img = gladexml.get_widget("decoration_page_img")
        self.decoration_page_desc = gladexml.get_widget("decoration_page_desc")
        img_path = os.path.join(config.exec_path,"/img/iconspack.png")
        if os.path.exists(img_path):
            self.decoration_page_img.set_from_file(img_path)
        self.decoration_page_desc.set_text(_("Icons:\nManage and install your icons themes..."))

        ## gconf and panel icons
        self.icon_panel_combobox = gladexml.get_widget("icon_panel_combobox")
        self.icon_panel_apply_btn = gladexml.get_widget("icon_panel_apply_btn")
        self.menuhaveicon_checkbox = gladexml.get_widget("icon_menuicons_select")
        self.btnhaveicon_checkbox = gladexml.get_widget("icon_btnicons_select")
        self.home_visible_checkbox = gladexml.get_widget("home_icon")
        self.computer_visible_checkbox = gladexml.get_widget("computer_icon")
        self.trash_visible_checkbox = gladexml.get_widget("trash_icon")
        self.network_visible_checkbox = gladexml.get_widget("network_icon")
        self.volumes_visible_checkbox = gladexml.get_widget("volumes_icon")
        ## initialize checkboxes
        self.check_gconf_options()

        ## panel icons
        self.panel_icon_dic = {}
        self.icon_panel_model = gtk.ListStore(str,gtk.gdk.Pixbuf,str)
        self.list_panel_icons()

        self.panelTree = gtk.TreeView()
        self.icon_panel_combobox.set_model(self.icon_panel_model)
        px = gtk.CellRendererPixbuf()
        text = gtk.CellRendererText()

        #Pack the cell renderer into the combobox.
        self.icon_panel_combobox.pack_start(px, False)
        self.icon_panel_combobox.pack_start(text, False)

        #Use the add_attribute method to specify which column in the model the
        self.icon_panel_combobox.add_attribute(px, "pixbuf", 1)
        #Do the same for CellRendererText()
        self.icon_panel_combobox.add_attribute(text, "text", 0)

        self.panel_icon_combo = ComboBox(self.icon_panel_combobox)
        self.get_active_panel_icon()

        ##load signal
        dic = {"on_icons_gest_addbtn_clicked" : self.action_add,
               "on_icons_gest_applybtn_clicked" : self.action_apply,
               "on_icons_gest_delbtn_clicked" : self.action_delete,
               "on_icon_panel_apply_btn_clicked" : self.apply_panel_icon,
               "on_icon_menuicons_select_toggled" : self.set_gconf_options,
               "on_icon_btnicons_select_toggled" : self.set_gconf_options,
               "on_panel_icon_addbtn_clicked" : self.add_panel_icon,
               "on_panel_icon_delbtn_clicked" : self.del_panel_icon,
               "on_computer_icon_toggled" : self.set_gconf_options,
               "on_home_icon_toggled" : self.set_gconf_options,
               "on_trash_icon_toggled" : self.set_gconf_options,
               "on_network_icon_toggled" : self.set_gconf_options,
               "on_volumes_icon_toggled" : self.set_gconf_options,
               }
        self.w_iconview.connect('selection_changed',self.action_get_model)
        self.w_iconview.connect('button-press-event',self.treeview_clicked)
        gladexml.signal_autoconnect(dic)

    def add_panel_icon(self,widget):
        filterlist = ["*.png","*.svg"]
        dialog = create_filechooser_open((_("Choose an icon image")),filterlist)
        result = dialog.run()
        if result != gtk.RESPONSE_OK:
            dialog.destroy()
            return
        ## if ok
        icon = dialog.get_filename()
        dialog.destroy()
        if icon:
            self.icon_dict.add_panelicon_todic(icon)
            name = os.path.basename(os.path.splitext(icon)[0])
            self.add_panel_model(name,icon)
            self.panel_icon_combo.setIndexFromString(name)
            self.apply_panel_icon()

    def get_active_panel_icon(self):
        parser = ConfigParser.RawConfigParser()
        parser.readfp(open(gstyle_conf_file))
        name = parser.get('panel-icon', 'name')
        if name:
            self.panel_icon_combo.setIndexFromString(name)

    def del_panel_icon(self,widget):
        name = self.panel_icon_combo.getSelected()
        img = self.panel_icon_dic[name]
        imgname = os.path.basename(img)
        self.icon_panel_model.clear()
        os.unlink(img)
        del self.panel_icon_dic[name]
        self.list_panel_icons()
        self.panel_icon_combo.select(0)

    def apply_panel_icon(self,widget=None):
        name = self.panel_icon_combo.getSelected()
        img = self.panel_icon_dic[name]
        imgname = os.path.basename(img)
        ext = os.path.splitext(imgname)[-1]
        ## get the path for active icon theme
        theme = self.icon_dict.get_active_item()
        if theme:
            path = theme.path
            mainpath = None
            if os.path.exists(path+'/24x24/places'):
                mainpath = path+'/24x24/places'
                if ext == '.png':
                    os.system('convert -resize 24x24! %s %s' % (img, img))
            elif os.path.exists(path+'/places/24'):
                mainpath = path+'/places/24'
                if ext == '.png':
                    os.system('convert -resize 24x24! %s %s' % (img, img))
            elif os.path.exists(path+'/places'):
                mainpath = path+'/places'
                if ext == '.png':
                    os.system('convert -resize 24x24! %s %s' % (img, img))
            elif os.path.exists(path+'/scalable/places'):
                mainpath = path+'/scalable/places'
                if ext == '.png':
                    os.system('convert -resize 128x128! %s %s' % (img, img))
            else:
                mainpath = path+'/scalable/places'
                if ext == '.png':
                    os.system('convert -resize 128x128! %s %s' % (img, img))

            target = mainpath+'/start-here'+ext
            if not os.path.islink(path) and ('/usr' in path):
                if not os.path.exists(mainpath):
                    run_as_root('mkdir -p %s' % mainpath, msg)
                for i in glob(mainpath+'/start-here*'):
                    run_as_root('rm %s' % i, msg)
                run_as_root("cp -f %s %s" % (img, target), msg)
            else:
                if not os.path.exists(mainpath):
                    os.makedirs(mainpath, 0755)
                for i in glob(mainpath+'/start-here*'):
                    os.system('rm %s' % i)
                copyfile(img, target)
            os.system('killall -9 gnome-panel')
            ## update gstyle .ini
            parser = ConfigParser.RawConfigParser()
            parser.readfp(open(gstyle_conf_file))
            parser.set('panel-icon', 'name', name)
            parser.set('panel-icon', 'path', img)
            with open(gstyle_conf_file, 'w+') as configfile:
                parser.write(configfile)

    def run_sudo(self, cmd, msg):
        gksu_context = gksu2.Context()
        gksu_context.set_message(msg)
        gksu2.run(cmd)

    def list_panel_icons(self):
        for file in glob(panel_icon_dir+'/*'):
            name = os.path.basename(os.path.splitext(file)[0])
            self.add_panel_model(name,file)

    def check_gconf_options(self):
        menuicon = gconf_get("/desktop/gnome/interface/menus_have_icons")
        btnicon = gconf_get("/desktop/gnome/interface/buttons_have_icons")
        homeicon = gconf_get("/apps/nautilus/desktop/home_icon_visible")
        compicon = gconf_get("/apps/nautilus/desktop/computer_icon_visible")
        trashicon = gconf_get("/apps/nautilus/desktop/trash_icon_visible")
        neticon = gconf_get("/apps/nautilus/desktop/network_icon_visible")
        volicon = gconf_get("/apps/nautilus/desktop/volumes_visible")
        if menuicon:
            self.menuhaveicon_checkbox.set_active(1)
        if btnicon:
            self.btnhaveicon_checkbox.set_active(1)
        if homeicon:
            self.home_visible_checkbox.set_active(1)
        if trashicon:
            self.trash_visible_checkbox.set_active(1)
        if neticon:
            self.network_visible_checkbox.set_active(1)
        if volicon:
            self.volumes_visible_checkbox.set_active(1)
        if compicon:
            self.computer_visible_checkbox.set_active(1)

    def set_gconf_options(self,widget):
        self.icon_dict.set_gconf_options(widget)

    def list_icon_themes(self):
        for item in self.icon_dict.values():
            self.add_model(item)

    def add_model(self,item):
        picture_path = item.picture
        extension = os.path.splitext(picture_path)[1]
        if extension == '.svg':
            img = gtk.gdk.pixbuf_new_from_file_at_size(picture_path, 60, 60)
        elif extension == '.png':
            gtk.ACCEL_LOCKED
            img = gtk.gdk.pixbuf_new_from_file_at_size(picture_path, 60, 60 )
        else:
            return
        self.iter = self.model.append()
        self.model.set(self.iter,
        0, item.dirname,
        1, img,
        2, item.path,
        3, item.description,
        4, item.name,
        )

    def add_panel_model(self,name,path):
        extension = os.path.splitext(path)[-1]
        img = None

        if extension == '.svg':
            img = gtk.gdk.pixbuf_new_from_file_at_scale(path, 24, 24, 1)
        elif extension == '.png':
            gtk.ACCEL_LOCKED
            img = gtk.gdk.pixbuf_new_from_file_at_scale(path, 24, 24, 1)
        else:
            return
        iter = self.icon_panel_model.append()
        self.icon_panel_model.set(iter,
        0, name,
        1, img,
        2, path,
        )
        self.panel_icon_dic[name] = path

    #Action
    def action_add(self,widget):
        filterlist = ["*.gz","*.bz2","*.tar","*.zip","*.rar"]
        dialog = create_filechooser_open((_("Choose a tar.gz/bz2 file")),filterlist)
        result = dialog.run()
        if result != gtk.RESPONSE_OK:
            dialog.destroy()
            return
        ## if ok
        icons_archive = dialog.get_filename()
        dirname = ""
        dialog.destroy()
        if not os.path.exists(icons_archive):
            print "Icon theme non-existent or corrupt \n"
            return
        theme_list = self.icon_dict.add_item_archive(icons_archive)
        if theme_list and theme_list.has_key('icons'):
            return self.action_add_todic(theme_list)
        else:
            print "no icons themes in this file... %s " % icons_archive
            return

    def action_add_todic(self,theme_list):
        icons_theme_list = theme_list['icons']
        for destination in icons_theme_list.values():
            if destination:
                item = self.icon_dict.add_item_system(destination)
                if item:
                    dirname = item.dirname
                    self.add_model(item)
        if item:
            path = self.model[-1].path
            self.w_iconview.select_path(path)
            self.w_iconview.set_cursor(path)
            self.icon_dict.set_active_item(dirname)

    def action_apply(self,widget=None,dirname=None):
        if dirname:
            self.item_dirname = dirname
            self.item_name = dirname
        self.icon_dict.set_active_item(self.item_dirname)
        self.w_status_bar.push(1,(_("Icons theme  %s successfully activated") % self.item_name))

    def action_delete(self,widget):
        confirm = yesno((_("Remove icons themes")),\
                (_("Are you sure you want to delete the icons Theme \n %s ?") % self.item_name))
        if confirm == "No":
            return
        ## remove the theme
        self.icon_dict.del_item(self.item_dirname)
        self.model.remove(self.iter)
        self.statbar.push(1,(_("Icons themes %s removed successfully") % self.item_name))

    def action_get_model(self,widget=None):
        selected = self.w_iconview.get_selected_items()
        ## check if path exist (or problems when clicking between rows..)
        try:
            row_index = selected[0]
        except:
             return
        self.iter = self.model.get_iter(row_index)
        self.item_name = self.model.get_value(self.iter,4)
        self.item_path = self.model.get_value(self.iter,2)
        self.item_description = self.model.get_value(self.iter,3)
        self.item_dirname = self.model.get_value(self.iter,0)
        self.wl_icon_gest.set_text(_("Description : %s") % self.item_description)
        self.w_status_bar.push(1,_("Selected icons theme : %s") % self.item_name)

    def treeview_clicked(self, widget, event):
        if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            self.action_get_model()
            self.action_apply()
