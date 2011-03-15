#!/usr/bin/env python
import os, sys
from distutils.core import setup
try:
    from DistUtilsExtra.command import *
except ImportError:
    print 'Cannot install gstyle :('
    print 'Would you please install package "python-distutils-extra" first?'
    sys.exit()
import glob

f = open('version')
version = f.read().strip()
f.close()

setup(name = 'gstyle',
      description = 'Customise your gnome desktop and more',
      long_description = 
'''Gstyle is a full gnome theme manager

Features:
* manage your gtk/icons/metacity/emerald/mouse/wallpapers...
* create dynamic wallpapers
* manage your gdm settings and themes
* create and manage cubemodels themes for compiz
* create/download or export full customised themes

''',
      version = version,
      maintainer = 'Laguillaumie sylvain',
      maintainer_email = 's.lagui@gmail.com',
      url = 'http://www.penguincape.org/',
      license = 'GPLv2',
      platforms = ['linux'],
      packages = ['gstyle', 'gstyle.gui', 'gstyle.lib' ],
      data_files = [
        ('share/man/man1/', ['gstyle.1']),
        ('share/applications/', ['gstyle.desktop']),
        ('share/gstyle/', ['ChangeLog']),
        ('share/gstyle/data/', glob.glob('data/*.*')),
        ('share/gstyle/data/', ['version']),
        ('share/pixmaps/', ['data/img/puzzle.png']),
        ('share/gstyle/data/glade/', [ e for e in glob.glob('data/glade/*.*') if os.path.isfile(e)]),
        ('share/gstyle/data/img/', [ e for e in glob.glob('data/img/*.*') if os.path.isfile(e)]),
        ('share/dbus-1/system-services/', ['support/dbus/cn.gstyle.service']),
        ('/etc/dbus-1/system.d/', ['support/dbus/cn.gstyle.conf']),
        ('share/PolicyKit/policy/', ['support/policykit0/cn.gstyle.policy']),
        ('share/polkit-1/actions/', ['support/policykit1/cn.gstyle.policy']),
        ('share/gstyle/support/', [ e for e in glob.glob('support/*') if os.path.isfile(e)]),
        ('share/gstyle/support/', [ e for e in glob.glob('support/dbus/*') if os.path.isfile(e)]),
        ('share/pyshared/gstyle/', ['gstyle/__init__.py']),
        ('share/pyshared/gstyle/gui/', ['gstyle/__init__.py']),
        ('share/pyshared/gstyle/lib/', ['gstyle/__init__.py']),
      ],
      scripts = ['bin/gstyle'],
      cmdclass = { 'build' :  build_extra.build_extra,
                   'build_i18n' :  build_i18n.build_i18n,
                   'build_help' :  build_help.build_help,
                   'build_icons' :  build_icons.build_icons
                 }
      )