#!/usr/bin/python
#-*- coding: UTF-8 -*-
import os
import gtk
import config
import gobject
import urllib
from tempfile import TemporaryFile
from lib.wallpapers import WallPaper,WallDyn, WallStat, LIST_FORMAT_STYLE, LIST_COLOR_STYLE
from functions import yesno
from functions import create_filechooser_open
from functions import SpinBtn
import config
from config import _
from shutil import rmtree
from shutil import copyfile
from xml.dom.minidom import Document

walldyn_dir = config.walltimes_home_srcdir
wallstats_dir = config.wallpapers_home_srcdir

STATIC_GLADE = os.path.join(config.glade_path,'static_walldyn.glade')
TRANSITION_GLADE = os.path.join(config.glade_path,'transition_walldyn.glade')
APP_NAME = 'Gstyle'

def translate_seconde(nb):
    try:
        nb = int(float(nb))
    except:
        return
    result = []
    nb_h =  nb/3600
    if nb_h:
        result.append("%sh" %nb_h)
    reste = nb%3600
    nb_min =  reste/60
    if nb_min:
        result.append("%smin" % nb_min)
    nb_s =  reste%60
    if nb_s:
        result.append("%ss" %nb_s)
    return " ".join(result)

def int_to_time(seconds):
    try:
        seconds = int(float(seconds))
    except:
        return
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    #res = "%02d:%02d:%02d" % (h, m, s)
    return h,m
    
class WallpaperGui(object):
    def __init__(self,gladexml,wallpapers_dict):
        ## Charge les wallpaper du systéme
        self.wallpapers_dict = wallpapers_dict
        
        #GUI
        #####################################
        #General
        self.wallpapers_notebook = gladexml.get_widget("notebook_wallpaper")
        self.statbar = gladexml.get_widget("statusbar")
        ## for threads
        self.progress_box = gladexml.get_widget("progress_box")
        self.progress_text = gladexml.get_widget("progress_box_text")
        self.main_progressbar = gladexml.get_widget("main_progressbar")

        self.wallpapers_page_img =  gladexml.get_widget("wallpapers_page_img")
        self.wallpapers_page_desc = gladexml.get_widget("wallpapers_page_desc")
#        self.wallpapers_dret_label = gladexml.get_widget("wallpapers_dret_label")
        self.wallpapers_page_img.set_from_file(config.img_path+"/decoration.png")
        self.wallpapers_page_desc.set_text(_("Wallpaper :\nManage and install your wallpapers or walltimes themes"))

        #####################################
        #Onglet wallpaper statique=> wallstat
        self.wallstats_addbtn = gladexml.get_widget("wallstats_addbtn")
        self.wallstats_applybtn = gladexml.get_widget("wallstats_applybtn")
        self.wallstats_delbtn = gladexml.get_widget("wallstats_delbtn")

        dic = {"on_wallstats_addbtn_clicked"   : self.on_wallstats_addbtn_clicked,
               "on_wallstats_applybtn_clicked" : self.on_wallstats_applybtn_clicked,
               "on_wallstats_delbtn_clicked"   : self.on_wallstats_delbtn_clicked,
               "cb_ws_style_changed_cb" : self.cb_ws_style_changed,
               }
        gladexml.signal_autoconnect(dic)

        ## setup the liststore model
        self.wallstats_model = gtk.ListStore(gobject.TYPE_STRING,gtk.gdk.Pixbuf,gobject.TYPE_PYOBJECT )
        ## setup the iconview
        self.wallstats_iconview = gtk.IconView(model=self.wallstats_model)
        self.wallstats_iconview.set_pixbuf_column(1)
        self.wallstats_iconview.set_text_column(0)
        self.wallstats_iconview.set_item_width(225)
