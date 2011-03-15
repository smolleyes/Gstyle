#!/usr/bin/env python
#-*- coding: UTF-8 -*-
#Module standart
import os
import config
import ConfigParser
import re
import shutil
#Module gstyle
from theme_scaner import ThemeScaner
from functions import scan_system_themes
from functions import gconf_set_string
from functions import gconf_get_string

srcdir = config.gtkThemes_srcdir
home_srcdir = config.gtkThemes_home_srcdir

class GtkDict(dict):
    def __init__(self,mode="sys",path_xml=None):
        super(GtkDict,self).__init__()
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
        themelist = scan_system_themes(srcdir, home_srcdir)
        for item in themelist:
            if not("Default" in item) and os.path.isdir(item):
                self.add_item_system(item)

    def add_item_system(self,path):
        rc = os.path.join(path,'gtk-2.0/gtkrc')
        if not(os.path.exists(rc)):
            return

        deskfile = os.path.join(path,'index.theme')
        name = os.path.basename(path)
        dirname = os.path.basename(path)
        metadata = {}
        if not(os.path.exists(deskfile)):
            metadata["metacity"] = ""
            metadata["icons"]  = ""
            metadata["cursor"]  = ""
            metadata["comment"]  = ""
        else:
            themeini = ConfigParser.RawConfigParser()
            try:
                themeini.readfp(open(deskfile))
            except:
                return
            if themeini.has_section('X-GNOME-Metatheme') :
                if themeini.has_option('X-GNOME-Metatheme',"GtkTheme"):
                   name = themeini.get( 'X-GNOME-Metatheme', 'GtkTheme' )
                if themeini.has_option('X-GNOME-Metatheme','MetacityTheme'):
                   metadata["metacity"] = themeini.get( 'X-GNOME-Metatheme', 'MetacityTheme' )
                if themeini.has_option('X-GNOME-Metatheme', 'IconTheme'):
                   metadata["icons"] = themeini.get( 'X-GNOME-Metatheme', 'IconTheme' )
                if themeini.has_option('X-GNOME-Metatheme','CursorTheme'):
                    metadata["cursor"] = themeini.get( 'X-GNOME-Metatheme', 'CursorTheme')
                if themeini.has_option('Desktop Entry','Comment'):
                    metadata["comment"] = themeini.get( 'Desktop Entry','Comment')
        
        gtk_obj = Gtk(name = name,
                      metacity = metadata.get("metacity"),
                      icons = metadata.get("icons"),
                      cursor = metadata.get("cursor"),
                      comment = metadata.get("comment"),
                      path = path,
                      rc = rc,
                      dirname = dirname,
                      )
        self[dirname] = gtk_obj
        return gtk_obj

    def add_item_archive(self,gtk_archive):
        """Ajouter un element dans le dictionnaire"""
        scaner = ThemeScaner(gtk_archive)
        theme_list = scaner.theme_loader(gtk_archive)
        if theme_list:
            return theme_list
        else:
            return

    def set_active_item(self,dirname):
        gtk_obj = self.get(dirname)
        if gtk_obj:
            value = gtk_obj.dirname
            gconf_set_string("/desktop/gnome/interface/gtk_theme",value)
            ## sinon met a jour pour etre sure
#            file = os.path.join(config.homedir,".gtkrc-2.0")
#            rc = open(file, 'w')
#            rc.write("# -- THEME AUTO-WRITTEN DO NOT EDIT \
#            include "+item.path+"/gtk-2.0/gtkrc\" \
#            # -- THEME AUTO-WRITTEN DO NOT EDIT"
#            )
#            rc.close()


    def get_active_item(self):
        name =  gconf_get_string("/desktop/gnome/interface/gtk_theme")
        return self.get(name)

    def action_delete(self,dirname):
        gtk_obj = self.get(dirname)
        if gtk_obj:
            path = gtk_obj.path
            if re.search("/usr", path):
                os.system(_("gksudo -m \"Root password needed to remove this theme\" \'\'"))
                os.system("sudo rm -R \"%s\"" % path)
            else:
                shutil.rmtree(path)
            del self[dirname]
            self.scan_system()


class Gtk(object):
    def __init__(self,name,metacity,icons,cursor,comment,path,rc,dirname):
        self._name = name
        self._metacity = metacity
        self._icons = icons
        self._cursor = cursor
        self._comment = comment
        self._path = path
        self._rcfile = rc
        self._dirname = dirname

    def get_name(self):
        return self._name
    name = property(get_name)

    def get_metacity(self):
        return self._metacity
    metacity = property(get_metacity)

    def get_icons(self):
        return self._icons
    icons = property(get_icons)

    def get_cursors(self):
        return self._cursors
    cursors = property(get_cursors)

    def get_comment(self):
        return self._comment
    comment = property(get_comment)

    def get_path(self):
        return self._path
    path = property(get_path)

    def get_rcfile(self):
        return self._rcfile
    rcfile = property(get_rcfile)

    def get_dirname(self):
        return self._dirname
    dirname = property(get_dirname)

