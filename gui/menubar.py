# -*- coding: utf-8 -*-
import gtk
import gobject
import threading
import subprocess
import os

from common import messager, settings
from gui import modales

from PIL import Image

class BullseyeMenuBar(gtk.MenuBar):
	def __init__(self, Core):
		gtk.MenuBar.__init__(self)
		
		self.core = Core
		self.core.connect('module-loaded', self.loadModuleMenus)
		self.bdd = Core.BDD
		
		file = gtk.MenuItem(_('_File'))
		menu = gtk.Menu()
		
		
		if('music' in Core.loadedModules):
			item = gtk.MenuItem(_("New _tab"))
			item.connect('activate', Core.queueManager.ajouter_un_onglet)
			menu.append(item)
		item = gtk.ImageMenuItem(_("_Quit"))
		item.set_image(gtk.image_new_from_stock(gtk.STOCK_QUIT, gtk.ICON_SIZE_MENU))
		item.connect('activate', Core.on_window_destroy)
		menu.append(item)
		file.set_submenu(menu)
		self.append(file)
		
		outils = gtk.MenuItem(_("_Tools"))
		menu = gtk.Menu()
		item = gtk.MenuItem("Récupérer les données Last.fm")
		item.connect('activate', self.retrieveFromLastFM)
		menu.append(item)
		item = gtk.MenuItem("Récupérer les données d'une ancienne base")
		item.connect('activate', self.retrieveFromSave)
		menu.append(item)
		item = gtk.MenuItem(_('Check for new files'))
		item.connect('activate', self.checkForNewFiles)
		menu.append(item)
		
		
		item = gtk.MenuItem(_('Edit settings'))
		item.connect('activate', self.editSettings)
		menu.append(item)
		
		outils.set_submenu(menu)
		
		self.append(outils)
		
		
		for module in Core.loadedModules:
			self.loadModuleMenus(None, module)

		
		
	def loadModuleMenus(self, core, module):
		if(module == 'pictures' or module == 'videos'):
			pictures = gtk.MenuItem(_("Pictures"))
			menu = gtk.Menu()
			item = gtk.MenuItem(_("Check for doubloons"))
			item.connect_object('activate', self.checkDoubloons, module)
			menu.append(item)
			
			browserMode = settings.get_option(module + '/browser_mode', 'panel')
			
			item = gtk.MenuItem(_("Move to UC structure"))
			item.connect('activate', self.core.managers[module].containerBrowser.moveToUCStructure)
			menu.append(item)
			
			panes = gtk.RadioMenuItem(None, _('Multi-panes'))
			if browserMode == 'panes':
				panes.set_active(True)
			panes.connect_object('toggled', self.core.managers[module].setBrowserMode, 'panes')
			
			panel = gtk.RadioMenuItem(panes, _('All in one panel'))
			if browserMode == 'panel':
				panes.set_active(True)

			panel.connect_object('toggled', self.core.managers[module].setBrowserMode, 'panel')
			
			menu.append(panes)
			menu.append(panel)
			
			pictures.set_submenu(menu)
			self.append(pictures)
		elif(module == 'music'):
			music = gtk.MenuItem(_("Music"))
			menu = gtk.Menu()
			item = gtk.MenuItem(_("Reload covers"))
			item.connect_object('activate', self.core.BDD.reloadCovers, self.core.statusBar.addProgressNotifier())
			menu.append(item)
			
			music.set_submenu(menu)
			self.append(music)
			
		self.show_all()
	
	#def temp(self, garbButton, mode):
		#if(garbButton.get_active()):
			#from uc_sections.panel import UC_Panel, UC_Panes
			#obj = self.core._imagePanel
			#box = obj.get_parent()
			
			#if(mode == "panel"):
				#newObj = UC_Panel(obj.module, obj.elementSelector)
			#else:
				#newObj = UC_Panes(obj.module, obj.elementSelector)
			#obj.destroy()
			#box.pack_start(newObj, False)
			#newObj.show_all()
			#self.core._imagePanel = newObj
	
		
	def checkDoubloons(self, module):
		self.core.managers[module].containerBrowser.checkForDoubloons()
		
		
	def checkForNewFiles(self, menuitem):
		notifier = self.core.statusBar.addProgressNotifier()
		self.bdd.check_for_new_files(notifier)
		
	
	def editSettings(self, *args):
		modales.SettingsEditor()
	
	def retrieveFromLastFM(self, menuitem):
		self.bdd.retrieveFromLastFM(self.P_Bar)
	
	def retrieveFromSave(self, menuitem):
		dialog = modales.ImportHelper(self.bdd)
		#dialog = gtk.FileChooserDialog(action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_OPEN, gtk.FILE_CHOOSER_ACTION_OPEN))
		#dialog.run()
		#fichier = dialog.get_filename()
		#dialog.destroy()
		#print(fichier)
		#self.bdd.retrieveFromSave(fichier)
	
class StatusBar(gtk.Statusbar):
	def __init__(self):
		gtk.Statusbar.__init__(self)
		
	def addProgressNotifier(self):
		notifier = ProgressNotifier()
		notifier.connect('done', self.removeNotifier)
		self.pack_start(notifier)
		self.show_all()
		return notifier
		
	def removeNotifier(self, notifier):
		self.remove(notifier)
		
class ProgressNotifier(gtk.ProgressBar):
	
	__gsignals__ = { "done": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()) }
	
	def __init__(self):
		gtk.ProgressBar.__init__(self)
		
	def emitDone(self):
		self.emit('done')
		
	def setFraction(self, val):
		self.set_fraction(val)
			

	