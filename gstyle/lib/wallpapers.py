#-*- coding: UTF-8 -*-

import os
import glob
import shutil
from xml.dom import minidom
from xml.dom.minidom import Document
from datetime import datetime
import re
from shutil import rmtree

import config
from utils import htmlentitydecode, translate_html
from functions import gconf_set_string, gconf_get_string

conf_global_directory = "/usr/share/gnome-background-properties/"
LIST_FORMAT_STYLE = ['stretched', 'zoom', 'scaled', 'centered','wallpaper']
LIST_COLOR_STYLE = ['solid','horizontal-gradient','vertical-gradient']
gstyle_wallstat_dir = config.gstyle_backgrounds_data_dir
## our own backgrounds.xml but fully compatible with gnome and xdg
gstyle_background_xml = gstyle_wallstat_dir+'/gstyle.xml'

gstyle_wallstat_dir = config.wallpapers_home_srcdir
gstyle_walldyn_dir = config.walltimes_home_srcdir
wallstat_sysdir = config.wallpapers_system_srcdir

def get_value_tag(name_tag,root_tag):
        tag = root_tag.getElementsByTagName(name_tag)
        if tag:
            tag = tag[0]
            first_child = tag.firstChild
            return None if not first_child else first_child.data
        else:
            return None

def set_value_tag(name_tag,root_tag,value):
        tag = root_tag.getElementsByTagName(name_tag)
        if tag:
            tag = tag[0]
            tag.firstChild.data = value

def get_new_node(xml_obj,name_node,value_node):
        if name_node:
            node_tag = xml_obj.createElement(name_node)
        else:
            return
        if value_node:
            node_text = xml_obj.createTextNode(value_node)
            node_tag.appendChild(node_text)
        else:
            return
        return node_tag