#        self.wallstats_iconview.set_markup_column(1)
        self.wallstats_iconview.set_selection_mode('single')
        self.wallstats_iconview.set_reorderable(1)
        ## iconview signal
        self.wallstats_iconview.connect('selection_changed',self.get_wallstats_model)
        ## add the iconview
        self.wallstats_gest_viewer = gladexml.get_widget("wallstats_gest_viewer")
        self.wallstats_gest_viewer.add(self.wallstats_iconview)
        self.wallstats_iconview.select_path(0)

        #Information wallstats
        self.wallstats_gest_info = gladexml.get_widget("wallstats_gest_info")
        self.wallstats_gest_info.set_text(_("Available themes list"))

        #Options
        self.wallstats_select_style = gladexml.get_widget("cb_ws_style")
        model_style = gtk.ListStore(gobject.TYPE_STRING)
        for style in LIST_FORMAT_STYLE:
            model_style.append((style,))
        self.wallstats_select_style.set_model(model_style)
        case = gtk.CellRendererText()
        self.wallstats_select_style.pack_start(case, True)
        self.wallstats_select_style.add_attribute(case, 'text', 0)
        self.wallstats_couleur1 = gladexml.get_widget("cob_ws_couleur1")
        self.wallstats_couleur2 = gladexml.get_widget("cob_ws_couleur2")

        self.wallstats_select_couleur = gladexml.get_widget("cb_ws_couleurs")
        model_couleur = gtk.ListStore(gobject.TYPE_STRING)
        for style_couleur in LIST_COLOR_STYLE:
            model_couleur.append((style_couleur,))
        self.wallstats_select_couleur.set_model(model_couleur)
        case_c = gtk.CellRendererText()
        self.wallstats_select_couleur.pack_start(case_c, True)
        self.wallstats_select_couleur.add_attribute(case_c, 'text', 0)


        #####################################
        #Wallpaper dynamic
        self.walldyns_addbtn = gladexml.get_widget("walldyns_addbtn")
        self.walldyns_applybtn = gladexml.get_widget("walldyns_applybtn")
        self.walldyns_delbtn = gladexml.get_widget("walldyns_delbtn")
        self.walldyns_list_btn = gladexml.get_widget("walldyns_list_btn")
        self.walldyns_edit_btn = gladexml.get_widget("walldyns_edit_btn")
        
        self.yearspin = SpinBtn(gladexml.get_widget("yearspin"))
        self.monthspin = SpinBtn(gladexml.get_widget("monthspin"))
        self.dayspin = SpinBtn(gladexml.get_widget("dayspin"))
        self.hourspin = SpinBtn(gladexml.get_widget("hourspin"))
        self.minutespin = SpinBtn(gladexml.get_widget("minutespin"))
        self.secondspin = SpinBtn(gladexml.get_widget("secondspin"))
        
        ## options
        self.walldyns_editor_opt = gladexml.get_widget("walldyn_editor_options")

        dic = {"on_walldyns_addbtn_clicked"   : self.on_walldyns_addbtn_clicked,
               "on_walldyns_applybtn_clicked" : self.on_walldyns_applybtn_clicked,
               "on_walldyns_delbtn_clicked"   : self.on_walldyns_delbtn_clicked,
               "on_walldyns_newbtn_clicked" : self.on_walldyns_newbtn_clicked,
               "on_walldyns_savebtn_clicked" : self.on_walldyns_recbtn_clicked,
               "on_walldyns_edit_btn_clicked"   : self.on_walldyns_editbtn_clicked,
               "on_add_transition_btn_clicked": self.on_add_walldyn_clicked,
               "on_add_static_btn_clicked":self.on_add_walldyn_clicked,
               }
        gladexml.signal_autoconnect(dic)

        ## setup the liststore models
        self.walldyns_model = gtk.ListStore(gobject.TYPE_STRING,gtk.gdk.Pixbuf,gobject.TYPE_PYOBJECT)
        self.walldyn_editdic = {}
        self.static_num = 0
        self.transition_num = 0
        ## setup the menu (left part)
        
        self.walldyns_menu = gtk.TreeView()
        self.walldyns_menu.set_model(self.walldyns_model)
        self.wallstats_iconview.set_pixbuf_column(1)
        self.wallstats_iconview.set_text_column(0)
        renderer = gtk.CellRendererPixbuf()
        imgColumn = gtk.TreeViewColumn(_("Preview"), renderer)
        imgColumn.set_fixed_width(350)
        pathColumn = gtk.TreeViewColumn()
        self.walldyns_menu.append_column(imgColumn)
        imgColumn.add_attribute(renderer, 'pixbuf', 1)
        self.walldyns_menu.append_column(pathColumn)

        ## setup the menu scrollview
        self.walldyns_menu_scroll = gladexml.get_widget("walldyns_preview_menu_scroll")
        self.menu_columns = self.walldyns_menu.get_columns()
        self.menu_columns[0].set_sort_column_id(1)
        self.menu_columns[1].set_visible(0)
        self.walldyns_menu_scroll.add(self.walldyns_menu)

        ## setup the main walldyn preview (right part)
        self.walldyns_preview_scroll = gladexml.get_widget("walldyns_preview_scroll")
        self.walldyns_menu.connect("cursor-changed",self.get_walldyns_model)

        #Information walldyns
        self.walldyns_gest_info = gladexml.get_widget("walldyns_gest_info")
        self.walldyns_gest_info.set_text(_("Available themes list"))
        ## walldyn container
        self.container = gtk.VBox()

        #Chargement des wallpaper dans la GUI
        self.list_wallstats_themes()
        self.list_walldyns_themes()

    def cb_ws_style_changed(self,widget):
        index = widget.get_active()
        model = widget.get_model()
        return model[index][0]

