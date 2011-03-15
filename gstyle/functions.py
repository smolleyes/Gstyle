#!/usr/bin/env python
# -*- coding: utf-8 -*-
import metacity
import gconf
import os
import gtk
from glob import glob
import time
import urllib
import shutil
import threading
import time
import sys
import random
import dbus
import config
from config import _
home = config.homedir
INSTALL_GLADE=os.path.join(config.glade_path,'install-preview.glade')
APP_NAME = "gstyle"
GUI = os.path.join(config.glade_path,'data/glade/Gstyle.glade')
secret_key = ''.join([chr(random.randint(97,122)) for i in range(0, 64)])

import dbus
import gobject
from dbus.mainloop.glib import DBusGMainLoop
#must be done before connecting to DBus
DBusGMainLoop(set_as_default=True)

#gobject.threads_init()

gclient = gconf.client_get_default()

## to change gconf bool keys ex : set_bool_key('/desktop/gnome/background/draw_background', 1)
map_type = {gconf.VALUE_BOOL : 'bool',
            gconf.VALUE_FLOAT : 'float',
            gconf.VALUE_INT : 'int',
            gconf.VALUE_LIST : 'list',
#            gconf.VALUE_PAIR : 'pair',
            gconf.VALUE_SCHEMA : 'schema',
            gconf.VALUE_STRING : 'string'}

def gconf_get(key):
    obj_key = gclient.get(key)
    result = None
    if obj_key:
        type_key = obj_key.type
        if type_key in map_type:
            result = getattr(obj_key, 'get_%s' % map_type[type_key])()
    return result

def gconf_set_bool(key, value_bool):
    gclient.set_bool(key, value_bool)

def gconf_set_string(key, value_string):
    gclient.set_string(key, value_string)

def gconf_get_string(key):
    return gclient.get_string(key)

def yesno(title,msg):
    dialog = gtk.MessageDialog(parent = None,
    buttons = gtk.BUTTONS_YES_NO,
    flags =gtk.DIALOG_DESTROY_WITH_PARENT,
    type = gtk.MESSAGE_QUESTION,
    message_format = msg
    )
    dialog.set_position("center")
    dialog.set_title(title)
    result = dialog.run()
    dialog.destroy()

    if result == gtk.RESPONSE_YES:
        return "Yes"
    elif result == gtk.RESPONSE_NO:
        return "No"

def error_dialog(message, parent = None):
    """
    Displays an error message.
    """

    dialog = gtk.MessageDialog(parent = parent, type = gtk.MESSAGE_ERROR, buttons = gtk.BUTTONS_OK, flags = gtk.DIALOG_MODAL)
    dialog.set_markup(message)
    dialog.set_position('center')

    result = dialog.run()
    dialog.destroy()

def add_filters(filechooser,myfilter):
    filter = gtk.FileFilter()
    name = _("Supported files")
    filter.set_name(name + ' ' + ','.join(myfilter))
    for f in myfilter:
        filter.add_pattern(f)
    filechooser.add_filter(filter)

    filter = gtk.FileFilter()
    filter.set_name(_("All files"))
    filter.add_pattern("*")
    filechooser.add_filter(filter)

def create_filechooser_open(title,myfilter):
    buttons     = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                   gtk.STOCK_OPEN,   gtk.RESPONSE_OK)
    filechooser = gtk.FileChooserDialog(title,
                                        None,
                                        gtk.FILE_CHOOSER_ACTION_OPEN,
                                        buttons)
    add_filters(filechooser,myfilter)
    filechooser.set_current_folder(home)
    filechooser.set_position('center')
    return filechooser


def create_filechooser_save():
    buttons     = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                   gtk.STOCK_SAVE,   gtk.RESPONSE_OK)
    filechooser = gtk.FileChooserDialog((_("Save...")),
                                        None,
                                        gtk.FILE_CHOOSER_ACTION_SAVE,
                                        buttons)
    filechooser.set_do_overwrite_confirmation(True)
    add_filters(filechooser)
    return filechooser

def get_theme_from_html(url):
    # Get something to work with.
    try:
        f = urllib.urlopen(url)
    except:
        print "can t connect website : %s" % url
        return
    s = f.read()
    # Try and process the page.
    # The class should have been defined first, remember.
    myparser = MyParser()
    myparser.parse(s)

    # Get the hyperlinks.
    return myparser.get_hyperlinks()

