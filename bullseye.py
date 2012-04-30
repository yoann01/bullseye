#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys, os, locale
import pygtk
pygtk.require("2.0")
import gtk
gtk.gdk.threads_init()


#Init translation
import gettext
locale.setlocale(locale.LC_ALL, '') # use user's preferred locale
# take first two characters of country code
loc = locale.getlocale()
filename = "locale/bullseye_%s.mo" % locale.getlocale()[0][0:2]
#import gettext
#gettext.install("bullseye")
try:
	trans = gettext.GNUTranslations(open( filename, "rb" ) )
except IOError:
	trans = gettext.NullTranslations()
trans.install()

import core
from common import settings
from gui.trayicon import BullseyeTrayIcon
from gui.menubar import BullseyeMenuBar


Core = core.Core()

#import profile

#profile.run('Core = core.Core()')
        
class Bullseye:
			
	def __init__(self):
		
		StatusIcon = BullseyeTrayIcon(Core)
		
		#Barre de menus
		Core.VBox_Main.pack_start(BullseyeMenuBar(Core), False)
		Core.F_Main.set_title(_('Bullseye Media Manager'))
		Core.F_Main.show_all()
		
		print( "Initialisation terminée" )


if __name__ == "__main__":
	gui = Bullseye()
	gtk.main()