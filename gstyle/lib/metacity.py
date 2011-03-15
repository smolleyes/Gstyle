#!/usr/bin/python
#-*- coding: UTF-8 -*-

import os
import config
from glob import glob
import re

from shutil import rmtree
#Module gstyle
from theme_scaner import ThemeScaner
from functions import gconf_set_string,gconf_get_string


system_srcdir = config.gtkThemes_srcdir
home_srcdir = config.gtkThemes_home_srcdir

class MetacityDict(dict):

    def __init__(self,mode="sys",path_xml=None):
        super(MetacityDict,self).__init__()
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
        ## liste les gtkThemes et envoi dans la simplelist
        usrlist = []
        homelist  = []
        self.list_theme = []
        self.clear()
        if os.path.exists(system_srcdir):
            usrlist = glob(os.path.join(system_srcdir,"*"))
        if os.path.exists(home_srcdir):
            homelist = glob(os.path.join(home_srcdir,"*"))
        themelist = set(usrlist + homelist)

        for dir in themelist:
            if os.path.isdir(os.path.join(dir,"metacity-1")):
                self.add_item_system(dir)


    def add_item_system(self,path):
        if not os.path.exists(path):
            print "theme path do not exist %s" % path
            return
        name = os.path.basename(path)
        path = path
        metacity_obj = Metacity(name = name,
                             path = path,
                             )
        self[name] = metacity_obj
        return metacity_obj


    def add_item_archive(self,path_archive):
        """Ajouter un element dans le dictionnaire"""
        scaner = ThemeScaner(path_archive)
        theme_list = scaner.theme_loader(path_archive)
        if theme_list.has_key('metacity'):
            return theme_list['metacity']
        else:
            print "no metacity theme in this file"

    def del_item(self,name):
        """Supprimer un element dans le dictionnaire"""
        if not self.has_key(name) :
            return
        metacity_obj = self[name]
        srcdir = metacity_obj.path
        if re.search("/usr",srcdir):
            os.system(_("gksudo -m \"Please enter your password\" \'\'"))
            os.system("sudo rm -R \"%s\"" % srcdir)
        else :
            rmtree(srcdir)

    def set_active_item(self,name):
        gconf_set_string("/apps/metacity/general/theme", name)
        
    def get_active_item(self):
        name = gconf_get_string("/apps/metacity/general/theme")
        return self.get(name)


class Metacity(object):
    def __init__(self,name,path):
        self._name = name
        self._path = path

    def get_name(self):
        return self._name

    name = property(get_name)

    def get_path(self):
        return self._path

    path = property(get_path)