#Chargement des wallpapers
    def list_wallstats_themes(self):
        filename_select = self.wallpapers_dict.get_active_item()
        index_selected = 0
        for index,item in enumerate(self.wallpapers_dict.get_dict_static_w().values()):
            if item.filename == filename_select:
                index_selected = index
            self.add_wallstats(item)

    def list_walldyns_themes(self):
        for item in self.wallpapers_dict.get_dict_dynamique_w().values():
            self.add_walldyns(item)

    def add_w(self,boxtype,item):
        model = getattr(self,"%s_model" % boxtype)
        if item.filename == '(none)':
            return
        try:
            os.path.isfile(item.filename)
        except:
            return
        try:
            img = gtk.gdk.pixbuf_new_from_file_at_scale(item.get_path_img(), 150, 150 , 1)
        except Exception,e:
            img = None
            return
        ## then add it to the iconview
        name = item.get_name()
        iter = model.append((name,img,item))

    def add_wallstats(self,item):
        self.add_w("wallstats",item)

    def add_walldyns(self,item):
        self.add_w("walldyns",item)

#Change wallpaper selectioned
    def get_model(self,boxtype,iter,path=None):
        """Action to get the information theme wallpapers"""
        model = getattr(self,"%s_model" % boxtype)
        if not iter:
            iter  = model.get_iter(path)
        setattr(self,"%s_iter" % boxtype,iter)
        item = model.get_value(iter,2)
        setattr(self,"%s_item" % boxtype,item)
        self.statbar.push(1,_("Selected wallpaper theme : %s") % item.name)
        return item

    def get_wallstats_model(self,widget):
        selected = widget.get_selected_items()
        ## check if path exist (or problems when clicking between rows..)
        try:
            row_index = selected[0]
        except:
            return
        item = self.get_model("wallstats",None,row_index)
        index_option = LIST_FORMAT_STYLE.index(item.options)
        self.wallstats_select_style.set_active(index_option)
        index_shade = LIST_COLOR_STYLE.index(item.shade_type)
        self.wallstats_select_couleur.set_active(index_shade)
        couleur1 = gtk.gdk.Color(item.pcolor)
        self.wallstats_couleur1.set_color(couleur1)
        couleur2  = gtk.gdk.Color(item.scolor)
        self.wallstats_couleur2.set_color(couleur2)
        
    def on_add_walldyn_clicked(self,widget):
        boxtype = None
        if ("static" in widget.name):
            boxtype = "static"
            self.static_num += 1
            self.num = self.static_num
        else:
            boxtype = "transition"
            self.transition_num += 1
            self.num = self.transition_num
        self.add_walldyn_box(boxtype)

    def get_walldyns_model(self,widget,edit=None):
        """Action to get the information on walldyn when clicked"""
        selected = widget.get_selection()
        iter = selected.get_selected()[1]
        item = self.get_model("walldyns",iter)
        if edit:
            self.make_walldyns_edit_view()
        else:
            self.make_walldyns_preview()
            self.walldyns_editor_opt.hide()
            self.statbar.push(1,_("Selected walldyns : %s") % self.walldyns_item.name)
        self.get_walldyn_data(item)
        self.walldyns_edit_btn.show()
        
    def get_walldyn_data(self,item):
        walldyn_xml = item.filename
        date,data_items = item.analyse_xml()
        if not date or not data_items:
            return
        self.yearspin.setTime(date['year'])
        self.monthspin.setTime(date['month'])
        self.dayspin.setTime(date['day'])
        self.hourspin.setTime(date['hour'])
        self.minutespin.setTime(date['minute'])
        self.secondspin.setTime(date['second'])
        
    ## normal preview
    def make_walldyns_preview(self):
        model = gtk.ListStore(gobject.TYPE_STRING,gtk.gdk.Pixbuf, gobject.TYPE_STRING)
        item_walldyn = getattr(self,"walldyns_item")
        if not item_walldyn:
            return
        list_img = item_walldyn.get_list_img()
        for item in list_img:
            file = item["file"]
            try:
                img = gtk.gdk.pixbuf_new_from_file_at_scale(file, 150, 150 , 1)
            except:
                img = None
            duration = translate_seconde(item["duration"])
            model.append((duration, img, file))
        for item in self.walldyns_preview_scroll.get_children():
            self.walldyns_preview_scroll.remove(item)
        walldyns_iconview = gtk.IconView(model)
        walldyns_iconview.set_pixbuf_column(1)
        walldyns_iconview.set_markup_column(0)
        walldyns_iconview.set_selection_mode('single')
        self.walldyns_preview_scroll.add(walldyns_iconview)
        self.walldyns_preview_scroll.show_all()
    
    def make_walldyns_edit_view(self):
        item_walldyn = getattr(self,"walldyns_item")
        if not item_walldyn:
            return
        ## clean the scrollview
        for item in self.walldyns_preview_scroll.get_children():
            self.walldyns_preview_scroll.remove(item)
        self.container = gtk.VBox()
        self.walldyns_preview_scroll.add_with_viewport(self.container)
        
        list_img = item_walldyn.get_list_img(True)
        for item in list_img:
            ## check if static or translation
            if item["type"] == "static":
                self.add_walldyn_box("static",item)
            elif item["type"] == "transition":
                self.add_walldyn_box("transition",item)
        ##print all the generated boxes...
        self.walldyns_edit_btn.hide()
        self.walldyns_editor_opt.show()
        
        
    def add_walldyn_box(self,boxtype,item=None):
        img1 = None
        try:
            if boxtype == "static":
                img1 = item["file"]
                self.static_num += 1
                self.num = self.static_num
            else:
                img1 = item["file_from"]
                self.transition_num += 1
                self.num = self.transition_num
        except:
            pass
        img2 = None
        try:
            img2 = item["file_to"]
        except:
            pass
        try:
            h,m = int_to_time(item["duration"])
        except:
            h,m = 0,0
        t_item = WalldynPreviewBox(self,boxtype,img1,h,m,img2).new()
        new_item = gtk.HBox()
        new_item.set_name("%d_%s" % (self.num,boxtype))
        t_item.box.reparent(new_item)
        self.container.add(new_item)
        self.walldyn_editdic[new_item.name] = t_item
        self.walldyns_preview_scroll.show_all()
        
