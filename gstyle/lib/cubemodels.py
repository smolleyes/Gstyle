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

cubemodels_home_srcdir = config.cubemodels_srcdir
cubemodels_imgdir = config.cubemodels_imgdir
cubemodels_url_dir = config.cubemodels_url_dir
compiz_config = config.compizConfig
homedir = config.homedir
gstyle_conf_file = config.gstyle_conf_file

class CubemodelsDict(dict):
    def __init__(self,mode="sys",path_xml=None):
        super(CubemodelsDict,self).__init__()
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
        themelist = os.listdir(cubemodels_home_srcdir)
        for item in themelist:
            dir = os.path.join(cubemodels_home_srcdir, item)
            if not os.path.isdir(dir) or item =="img":
                pass
            else:
                #print "%s is not a valid cubemodel theme" % item
                self.add_item_system(item)

    def add_item_system(self,name):
        path = os.path.join(cubemodels_home_srcdir, name)
        pic = os.path.join(path, 'thumb.png')
        config = os.path.join(path, 'Default.ini')
        if not(pic):
             return

        cubemodels_obj = Cubemodel(pic, name, path, config)
        self[name] = cubemodels_obj
        return cubemodels_obj

    def get_img_folder(self,path):
        pass

    def add_item_archive(self, cubemodel_archive):
        """Ajouter un element dans le dictionnaire"""
        scaner = ThemeScaner(cubemodel_archive)
        theme_list = scaner.theme_loader(cubemodel_archive)
        if theme_list:
            return theme_list
        else:
            print "no cubemodels theme to install"

    def del_item(self,name):
        """Supprimer un element dans le dictionnaire"""
        cubemodel_obj = self.get(name)
        if cubemodel_obj:
            path = cubemodel_obj.path
            shutil.rmtree(path)
            del self[name]

    def active_item(self,name):
        cubemodel_obj = self.get(name)
        if not cubemodel_obj:
            return
        compiz_ini = ConfigParser.SafeConfigParser()
        compiz_ini.readfp(open(compiz_config))
        compiz_ini.remove_section('cube')
        compiz_ini.remove_section('cubemodel')
        with open(compiz_config, 'wb') as configfile:
                    compiz_ini.write(configfile)
        os.system("cat %s | tee -a %s >/dev/null" % (cubemodel_obj.ini, compiz_config))
        
        ## edit gstyle conf file
        parser = ConfigParser.RawConfigParser()
        parser.readfp(open(gstyle_conf_file))
        parser.set('cubemodel', 'name', cubemodel_obj.name)
        parser.set('cubemodel', 'path', cubemodel_obj.path)
            
        with open(gstyle_conf_file, 'wb') as configfile:
            parser.write(configfile)

    def check_plugins(self):
        compiz_ini = ConfigParser.SafeConfigParser()
        if not os.path.exists(compiz_config):
			print compiz_config + " do not exist..."
			return
        compiz_ini.readfp(open(compiz_config))
        list_section = compiz_ini.sections()
        if compiz_ini.has_section('core'):
            if compiz_ini.has_option('core','as_active_plugins'):
                plug_list = compiz_ini.get('core','as_active_plugins')
            else:
                return
        else:
            print "Compiz Default.ini exist but empty or core section do not exist"
            return

        list = ['cubemodel', 'cube']
        for plug in list:
            ## check cubemodel
            if re.search('%s;' % plug, plug_list):
                print "plugin %s actif... OK" % plug
            else :
                print "plugin %s inactif, activation..." % plug
                #compiz_ini.remove_option('core', 'as_active_plugins')
                plug_list = plug_list + plug + ";"
                compiz_ini.set('core', 'as_active_plugins', plug_list)
                with open(compiz_config, 'wb') as configfile:
                    compiz_ini.write(configfile)

        print "Compiz/cubemodel check finished... OK\n"

    def edit_theme_ini(self,item):
    ## prepare replacement link for the skydome and 3d models in the .ini
        obj_path = os.path.join(item.path, 'obj/')
        skydome_path = os.path.join(item.path, 'skydome/')
        ## open the theme .ini and load sections
        theme_ini = ConfigParser.SafeConfigParser()
        theme_ini.readfp(open(item.ini))
        sections = theme_ini.sections()
        ## check cube and cubemodel sections and extract values
        if theme_ini.has_section('cubemodel'):
            if theme_ini.has_option('cubemodel','s0_model_filename'):
                obj_list = theme_ini.get('cubemodel','s0_model_filename')
                res = ''.join([obj_path + match.group(1) for match in re.finditer('([^/]+/[^/]+.obj;)', obj_list)])
                theme_ini.set('cubemodel', 's0_model_filename', res)
            else:
                return
        if theme_ini.has_section('cube'):
            if theme_ini.has_option('cube','s0_skydome_image'):
                skydome_link = theme_ini.get('cube','s0_skydome_image')
                oldpath = os.path.dirname(skydome_link)
                res = re.sub(oldpath, skydome_path, skydome_link)
                theme_ini.set('cube', 's0_skydome_image', res)
            else:
                return

        with open(item.ini, 'wb') as configfile:
                theme_ini.write(configfile)

    def create_theme(self, theme_name, img_path):
        compiz_ini = ConfigParser.SafeConfigParser()
        compiz_ini.readfp(open(compiz_config))
        list_section = compiz_ini.sections()
        if compiz_ini.has_section('cubemodel'):
            obj_list = compiz_ini.get('cubemodel','s0_model_filename')
        else:
            return
        if compiz_ini.has_section('cube'):
            skydome_link = compiz_ini.get('cube','s0_skydome_image')
        else:
            return
        ## create themedir
        target = os.path.join(cubemodels_home_srcdir, theme_name)
        if os.path.exists(target):
            shutil.rmtree(target)
        os.makedirs(target+"/obj", 0755)
        os.makedirs(target+"/skydome", 0755)
        ## copy obj files
        objlist = obj_list.split(";")
        for file in objlist:
            if os.path.exists(file):
                shutil.copy(file, target+"/obj")

        ## copy skydome
        shutil.copy(skydome_link, target+"/skydome")
        ## rename image file
        shutil.copy(img_path, target+"/thumb.png")

        ################################################
        # Now extract cubemodels and cube section from compiz ini and edit it
        theme_ini = target+"/Default.ini"
        with open(theme_ini, 'wb') as configfile:
            compiz_ini.write(configfile)
        parser = ConfigParser.SafeConfigParser()
        parser.readfp(open(theme_ini))
        ## first remove all sections but cube and cubemodel
        for section in list_section:
            if not(section == "cubemodel" or section == "cube"):
                parser.remove_section(section)

        # changes object links
        obj_list = parser.get('cubemodel','s0_model_filename').split(";")
        new_list = []
        for link in obj_list:
            name = os.path.basename(link)
            path = os.path.dirname(link)
            dirname = os.path.basename(path)
            if os.path.exists(path):
                if not os.path.exists(target+"/obj/"+dirname):
                    shutil.copytree(path, target+"/obj/"+dirname)
                elif not os.path.exists(target+"/obj/"+dirname+"/"+name):
                    shutil.copy(path, target+"/obj/"+dirname+"/"+name)
                res = re.sub(link,target+"/obj/"+dirname+"/"+name+";",link)
                new_list.append(res)
            else:
                continue
        l = "".join(new_list)
        parser.set('cubemodel', 's0_model_filename', l)

        ## for the skydome
        sky = parser.get('cube','s0_skydome_image')
        skyname = os.path.basename(sky)
        if sky:
            if os.path.exists(sky):
                res = re.sub(sky,target+"/skydome/"+skyname,sky)
            else:
                return
            parser.set('cube', 's0_skydome_image', res)

        with open(theme_ini, 'wb') as configfile:
            parser.write(configfile)
        ## then compress the theme with lzma
        target_file = homedir+"/"+theme_name+".tar.lzma"
        if os.path.exists(target_file):
            os.remove(target_file)
        try:
            os.chdir(cubemodels_home_srcdir)
            os.system("tar -cv \""+theme_name+"\" | lzma -z --best > \""+target_file+"\"")
            print "\nTheme successfully created in "+target_file
        except:
            print "Lzma archive %s can't be created" % target_file

        ## and finally add it to the gstyle list
        self.add_item_system(theme_name)
        
    def get_active_item(self):
        parser = ConfigParser.SafeConfigParser()
        parser.readfp(open(gstyle_conf_file))
        if parser.has_section('cubemodel'):
              name = parser.get('cubemodel','name')
              obj = self.get(name)
              if obj:
                  return obj 
        
class Cubemodel(object):
    def __init__(self,pic,name,path,config):
        self._name = name
        self._picture = pic
        self._path = path
        self._ini = config

    def get_path(self):
        return self._path
    path = property(get_path)

    def get_picture(self):
        return self._picture
    picture = property(get_picture)

    def get_name(self):
        return self._name
    name = property(get_name)

    def get_ini(self):
        return self._ini
    ini = property(get_ini)