class WallPaperDict(dict):
    def __init__(self,mode="sys",path_xml=None):
        super(WallPaperDict,self).__init__()
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
        theme_list= {}
        wallpapers_global = {}
        gstyle_wallpapers = {}
        ## for each xml file in /usr/share/gnome-background-properties
        for file_path in  glob.glob(conf_global_directory + "/*"):
            wallpapers_global.update(self.scan_file_xml(file_path))
        wallpapers_local = {}
        ## check the main gstyle background xml file
        if os.path.exists(gstyle_background_xml):
            wallpapers_local = self.scan_file_xml(gstyle_background_xml)
        else:
            ## create a basic wallpapers xml if not exist
            xml_obj = minidom.Document()
            root = xml_obj.createElement("wallpapers")
            xml_obj.appendChild(root)
            root.appendChild(xml_obj.createTextNode("\n"))
            root.appendChild(xml_obj.createComment("File backgrounds.xml create by Gstyle"))
            root.appendChild(xml_obj.createTextNode("\n\t"))
            xml_obj.writexml(open(gstyle_background_xml,"w"), "", "", "\n", "UTF-8")
            wallpapers_local = self.scan_file_xml(gstyle_background_xml)
        ## scan the system files
        gstyle_wallpapers = self.scan_system_files()
        if not gstyle_wallpapers:
            print "No wallpapers installed..."
            return
        wallpapers_global.update(gstyle_wallpapers)
        ## compare system and gstyle xml content
        wallpapers_add = set(wallpapers_global) - set(wallpapers_local)
        self.add_items_system( [value for key,value in wallpapers_global.items() if
                key in wallpapers_add])
        self.update(self.scan_file_xml(gstyle_background_xml))

    def scan_system_files(self):
    ## check files on the system specific to gstyle
        files_list = self.scan_for_backgrounds()
        if files_list:
            return files_list

    def scan_for_backgrounds(self):
        wallpapers_global = []
        wallstat_list = []
        walldyn_list = []
        # get wallpapers from /usr and home
        wallpapers_global = self.get_main_wall_list(wallstat_sysdir,
                                                    gstyle_wallstat_dir,
                                                    gstyle_walldyn_dir)
        for item in wallpapers_global:
            ## check for dirs in the list
            if os.path.isdir(item):
                flist = glob.glob(item+'/*')
                ## if yes look if we have a xml file in it for walldyn
                for file in flist:
                    if re.search('.xml$',file):
                        walldyn_xml = os.path.join(item,file)
                        walldyn_list.append(walldyn_xml)
                    if re.search('(.png|.svg|.jpeg|.jpg)$', file):
                        wallstat_list.append(os.path.join(item,file))
            if re.search('(.png|.svg|.jpeg|.jpg)$', item):
                wallstat_list.append(item)
        ## define global list
        wallpapers_index = {}
        list_wallpaper_obj = set(wallstat_list + walldyn_list)
        for file in list_wallpaper_obj:
            fname = os.path.basename(file)
            name = os.path.splitext(fname)[0]
            wallpapers_index[file] = WallPaper(file,name)
        return wallpapers_index

    def get_main_wall_list(self,srcdir,wallstat_dir,walldyn_dir):
        walldynlist = []
        if os.path.exists(srcdir):
            usrlist = glob.glob(srcdir+"/*")
        if os.path.exists(wallstat_dir):
            homelist = glob.glob(wallstat_dir+"/*")
        if os.path.exists(walldyn_dir):
            walldynlist = glob.glob(walldyn_dir+"/*")
        themelist = set(homelist + usrlist + walldynlist)
        return themelist

    def scan_file_xml(self,path):
        wallpapers_index = {}
        file_obj = open(path)
        xml_obj = minidom.parse(file_obj)
        file_obj.close()
        list_tag_wallpaper = xml_obj.getElementsByTagName("wallpaper")
        for tag in list_tag_wallpaper:
            deleted = tag.getAttribute("deleted")

            name = htmlentitydecode(get_value_tag("name",tag) or '' )
            filename =  htmlentitydecode(get_value_tag("filename",tag) or '')
            if filename == "(none)":
                continue
            options =  get_value_tag("options",tag)
            shade_type = get_value_tag("shade_type",tag)
            pcolor = get_value_tag("pcolor",tag)
            scolor = get_value_tag("scolor",tag)
            wallpapers_index[filename] = WallPaper(filename,name,options,shade_type,pcolor,scolor,deleted)
        return wallpapers_index

    def add_items_system(self,list_wallpaper_obj):
        if os.path.exists(gstyle_background_xml):
            file_obj = open(gstyle_background_xml,"r")
            xml_obj = minidom.parse(file_obj)
            file_obj.close()
        root_node = xml_obj.documentElement
        for wallpaper_obj in list_wallpaper_obj:
            xml_data = wallpaper_obj.get_xml(xml_obj)
            root_node.appendChild(xml_obj.createTextNode("\n\t"))
            root_node.appendChild(xml_data)
            root_node.appendChild(xml_obj.createTextNode("\n"))
        xml_obj.writexml(open(gstyle_background_xml,"w"), "", "", "", "UTF-8")

    def add_item_system(self,file):
        fname = os.path.basename(file)
        name = os.path.splitext(fname)[0]
        wallpaper_obj = WallPaper(file,name)
        filename = file
        file_obj = open(gstyle_background_xml,"r")
        xml_obj = minidom.parse(file_obj)
        file_obj.close()
        root_node = xml_obj.documentElement
        list_tag = xml_obj.getElementsByTagName("wallpaper")
        #Si la configuration existe déja dans le fichier xml
        #On la supprime et on remplace par la nouvelle
        if wallpaper_obj.filename in self:
            for tag in list_tag:
                if wallpaper_obj.filename == get_value_tag("filename",tag):
                    root_node.removeChild(tag)
                    del self[wallpaper_obj.filename]
                    break
        new_wallpaper = wallpaper_obj.get_xml(xml_obj)
        root_node.appendChild(new_wallpaper)
        root_node.appendChild(xml_obj.createTextNode("\n"))
        xml_obj.writexml(open(gstyle_background_xml,"w"), "", "", "", "UTF-8")
        file_obj.close()
        self[filename] = wallpaper_obj
        return wallpaper_obj

    def add_item_archive(self,path_archive):
        """Ajouter un element dans le dictionnaire"""
        pass


    def del_item(self,filename):
        """Supprimer un element dans le dictionnaire"""
        file_obj = open(gstyle_background_xml,"r")
        xml_obj = minidom.parse(file_obj)
        file_obj.close()
        list_tag = xml_obj.getElementsByTagName("wallpaper")
        root_node = xml_obj.documentElement
        for tag in list_tag:
            if filename == get_value_tag("filename",tag):
               tag.setAttribute("deleted","true")
               file_obj = open(gstyle_background_xml,'w')
               xml_obj.writexml(file_obj, "", "", "", "UTF-8")
               if filename in self:
                   self[filename].deleted = True
               break

    def set_active_item(self,filename):
        if os.path.exists(filename):
            gconf_set_string("/desktop/gnome/background/picture_filename",filename)

    def get_active_item(self):
        filename =  gconf_get_string("/desktop/gnome/background/picture_filename")
        if not filename:
            return
        if filename in self:
            obj = self[filename]
            return obj
        else:
            print "can't get wallpaper object for %s" % filename

    def get_dict_static_w(self):
        return  dict([(key,value) for key,value in self.items()
            if value.type == "static" and value.deleted == False])

    def get_dict_dynamique_w(self):
        return dict([(key,value) for key,value in self.items()
            if value.type == "dynamic" and value.deleted == False])