#Apply wallpaper to the system (compatible gnome)
    def apply_wallpaper(self,boxtype,widget=None,value=None):
        filename = ""
        name = ""
        if value:
            name = os.path.splitext(value)[0]
            for item in self.wallpapers_dict.values():
                if item.name == name:
                    wallpaper = WallPaper(item.filename,name)
        else:
            wallpaper = getattr(self,'%s_item' %  boxtype)
        if wallpaper:
            filename = wallpaper.filename
            name = wallpaper.name
            print "Activating wallpaper : %s " % name
            self.wallpapers_dict.set_active_item(filename)
            self.statbar.push(1,_("wallpaper \"%s\" successfully activated") % name)

    def on_wallstats_applybtn_clicked(self,widget):
        self.apply_wallpaper("wallstats",widget)

    def on_walldyns_applybtn_clicked(self,widget):
        self.apply_wallpaper("walldyns",widget)
        
    def on_walldyns_editbtn_clicked(self,widget):
        self.walldyn_editdic = {}
        self.make_walldyns_edit_view()

#Delete wallpaper
    def delete_wallpaper(self,boxtype,widget):
        """Delete wallpaper in the file .background"""
        item = getattr(self,"%s_item" % boxtype)
        confirm = yesno(_("Remove wallpaper"),_("Are you sure you want to delete the wallpapers Theme \n%s ?") % item.name)
        if confirm == "No":
            return
        filename = item.filename
        self.wallpapers_dict.del_item(filename)
        iter = getattr(self,"%s_iter" % boxtype)
        getattr(self,"%s_model" % boxtype).remove(iter)
        if boxtype == "walldyns":
            path = self.walldyns_model[0].path
            self.walldyns_menu.set_cursor(path)
            rmtree(os.path.dirname(filename))
        self.statbar.push(1,_("%(type)s %(name)s successfully removed") % 
                          {'type' : boxtype,
                           'name' : item.name})

    def on_wallstats_delbtn_clicked(self,widget):
        self.delete_wallpaper("wallstats",widget)

    def on_walldyns_delbtn_clicked(self,widget):
        self.delete_wallpaper("walldyns",widget)