def parse_name_from_link(links, ext):
    for link in links:
            elem_thname = fileparse(link, ext)
            theme_folder = os.path.join(elem_themedir,elem_thname)
            img_name = os.path.join(elem_imgdir,elem_thname+".png")

            if not os.path.exists(theme_folder):
                if not os.path.exists(img_name):
                    print "telecharge le fichier thumb... \n"
                    os.system("wget -q %s/%s/thumb.png -O img_name" % (elem_themedir, elem_thname))
                    rename(elem_imgdir+"/thumb.png", img_name)
                else:
                    pass

def refresh_themes_download(theme_list, model, basedir):
    i = 0
    for link in theme_list:
        if ('php' in link):
            continue
        archive = os.path.basename(link)
        srcdir = os.path.dirname(link)
        name = os.path.basename(srcdir)
        img = os.path.join(srcdir, 'thumb.png')
        localdir = os.path.join(basedir, name)
        localimg = os.path.join(basedir,'img', name+'.png')
        if not os.path.exists(localdir):
            i += 1
            if not os.path.exists(localimg):
                os.system("wget -q %s -O %s" % (img, localimg))
        else :
            continue
        try:
            img = gtk.gdk.pixbuf_new_from_file_at_scale(localimg,  100, 100 , 1)
        except:
            continue
        iter = model.append()
        model.set(iter,
                  0, img,
                  1, name,
                  2, link,
                  )
    ## just return number of available themes
    return(i)

def theme_downloader(link, name):
    path = os.path.join(link,'/tmp/cubedown-'+name)
    target = os.path.join(path,name+".tar.lzma")
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)
    data = urllib.urlretrieve(link,target)
    return target

def scan_system_themes(srcdir, home_src):
    usrlist = []
    homelist = []
    if os.path.exists(home_src):
        for i in os.listdir(home_src):
            if not os.path.islink(home_src+'/'+i):
                usrlist.append(home_src+'/'+i)
    if os.path.exists(srcdir):
        for i in os.listdir(srcdir):
            if not os.path.islink(srcdir+'/'+i):
                usrlist.append(srcdir+'/'+i)
    themelist = set(homelist + usrlist)
    return themelist

### Html parsing class
import sgmllib
class MyParser(sgmllib.SGMLParser):
    "A simple parser class."

    def parse(self, s):
        "Parse the given string 's'."
        self.feed(s)
        self.close()

    def __init__(self, verbose=0):
        "Initialise an object, passing 'verbose' to the superclass."

        sgmllib.SGMLParser.__init__(self, verbose)
        self.hyperlinks = []

    def start_a(self, attributes):
        "Process a hyperlink and its 'attributes'."

        for name, value in attributes:
            if name == "href":
                self.hyperlinks.append(value)

    def get_hyperlinks(self):
        "Return the list of hyperlinks."
        return self.hyperlinks


def make_metacity_preview(metacity_viewer, name):
        theme = metacity.theme_load(name)
        if theme:
            theme_preview = metacity.Preview()
            viewport = gtk.Viewport()
            theme_preview.add(viewport)
            theme_preview.set_border_width(5)
            theme_preview.set_theme(theme)
            theme_preview.set_title(name+" Preview")
            for item in metacity_viewer.get_children():
                metacity_viewer.remove(item)
            metacity_viewer.add(theme_preview)
            theme_preview.realize()
            theme_preview.show()

        #take_screenshot(theme_preview)

def take_screenshot(theme_preview):
    w = theme_preview.window
    root = gtk.gdk.get_default_root_window()
    sz = w.get_size()
    pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,1,8,sz[0],sz[1])
    ## This line was deleted: #pb = pb.get_from_drawable(w,root.get_colormap(),0,0,0,0 ,sz[0],sz[1])
    # The following two lines were added:
    pm = theme_preview.get_snapshot(None)
    pb = pb.get_from_drawable(pm, pm.get_colormap(), 0,0,0,0,sz[0],sz[1])
    if pb is not None:
        pb.save(os.path.expanduser("~/pb.png"),"png")
        print "saved"
    else:
        print "error"

def create_archive(src,name,target,type):
    pass

