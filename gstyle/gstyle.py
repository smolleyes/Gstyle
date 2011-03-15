#!/usr/bin/env python
#-*- coding: UTF-8 -*-
from gui.main import MainWindow
import config
import gtk

from lib.emerald import EmeraldDict
from lib.metacity import MetacityDict
from lib.icon import IconDict
from lib.mouse import MouseDict
from lib.gtk import GtkDict
from lib.wallpapers import WallPaperDict
from lib.cubemodels import CubemodelsDict
from lib.fullpack import FullPackDict

class Gstyle(object):
    def __init__(self):
        #Vérification de la config du system
        config.check_config()
        #Instanciation des objet metier
        #Icon
        print "start icons scan"
        self.icon_dict  =  IconDict()
        #Emerald
        print "start emerald scan"
        self.emerald_dict = EmeraldDict()
        #Metacity
        print "start metacity scan"
        self.metacity_dict = MetacityDict()
        #Mouse
        print "start mouse scan"
        self.mouse_dict = MouseDict()
        #Gtk
        print "start gtk scan"
        self.gtk_dict = GtkDict()
        #Wallpaper
        self.wallpapers_dict = WallPaperDict()
        print "start wallpapers scan"
        #Cubemodel
        print "start cubemodels scan"
        self.cubemodels_dict = CubemodelsDict()
        #Fullpack
        print "start fullpacks scan"
        self.fullpack_dict = FullPackDict()
        
        #Instanciation de l'interface graphique
        self.gtk_gui = MainWindow()
        self.gtk_gui.initialisation_gui(self)
        
        gtk.main()
        
if __name__ == "__main__":
    Gstyle()