#Add wallpaper
    def add_wallpaper(self,boxtype,widget=None):
        """Add new wallpaper in the file .background"""
        extension_wallstats = ["*.png","*.svg","*.jpeg","*.jpg","*.bmp"]
        extension_walldyns = ["*.xml"]
        dialog = create_filechooser_open(_("Choose a wallpaper"),locals()["extension_%s" % boxtype])
        result = dialog.run()
        if result != gtk.RESPONSE_OK:
            dialog.destroy()
            return
        ## if ok
        filename = dialog.get_filename()
        dialog.destroy()
        if not os.path.exists(filename):
            print "wallpaper do not exist \n"
            return

        item = self.wallpapers_dict.add_item_system(filename)
        if item:
            self.add_w(boxtype,item)
            if boxtype == "wallstats":
                path = getattr(self,'%s_model' % boxtype )[-1].path
                getattr(self,"%s_iconview" % boxtype).select_path(path)
                getattr(self,"%s_iconview" % boxtype).set_cursor(path)
            elif boxtype == "walldyns":
                self.add_walldyns(item)
                gtk.gdk.Window.process_updates()
            self.wallpapers_dict.set_active_item(filename)

    def on_wallstats_addbtn_clicked(self,widget):
        self.add_wallpaper("wallstats",widget)
        
    def on_walldyns_addbtn_clicked(self,widget):
        self.add_wallpaper("walldyns",widget)

