#!/usr/bin/env python
#-*- coding: UTF-8 -*-
#Module standart
import os
import config
from shutil import rmtree,copyfile
from xml.dom import minidom
import tarfile

#Module gstyle
from theme_scaner import ThemeScaner
from functions import gthread

fullpack_home_srcdir = config.fullpacks_srcdir
fullpack_imgdir = config.fullpacks_imgdir
fullpack_url_dir = config.fullpacks_url_dir
homedir = config.homedir

class FullPackDict(dict):
    def __init__(self,mode="sys",path_xml=None):
        super(FullPackDict,self).__init__()
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
        themelist = os.listdir(fullpack_home_srcdir)
        for item in themelist:
            dir = os.path.join(fullpack_home_srcdir, item)
            if not os.path.isdir(dir) or item =="img":
                pass
                #print "%s is not a valid fullpack theme" % item
            else:
                self.add_item_system(item)

    def add_item_system(self,name):
        path = os.path.join(fullpack_home_srcdir, name)
        pic = os.path.join(path, 'thumb.png')
        xml = os.path.join(path, 'elements.xml')
        if not(pic):
             return

        fullpack_obj = Fullpack(pic, name, path, xml)
        self[name] = fullpack_obj
        return fullpack_obj

    def get_img_folder(self,path):
        pass

    def add_item_archive(self, fullpack_archive):
        """Ajouter un element dans le dictionnaire"""
        scaner = ThemeScaner(fullpack_archive)
        theme_list = scaner.theme_loader(fullpack_archive)
        if theme_list:
            return theme_list
        else:
            print "no fullpack theme to install"

    def del_item(self,name):
        """Supprimer un element dans le dictionnaire"""
        fullpack_obj = self.get(name)
        if fullpack_obj:
            path = fullpack_obj.srcdir
            rmtree(path)
            del self[name]

    def gen_xml(self,fpack_dic,new=None):
        name = fpack_dic["packname"]
        if name:
            xml_file = os.path.join(fullpack_home_srcdir,name,"elements.xml")
            target_dir = os.path.join(fullpack_home_srcdir,name)
            try:
                os.mkdir(target_dir)
            except:
                pass
            dirs = ("gtk","metacity","icons","wallstat","walldyn",
                         "emerald","cubemodel","mouse")
            for dir in dirs:
                ndir = os.path.join(target_dir,dir)
                if not os.path.exists(ndir):
                    os.mkdir(ndir)
            xml_obj = minidom.Document()
            root = xml_obj.createElement("fullpack")
            xml_obj.appendChild(root)
            root.appendChild(xml_obj.createTextNode("\n"))
            root.appendChild(xml_obj.createComment("File elements.xml created by Gstyle"))
            root.appendChild(xml_obj.createTextNode("\n"))
            for key in fpack_dic.keys():
                value = fpack_dic[key]
                node = self.get_new_node(xml_obj,key,value)
                if node:
                    root.appendChild(node)
                    root.appendChild(xml_obj.createTextNode("\n"))
            xml_obj.writexml(open(xml_file,"w"),'','','', "UTF-8")

            if new:
                img = fpack_dic["img"]
                target = os.path.join(fullpack_home_srcdir,name,'thumb.png')
                copyfile(img,target)
                item = self.add_item_system(name)
                return item

    def active_item(self,name, gstyle_obj):
        fullpack_obj = self.get(name)
        file_obj = open(fullpack_obj.ini)
        xml_obj = minidom.parse(file_obj)
        file_obj.close()

        types_element = ("gtk","metacity","icons","wallstat","walldyn",
                         "emerald","cubemodel","mouse")
        for type in types_element:
            value = ""
            try:
                value = self.get_value_tag("%s" % type, xml_obj)
            except:
                continue
            if value != "":
                if type == "icons":
                    gstyle_obj.gtk_gui.icon_obj.action_apply(None,value)
                elif type == "gtk":
                    gstyle_obj.gtk_gui.gtk_obj.action_apply(None,value)
                elif type == "metacity":
                    gstyle_obj.gtk_gui.metacity_obj.apply_metacity_theme(None,value)
                elif type == "wallstat":
                    print value
                    gstyle_obj.gtk_gui.wallpaper_obj.apply_wallpaper("wallstats",None,value)
                elif type == "walldyn":
                    print value
                    gstyle_obj.gtk_gui.wallpaper_obj.apply_wallpaper("walldyns",None,value)
                elif type == "emerald":
                    gstyle_obj.gtk_gui.emerald_obj.apply_emerald_theme(None,value)
                elif type == "cubemodel":
                    gstyle_obj.gtk_gui.cubemodel_obj.action_apply(None,value)
                elif type == "mouse":
                    gstyle_obj.gtk_gui.mouse_obj.action_apply(None,None,value)
            else:
                print "no %s theme in this fullpack" % type

    def get_value_tag(self,name_tag,root_tag):
        tag = root_tag.getElementsByTagName(name_tag)
        if tag:
            tag = tag[0]
            return tag.firstChild.data
        else:
            return ""

    def set_value_tag(name_tag,root_tag,value):
        tag = root_tag.getElementsByTagName(name_tag)
        if tag:
            tag = tag[0]
            tag.firstChild.data = value

    def get_new_node(self,xml_obj,name_node,value_node):
        if value_node is None:
            value_node = ''
        node_tag = xml_obj.createElement(name_node)
        node_text = xml_obj.createTextNode(value_node)
        node_tag.appendChild(node_text)
        return node_tag

    def get_active_item(self):
        parser = ConfigParser.SafeConfigParser()
        parser.readfp(open(gstyle_conf_file))
        if parser.has_section('fullpack'):
              name = parser.get('fullpack','name')
              obj = self.get(name)
              if obj:
                  return obj

    def create_archive(self,name,source_dir,type, target, ext):
        archive_name = name+ext
        target_dir = os.path.join(target)
        target_file = os.path.join(target_dir,archive_name)
        os.chdir(target_dir)
        archive = tarfile.open(archive_name, 'w:gz')
        archive.add(source_dir, os.path.basename(source_dir))
        archive.close()

class Fullpack(object):
    def __init__(self,pic,name,srcdir,config):
        self._name = name
        self._picture = pic
        self._srcdir = srcdir
        self._ini = config

    def get_srcdir(self):
        return self._srcdir
    srcdir = property(get_srcdir)

    def get_picture(self):
        return self._picture
    picture = property(get_picture)

    def get_name(self):
        return self._name
    name = property(get_name)

    def get_ini(self):
        return self._ini
    ini = property(get_ini)


