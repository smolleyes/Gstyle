#-*- coding: UTF-8 -*-
import os
import config
import ConfigParser
import time
from shutil import rmtree,copy,move
#Module gstyle
from theme_scaner import ThemeScaner
from functions import gconf_set_string
from functions import scan_system_themes
from functions import gconf_set_string,gconf_get_string

srcdir = config.icons_srcdir
icons_home_srcdir = config.icons_home_srcdir
mouse_srcdir = config.gstyle_mouse_srcdir+"/img"
converter = "/usr/bin/xcur2png"
no_preview = config.no_preview_img

import config

class MouseDict(dict):
    def __init__(self,mode="sys",path_xml=None):
        super(MouseDict,self).__init__()
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
        themelist = scan_system_themes(srcdir, icons_home_srcdir)
        os.chdir('/tmp')
        for path in themelist:
            if os.path.isdir(path) and not("Default" in path):
                if os.path.exists(path+"/cursors"):
                    self.add_item_system(path)

    def add_item_system(self,theme_path):
        dirname = os.path.basename(theme_path)
        name = dirname ## by default
        ## xcur2png do not support spaces so replace it by _ if needed
        from string import replace
        if (' ' in name):
            name = name.replace(' ','_')
            old_path=theme_path
            dirbase= os.path.dirname(old_path)
            theme_path=os.path.join(dirbase,name)
            os.rename(old_path,theme_path)
    
        deskfile = os.path.join(theme_path,"index.theme")
        target_img = os.path.join(mouse_srcdir, name+".png")
        ## check if theme thumb already exists
        if not os.path.exists(target_img):
            if not os.path.exists(converter):
                return "xcur2png not installed"
            ## generate thumbnail for gstyle
            img_list = ["left_ptr","Button","right_ptr"]
            base_img = None
            for img in img_list:
                src_img = os.path.join(theme_path,'cursors/'+img)
                if os.path.exists(src_img):
                    os.chdir('/tmp')
                    base_img = src_img
                    t = None
                    try:
                        t = os.system(converter +" %s -d %s" % (base_img,mouse_srcdir))
                    except:
                        return
                    while 1:
                        if not os.path.exists(mouse_srcdir+"/"+img+"_000.png"):
                            time.sleep(1)
                        else:
                            break
                    move(mouse_srcdir+"/"+img+"_000.png", target_img)
                    os.chdir(config.exec_path)
                else:
                    continue
            ## check for image preview
            if not base_img:
                print "mouse image preview not available"
                base_img = no_preview
                copy(base_img, target_img)
                
        metadata = {}
        metadata["comment"] = ""
        metadata["example"] = ""
        metadata["inherit"] = ""
        
        if os.path.exists(deskfile):
            themeini = ConfigParser.RawConfigParser()
            themeini.readfp(open(deskfile))
            if themeini.has_section('Icon Theme') :
                if themeini.has_option('Icon Theme', 'Comment'):
                   metadata["comment"] = themeini.get( 'Icon Theme', 'Comment' )
                if themeini.has_option('Icon Theme','Example'):
                    metadata["example"] = themeini.get( 'Icon Theme', 'Example')
                if themeini.has_option('Icon Theme','Inherit'):
                    metadata["inherit"] = themeini.get( 'Icon Theme','Inherit')

        mouse_obj = mouse(name = name,
                      comment = metadata.get("comment"),
                      example = metadata.get("example"),
                      inherit = metadata.get("inherit"),
                      pic = target_img,
                      path = theme_path,
                      dirname = dirname,
                      )

        self[name] = mouse_obj
        return mouse_obj

    def add_item_archive(self,archive):
        """Ajouter un element dans le dictionnaire"""
        scaner = ThemeScaner(archive)
        theme_list = scaner.theme_loader(archive)
        if theme_list:
            return theme_list
        else:
            print "no mouse theme in this file"

    def del_item(self,dirname):
        """Supprimer un element dans le dictionnaire"""
        mouse_obj = self.get(dirname)
        if mouse_obj:
            path = mouse_obj.path
            rmtree(path)
            os.remove(os.path.join(mouse_srcdir, dirname+".png"))
            del self[dirname]

    def set_active_item(self,dir):
        value = os.path.basename(dir)
        gconf_set_string("/desktop/gnome/peripherals/mouse/cursor_theme",value)
            
    def get_active_item(self):
        name =  gconf_get_string("/desktop/gnome/peripherals/mouse/cursor_theme")
        return self.get(name)


class mouse(object):
    def __init__(self,name,comment,example,inherit,pic,path,dirname):
        self._name = name
        self._comment = comment
        self._example = example
        self._inherit = inherit
        self._pic = pic
        self._path = path
        self._dirname = dirname

    def get_name(self):
        return self._name
    name = property(get_name)

    def get_comment(self):
        return self._comment
    comment = property(get_comment)

    def get_example(self):
        return self._example
    example = property(get_example)

    def get_inherit(self):
        return self._inherit
    inherit = property(get_inherit)

    def get_pic(self):
        return self._pic
    pic = property(get_pic)

    def get_path(self):
        return self._path
    path = property(get_path)
    
    def get_dirname(self):
        return self._dirname
    dirname = property(get_dirname)


