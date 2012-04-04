# -*- coding: utf-8 -*-
import gtk
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
		self.P_Bar = Core.P_Bar
		
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
		
		music = gtk.MenuItem(_("Music"))
		menu = gtk.Menu()
		item = gtk.MenuItem(_("Reload covers"))
		item.connect('activate', Core.BDD.reloadCovers)
		menu.append(item)
		
		music.set_submenu(menu)
		self.append(music)
		
		if('pictures' in Core.loadedModules):
			loadModuleMenus(None, 'pictures')
		
		
	def loadModuleMenus(self, core, module):
		if(module == 'pictures' or module == 'videos'):
			pictures = gtk.MenuItem(_("Pictures"))
			menu = gtk.Menu()
			item = gtk.MenuItem(_("Check for doubloons"))
			item.connect('activate', self.checkDoubloons)
			menu.append(item)
			
			item = gtk.MenuItem(_("Move to UC structure"))
			item.connect('activate', self.core.managers[module].containerBrowser.moveToUCStructure)
			menu.append(item)
			
			panes = gtk.RadioMenuItem(None, _('Multi-panes'))
			panes.set_active(True)
			panes.connect_object('toggled', self.core.managers[module].setBrowserMode, 'panes')
			panel = gtk.RadioMenuItem(panes, _('All in one panel'))

			panel.connect_object('toggled', self.core.managers[module].setBrowserMode, 'panel')
			
			menu.append(panes)
			menu.append(panel)
			
			pictures.set_submenu(menu)
			self.append(pictures)
		self.show_all()
	
	def temp(self, garbButton, mode):
		if(garbButton.get_active()):
			from uc_sections.panel import UC_Panel, UC_Panes
			obj = self.core._imagePanel
			box = obj.get_parent()
			
			if(mode == "panel"):
				newObj = UC_Panel(obj.module, obj.elementSelector)
			else:
				newObj = UC_Panes(obj.module, obj.elementSelector)
			obj.destroy()
			box.pack_start(newObj, False)
			newObj.show_all()
			self.core._imagePanel = newObj
	
		
	def checkDoubloons(self, *args):
		print('todo')
		type = 'image'
		self.bdd.c.execute('SELECT * FROM images GROUP BY size HAVING COUNT(size) > 1;')
		table = []
		rows = self.bdd.c.fetchall()
		for row in rows:
			t = (row[6],)
			self.bdd.c.execute('SELECT * FROM images WHERE size = ?', t)
			for row in self.bdd.c:
				path = unicode(row[1] + "/" + row[2])
				print(path)
				ID = str(row[0])
				try:
					thumbnail_path = "thumbnails/" + type + "s/" + ID + ".jpg"
					if not os.path.exists(thumbnail_path):
						if(type == "image"):
							im = Image.open(path)
							im.thumbnail((128, 128), Image.ANTIALIAS)
							im.save(thumbnail_path, "JPEG")
						elif(type == "video"):
							cmd = ['totem-video-thumbnailer', path, thumbnail_path]
							ret = subprocess.call(cmd)
						else:
							thumbnail_path = "thumbnails/none.jpg"
				except IOError:
					thumbnail_path = "thumbnails/none.jpg"
						
				#if os.path.exists(thumbnail_path):
					#thumbnail = gtk.gdk.pixbuf_new_from_file(thumbnail_path)
				#else:
				thumbnail = gtk.gdk.pixbuf_new_from_file(thumbnail_path)
				#On veut : ID, chemin, libellé,  apperçu, note, categorie_ID, univers_ID
				table.append((row[0], path, row[1], thumbnail, row[3], row[4], row[5]))
		messager.diffuser("des_" + type +"s", self, table)
		
	def checkForNewFiles(self, menuitem):
		#def doit():
			
			#check_for_new_files('/home/piccolo/Musique', self.P_Bar)
		folders = settings.get_option('music/folders', [])
		a = threading.Thread(target=self.bdd.check_for_new_files, args=(folders, self.P_Bar))
		a.start()
		
	
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
	