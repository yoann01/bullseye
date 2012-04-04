# -*- coding: utf-8 -*-
from common import messager, settings
import gtk
import gobject


class Core(gobject.GObject):
	"""
		Object that contain all Bullseye core widgets
		TODO controle dbus
		TODO setting is maximised
		TODO verifier l'existence des fichiers
		TODO possibilité de supprimer les fichiers
		
		TODO scroll to current
		TODO filter
		TODO stop flag when temp
		TODO add a tableview for UC Sections + playlists
	"""
	
	__gsignals__ = { "module-loaded": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (str,))
	}
	
	def __init__(self):
		gobject.GObject.__init__(self)
		from data.bdd import MainBDD
		#from music.queue import QueueManager
		#from music.musicpanel import LibraryPanel, Playlists_Panel

		#from uc_sections import iconselector
		#from uc_sections.panel import UC_Panel

		#import audioscrobbler
		#self.interface = gtk.Builder()
		#self.interface.set_translation_domain('bullseye')
		#self.interface.add_from_file('bullseye.glade')
		
		
		self.BDD = MainBDD()
		
		self.loadedModules = []
		self.managers = {}
		# **** PARTIE GRAPHIQUE ****
		
		self.F_Main = gtk.Window()
		self.F_Main.move(settings.get_option('gui/window_x', 50), settings.get_option('gui/window_y', 50))
		self.F_Main.resize(settings.get_option('gui/window_width', 700), settings.get_option('gui/window_height', 500))
		if(settings.get_option('gui/maximized', False)):
			self.maximized = True
			self.F_Main.maximize()
		else:
			self.maximized = False
		
		self.VBox_Main = gtk.VBox()
		
		self.NB_Main = gtk.Notebook()
		self.NB_Main.set_tab_pos(gtk.POS_LEFT)

		#print(self.F_Main.set_icon_from_file('icons/playlist.png'))
		messager.inscrire(self.ajouter_raccourcis, 'desRaccourcis')
		
		
		
		
		#Musique
		self.HPaned_Music = gtk.HPaned()
		if(settings.get_option('pictures/preload', False)):
			self.loadMusic()
		else:
			B_loadMusic = gtk.Button(_('Load'))
			B_loadMusic.connect('clicked', self.loadMusic)
			self.HPaned_Music.pack1(B_loadMusic)
			
			label = gtk.Label(_('Music'))
			label.set_angle(90)
			self.NB_Main.append_page(self.HPaned_Music, label)
		

		
		#Image
		if(settings.get_option('pictures/enabled', False) == True):
			Box_PicturesMain = gtk.VBox()
			if(settings.get_option('pictures/preload', False)):
				from uc_sections.pictures.image_widget import ImageWidget
				
				Box_UpperP = gtk.HBox()
				
				display = self.F_Main.get_screen().get_display()
				imageWidget = ImageWidget(display)
				
				Box_ControlsP = gtk.HBox()
				self._imageSelector = iconselector.ImageSelector(imageWidget, Box_ControlsP)
				SW_IconsP = gtk.ScrolledWindow()
				SW_IconsP.set_size_request(-1, 170)
				SW_IconsP.add(self._imageSelector)

				self._imagePanel = UC_Panel("image", self._imageSelector)

				Box_UpperP.pack_start(self._imagePanel ,False)
				Box_UpperP.pack_start(imageWidget)
				
				Box_PicturesMain.pack_start(Box_UpperP)
				Box_PicturesMain.pack_start(SW_IconsP, False)
				Box_PicturesMain.pack_start(Box_ControlsP, False)
				
				
			else:
				B_loadPictures = gtk.Button(_('Load'))
				B_loadPictures.connect('clicked', self.loadModule, 'pictures')
				Box_PicturesMain.pack_start(B_loadPictures)

			label = gtk.Label(_('Pictures'))
			label.set_angle(90)
			self.NB_Main.append_page(Box_PicturesMain, label)
			
		#Vidéo
		if(settings.get_option('videos/enabled', False) == True):
			Box_Video = gtk.VBox()
			if(settings.get_option('videos/preload', False)):
				self.loadModule('videos')
			else:
				B_loadVideos = gtk.Button(_('Load'))
				B_loadVideos.connect('clicked', self.loadModule, 'videos')
				Box_Video.pack_start(B_loadVideos)
				
			label = gtk.Label(_('Videos'))
			label.set_angle(90)
			self.NB_Main.append_page(Box_Video, label)




		
		
		#Barre de status
		StatusBar = gtk.Statusbar()
		self.Label = gtk.Label("Gestionnaire initialisé")
		StatusBar.pack_start(self.Label)
		messager.inscrire(self.notifier, "notification_etat")
		
		self.P_Bar = gtk.ProgressBar()
		StatusBar.pack_start(self.P_Bar)
		
		self.VBox_Main.pack_end(StatusBar, False)
		self.VBox_Main.pack_end(self.NB_Main)
		self.F_Main.add(self.VBox_Main)
		
		
		#Scrobbler
		#self.scrobbler = audioscrobbler.BullseyeScrobbler()
		
		#self.HPaned_documents = gtk.HPaned()
		#self.NB_Main.append_page(self.HPaned_documents, gtk.Label(_("Documents")))
		#self.documentPanel = Panel("document")
		#self.documentIcon = iconselector.IconSelector("document")
		#self.HPaned_documents.pack1(self.documentPanel)
		#self.HPaned_documents.pack2(self.documentIcon)
		#self.NB_Main.show_all()
		
		self.F_Main.connect('window-state-event', self.on_window_state_change)
		self.F_Main.connect('configure-event', self.on_window_resize)
		self.F_Main.connect('destroy', self.on_window_destroy)
		
	
	
		
		
	def ajouter_raccourcis(self, unGroupeDeRaccourcis):
		self.F_Main.add_accel_group(unGroupeDeRaccourcis)
	
	
	def loadModule(self, button, section):
		from uc_sections.manager import UCManager
		widget = UCManager(section, self.F_Main)
		self.managers[section] = widget
		parentBox = button.get_parent()
		parentBox.pack_start(widget)
		button.destroy()
			
		self.emit('module-loaded', section)
			
	
	def loadMusic(self, button=None):
		from music.queue import QueueManager
		from music.musicpanel import LibraryPanel, Playlists_Panel
		from music.playerwidget import PlayerWidget
		
		if(button is not None):
			button.destroy()
		
		Left_music_box = gtk.VBox()
		Right_music_box = gtk.VBox()
		
		backend = (settings.get_option('music/playback_lib', 'GStreamer'))
		if(backend == 'VLC'):
			from media import vlcplayer
			self.player = vlcplayer.MusicPlayer(Box_PlayerM)
		elif(backend == 'MPlayer'):
			from media import mplayers
			self.player = mplayers.MusicPlayer(Box_PlayerM)
			Right_music_box.pack_start(self.player, False)
		else:
			from media.player import Player
			self.player = Player()
			
		playerWidget = PlayerWidget(self.player)
		self.queueManager = QueueManager(playerWidget)
		
		NB_PanelM = gtk.Notebook()
		self.library_panel = LibraryPanel(self.BDD, self.queueManager)
		self.playlists_panel = Playlists_Panel()
		NB_PanelM.append_page(self.library_panel, gtk.Label(_("Library")))
		NB_PanelM.append_page(self.playlists_panel, gtk.Label(_("Playlists")))
		

		Left_music_box.pack_start(NB_PanelM)
		Right_music_box.pack_start(self.queueManager)
		Right_music_box.pack_start(playerWidget, False)
		
		self.HPaned_Music.pack1(Left_music_box, False, False)
		self.HPaned_Music.pack2(Right_music_box)

		self.HPaned_Music.set_position(settings.get_option('music/paned_position', 200))
		self.HPaned_Music.connect('notify::position', self.onPanedPositionChanged, 'music/paned_position')
		
		self.HPaned_Music.show_all()
		self.loadedModules.append('music')
	
	def notifier(self, message):
		self.Label.set_text(message)
		
	def hot_swap_widget(self, button, name, option):
		from uc_sections.panel import UC_Panel, UC_Panes
		if(name == 'imagePanel'):
			print 'TODO'
			box = self._imagePanel.get_parent()
			self._imagePanel.hide()
			self._imagePanel = UC_Panel("image", self._imageSelector)
			box.pack_start(self._imagePanel, False)
			self._imagePanel.show_all()
			
		
	def on_window_destroy(self, widget):
		from data.bdd import BDD
		BDD.saveCache()
		settings.set_option('gui/maximized', self.maximized)
		
		if('music' in self.loadedModules):
			self.player.stop()
			self.queueManager.save_state()
		if('videos' in self.loadedModules):
			self.videoPlayer.stop()
	
		settings.MANAGER.save()
		print(_('Closing the eye...'))
		gtk.main_quit()
		
	def on_window_resize(self, widget, event):
		if(not self.maximized):
			settings.set_option('gui/window_x', event.x)
			settings.set_option('gui/window_y', event.y)
			settings.set_option('gui/window_width', event.width)
			settings.set_option('gui/window_height', event.height)
			
	def on_window_state_change(self, widget, event):
		if event.new_window_state == gtk.gdk.WINDOW_STATE_MAXIMIZED:
			self.maximized = not self.maximized
		
	def onPanedPositionChanged(self, paned, position, setting):
		"""
			@param setting : chaîne contenant la valeur du paramètre que la fonction mettra à jour
		"""
		settings.set_option(setting, paned.get_position())