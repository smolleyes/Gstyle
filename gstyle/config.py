#-*- coding: UTF-8 -*-
import os
import sys
import logging
import gtk
import gtk.glade
import ConfigParser

import gettext
from Translation import Translation

GLADE_FILE = '/usr/share/Gstyle.glade'
APP_NAME = 'gstyle'

exec_path =  os.path.dirname(os.path.abspath(__file__))
## check if we run gstyle from system or static dir
data_path=''
if not ('/usr' in exec_path):
    d = os.path.dirname(exec_path)
    data_path  = os.path.join(d,'data')
else:
    data_path  = '/usr/share/gstyle/data'
img_path = os.path.join(data_path,"img")
glade_path = os.path.join(data_path,"glade")
homedir = os.getenv("HOME")
user = os.getenv("USER")
modules_list = ["cubemodel","fullpacks","walltimes","xsplash","icons gtk","gdm","nautilus_background","emerald","metacity","cairo-dock","mouse","panel-icons"]
gstyle_confdir = homedir+"/.config/gstyle"
gstyle_conf_file = homedir+"/.config/gstyle/conf.ini"
compizConfig = homedir+"/.config/compiz/compizconfig/Default.ini"
cfgfile = homedir+"/.config/gstyle/config"
icons_srcdir = "/usr/share/icons"
icons_home_srcdir = homedir+"/.icons"
gtkThemes_srcdir = "/usr/share/themes"
gtkThemes_home_srcdir = homedir+"/.themes"
emerald_srcdir = "/usr/local/share/emerald/themes"
emerald_home_srcdir = homedir+"/.emerald/themes"
emerald_active_srcdir = homedir+"/.emerald/theme"
gtkrcfile = homedir+"/.gtkrc-2.0"
cubemodels_imgdir = gstyle_confdir+"/elements/cubemodel/img"
cubemodels_url_dir = "http://scripts.penguincape.org/gstyle/themes/cubemodels"
cubemodels_index_url = "http://scripts.penguincape.org/gstyle/themes/cubemodels/index.php"
cubemodels_srcdir = gstyle_confdir+"/elements/cubemodel"
fullpacks_srcdir = gstyle_confdir+"/elements/fullpacks"
fullpacks_imgdir = gstyle_confdir+"/elements/fullpacks/img"
fullpacks_url_dir = "http://scripts.penguincape.org/gstyle/themes/fullpacks"
fullpacks_index_url = "http://scripts.penguincape.org/gstyle/themes/fullpacks/index.php"
wallpapers_home_srcdir = homedir+"/.wallpapers"
wallpapers_system_srcdir = "/usr/share/backgrounds"
walltimes_home_srcdir = homedir+"/.wallpapers/walltimes"
no_preview_img = os.path.join(exec_path, "data/img/question_img.png")
gstyle_backgrounds_data_dir = homedir+'/.local/share/gnome-background-properties'
icon_panel_dir = gstyle_confdir+'/elements/panel-icons'

def check_config():
    ## update gtk and icons themes for gdm/xsplash
    confdir = gstyle_confdir
    if not os.path.exists(confdir) :
        os.mkdir(confdir, 0755)
        os.mkdir(confdir+"/elements", 0755)
    for d in modules_list :
        dir = confdir+"/elements/"+d
        if not os.path.exists(dir):
            os.mkdir(dir, 0755)
            os.mkdir(dir+"/img", 0755)

    if not os.path.exists(cubemodels_srcdir):
        os.mkdir(cubemodels_srcdir, 0755)
        os.mkdir(cubemodels_imgdir, 0755)

    if not os.path.exists(emerald_home_srcdir) :
        os.makedirs(emerald_home_srcdir, 0755)

    if not os.path.exists(wallpapers_home_srcdir) :
        os.mkdir(wallpapers_home_srcdir, 0755)
        os.mkdir(walltimes_home_srcdir, 0755)
        
    list = ("cubemodel","emerald","fullpack","panel-icon")
    parser = ConfigParser.RawConfigParser()
    if not os.path.exists(gstyle_conf_file):
        for item in list:
            parser.add_section(item)
            parser.set(item, 'name', '')
            parser.set(item, 'path', '')
        with open(gstyle_conf_file, 'wb') as configfile:
            parser.write(configfile)
    else:
        parser.readfp(open(gstyle_conf_file))
        for section in list:
            if not parser.has_section(section):
                print section
                parser.add_section(section)
                parser.set(section, 'name', '')
                parser.set(section, 'path', '')
        with open(gstyle_conf_file, 'w+') as configfile:
            parser.write(configfile)
            
    ## check the gnome background dir for Xdg 
    if not os.path.exists(gstyle_backgrounds_data_dir):
        os.makedirs(gstyle_backgrounds_data_dir, 0700)
        
    print "Gstyle Config ok"

## arg debug levels
LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}

if len(sys.argv) > 1:
    level_name = sys.argv[1]
    level = LEVELS.get(level_name, logging.NOTSET)
    logging.basicConfig(level=level)

## LOCALISATION
source_lang = "en"
rep_trad = "/usr/share/locale"
traduction = Translation(APP_NAME, source_lang, rep_trad)
gettext.install(APP_NAME)
gtk.glade.bindtextdomain(APP_NAME, rep_trad)
gettext.textdomain(APP_NAME)
_ = traduction.gettext
