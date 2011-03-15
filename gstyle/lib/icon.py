#-*- coding: UTF-8 -*-
#Module standart
import os
import config
import ConfigParser
import re
import shutil
import gtk
#Module gstyle
from theme_scaner import ThemeScaner
from functions import gconf_set_string
from functions import scan_system_themes
from functions import gconf_set_string,gconf_get_string,gconf_set_bool
from shutil import copyfile

srcdir = config.icons_srcdir
icons_home_srcdir = config.icons_home_srcdir
panel_icon_dir = config.icon_panel_dir+"/img"

class IconDict(dict):

    def __init__(self,mode="sys",path_xml=None):
        super(IconDict,self).__init__()
        if mode == "sys":
            self.scan_system()
        elif mode == "xml":
            self.load_xml()

    def load_xml(self):
        """Charger le dictionnaire à partir d'un fichier xml"""
        pass

    def save_xml(self):
        """Enregistrer le dictionnaire sous forme d'un fichier xml"""
        pass

    def scan_system(self):
        """Charger le dictionnaire en scannant les dossiers"""
        themelist = scan_system_themes(srcdir, icons_home_srcdir)
        for item in themelist:
            if not("default" in item) and os.path.isdir(item):
                self.add_item_system(item)

    def add_item_system(self,path):
        deskfile = os.path.join(path,'index.theme')
        icon_dirname = os.path.basename(path)
        icon_name = icon_dirname
        if not(os.path.exists(deskfile)):
            return
        if os.path.exists(os.path.join(path,'cursors')):
            return
        themeini = ConfigParser.RawConfigParser()
        themeini.readfp(open(deskfile))
        list_section = themeini.sections()
        if themeini.has_section('Icon Theme') :
            if themeini.has_option("Icon Theme","Name"):
                icon_name = themeini.get('Icon Theme',"Name")
            else:
                return
            if themeini.has_option("Icon Theme","Comment"):
                icon_desc = themeini.get('Icon Theme','Comment')
            else:
                icon_desc = ""
        else:
            return

        if self.has_key(icon_name):
            return
        else:
            icons_pic = self.get_img_folder(path)
            if not(icons_pic):
                return
        icon_obj = Icon(icon_name,icon_desc,icons_pic,path,icon_dirname)
        self[icon_dirname] = icon_obj
        return icon_obj

    def get_img_folder(self,path):
        exp_reg = re.compile("^(gnome-folder|folder).(svg|png)")
        panel_reg = re.compile("^(start-here).(svg|png)")
        ## detect gnome panel menu icon
        folderlist = ("24x24/places","22x22/places","scalable/places","places")
        for dir in folderlist:
            path_dir = os.path.join(path,dir)
            if not os.path.exists(path_dir):
                continue
            for root, dirs, files in os.walk(path_dir):
                for i in files:
                    if re.search(panel_reg, i):
                        fpath = root+'/'+i
                        self.add_panelicon_todic(fpath, path)
                        break
        
        ## scan for gnome-folder    
        folderlist = ("scalable/places","48x48","64x64","128x128","scalable","places")
        for dir in folderlist:
            path_dir = os.path.join(path,dir)
            if not os.path.exists(path_dir):
                continue
            for root, dirs, files in os.walk(path_dir):
                for i in files:
                    if re.search(exp_reg, i):
                        return os.path.join(root,i)
                    
    def add_panelicon_todic(self, img, path=None):
        name = None
        if path:
            name = os.path.basename(path)
        else:
            name = os.path.splitext(os.path.basename(img))[0]
        ext = os.path.splitext(img)[-1]
        localfile = os.path.join(panel_icon_dir,name+ext)
        basename = os.path.join(panel_icon_dir,name)
        if not os.path.exists(basename+'.png') and not os.path.exists(basename+'.svg'):
            copyfile(img,localfile)
                    
    def add_item_archive(self,icon_archive=None, theme_list=None):
        """Ajouter un element dans le dictionnaire"""
        if icon_archive:
            scaner = ThemeScaner(icon_archive)
            theme_list = scaner.theme_loader(icon_archive)
        if theme_list.has_key('icons'):
            return theme_list
        else:
            print "no icons theme in this file"


    def del_item(self,dirname):
        """Supprimer un element dans le dictionnaire"""
        icon_obj = self.get(dirname)
        if icon_obj:
            path = icon_obj.path
            if re.search("/usr", path):
                os.system(_("gksudo -m \"Root password needed to remove this theme\" \'\'"))
                os.system("sudo rm -R \"%s\"" % path)
            else:
                shutil.rmtree(path)
            del self[dirname]

    def set_active_item(self,dirname):
        icon_obj = self.get(dirname)
        if icon_obj:
            value = icon_obj.dirname
            gconf_set_string("/desktop/gnome/interface/icon_theme",value)

    def get_active_item(self):
        name = gconf_get_string("/desktop/gnome/interface/icon_theme")
        return self.get(name)
    
    def set_gconf_options(self,widget):
        if ('menuicons' in widget.name):
            if widget.get_active():
                gconf_set_bool("/desktop/gnome/interface/menus_have_icons", True)
            else:
                gconf_set_bool("/desktop/gnome/interface/menus_have_icons", False)
        elif ('btnicons' in widget.name):
            if widget.get_active():
                gconf_set_bool("/desktop/gnome/interface/buttons_have_icons", True)
            else:
                gconf_set_bool("/desktop/gnome/interface/buttons_have_icons", False)
        elif ('computer_icon' in widget.name):
            if widget.get_active():
                gconf_set_bool("/apps/nautilus/desktop/computer_icon_visible", True)
            else:
                gconf_set_bool("/apps/nautilus/desktop/computer_icon_visible", False)
        elif ('home_icon' in widget.name):
            if widget.get_active():
                gconf_set_bool("/apps/nautilus/desktop/home_icon_visible", True)
            else:
                gconf_set_bool("/apps/nautilus/desktop/home_icon_visible", False)
        elif ('trash_icon' in widget.name):
            if widget.get_active():
                gconf_set_bool("/apps/nautilus/desktop/trash_icon_visible", True)
            else:
                gconf_set_bool("/apps/nautilus/desktop/trash_icon_visible", False)
        elif ('volumes_icon' in widget.name):
            if widget.get_active():
                gconf_set_bool("/apps/nautilus/desktop/volumes_visible", True)
            else:
                gconf_set_bool("/apps/nautilus/desktop/volumes_visible", False)
        elif ('network_icon' in widget.name):
            if widget.get_active():
                gconf_set_bool("/apps/nautilus/desktop/network_icon_visible", True)
            else:
                gconf_set_bool("/apps/nautilus/desktop/network_icon_visible", False)


class Icon(object):
    def __init__(self,name,desc,picture,dir,dirname):
        self._name = name
        self._desc = desc
        self._picture = picture
        self._path = dir
        self._dirname = dirname

    def get_path(self):
        return self._path
    path = property(get_path)

    def get_picture(self):
        return self._picture
    picture = property(get_picture)

    def get_desription(self):
        return self._desc
    description = property(get_desription)

    def get_name(self):
        return self._name
    name = property(get_name)

    def get_dirname(self):
        return self._dirname
    dirname = property(get_dirname)
