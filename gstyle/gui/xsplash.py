#-*- coding: UTF-8 -*-

import os
import subprocess
import gconf
import gtk
import pwd
import ConfigParser

from shutil import copyfile
from config import _
from config import gtkThemes_home_srcdir, icons_home_srcdir
from config import exec_path
from functions import *

HOME = os.getenv("HOME")
GDMCONF = "/etc/gdm/custom.conf"

class XsplashGui(object):
    def __init__(self,gladexml,gstyle_obj):
        self.selected_gtk = None
        self.selected_icon = None
        self.selected_background = None
        
        self.gclient = gconf.client_get_default()
        self.gstyle_obj = gstyle_obj
        self.gtk_dict = self.gstyle_obj.gtk_dict
        self.wall_dict = self.gstyle_obj.wallpapers_dict.get_dict_static_w()
        self.icons_dict = self.gstyle_obj.icon_dict
        self.icon_obj = self.gstyle_obj.gtk_gui.icon_obj
        self.gtk_obj = self.gstyle_obj.gtk_gui.gtk_obj
        self.wallpaper_obj = self.gstyle_obj.gtk_gui.wallpaper_obj

        self.window = gladexml.get_widget("main_window")
        self.statbar = gladexml.get_widget("statusbar")

        self.gdm_toplabel = gladexml.get_widget("gdm_top_label")
        self.gdm_toplabel.set_text(_("Gdm:\nSelect your gtk/icons and wallpaper theme for gdm and choose your login options"))
        self.gdm_topimg = gladexml.get_widget("gdm_top_img")
        self.gdm_topimg.set_from_file(config.img_path+"/xsplash.png")
        
        ## img preview
        self.gdm_gtk_img = gladexml.get_widget("gdm_gtk_img")
        self.gdm_icon_img = gladexml.get_widget("gdm_icon_img")
        self.gdm_background_img = gladexml.get_widget("gdm_background_img")
        
        ## gdm options
        self.user_combo_widget = gladexml.get_widget("userlist_combo")
        model = gtk.ListStore(str)
        self.user_combo_widget.set_model(model)
        self.userlist_combo = ComboBox(self.user_combo_widget)
        
        self.showlogin_btn = gladexml.get_widget("showlogin_btn")
        self.autologin_btn = gladexml.get_widget("autologin_btn")
        self.userlist_btn = gladexml.get_widget("user_list_btn")
        self.welcome_btn = gladexml.get_widget("welcome_btn")
        self.welcome_textentry = gladexml.get_widget("welcome_textentry")
        self.playsound_btn = gladexml.get_widget("playsound_btn")
        self.restart_btn = gladexml.get_widget("restart_btn")
        
        self.gtk_combobox = gladexml.get_widget("gtk_combobox")
        self.gtk_combobox.set_model(self.gtk_obj.model)
        self.icons_combobox = gladexml.get_widget("icons_combobox")
        self.icons_combobox.set_model(self.icon_obj.model)
        self.background_combobox = gladexml.get_widget("background_combobox")
        self.background_combobox.set_model(self.wallpaper_obj.wallstats_model)
        
        dic = {"on_gtk_combobox_changed" : self.action_gtk,
               "on_icons_combobox_changed" : self.action_icons,
               "on_background_combobox_changed" : self.action_background,
               "on_gdm_apply_btn_clicked" : self.apply_gdm_config,
               "on_gdm_autosetup_clicked" : self.autosetup_gdm,
               "on_gdm_options_apply_btn_clicked" : self.save_gdm_conf,
              }
        gladexml.signal_autoconnect(dic)
        
    def check_gdm_options(self):
        ## get the user list
        list = pwd.getpwall()
        for user in list:
            if user.pw_uid >= 1000 and user.pw_name != "nobody":
                self.userlist_combo.append(user.pw_name)
        
        ## check conf file
        if not os.path.exists(GDMCONF):
            #os.popen("Gstyle", "")
            run_as_root("touch /etc/gdm/custom.conf")
        self.parser = ConfigParser.RawConfigParser()
        self.parser.optionxform = str
        self.parser.readfp(open(GDMCONF))
        if not self.parser.has_section('daemon'):
            self.parser.add_section('daemon')
            self.parser.set('daemon', 'AutomaticLoginEnable', False)
            self.parser.set('daemon', 'AutomaticLogin', "")
        
        if not self.parser.has_option("daemon","AutomaticLoginEnable"):
            self.parser.set('daemon', 'AutomaticLoginEnable', False)
        if not self.parser.has_option("daemon","AutomaticLogin"):
            self.parser.set('daemon', 'AutomaticLogin', "")
        
        self.autologin_state = self.parser.get('daemon', 'AutomaticLoginEnable')
        self.autologin_name = self.parser.get('daemon', 'AutomaticLogin')
        ## show user list
        self.browser_state = run_as_root("gconftool-2 --direct --config-source xml:readwrite:/var/lib/gdm/.gconf -g /apps/gdm/simple-greeter/disable_user_list")
        ## welcome msg
        self.welcome_state = run_as_root("gconftool-2 --direct --config-source xml:readwrite:/var/lib/gdm/.gconf -g /apps/gdm/simple-greeter/banner_message_enable")
        ## welcome text
        self.welcome_text = run_as_root("gconftool-2 --direct --config-source xml:readwrite:/var/lib/gdm/.gconf -g '/apps/gdm/simple-greeter/banner_message_text'")
        ## playsound_btn
        self.playsound_state = run_as_root("gconftool-2 --direct --config-source xml:readwrite:/var/lib/gdm/.gconf -g '/apps/gdm/simple-greeter/settings-manager-plugins/sound/active'")
        ## restart_btn
        self.restart_state = run_as_root("gconftool-2 --direct --config-source xml:readwrite:/var/lib/gdm/.gconf -g '/apps/gdm/simple-greeter/disable_restart_buttons'")
        
        if self.browser_state == "false":
            self.userlist_btn.set_active(1)
        if self.welcome_state == "true":
            self.welcome_btn.set_active(1)
        if self.welcome_text:
            self.welcome_textentry.set_text(self.welcome_text)
        if self.playsound_state == "true":
            self.playsound_btn.set_active(1)
        if self.restart_state == "true":
            self.restart_btn.set_active(1)
        if not self.autologin_state == "" and not self.autologin_state == "False":
            self.autologin_btn.set_active(1)
            if self.autologin_name:
                self.userlist_combo.setIndexFromString(self.autologin_name)
        else:
            self.showlogin_btn.set_active(1)
        
        if open(GDMCONF).read() == "":
            self.save_gdm_conf()
    
    def save_gdm_conf(self,widget=None):
        if os.path.exists('/tmp/custom.conf'):
            os.remove('/tmp/custom.conf')
        copyfile(GDMCONF,'/tmp/custom.conf')
        
        if self.autologin_btn.get_active():
            self.user_combo_widget.set_sensitive(1)
            self.autologin_state = True
            self.autologin_name = self.userlist_combo.getSelected()
            self.parser.set('daemon', 'AutomaticLoginEnable', True)
            self.parser.set('daemon', 'AutomaticLogin', self.autologin_name)
            
        if self.showlogin_btn.get_active():
            self.user_combo_widget.set_sensitive(0)
            self.autologin_state = False
            self.parser.set('daemon', 'AutomaticLoginEnable', False)
            self.autologin_name = ""
        
        with open('/tmp/custom.conf', 'wb') as configfile:
            self.parser.write(configfile)
        #run_as_root("Gstyle", "")
        
        run_as_root("mv -f /tmp/custom.conf /etc/gdm/custom.conf")
        run_as_root("sed -i 's/ = /=/g' %s" % GDMCONF)
        
        ## browser settings
        if self.userlist_btn.get_active():
            if not self.browser_state == "false":
                self.browser_state = False
                run_as_root("gconftool-2 --direct --config-source xml:readwrite:/var/lib/gdm/.gconf -s -t bool '/apps/gdm/simple-greeter/disable_user_list' 'False'")
        else:
            if self.browser_state == "false":
                self.browser_state = True
                run_as_root("gconftool-2 --direct --config-source xml:readwrite:/var/lib/gdm/.gconf -s -t bool '/apps/gdm/simple-greeter/disable_user_list' 'True'")
        ## welcome msg
        if self.welcome_btn.get_active():
            if not self.welcome_state == "true":
                self.welcome_state = True
                run_as_root("gconftool-2 --direct --config-source xml:readwrite:/var/lib/gdm/.gconf -s -t bool '/apps/gdm/simple-greeter/banner_message_enable' 'True'")
        else:
            if self.welcome_state == "true":
                self.welcome_state = False
                run_as_root("gconftool-2 --direct --config-source xml:readwrite:/var/lib/gdm/.gconf -s -t bool '/apps/gdm/simple-greeter/banner_message_enable' 'False'")
        ## text
        text = self.welcome_textentry.get_text()
        run_as_root("gconftool-2 --direct --config-source xml:readwrite:/var/lib/gdm/.gconf -s -t string '/apps/gdm/simple-greeter/banner_message_text' '%s'" % text)
            
        ## play sound settings
        if self.playsound_btn.get_active():
            if not self.playsound_state == "true":
                self.playsound_state = True
                run_as_root("gconftool-2 --direct --config-source xml:readwrite:/var/lib/gdm/.gconf -s -t bool '/apps/gdm/simple-greeter/settings-manager-plugins/sound/active' 'True'")
        else:
            if self.playsound_state == "true":
                self.playsound_state = False
                run_as_root("gconftool-2 --direct --config-source xml:readwrite:/var/lib/gdm/.gconf -s -t bool '/apps/gdm/simple-greeter/settings-manager-plugins/sound/active' 'False'")
        
        ## restart btn settings
        if self.restart_btn.get_active():
            if not self.restart_state == "true":
                self.restart_state = True
                run_as_root("gconftool-2 --direct --config-source xml:readwrite:/var/lib/gdm/.gconf -s -t bool '/apps/gdm/simple-greeter/disable_restart_buttons' 'True'")
        else:
            if self.restart_state == "true":
                self.restart_state = False
                run_as_root("gconftool-2 --direct --config-source xml:readwrite:/var/lib/gdm/.gconf -s -t bool '/apps/gdm/simple-greeter/disable_restart_buttons' 'False'")
        
    def action_gtk(self,widget):
        if not self.gtk_combobox.get_active_iter():
            return
        self.selected_gtk = self.gtk_combobox.get_active_text()
        theme = self.gstyle_obj.gtk_dict.get(self.selected_gtk)
        if not theme:
            self.gdm_gtk_img.set_from_stock("gtk-missing-image", gtk.ICON_SIZE_BUTTON)
            return
        env = os.environ
        env["GTK2_RC_FILES"] = theme.rcfile
        subprocess.call(["python", exec_path+"/imggen.py","/tmp/gtk-preview.png",theme.rcfile])
        try:
            pb = gtk.gdk.pixbuf_new_from_file("/tmp/gtk-preview.png")
        except Exception, ee:
            import traceback
            traceback.print_exc()
            return None
        if not pb is None:
            self.preview = pb
            self.gdm_gtk_img.set_from_pixbuf(pb)
        else:
            return None    

    def action_icons(self,widget):
        self.selected_icon = self.icons_combobox.get_active_text()
        theme = self.icons_dict.get(self.selected_icon)
        if theme:
            extension = os.path.splitext(theme.picture)[1]
            if extension == '.svg':
                img = gtk.gdk.pixbuf_new_from_file_at_size(theme.picture, 60, 60)
            elif extension == '.png':
                gtk.ACCEL_LOCKED
                img = gtk.gdk.pixbuf_new_from_file_at_size(theme.picture, 60, 60 )
            else:
                return
            self.gdm_icon_img.set_from_pixbuf(img)
        else:
            self.gdm_icon_img.set_from_stock("gtk-missing-image", gtk.ICON_SIZE_BUTTON)
            return
            
    def action_background(self,widget):
        name = self.background_combobox.get_active_text()
        for item in self.wall_dict.values():
            if item.name == name:
                self.selected_background = self.wall_dict[item.filename]
            else:
                continue
        if self.selected_background:
            img = gtk.gdk.pixbuf_new_from_file_at_scale(self.selected_background.path_img, 100, 100, 1 )
            self.gdm_background_img.set_from_pixbuf(img)
        else: 
            self.gdm_gtk_img.set_from_stock("gtk-missing-image", gtk.ICON_SIZE_BUTTON)
            return
   
    def run_sudo(self, cmd, msg):
        gksu_context = gksu2.Context()
        gksu_context.set_message(msg)
        gksu2.run(cmd)
        #try:
        #    password = gksu2.ask_password_full(gksu_context,_("Enter password : "))
        #except gobject.GError, e:
        #    if e.domain == "libgksu" and e.code == 11:
        #        "aborted"
        #    else:
        #        "print can't apply your theme"
        #return
        
    def apply_gdm_config(self,widget=None):
        #run_as_root("Gstyle", "gstyle need your password to set gdm/xsplash themes")
        if self.selected_icon:
            run_as_root("gconftool-2 --direct --config-source xml:readwrite:/var/lib/gdm/.gconf -t string -s '/desktop/gnome/interface/icon_theme' '%s'" % self.selected_icon)
        if self.selected_background:
            run_as_root("gconftool-2 --direct --config-source xml:readwrite:/var/lib/gdm/.gconf -t string -s '/desktop/gnome/background/picture_filename' '%s'" % self.selected_background.filename)
        if self.selected_gtk:
            run_as_root("gconftool-2 --direct --config-source xml:readwrite:/var/lib/gdm/.gconf -t string -s '/desktop/gnome/interface/gtk_theme' '%s'" % self.selected_gtk)
        self.update_themes()
        
    def autosetup_gdm(self,widget=None):
        ## search theme name from gconf
        #self.update_themes()
        icon_theme = self.gstyle_obj.icon_dict.get_active_item()
        wallpaper = self.gstyle_obj.wallpapers_dict.get_active_item()
        gtk_theme = self.gstyle_obj.gtk_dict.get_active_item()
        ## then show it in their comboboxes
        self.gtk_combo = ComboBox(self.gtk_combobox)
        self.icons_combo = ComboBox(self.icons_combobox)
        self.wallstat_combo = ComboBox(self.background_combobox)
        
        if gtk_theme:
            self.gtk_combo.setIndexFromString(gtk_theme.dirname)
        if icon_theme:
            self.icons_combo.setIndexFromString(icon_theme.dirname)
        if wallpaper.name:
            self.wallstat_combo.setIndexFromString(wallpaper.name)
        ## activate the selected themes if asked
        if widget:
            self.apply_gdm_config()
        
    def update_themes(self):
        if self.selected_gtk:
            gtk_syspath = os.path.join("/usr/share/themes",self.selected_gtk)
            gtk_homepath = os.path.join(gtkThemes_home_srcdir,self.selected_gtk)
            if not os.path.exists(gtk_syspath):
                run_as_root(""" ln -s "%s" "%s" """ % (gtk_homepath,gtk_syspath))
        if self.selected_icon:
            icons_syspath = os.path.join("/usr/share/icons",self.selected_icon)
            icons_homepath = os.path.join(icons_home_srcdir,self.selected_icon)
            if not os.path.exists(icons_syspath):
                run_as_root(""" ln -s "%s" "%s" """ % (icons_homepath,icons_syspath))

        
        
        