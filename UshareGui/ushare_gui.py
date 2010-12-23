#!/usr/bin/env python
#-*- coding: UTF-8 -*-
import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
import os
from configobj import ConfigObj

exec_path =  os.path.dirname(os.path.abspath(__file__))
if ('/usr' in exec_path):
    data_path = '/usr/local/share/ushare-gui/data'
else:
    data_path =  os.path.join(exec_path,"../data")
img_path = os.path.join(data_path,"img")
inactive_img = os.path.join(img_path,"no.png")
active_img = os.path.join(img_path,'usable.png') 
glade_path = os.path.join(data_path,"glade")
APP_NAME = 'Ushare-gui'
GLADE_FILE = os.path.join(glade_path,'gui.glade')
CONFFILE = '/etc/ushare.conf'

class Ushare_gui(object):
    def __init__(self):
        if os.getuid() != 0:
            self.error_dialog("Please restart Ushare-gui as root (sudo...)",None)
            exit()
        ## set the gladexml file
        gladexml = gtk.glade.XML(GLADE_FILE, None ,APP_NAME)
        ## the main window and properties
        self.window = gladexml.get_widget("main_window")
        self.window.set_resizable(1)
        self.window.set_default_size(500,500)
        self.window.set_position("center")
        self.window.set_icon_from_file(os.path.join(img_path,'usharegui.png'))
        ## ushare state
        self.ushare_state_label = gladexml.get_widget("ushare_state_label")
        self.ushare_state_img = gladexml.get_widget("ushare_state_img")
        ## main options
        self.ushare_name_entry = gladexml.get_widget("ushare_name")
        self.ushare_iface_entry = gladexml.get_widget("ushare_iface")
        self.ushare_port_entry = gladexml.get_widget("ushare_port")
        ## extra options
        self.telnet_checkbox = gladexml.get_widget("enable_telnet")
        self.telnet_port_entry = gladexml.get_widget("telnet_port")
        self.web_checkbox = gladexml.get_widget("enable_web")
        self.xbox_checkbox = gladexml.get_widget("enable_xbox")
        self.dlna_checkbox = gladexml.get_widget("enable_dlna")
        ## shared directories paths
        self.scrollview = gladexml.get_widget("paths_scroll")
        self.model = gtk.ListStore(str)
        self.treeview = gtk.TreeView()
        self.treeview.set_model(self.model)
        renderer = gtk.CellRendererText()
        titleColumn = gtk.TreeViewColumn("", renderer, text=0)
        self.treeview.append_column(titleColumn)
        titleColumn.set_sort_column_id(1)
        self.scrollview.add(self.treeview)
        self.treeview.connect('cursor-changed',self.get_selected)
        
        ## connect glade signals
        dic = {"on_main_window_delete" : gtk.main_quit,
               "on_quit_btn_clicked" : gtk.main_quit,
               "on_restart_btn_clicked" : self.restartUshare,
               "on_enable_telnet_toggled" : self.on_option_toggled,
               "on_enable_web_toggled" : self.on_option_toggled,
               "on_enable_xbox_toggled" : self.on_option_toggled,
               "on_enable_dlna_toggled" : self.on_option_toggled,
               "on_add_path_btn_clicked" : self.add_new_path,
               "on_del_path_btn_clicked" : self.remove_path,
        }
        gladexml.signal_autoconnect(dic)
        ## show the gui
        self.window.show_all()
        ## start reading conffile
        self.readConf()
        ## check ushare state
        self.get_ushare_state()
        ## start
        gtk.main()
        
    def get_ushare_state(self):
        self.state = os.popen('ps ax | grep [b]in/ushare').readlines()
        if self.state:
            self.state = True
            self.ushare_state_label.set_text("ushare is up and running !")
            self.ushare_state_img.set_from_file(active_img)
        else:
            self.state = False
            self.ushare_state_label.set_text("ushare is not started...")
            self.ushare_state_img.set_from_file(inactive_img)
            
    def readConf(self):
        if os.path.exists(CONFFILE):
            try:
                self.config = ConfigObj(CONFFILE,write_empty_values=True)
            except:
                print "corrupted conf file, please verify"
                return
        else:
            self.config = self.createConfFile()
        
        self.ushare_name = self.config["USHARE_NAME"]
        self.ushare_name_entry.set_text(self.ushare_name)
        self.ushare_iface = self.config["USHARE_IFACE"]
        self.ushare_iface_entry.set_text(self.ushare_iface)
        self.ushare_port = self.config["USHARE_PORT"]
        self.ushare_port_entry.set_text(self.ushare_port)
        self.ushare_telnet_state = self.config["USHARE_ENABLE_TELNET"]
        if self.ushare_telnet_state == "" or self.ushare_telnet_state == False:
            self.telnet_checkbox.set_active(False)
        else:
            self.telnet_checkbox.set_active(True)
        self.ushare_telnet_port = self.config["USHARE_TELNET_PORT"]
        self.telnet_port_entry.set_text(self.ushare_telnet_port)
        
        self.ushare_web_state = self.config["USHARE_ENABLE_WEB"]
        if self.ushare_web_state == "" or self.ushare_web_state == False:
            self.web_checkbox.set_active(False)
        else:
            self.web_checkbox.set_active(True)
        
        self.ushare_xbox_state = self.config["USHARE_ENABLE_XBOX"]
        if self.ushare_xbox_state == "" or self.ushare_xbox_state == False:
            self.xbox_checkbox.set_active(False)
        else:
            self.xbox_checkbox.set_active(True)
        
        self.ushare_dlna_state = self.config["USHARE_ENABLE_DLNA"]
        if self.ushare_dlna_state == "" or self.ushare_dlna_state == False:
            self.dlna_checkbox.set_active(False)
        else:
            self.dlna_checkbox.set_active(True)
            
        ## and the paths list
        list = self.config["USHARE_DIR"]
        for path in list:
            self.add_path(path)
            
    def createConfFile(self):
        config = ConfigObj(write_empty_values=True)
        config.filename = CONFFILE
        config["USHARE_NAME"]="Ushare"
        config["USHARE_IFACE"]="eth0"
        config["USHARE_PORT"]=''
        config["USHARE_TELNET_PORT"]=''
        config["USHARE_DIR"]=''
        config["USHARE_OVERRIDE_ICONV_ERR"]='' 
        config["USHARE_ENABLE_WEB"]=''
        config["USHARE_ENABLE_TELNET"]=''
        config["USHARE_ENABLE_XBOX"]='' 
        config["USHARE_ENABLE_DLNA"]=''
        ## return a dic as conf
        try:
            self.writeConf(config)
        except:
            self.error_dialog("Can't write the /etc/ushare.conf file,\nPlease restart Ushare-gui as root)", self.window)
        return config
    
    def saveConfig(self,widget=None):
        config = ConfigObj(write_empty_values=True)
        config.filename = CONFFILE
        config["USHARE_NAME"]=self.ushare_name_entry.get_text() 
        config["USHARE_IFACE"]=self.ushare_iface_entry.get_text()
        config["USHARE_PORT"]=self.ushare_port_entry.get_text()
        config["USHARE_TELNET_PORT"]=self.telnet_port_entry.get_text()
        dirs = []
        for row in self.model:
            name = row[0]
            dirs.append(name)
        config["USHARE_DIR"]=dirs
        config["USHARE_OVERRIDE_ICONV_ERR"]='' 
        config["USHARE_ENABLE_WEB"]=self.web_checkbox.get_active()
        config["USHARE_ENABLE_TELNET"]=self.telnet_checkbox.get_active()
        config["USHARE_ENABLE_XBOX"]=self.xbox_checkbox.get_active()
        config["USHARE_ENABLE_DLNA"]=self.dlna_checkbox.get_active()
        ## return a dic as conf
        try:
            self.writeConf(config)
        except:
            self.error_dialog("Can't write the /etc/ushare.conf file,\nPlease restart Ushare-gui as root)", self.window)
    
    def writeConf(self,config):
        try:
            config.write()
        except:
            self.error_dialog("Can't write the /etc/ushare.conf file,\nPlease restart Ushare-gui as root)", self.window)
            return False
        os.system("sed -i 's/ = /=/g;s/, /,/g;s/True/TRUE/g;s/False//g' %s" % CONFFILE)
        ## restart ushare
        return self.restartUshare()
            
    def restartUshare(self,widget=None):
        ## kill all process since ushare often let active processes...
        os.system("killall -9 ushare")
        cmd = os.system("/etc/init.d/ushare start")
        if cmd == 1:
            self.error_dialog("Can't restart ushare...", self.window)
            return
        self.get_ushare_state()
        
    def on_option_toggled(self,widget):
        print widget.name
        
    def get_selected(self,widget):
        selected = self.treeview.get_selection()
        self.iter = selected.get_selected()[1]
        self.path = self.model.get_path(self.iter)
        ## else extract needed metacity's infos
        self.selected_path = self.model.get_value(self.iter, 0)
        print self.selected_path
        
    def add_path(self, path):
        self.iter = self.model.append()
        self.model.set(self.iter,
                       0, path,
                       )
        return self.saveConfig()
    
    def add_new_path(self,widget):
        buttons     = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                       gtk.STOCK_OK,   gtk.RESPONSE_OK)
        filechooser = gtk.FileChooserDialog("choose a folder to share...",
                                            None,
                                            gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                            buttons)
        filechooser.set_do_overwrite_confirmation(True)
        result = filechooser.run()
        if result != gtk.RESPONSE_OK:
            filechooser.destroy()
            return
        ## if ok
        path = filechooser.get_filename()
        filechooser.destroy()
        if not os.path.exists(path):
            print "wrong path selected... %s do not exist" % path 
            return
        return self.add_path(path)
        
    def remove_path(self,widget):
        self.model.remove(self.iter)
        return self.saveConfig()
        
    def error_dialog(self,message, parent = None):
        """Displays an error message."""
        dialog = gtk.MessageDialog(parent = parent, type = gtk.MESSAGE_ERROR, buttons = gtk.BUTTONS_OK, flags = gtk.DIALOG_MODAL)
        dialog.set_markup(message)
        dialog.set_position('center')
        result = dialog.run()
        dialog.destroy()


if __name__ == "__main__":
    Ushare_gui()
    
        
