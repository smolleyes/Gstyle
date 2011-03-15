#!/usr/bin/python
#-*- coding: UTF-8 -*-
import os

exec_path =  os.path.dirname(os.path.abspath(__file__))
homedir = os.getenv("HOME")
user = os.getenv("USER")
modules_list = ["cubemodel","fullpacks","walltimes","xsplash","icons gtk","gdm","nautilus_background","emerald","metacity","cairo-dock","mouse"]
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
gstyle_mouse_srcdir = gstyle_confdir+"/elements/mouse"
fullpacks_srcdir = gstyle_confdir+"/elements/fullpacks"
fullpacks_imgdir = gstyle_confdir+"/elements/fullpacks/img"
fullpacks_url_dir = "http://scripts.penguincape.org/gstyle/themes/fullpacks"
fullpacks_index_url = "http://scripts.penguincape.org/gstyle/themes/fullpacks/index.php"
wallpapers_home_srcdir = homedir+"/.wallpapers"
walltimes_home_srcdir = homedir+"/.wallpapers/walltimes"
wallpapers_system_srcdir = "/usr/share/backgrounds"
no_preview_img = os.path.join(exec_path, 'data/img/question_img.png')
gstyle_backgrounds_data_dir = homedir+'/.local/share/gnome-background-properties'
icon_panel_dir = gstyle_confdir+'/elements/panel-icons'
