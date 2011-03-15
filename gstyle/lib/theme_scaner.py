#!/usr/bin/env python
#-*- coding: UTF-8 -*-
######################
# detect theme type automatically by extension name and more
#

import tarfile
import re
import os
import tempfile
from xml.dom import minidom

## custom
import config
from shutil import move
from distutils.dir_util import copy_tree

from functions import install_dialog
from functions import gthread
icons_target = config.icons_home_srcdir
gtk_target = config.gtkThemes_home_srcdir
emerald_target = config.emerald_home_srcdir
cubemodels_target = config.cubemodels_srcdir
wallstats_target = config.wallpapers_home_srcdir
walltimes_target = config.walltimes_home_srcdir
fullpacks_target = config.fullpacks_srcdir


class ThemeScaner(object):
    def __init__(self,main_archive,gstyle_obj=None):
        self.dirlist = []
        self.main_archive = main_archive
        self.theme_list = {}
        self.gtk_list = {}
        self.icons_list = {}
        self.metacity_list = {}
        self.mouse_list = {}
        self.emerald_list = {}
        self.cubemodels_list = {}
        ## special fullpacks
        self.fullpacks_list = {}
        self.wallpapers_list = {}
        self.wallstats_list = {}
        self.walltimes_list = {}
        self.gstyle_obj = gstyle_obj


    def theme_loader(self,archive,destination=None):
        archive = archive.strip()
        print "checking your file %s ..." % archive
        self.workdir = self.extract_archive(archive)
        print "############ Main archive : %s" % self.workdir
        if self.workdir:
            self.dirlist.append(self.workdir)
            ## now we have all the content of the main archive in a tmpdir
            ## scan all files for dir/files or others archives
            print self.workdir+" ready, checking files for others archives"
            self.dirlist = self.scan_for_archives(self.workdir)
            #if len(self.dirlist) > 0:
            #    for themedir in self.dirlist:
            #        self.scan_for_archives(themedir)
            ## now all archives have their own dirs, just scan theme for gtk/icons ...
            for dir in self.dirlist:
                self.analyse_dir_for_theme(dir)
    
            ## count themes in the returned dic
            self.gtk_count = len(self.gtk_list)
            self.icons_count = len(self.icons_list)
            self.metacity_count = len(self.metacity_list)
            self.mouse_count = len(self.mouse_list)
            self.emerald_count = len(self.emerald_list)
            self.cubemodels_count = len(self.cubemodels_list)
            self.fullpacks_count = len(self.fullpacks_list)
            self.wallpapers_count = len(self.wallstats_list)
            self.walltimes_count = len(self.walltimes_list)
    
            print """
    #########################################
    Cumulated scan results for your theme archive %s:
    %s Gtk themes : %s
    %s Icons themes : %s
    %s Metacity themes : %s
    %s Mouse themes : %s
    %s Emerald themes : %s
    %s cubemodels themes : %s
    %s wallpapers : %s
    %s walltimes : %s
    %s fullpacks themes : %s
    """ % (self.main_archive, self.gtk_count, ', '.join(self.gtk_list),
           self.icons_count, ', '.join(self.icons_list),
           self.metacity_count,', '.join(self.metacity_list),
           self.mouse_count, ', '.join(self.mouse_list),
           self.emerald_count, ', '.join(self.emerald_list),
           self.cubemodels_count, ', '.join(self.cubemodels_list),
           self.wallpapers_count, ', '.join(self.wallstats_list),
           self.walltimes_count, ', '.join(self.walltimes_list),
           self.fullpacks_count, ', '.join(self.fullpacks_list),
           )
            ## resume install
            resume = install_dialog(self.theme_list, archive)
            if resume != False:
                gthread(self.install_themes)
                os.system("rm -R /tmp/tmp*")
                return self.theme_list
            else:
                print "installation canceled"
                return
        else:
            print "can't get main tempdir for installation (extraction problem)"
            return

    def extract_archive(self, archive):
        exp_reg = re.compile("(.tar|.tar.gz|.tar.bz2|.bz2|.gz|.tar.lzma|.emerald|.zip|.rar|.7z)$")
        check = re.search(exp_reg, archive)
        ## create a main tempfile
        tmpdir = tempfile.mkdtemp()
        ## start scanning
        if check:
            ext = check.group()
            if re.match('(.tar)$', ext):
                mode = 'r:'
            if re.match('(.tar.gz|.gz|.emerald)$', ext):
                mode = 'r:gz'
            elif re.match('(.tar.bz2|.bz2)$', ext):
                mode = 'r:bz2'
            elif ext == ".tar.lzma":
                name = os.path.basename("".join(archive.split(".tar.lzma")))
                os.system("cat \""+archive+"\" | lzma -d -q | tar xv -C "+tmpdir)
                self.dirlist.append(tmpdir)
            elif ext == ".zip":
                name = os.path.basename("".join(archive.split(".zip")))
                os.system("unzip -o \"%s\" -d \"%s\"" % (archive, tmpdir))
                self.dirlist.append(tmpdir)
            elif ext == ".7z":
                name = os.path.basename("".join(archive.split(".zip")))
                os.system("7z e \"%s\" -o\"%s\"" % (archive, tmpdir))
                self.dirlist.append(tmpdir)

            elif ext == ".rar":
                name = os.path.basename("".join(archive.split(".zip")))
                os.system("unrar x \"%s\" \"%s\"" % (archive, tmpdir))
                self.dirlist.append(tmpdir)
        else:
            print "file type not supported : %s" % archive
            return

        #print "file type %s ok..." % ext

        ## if ok get archive name
        if not re.match('(.tar.lzma|.rar|.zip|.7z)$', ext):
            name = os.path.basename("".join(archive.split(ext)))
            ## create tarfile
            obj = tarfile.open(archive, mode)
            if obj:
                #print "file integrity ok, extracting..."
                tmpdir = tempfile.mkdtemp()
                ## special for emerald to keep the dir name
                if re.match('(.emerald)$', ext):
                    name = os.path.basename("".join(archive.split(".emerald")))
                    tmpdir = os.path.join(tmpdir, name)
                    self.emerald_list[name] = tmpdir
                    self.theme_list['emerald'] = self.emerald_list
                    self.dirlist.append(tmpdir)

                return self.extract_theme(obj, tmpdir)
            else:
                print "can't create tarfile"
                return
        return tmpdir

    def scan_for_archives(self, tmpdir):
        exp_reg = re.compile("(.tar|.tar.gz|.tar.bz2|.bz2|.gz|.tar.lzma|.emerald|.zip|.7z)$")
        for root, dirs, files in os.walk(tmpdir):
            set(self.dirlist)
            for file in files:
                new_archive = os.path.join(root, file)
                if re.search(exp_reg, new_archive):
                    #print "Archive \"%s\" found in your file, try to install it..." % new_archive
                    tdir = self.extract_archive(new_archive)
                    self.dirlist.append(tdir)
                    self.scan_for_archives(tdir)
        d = {}
        for x in self.dirlist:
            d[x]=x
            self.dirlist = d.values()
        return set(self.dirlist)

    def analyse_dir_for_theme(self, tmpdir):
        ## scan all the archive for gtk elements or index.theme
        for root, dirs, files in os.walk(tmpdir):
            for file in files:
                file_path = os.path.join(root, file)
                dir_path = os.path.dirname(root)
                dirname = os.path.basename(dir_path)
                wallreg = re.search('\/(wallpaper|wallstat)\/(.+)(.png|.svg|.jpeg|.jpg)$', file_path)
                if re.search('\/gtk-2.0$', root):
                    self.gtk_list[dirname] = dir_path
                    self.theme_list['gtk'] = self.gtk_list
                elif re.search('\/metacity-1$', root):
                    self.metacity_list[dirname] = dir_path
                    self.theme_list['metacity'] = self.metacity_list
                elif re.search('\/cursors$', root):
                    self.mouse_list[dirname] = dir_path
                    self.theme_list['mouse'] = self.mouse_list
                elif re.search('\/index.theme$', file_path):
                    icon_path = os.path.dirname(file_path)
                    name = os.path.basename(icon_path)
                    print "unknown theme type but index.theme exists, testing it..."
                    tmp_data = open(file_path,'r')
                    txt = tmp_data.read()
                    if ('[Icon Theme]' in txt) and not os.path.exists(root+"/cursors"):
                        self.icons_list[name] = icon_path
                        self.theme_list['icons'] = self.icons_list
                    else:
                        print "unknown theme... %s" % root
                    tmp_data.close()
                elif re.search('\/Default.ini$', file_path):
                    tmp_data = open(file_path,'r')
                    txt = tmp_data.read()
                    if ('[cubemodel]' in txt):
                        cubemodels_path = os.path.dirname(file_path)
                        name = os.path.basename(cubemodels_path)
                        self.cubemodels_list[name] = cubemodels_path
                        self.theme_list['cubemodels'] = self.cubemodels_list
                    tmp_data.close()
                elif wallreg:
                    name = "%s%s" % (wallreg.group(2),wallreg.group(3))
                    print "wallpaper"
                    print name
                    self.wallstats_list[name] = file_path
                    self.theme_list['wallstats'] = self.wallstats_list
                elif re.search('.xml$', file_path):
                    file_obj = open(file_path)
                    xml_obj = minidom.parse(file_obj)
                    file_obj.close()
                    if xml_obj.getElementsByTagName("background"):
                        walldyn_path = os.path.dirname(file_path)
                        name = os.path.basename(walldyn_path)
                        self.walltimes_list[name] = walldyn_path
                        self.theme_list['walltimes'] = self.walltimes_list
                    elif re.search('\/elements.xml$', file_path):
                        fullpack_path = os.path.dirname(file_path)
                        name = os.path.basename(fullpack_path)
                        self.fullpacks_list[name] = fullpack_path
                        self.theme_list['fullpacks'] = self.fullpacks_list

    def install_themes(self):
        ## install themes
        types_element = ("gtk","metacity","icons","wallstats","walltimes","emerald","cubemodels",
                         "fullpacks","mouse")
        for type in types_element:
            self.install_element(type)
        ## refresh lists
        if not self.gstyle_obj:
            return
        for type,value in self.theme_list.items():
                if type == "icons":
                    self.gstyle_obj.gtk_gui.icon_obj.action_add_todic(self.theme_list)
                elif type == "gtk":
                    self.gstyle_obj.gtk_gui.gtk_obj.action_add_todic(self.theme_list)
                elif type == "metacity":
                    self.gstyle_obj.gtk_gui.metacity_obj.action_add_todic(self.theme_list)
                elif type == "wallstat":
                    self.gstyle_obj.gtk_gui.wallpaper_obj.action_add_todic(self.theme_list)
                elif type == "walltimes":
                    self.gstyle_obj.gtk_gui.wallpaper_obj.action_add_todic(self.theme_list)
                elif type == "emerald":
                    self.gstyle_obj.gtk_gui.emerald_obj.action_add_todic(self.theme_list)
                elif type == "cubemodel":
                    self.gstyle_obj.gtk_gui.cubemodel_obj.action_add_todic(self.theme_list)
                elif type == "mouse":
                    self.gstyle_obj.gtk_gui.mouse_obj.action_add_todic(self.theme_list)

    def install_element(self,main_type):
        type = main_type # by default
        destination = ""
        for name,temp_path in getattr(self,"%s_list" % type ,{}).items():
            copy = True   
            if main_type == "metacity":
                type = "gtk"
                if self.gtk_list.has_key(name):
                    copy = False
            elif main_type == "mouse":
                type = "icons"
                if self.icons_list.has_key(name):
                    copy = False
            target = globals().get("%s_target" % type)
            fam_liste = getattr(self,"%s_list" % main_type ,{})
            destination = os.path.join(target,name)
            if copy and os.path.exists(temp_path):
                self.copy_theme(temp_path,destination)
            fam_liste[name] = destination
            self.theme_list[main_type] = fam_liste

            print "%s theme successfully installed in %s" % (main_type,destination)
            
    def copy_theme(self,source,destination):
        if source == destination:
            return
        if os.path.exists(source):
            if os.path.isfile(source):
                move(source, destination)
            else:
                copy_tree(source, destination, 1, 1, 0, 1, 0)

    def extract_theme(self, obj, tmpdir):
        ## extraction
        try:
            obj.extractall(tmpdir)
            obj.close()
            return tmpdir
        except tarfile.TarError,e:
            print "extraction error : \n" + e
            return
        