class WallPaper(object):
    def __new__(cls, *args, **kwargs):
        filename = args[0]
        if filename.strip().endswith(".xml"):
            return  WallDyn(*args, **kwargs)
        else:
            return  WallStat(*args, **kwargs)

class WallStat(object):
    type = "static"

    def __init__(self, filename, name=None, options="zoom", shade_type="solid",
            pcolor="#000000000000", scolor="#000000000000",deleted = False):

        if not name:
            self._name = filename.split("/")[-1].split(".")[0]
        self._name = name
        self._filename = filename
        self._options = options
        self._shade_type = shade_type
        self._pcolor = pcolor
        self._scolor = scolor
        if isinstance(deleted,str) or isinstance(deleted, unicode):
            if deleted.lower() == 'false':
                self._deleted = False
            else:
                self._deleted = True
        else:
            self._deleted = deleted


    def get_name(self):
        return self._name
    name = property(get_name)

    def get_filename(self):
        return self._filename
    filename = property(get_filename)

    def get_options(self):
        return self._options
    options = property(get_options)

    def get_shade_type(self):
        return self._shade_type
    shade_type = property(get_shade_type)

    def get_pcolor(self):
        return self._pcolor
    pcolor = property(get_pcolor)

    def get_scolor(self):
        return self._scolor
    scolor = property(get_scolor)

    def get_deleted(self):
        return self._deleted
    def set_deleted(self,value):
        if value in (True,False):
            self._deleted = value
    deleted = property(get_deleted,set_deleted)

    def get_path_img(self):
        return self._filename
    path_img = property(get_path_img)

    def get_xml(self,xml_obj):
        name = translate_html(unicode(self._name))
        if not name or name == "":
            return
        filename = translate_html(unicode(self._filename))
        if not filename or filename == "":
            return
        new_wallpaper = xml_obj.createElement("wallpaper")
        new_wallpaper.setAttribute("deleted","False")

        new_wallpaper.appendChild(xml_obj.createTextNode("\n\t\t"))
        new_wallpaper.appendChild(
            get_new_node(xml_obj,"name",name))
        new_wallpaper.appendChild(xml_obj.createTextNode("\n\t\t"))
        new_wallpaper.appendChild(
            get_new_node(xml_obj,"filename",filename))
        if not self._options or self._options == "":
            self._options = "zoom"
        new_wallpaper.appendChild(xml_obj.createTextNode("\n\t\t"))
        new_wallpaper.appendChild(
            get_new_node(xml_obj,"options",self._options))
        if not self._shade_type or self._shade_type == "":
            self._shade_type = "solid"
        new_wallpaper.appendChild(xml_obj.createTextNode("\n\t\t"))
        new_wallpaper.appendChild(
            get_new_node(xml_obj,"shade_type",self._shade_type))
        if not self._pcolor or self._pcolor == "":
            self._pcolor = "#000000000000"
        new_wallpaper.appendChild(xml_obj.createTextNode("\n\t\t"))
        new_wallpaper.appendChild(
            get_new_node(xml_obj,"pcolor",self._pcolor))
        if not self._scolor or self._scolor == "":
            self._scolor = "#000000000000"
        new_wallpaper.appendChild(xml_obj.createTextNode("\n\t\t"))
        new_wallpaper.appendChild(
            get_new_node(xml_obj,"scolor",self._scolor))
        new_wallpaper.appendChild(xml_obj.createTextNode("\n\t"))

        return new_wallpaper