#New walldyn
    def on_walldyns_newbtn_clicked(self,widget):
        self.walldyn_editdic = {}
        self.walldyns_editor_opt.show()
        for item in self.walldyns_preview_scroll.get_children():
            self.walldyns_preview_scroll.remove(item)
        self.walldyns_preview_scroll.add_with_viewport(self.container)
        self.walldyns_preview_scroll.show_all()
        #self.model_new = gtk.ListStore(gobject.TYPE_STRING,gtk.gdk.Pixbuf, gobject.TYPE_STRING)
        #walldyns_iconview = gtk.IconView(self.model_new)
        #walldyns_iconview.set_pixbuf_column(1)
        #walldyns_iconview.set_markup_column(0)
        #walldyns_iconview.set_selection_mode('single')
        #walldyns_iconview.set_size_request(200, 150)
        #walldyns_iconview.drag_dest_set(0, [], 0)
        #walldyns_iconview.connect('drag_motion', self.motion_cb)
        #walldyns_iconview.connect('drag_drop', self.drop_cb)
        #walldyns_iconview.connect('drag_data_received', self.got_data_cb)
        #self.walldyns_preview_scroll.add(walldyns_iconview)
        #self.walldyns_preview_scroll.show_all()
        
    # function to track the motion of the cursor while dragging
    def motion_cb(self, wid, context, x, y, time):
        if "text/uri-list" in context.targets:
            context.drag_status(gtk.gdk.ACTION_COPY, time)
            return True
        else:
            return False

    # function to print out the mime type of the drop item
    def drop_cb(self, wid, context, x, y, time):
        value = 0
        for index, info in enumerate(context.targets):
            if info.strip() == "text/plain":
                value = index
                break

        wid.drag_get_data(context, context.targets[value], time)
        context.finish(True, False, time)
        return True

    def got_data_cb(self, wid, context, x, y, data, info, time):
        # Got data.
        list_filename = [element for element in data.get_text().split("\n") if element]
        for item in list_filename:
            if item.split('.')[-1].strip() in ('jpg','jpeg','svg','png','gif'):
                protocol = item.split('://')[0].strip()
                if protocol == 'http':
                    path_img =  os.path.join( config.walltimes_home_srcdir,
                        "temps",
                        item.split('/')[-1])
                    file_temps = open(path_img, "w")
                    data = urllib.urlopen(item)
                    file_temps.write(data.read())
                    file_temps.close()
                elif protocol == 'file':
                    path_img = item[7:].strip()
                img = gtk.gdk.pixbuf_new_from_file_at_scale(path_img, 150, 150 , 1)
                duration  = 10
                self.model_new.append((duration,img,path_img))
        context.finish(True, False, time)

    def on_walldyns_recbtn_clicked(self,widget=None):
        dialog = gtk.Dialog(title =(_("Enter a name for your walldyn (no spaces)")),
            parent = None,
            flags = gtk.DIALOG_MODAL,
            buttons = (gtk.STOCK_OK, gtk.RESPONSE_OK,
            gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        dialog.set_position("center")
        dialog.set_size_request(500, 80)
        # Creation de la zone de saisie
        entry = gtk.Entry()
        # Insertion de la zone de saisie dans la boite de dialogue
        # Rappel : paramètre 1 de gtk_box_pack_start de type GtkBox
        dialog.vbox.pack_start(entry, True, False, 0)
        # Affichage des elements de la boite de dialogue
        dialog.vbox.show_all()

        # On lance la boite de dialogue et on recupere la reponse
        reponse = dialog.run()
        name = None
        if reponse == gtk.RESPONSE_OK:
            # L'utilisateur valide
            name = entry.get_text()
            if name == "":
                dialog.destroy()
                return self.on_walldyns_recbtn_clicked()
                
            target=os.path.join(config.walltimes_home_srcdir,name,'%s.xml' % name)
            self.create_xml(target)
            if os.path.exists(target):
                obj_wall = WallDyn(target)
                self.add_walldyns(obj_wall)
                ## select in the preview list
                path = self.walldyns_model[-1].path
                self.walldyns_menu.set_cursor(path)
                ## apply the new walldyn
                self.wallpapers_dict.set_active_item(obj_wall.filename)
                self.walldyns_editor_opt.hide()
            self.walldyn_editdic = {}
            # Destruction de la boite de dialogue
        dialog.destroy()

#For fullpack
    def action_add_todic(self,theme_list):
        if theme_list:
            if theme_list.has_key('wallstats'):
                list_wallpapers = theme_list["wallstats"]
                for file in list_wallpapers.values():
                    if file:
                        item = self.wallpapers_dict.add_item_system(file)
                        if item:
                            self.add_wallstats(item)
                            path = self.wallstats_model[-1].path
                            self.wallstats_iconview.set_cursor(path)
                            self.wallpapers_dict.set_active_item(item.filename)
                else:
                    print "no wallpaper to install"
            if theme_list.has_key("walltimes"):
                list_walltimes = theme_list["walltimes"]
                for name in list_walltimes.keys():
                    if name:
                        tpath = list_walltimes[name]
                        list_path = os.path.join(tpath,name+".xml")
                        if not (list_path):
                            continue
                        path = list_path
                        WallDyn.set_path_img(path)
                        item = self.wallpapers_dict.add_item_system(path)
                        if item:
                            self.add_walldyns(item)
                            path = self.walldyns_model[-1].path
                            self.walldyns_menu.set_cursor(path)
                            self.wallpapers_dict.set_active_item(item.filename)
            else:
                print "no walltime to install"
                
    def create_xml(self,filename):
        path_name = os.path.dirname(filename)
        year = self.yearspin.getTime()
        month = self.monthspin.getTime()
        day = self.dayspin.getTime()
        hour = self.hourspin.getTime()
        minute = self.minutespin.getTime()
        second = self.secondspin.getTime()
        #Create dir
        if os.path.exists(path_name) and not path_name == walldyn_dir :
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
        self._createN(self._starttime,"year",year)
        self._starttime.appendChild(self.doc.createTextNode("\n"))
        self._createN(self._starttime,"month",month)
        self._starttime.appendChild(self.doc.createTextNode("\n"))
        self._createN(self._starttime,"day",day)
        self._starttime.appendChild(self.doc.createTextNode("\n"))
        # TOCHECK
        # Bug de gnome chez moi? je dois commencer a 1 heure, et faire dans la suite comme ci cela etait 0h.
        # sinon au lieu d'avoir un apres midi (2.jpg) jusqu'a 5pm, je l'ai jusqu'a 4pm (pb heure gmt?)
        self._createN(self._starttime,"hour",hour)
        self._starttime.appendChild(self.doc.createTextNode("\n"))
        self._createN(self._starttime,"minute",minute)
        self._starttime.appendChild(self.doc.createTextNode("\n"))
        self._createN(self._starttime,"second",second)
        self._starttime.appendChild(self.doc.createTextNode("\n"))

        for item in sorted(set(self.walldyn_editdic)):
            name = item
            walldyn_part = self.walldyn_editdic[name]
            if walldyn_part.type == "static":
                image_dest = os.path.join(path_name,walldyn_part.img.split('/')[-1])
                copyfile(walldyn_part.img,image_dest)
                walldyn_part.img = image_dest
                time = walldyn_part.get_time() 
                self._createNStatic(time, walldyn_part.img)
            else:
                image_dest = os.path.join(path_name,walldyn_part.img2.split('/')[-1])
                if not os.path.exists(image_dest):
                    copyfile(walldyn_part.img,image_dest)
                walldyn_part.img2 = image_dest
                time = walldyn_part.get_time()
                self._createNTransition(time,walldyn_part.img,walldyn_part.img2)
            self._background.appendChild(self.doc.createTextNode("\n"))
        
        if not os.path.exists(path_name):
            os.makedirs(path_name)
        ## write final xml
        self.doc.writexml(open(filename ,"w"), "", "", "", "UTF-8")

    def _createNoeud(self,nom):
          noeud = self.doc.createElement(nom)
          return noeud

    def _createN(self,pere,fils,valeur=""):
        fils = self._createNoeud(fils)
        texte = self.doc.createTextNode("%s" % valeur)
        fils.appendChild(texte)
        pere.appendChild(fils)

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
                
    
class WalldynPreviewBox:
    def __init__(self,gui, boxtype, img, hour, minutes, img2=None):
        ## get elements from glade
        self.type = boxtype
        self.img = img
        self.hour = hour
        self.minutes = minutes
        self.gui = gui
        
        self.gladexml = None
        if boxtype == "static":
            self.gladexml= gtk.glade.XML(STATIC_GLADE,None,config.APP_NAME)
            
        elif boxtype == "transition":
            self.gladexml = gtk.glade.XML(TRANSITION_GLADE,None,config.APP_NAME)
            self.imgbox2 = self.gladexml.get_widget("img2")
            self.img2 = img2
            
        self.imgbox = self.gladexml.get_widget("img")
        self.static_hourspin = self.gladexml.get_widget("hourspin")
        self.static_minutespin = self.gladexml.get_widget("minutespin")
        
        self.box = self.gladexml.get_widget("walldynbox")
        self.box.expander = self
        
        dic = {"on_static_remove_btn_clicked" : self.remove_box,
               "on_transition_remove_btn_clicked" : self.remove_box,
               "on_img_event"   : self.select_image,
               "on_img2_event" : self.select_image,
               }
        self.gladexml.signal_autoconnect(dic)
        
    
    def new(self):
        if self.img:
            pixbuf1 = gtk.gdk.pixbuf_new_from_file_at_scale(self.img, 150, 150 , 1)
            self.imgbox.set_from_pixbuf(pixbuf1)
        if self.type == "transition":
            if self.img2:
                pixbuf2 = gtk.gdk.pixbuf_new_from_file_at_scale(self.img2, 150, 150 , 1)
                self.imgbox2.set_from_pixbuf(pixbuf2)
        self.static_hourspin.set_value(self.hour)
        self.static_minutespin.set_value(self.minutes)
        return self
    
    def get_time(self):
        h = self.static_hourspin.get_value_as_int()
        m = self.static_minutespin.get_value_as_int()
        ret = self.time_to_int(h, m)
        return ret
        
    def select_image(self,widget,event):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            extensions = ["*.png","*.svg","*.jpeg","*.jpg","*.bmp"]
            dialog = create_filechooser_open(_("Choose an image"),extensions)
            result = dialog.run()
            if result != gtk.RESPONSE_OK:
                dialog.destroy()
                return
            ## if ok
            filename = dialog.get_filename()
            dialog.destroy()
            if not os.path.exists(filename):
                print "image file do not exist \n"
                return
            if ('img2' in widget.name):
                 try:
                     self.pixbuf2 = gtk.gdk.pixbuf_new_from_file_at_scale(filename, 150, 150 , 1)
                 except:
                     print "can t create pixbuf from image %s" % filename
                 self.img2 = filename
                 self.imgbox2.set_from_pixbuf(self.pixbuf2)
            else:
                try:
                     self.pixbuf = gtk.gdk.pixbuf_new_from_file_at_scale(filename, 150, 150 , 1)
                except:
                     print "can t create pixbuf from image %s" % filename
                self.img = filename
                self.imgbox.set_from_pixbuf(self.pixbuf)
                
    def remove_box(self,widget):
        parent = self.box.get_parent()
        parent.unparent()
        del self.gui.walldyn_editdic[parent.name]
        
    def time_to_int(self, h,m):
        res = (60 * 60 * h) + (60 * m)
        return res
