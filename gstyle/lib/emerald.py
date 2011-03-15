#-*- coding: UTF-8 -*-
#Module standart
import os
import config
from glob import glob
import ConfigParser
import re
from shutil import rmtree,copytree
#Module gstyle
from theme_scaner import ThemeScaner

system_srcdir = "/usr/local/share/emerald/themes"
system_srcdir2 = "/usr/share/emerald/themes"
active_srcdir = os.path.join(config.homedir,".emerald/theme")
home_srcdir = os.path.join(config.homedir,".emerald/themes")
gstyle_conf_file = config.gstyle_conf_file

#emerald_active_srcdir = homedir+"/.emerald/theme"

class EmeraldDict(dict):

    def __init__(self,mode="sys",path_xml=None):
        super(EmeraldDict,self).__init__()
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
        usrlist2 = []
        homelist  = []
        self.list_theme = []
        if os.path.exists(system_srcdir):
            usrlist = glob(os.path.join(system_srcdir,"*"))
        if os.path.exists(home_srcdir):
            homelist = glob(os.path.join(home_srcdir,"*"))
        if os.path.exists(system_srcdir2):
            usrlist2 = glob(os.path.join(system_srcdir2,"*"))
        themelist = set(usrlist + homelist + usrlist2)

        for dir in themelist:
            if os.path.isdir(dir):
                self.add_item_system(dir)

    def add_item_system(self,path):
        if not os.path.exists(path):
            print "archive :  %s do not exists" % path
            return

        deskfile = os.path.join(path,"theme.ini")
        if not os.path.exists(deskfile):
            return
        image_path = os.path.join(path,"theme.screenshot.png")
        if not os.path.exists(image_path):
            return
        # TODO: verify if already exist
        name = os.path.basename(path)
        themeini = ConfigParser.RawConfigParser()
        themeini.readfp(open(deskfile))
        metadata = {}
        if themeini.has_section('theme') :
            if themeini.has_option("theme","creator"):
               metadata["creator"] = themeini.get( 'theme', 'creator' )
            if themeini.has_option("theme","description"):
               metadata["description"] = themeini.get( 'theme', 'description' )
            if themeini.has_option("theme","theme_version"):
               metadata["theme_version"] = themeini.get( 'theme', 'theme_version' )
            if themeini.has_option("theme","suggested"):
                metadata["suggested"] = themeini.get( 'theme', 'suggested' )
            if themeini.has_option("theme","version"):
                metadata["version"] = themeini.get( 'theme', 'version' )
            if not themeini.has_option("theme","name"):
                themeini.set('theme', 'name', name)
                if not('/usr' in deskfile):
                    with open(deskfile, 'wb') as configfile:
                        themeini.write(configfile)
        emerald_obj = Emerald(name = name,
                             path_theme = path,
                             creator = metadata.get("creator"),
                             img_path = image_path,
                             suggested = metadata.get("suggested"),
                             description = metadata.get("description"),
                             theme_version = metadata.get("theme_version")
                             )
        self[name] = emerald_obj
        return emerald_obj


    def add_item_archive(self,path_archive):
        """Ajouter un element dans le dictionnaire"""
        scaner = ThemeScaner(path_archive)
        theme_list = scaner.theme_loader(path_archive)
        if theme_list:
            return theme_list

    def del_item(self,name):
        """Supprimer un element dans le dictionnaire"""
        if not self.has_key(name) :
            return
        emerald_obj = self[name]
        srcdir = emerald_obj.path
        if re.search("/usr",srcdir):
            os.system(_("gksudo -m \"Please enter your password\" \'\'"))
            os.system("sudo rm -R \"%s\"" % srcdir)
        else :
            rmtree(srcdir)


    def active_item(self,name):
        emerald_obj = self[name]
        ##remove files in defaut theme dir
        if not os.path.exists(active_srcdir):
            os.makedirs(active_srcdir, 700)
        ## copy active theme's files...=
        rmtree(active_srcdir)
        copytree(emerald_obj.path,active_srcdir)
        os.system("nohup emerald --replace 2>/dev/null &")
        if os.path.exists("nohup.out"):
            os.remove("nohup.out")
        
        ## edit gstyle conf file
        parser = ConfigParser.RawConfigParser()
        parser.readfp(open(gstyle_conf_file))
        parser.set('emerald', 'name', emerald_obj.name)
        parser.set('emerald', 'path', emerald_obj.path)
        with open(gstyle_conf_file, 'wb') as configfile:
            parser.write(configfile)
        
    def get_active_item(self):
        parser = ConfigParser.RawConfigParser()
        parser.readfp(open(gstyle_conf_file))
        name = parser.get('emerald', 'name')
        if name:
            obj = self.get(name)
            if obj:
                return obj
         
class Emerald(object):
    def __init__(self,name,path_theme,creator,img_path,suggested,description=None,theme_version=None,version=None):
        self._img_path = img_path
        self._name = name
        self._path = path_theme
        self._creator = creator
        self._description = description
        self._theme_version = theme_version
        self._suggested = suggested
        self._version = version


    def get_img_path(self):
        return self._img_path

    img_path = property(get_img_path)

    def get_name(self):
        return self._name

    name = property(get_name)

    def get_path_theme(self):
        return self._path

    path = property(get_path_theme)

    def get_creator(self):
        return self._creator

    creator = property(get_creator)

    def get_description(self):
        return self._description

    description = property(get_description)

    def get_theme_version(self):
        return self._theme_version

    theme_version = property(get_theme_version)

    def get_suggested(self):
        return self._suggested

    suggested = property(get_suggested)

    def get_version(self):
        return self._version

    version = property(get_version)

