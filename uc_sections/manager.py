import gtk
from common import settings

class UCManager(gtk.VBox):
	def __init__(self, moduleType, window):
		gtk.VBox.__init__(self)
		from uc_sections import iconselector
		from uc_sections.panel import UC_Panel, UC_Panes
		
		self.fullScreen = False

		if(moduleType == 'pictures'):
			self.module = 'picture'
			from uc_sections.pictures.image_widget import ImageWidget
				
			Box_UpperP = gtk.HBox()
			
			display = window.get_screen().get_display()
			imageWidget = ImageWidget(display)
			
			Box_ControlsP = gtk.HBox()
			self.elementSelector = iconselector.ImageSelector(imageWidget, Box_ControlsP)
			SW_IconsP = gtk.ScrolledWindow()
			SW_IconsP.set_size_request(-1, 170)
			SW_IconsP.add(self.elementSelector)

			#self._imagePanel = UC_Panel("image", self._imageSelector)
			
			if(settings.get_option(self.module + 's/browser_mode', 'panel') == 'panes'):
				self.containerBrowser = UC_Panes(self.module, self.elementSelector)
			else:
				self.containerBrowser = UC_Panel(self.module, self.elementSelector)

			Box_UpperP.pack_start(self.containerBrowser ,False)
			Box_UpperP.pack_end(imageWidget)
			
			self.pack_start(Box_UpperP)
			self.pack_start(SW_IconsP, False)
			self.pack_start(Box_ControlsP, False)
			self.show_all()
			
			imageWidget.connect("button-press-event", self.toggleFullScreen)
			self.DA_Parent = imageWidget.get_parent()
			
		elif(moduleType == 'videos'):
			self.module = 'video'
			backend = settings.get_option('videos/playback_lib', 'GStreamer')
			
			from uc_sections.videos.videoplayerwidget import VideoPlayerWidget
			if(backend == 'VLC'):
				from media import vlcplayer
				self.videoPlayerWidget = VideoPlayerWidget(vlcplayer.Player())
			elif(backend == 'MPlayer'):
				from media import mplayers
				self.videoPlayerWidget = VideoPlayerWidget(mplayers.Player())
				#Right_music_box.pack_start(self.player, False)
			else:
				from media import player
				self.videoPlayerWidget = VideoPlayerWidget(player.Player())
				
			#ZoneVideo = self.interface.get_object("DA_Video")
			self.elementSelector = iconselector.VideoSelector(self.videoPlayerWidget)
			SW_IconsV = gtk.ScrolledWindow()
			SW_IconsV.set_size_request(-1, 170)
			SW_IconsV.add(self.elementSelector)
			
			if(settings.get_option(self.module + 's/browser_mode', 'panel') == 'panes'):
				self.containerBrowser = UC_Panes(self.module, self.elementSelector)
			else:
				self.containerBrowser = UC_Panel(self.module, self.elementSelector)
			
			#HPaned_Video = gtk.HPaned()
			#HPaned_Video.pack1(self.containerBrowser)
			#HPaned_Video.pack2(SW_IconsV)
			
			upperBox = gtk.HBox()
			upperBox.pack_start(self.containerBrowser ,False)
			upperBox.pack_end(self.videoPlayerWidget)
			
			self.pack_start(upperBox)
			self.pack_start(SW_IconsV, False)
			self.show_all()
			
			self.videoPlayerWidget.connect("button-press-event", self.toggleFullScreen)
			self.DA_Parent = self.videoPlayerWidget.get_parent()
			
	def setBrowserMode(self, viewType):
		'''
			Hot swap the widget used to display containers
		'''
		from uc_sections.panel import UC_Panel, UC_Panes
		
		if(viewType == 'panel'):
			newObj = UC_Panel(self.module, self.elementSelector)
		else:
			newObj = UC_Panes(self.module, self.elementSelector)
			
		
		box = self.containerBrowser.get_parent()
		self.containerBrowser.destroy()
		box.pack_start(newObj, False)
		#else:
			#box.pack1(newObj, False)
		newObj.show_all()

		self.containerBrowser = newObj
		settings.set_option(self.module + 's/browser_mode', viewType)
		
	def toggleFullScreen(self, widget, event):
		if event.type == gtk.gdk._2BUTTON_PRESS:
			if self.fullScreen:
				parent = widget.get_parent()
				widget.reparent(self.DA_Parent)
				parent.destroy()

			else:
				fenetre = gtk.Window()
				fenetre.fullscreen()
				fenetre.show()
				widget.reparent(fenetre)
				
			self.fullScreen = not self.fullScreen