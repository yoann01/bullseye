#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys, os
import pygtk
pygtk.require("2.0")
import gtk
gtk.gdk.threads_init()


#Initialisation de la traduction
import gettext
gettext.install("bullseye")

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

	
	def fermer(self, b, c, d):
		self.F_Main.destroy()
	

		
	def CreerNouvelOnglet(self, widget):
		
		#wineDlg = Dialog_Nom();
		#result,newWine = wineDlg.run()
		#reponse = self.Dialog_Nom.run()
		Core.queueManager.ajouter_un_onglet()
		#Dialog_Nom.destroy()
		#print(reponse)interface = gtk.Builder()
		print( "Nouvel onglet créé" )
			
	def OuvrirAbout(self, widget):

		
		
		gui.about.run()
		gui.about.hide()
		#messagedialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, "Est-ce votre dernier mot ?")
		#messagedialog.run()
		#messagedialog.destroy()



class Dialog_Nom:
	def __init__(self):

		print("Dialog_Nom démarré")

	def run(self):

		DN = gtk.Dialog()
		Entry = gtk.Entry()
		hbox = gtk.HBox()
		hbox.pack_start(gtk.Label("Name:"), False, 5, 5)
		hbox.pack_end(Entry)
		DN.vbox.add(hbox)
		DN.show_all()
		DN.run()
		nom = interface.get_object("TB_Name").get_text()
		
		EB = gtk.EventBox()
		
		TL = gtk.Label(nom)
		TL.show()
		EB.add(TL)
		treeview = gtk.TreeView()
		treeview.show()
		
		interface.get_object("NB_Music").append_page(treeview, EB)
		print(nom)
		
		

		
if __name__ == "__main__":
	gui = Bullseye()
	gtk.main()