def install_dialog(theme_list, archive):
    ## glade dialog
    dialog_gui = gtk.glade.XML(INSTALL_GLADE,None,APP_NAME)
    install_dialog = dialog_gui.get_widget("install_dialog")
    install_dialog.set_title(_("Scan results"))
    install_dialog.set_position("center")
    install_label = dialog_gui.get_widget("install_dialog_label")
    install_label.set_text(_("Scan report for : \n\
%s \n\n The followings themes are ready to install !") % archive)
    ## gtk
    if theme_list.has_key('gtk'):
        gtk_label = dialog_gui.get_widget("gtk_label")
        gtk_label.set_text('\n'.join(theme_list['gtk']))
    ## icons
    if theme_list.has_key('icons'):
        icons_label = dialog_gui.get_widget("icons_label")
        icons_label.set_text('\n'.join(theme_list['icons']))
    ## metacity
    if theme_list.has_key('metacity'):
        metacity_label = dialog_gui.get_widget("metacity_label")
        metacity_label.set_text('\n'.join(theme_list['metacity']))
    ## cursors
    if theme_list.has_key('mouse'):
        cursors_label = dialog_gui.get_widget("cursors_label")
        cursors_label.set_text('\n'.join(theme_list['mouse']))
    ## emerald
    if theme_list.has_key('emerald'):
        emerald_label = dialog_gui.get_widget("emerald_label")
        emerald_label.set_text('\n'.join(theme_list['emerald']))
    ## cubemodel
    if theme_list.has_key('cubemodels'):
        cubemodels_label = dialog_gui.get_widget("cubemodels_label")
        cubemodels_label.set_text('\n'.join(theme_list['cubemodels']))
    ## wallpaper
    if theme_list.has_key('wallstats'):
        wallpapers_label = dialog_gui.get_widget("wallpapers_label")
        wallpapers_label.set_text('\n'.join(theme_list['wallstats']))
    ## walltimes
    if theme_list.has_key('walltimes'):
        wallpapers_label = dialog_gui.get_widget("walltimes_label")
        wallpapers_label.set_text('\n'.join(theme_list['walltimes']))
    ## fullpack
    if theme_list.has_key('fullpacks'):
        fullpack_label = dialog_gui.get_widget("fullpacks_label")
        fullpack_label.set_text('\n'.join(theme_list['fullpacks']))

    install_result = install_dialog.run()
    install_dialog.destroy()
    ## get glade return code
    if install_result == 0:
        return True
    else:
        return False


def _reporthook(numblocks, blocksize, filesize, progress, url=None):
    #print "reporthook(%s, %s, %s)" % (numblocks, blocksize, filesize)
    base = os.path.basename(url)
    #XXX Should handle possible filesize=-1.
    if numblocks != 0:
        try:
            percent = min((numblocks*blocksize*100)/filesize, 100)
        except:
            percent = 100
        if percent < 100:
            time.sleep(0.005)
            progress.set_text(_("Downloading %-66s%3d%% done") % (base, percent))
            progress.set_fraction(percent/100.0)
            gtk.main_iteration_do(False)
        else:
            #progress.set_text("%-66s%3d%%" % (base, percent))
            progress.hide()
            return
    return

def geturl(url, dst, progressbar):
    progressbar.show()
    #print "get url '%s' to '%s'" % (url, dst)
    urllib.urlretrieve(url, dst,
    lambda nb, bs, fs, url=url: _reporthook(nb,bs,fs,progressbar,url))
    return dst

def gthread(cmd):
    thread = threading.Thread(None, cmd)
    thread.start()
    
    while(1):
        while(gtk.events_pending()):
            gtk.main_iteration()
        if not thread.isAlive():
            break
        else:
            time.sleep(0.2)
            
def run(cmd, ignore_error=False):
    is_string_not_empty(cmd)
    if not isinstance(ignore_error,  bool): raise TypeError

    if getattr(run, 'terminal', None):
        assert run.terminal.__class__.__name__ == 'Terminal'
        try:
            run.terminal.run(cmd)
        except CommandFailError:
            if not ignore_error: raise
    else:
        print '\x1b[1;33m', _('Run command:'), cmd, '\x1b[m'
        import os
        if os.system(cmd) and not ignore_error: raise CommandFailError(cmd)

def pack(D):
    assert isinstance(D, dict)
    import StringIO
    buf = StringIO.StringIO()
    for k,v in D.items():
        print >>buf, k
        print >>buf, v
    return buf.getvalue()
            
