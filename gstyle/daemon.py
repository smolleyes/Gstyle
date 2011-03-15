#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# gstyle - make Linux easier to use
#
# Copyright (C) 2009-2010, gstyle Developers Team
#
# gstyle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# gstyle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gstyle; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

from __future__ import with_statement
import dbus
import dbus.service
import dbus.glib
import gobject

class AccessDeniedError(dbus.DBusException):
    _dbus_error_name = 'cn.gstyle.AccessDeniedError'

class CommandFailError(dbus.DBusException):
    _dbus_error_name = 'cn.gstyle.CommandFailError'

class GstyleFulgens(dbus.service.Object):
    @dbus.service.method('cn.gstyle.Interface', 
                                          in_signature='sssb', 
                                          out_signature='s', 
                                          sender_keyword='sender')
    
    def run(self, command, env_string, secret_key, ignore_error, sender=None):
        if not secret_key in self.authorized_secret_key:
            self.__check_permission(sender)
            self.authorized_secret_key.add(secret_key)
        
        command = command.encode('utf8')
        env_string = env_string.encode('utf8')
        
        env = self.__get_dict(env_string)
        
        import os
        os.chdir(env['PWD'])
        
        import subprocess
        task = subprocess.Popen(command, shell=True,stdout=subprocess.PIPE)
        out, err = task.communicate()
        res = str(out.strip())
        return res
        
    @dbus.service.method('cn.gstyle.Interface', 
                                            in_signature='sss', 
                                            out_signature='s', 
                                            sender_keyword='sender')
    
    def spawn(self, command, env_string, secret_key, sender=None):
        if not secret_key in self.authorized_secret_key:
            self.__check_permission(sender)
            self.authorized_secret_key.add(secret_key)

        command = command.encode('utf8')
        env_string = env_string.encode('utf8')
        
        env = self.__get_dict(env_string)
        
        import os
        os.chdir(env['PWD'])
        
        import subprocess
        task = subprocess.Popen(command, shell=True, env=env)
        return task.pid

    @dbus.service.method('cn.gstyle.Interface', 
                                          in_signature='', 
                                          out_signature='i') 
    
    def get_check_permission_method(self):
        return self.check_permission_method
    

    @dbus.service.method('cn.gstyle.Interface', 
                                          in_signature='', 
                                          out_signature='')
    def exit(self):
        mainloop.quit()

    def __check_permission(self, sender):
        if self.check_permission_method == 0:
            self.__check_permission_0(sender)
        elif self.check_permission_method == 1:
            self.__check_permission_1(sender)
        else:
            raise ValueError

    def __init__(self):
        self.authorized_secret_key = set()
        bus_name = dbus.service.BusName('cn.gstyle', bus = dbus.SystemBus())
        dbus.service.Object.__init__(self, bus_name, '/')
        
        self.check_permission_method = -1
        try:
            obj = dbus.SystemBus().get_object('org.freedesktop.PolicyKit1', '/org/freedesktop/PolicyKit1/Authority')
            obj = dbus.Interface(obj, 'org.freedesktop.PolicyKit1.Authority')
            self.check_permission_method = 1
        except dbus.DBusException:
            obj = dbus.SystemBus().get_object('org.freedesktop.PolicyKit', '/')
            obj = dbus.Interface(obj, 'org.freedesktop.PolicyKit')
            self.check_permission_method = 0

    def __check_permission_0(self, sender):
        if not sender: raise ValueError('sender == None')
        
        obj = dbus.SystemBus().get_object('org.freedesktop.PolicyKit', '/')
        obj = dbus.Interface(obj, 'org.freedesktop.PolicyKit')
        granted = obj.IsSystemBusNameAuthorized('cn.gstyle', sender, False)
        if 'yes' != granted:
            raise AccessDeniedError('Session is not authorized. Authorization method = 0')

    def __check_permission_1(self, sender):
        # This function is from project "gnome-lirc-properties". Thanks !
        if not sender: raise ValueError('sender == None')
        
        obj = dbus.SystemBus().get_object('org.freedesktop.PolicyKit1', '/org/freedesktop/PolicyKit1/Authority')
        obj = dbus.Interface(obj, 'org.freedesktop.PolicyKit1.Authority')
        (granted, _, details) = obj.CheckAuthorization(
                ('system-bus-name', {'name': sender}), 'cn.gstyle', {}, dbus.UInt32(1), '', timeout=600)
        if not granted:
            raise AccessDeniedError('Session is not authorized. Authorization method = 1')

    def __get_dict(self, string):
        assert string.endswith('\n')
        List = string.split('\n')
        Dict = {}
        for i in range(0, len(List)-1, 2):
            k = List[i]
            v = List[i+1]
            Dict[k] = v
        return Dict
    
    @dbus.service.method('cn.gstyle.Interface', 
                                    in_signature='s',
                                    out_signature='') 
    def drop_priviledge(self, secret_key):
        if secret_key in self.authorized_secret_key:
            self.authorized_secret_key.remove(secret_key)

        
def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    GstyleFulgens()
    mainloop = gobject.MainLoop()
    mainloop.run()    

if __name__ == '__main__':
    main()