class WallDyn(WallStat):
    type = "dynamic"

    def __init__(self, filename, name = None, options = "zoom", shade_type = "solid",
            pcolor = "#000000000000", scolor = "#000000000000",deleted = False):
        if not name:
            name = os.path.splitext(os.path.basename(filename))[0]
        super(WallDyn,self).__init__(filename,name,options,shade_type,pcolor,scolor,deleted)
        if filename:
            self.analyse_xml()

    def analyse_xml(self):
        self.flow_img = []
        if not os.path.exists(self.filename):
            return
        file_obj = open(self.filename)
        xml_obj = minidom.parse(file_obj)
        file_obj.close()
        try:
            list_background = xml_obj.getElementsByTagName("background")
        except:
            print "the walldyn %s is corrupted" % self.filename
            return
        if not list_background:
            return
        tag_background = list_background[0]
        self.starttime = None
        for tag in tag_background.childNodes:
            try:
                if tag.nodeName == u'starttime':
                    year = int(get_value_tag("year",tag).strip())
                    month = int(get_value_tag("month",tag).strip())
                    day = int(get_value_tag("day",tag).strip())
                    hour = int(get_value_tag("hour",tag).strip())
                    minute = int(get_value_tag("minute",tag).strip())
                    second = int(get_value_tag("second",tag).strip())
                    self.starttime = {'year':year,'month':month,'day':day,'hour':hour,'minute':minute,'second':second}
                elif tag.nodeName == u'static':
                    duration = get_value_tag("duration",tag)
                    file = get_value_tag("file",tag)
                    self.flow_img.append({"type":"static","duration":duration,"file":file})
                elif tag.nodeName == u'transition':
                    duration = get_value_tag("duration",tag)
                    file_from = get_value_tag("from",tag)
                    file_to = get_value_tag("to",tag)
                    self.flow_img.append({"type":"transition","duration":duration,\
                            "file_from":file_from,"file_to":file_to})
            except Exception,e:
                print "Walltime mal formé"
                print "erreur",e
                print self.filename
                continue
        if self.starttime and self.flow_img:
            return (self.starttime,self.flow_img)
    
    def get_list_img(self,trans=False):
        list_img = []
        for item in self.flow_img:
            ## remove transition when normal preview called this function
            if not trans and item["type"] == "transition":
                continue
            list_img.append(item)
        return list_img

    def get_path_img(self):
        if self.flow_img:
            step = self.flow_img[0]
            if step["type"] == "static":
                return step["file"]
            else:
                return step["file_to"]

    @staticmethod
    def set_path_img(path):
        dir = os.path.dirname(path)
        file_obj = open(path)
        xml_obj = minidom.parse(file_obj)
        file_obj.close()
        list_background = xml_obj.getElementsByTagName("background")
        if not(list_background):
            raise Exception,"Fichier xml non valide"
        tag_background = list_background[0]
        for tag in tag_background.childNodes:
            if tag.nodeName == u'static':
                file = get_value_tag("file",tag)
                file = os.path.join(dir,file.split("/")[-1])
                set_value_tag("file",tag,file)
            elif tag.nodeName == u'transition':
                file_from = get_value_tag("from",tag)
                file_from = os.path.join(dir,file_from.split("/")[-1])
                set_value_tag("from",tag,file_from)

                file_to = get_value_tag("to",tag)
                file_to = os.path.join(dir,file_to.split("/")[-1])
                set_value_tag("to",tag,file_to)
        xml_obj.writexml(open(path ,"w"), "", "", "", "UTF-8")


    def create_xml(self,filename, list_image):
        path_name = os.path.dirname(filename)
        #Create dir
        if os.path.exists(path_name):
            rmtree(path_name)
            os.makedirs(path_name)
        self.doc = Document()
        # Creation de la balise background
        self._background = self.doc.createElement("background")
        self.doc.appendChild(self._background)
        # Creation de la balise starttime
        self._starttime = self.doc.createElement("starttime")
        self._background.appendChild(self._starttime)
        self._background.appendChild(self.doc.createTextNode("\n"))
        # Creation des noeuds de startime
        self._starttime.appendChild(self.doc.createTextNode("\n"))
        self._createN(self._starttime,"year","2006")
        self._starttime.appendChild(self.doc.createTextNode("\n"))
        self._createN(self._starttime,"month","01")
        self._starttime.appendChild(self.doc.createTextNode("\n"))
        self._createN(self._starttime,"day","01")
        self._starttime.appendChild(self.doc.createTextNode("\n"))
        # TOCHECK
        # Bug de gnome chez moi? je dois commencer a 1 heure, et faire dans la suite comme ci cela etait 0h.
        # sinon au lieu d'avoir un apres midi (2.jpg) jusqu'a 5pm, je l'ai jusqu'a 4pm (pb heure gmt?)
        self._createN(self._starttime,"hour","1")
        self._starttime.appendChild(self.doc.createTextNode("\n"))
        self._createN(self._starttime,"minute","00")
        self._starttime.appendChild(self.doc.createTextNode("\n"))
        self._createN(self._starttime,"second","00")
        self._starttime.appendChild(self.doc.createTextNode("\n"))
        lenght = len(list_image)
        for index, image in enumerate(list_image):

            if  os.path.join(config.walltimes_home_srcdir,'temps') in image:
                image_dest = os.path.join(path_name,image.split('/')[-1])
                shutil.copyfile(image, image_dest)
                image = image_dest
            self._createNStatic('360', image)
            self._background.appendChild(self.doc.createTextNode("\n"))
            if index + 1 > lenght:
                image2 = list_image[0]
            else:
                image2 = list_image[index]
            self._createNTransition('180',image,image2)
            self._background.appendChild(self.doc.createTextNode("\n"))

        self.doc.writexml(open(filename ,"w"), "", "", "", "UTF-8")

    def _createNoeud(self,nom):
        noeud = self.doc.createElement(nom)
        return noeud

    def _createN(self,pere,fils,valeur=""):
        fils = self._createNoeud(fils)
        texte = self.doc.createTextNode(valeur)
        fils.appendChild(texte)
        pere.appendChild(fils)
        pere.appendChild(self.doc.createTextNode("\n"))

    def _createNStatic(self,durer,fichier):
        static = self.doc.createElement("static")
        self._background.appendChild(static)
        self._createN(static,"duration",durer)
        self._createN(static,"file",fichier)

    def _createNTransition(self,durer,fichier1,fichier2,mode="overlay"):
        transition = self.doc.createElement("transition")
        transition.setAttribute("type", mode)
        self._background.appendChild(transition)
        self._createN(transition,"duration",durer)
        self._createN(transition,"from",fichier1)
        self._createN(transition,"to",fichier2)
        