def packed_env_string():
        import os
        env = dict( os.environ )
        env['PWD'] = os.getcwd()
        return pack(env)

def get_authentication_method():
    import dbus
    bus = dbus.SystemBus()
    obj = bus.get_object('cn.gstyle', '/')
    ignore_error=True
    ret = obj.get_check_permission_method(dbus_interface='cn.gstyle.Interface')
    ret = int(ret)
    assert ret == 0 or ret == 1, ret
    return ret

def authenticate():
    if get_authentication_method() == 0:
        import dbus
        bus = dbus.SessionBus()
        policykit = bus.get_object('org.freedesktop.PolicyKit.AuthenticationAgent', '/')
        import os
        policykit.ObtainAuthorization('cn.gstyle', dbus.UInt32(0), dbus.UInt32(os.getpid()))

def spawn_as_root(command):
    is_string_not_empty(command)
    authenticate()
    import dbus
    bus = dbus.SystemBus()
    obj = bus.get_object('cn.gstyle', '/')
    t = obj.spawn(command, packed_env_string(), secret_key, dbus_interface='cn.gstyle.Interface')
    return t
    
def drop_priviledge():
    import dbus
    bus = dbus.SystemBus()
    obj = bus.get_object('cn.gstyle', '/')
    obj.drop_priviledge(secret_key, dbus_interface='cn.gstyle.Interface')


def run_as_root(cmd, ignore_error=False):
    is_string_not_empty(cmd)
    assert isinstance(ignore_error, bool)
    
    import os
    if os.getuid()==0:
        run(cmd, ignore_error)
        return
    
    print '\x1b[1;33m', _('Run command:'), cmd, '\x1b[m'
    authenticate()
    bus = dbus.SystemBus()
    obj = bus.get_object('cn.gstyle','/')
    ret=None
    try:
        ret = obj.run(cmd, packed_env_string(), secret_key, ignore_error,
                              timeout=36000,dbus_interface='cn.gstyle.Interface')
    except dbus.exceptions.DBusException, e:
        if e.get_dbus_name() == 'cn.gstyle.AccessDeniedError': raise AccessDeniedError
        else: raise
    return ret
        
def on_message_received(self):
    print "message_signal caught"
    
class AccessDeniedError(Exception):
    'User press cancel button in policykit window'

def is_string_not_empty(string):
    if type(string)!=str and type(string)!=unicode: raise TypeError(string)
    if string=='': raise ValueError

def get_output(cmd, ignore_error=False):
    is_string_not_empty(cmd)
    assert isinstance(ignore_error, bool)
    
    import commands
    status, output=commands.getstatusoutput(cmd)
    if status and not ignore_error: raise CommandFailError(cmd)
    return output

def with_same_content(file1, file2):
    import os
    if not os.path.exists(file1) or not os.path.exists(file2):
        return False
    with open(file1) as f:
        content1 = f.read()
    with open(file2) as f:
        content2 = f.read()
    return content1 == content2

class ComboBox:
    def __init__(self,combobox):
        self.combobox = combobox
        self.model = self.combobox.get_model()

    def append(self,what):
        self.combobox.append_text(what)

    def remove(self,what):
        self.combobox.remove_text(what)

    def select(self,which):
        self.combobox.set_active(which)

    def getSelectedIndex(self):
        return self.combobox.get_active()

    def getSelected(self):
        return self.model[self.getSelectedIndex()][0]

    def setIndexFromString(self,usr_search):
        found = 0
        for item in self.model:
            iter = item.iter
            path = item.path
            name = self.model.get_value(iter, 0)
            if name == usr_search:
                found = 1
                self.select(path[0])
                break
        if found == 0:
            self.select(0)
            parent = self.combobox.get_parent().get_parent().get_parent()
            try:
                img = parent.get_children()[1]
            except:
                return
            #txt = parent.get_children()[1]
            if img.name == "metacity_previewbox":
                for item in img.get_children():
                    img.remove(item)
            else:
                img.set_from_stock('gtk-missing-image',gtk.ICON_SIZE_BUTTON)
            self.combobox.set_active(-1)

class SpinBtn:
    def __init__(self,widget):
        self.spinbtn = widget

    def getTime(self):
        return self.spinbtn.get_value_as_int()

    def setTime(self, value):
        self.spinbtn.set_value(value)
        
        
        
    



