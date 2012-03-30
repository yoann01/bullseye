# -*- coding: utf-8 -*-
import gtk
import gobject
from abstract.videoplayerwidget import AbstractVideoPlayerWidget 

class VideoPlayerWidget(AbstractVideoPlayerWidget, gtk.VBox):
	
	def __init__(self, player):
		AbstractVideoPlayerWidget.__init__(self, player)
		gtk.VBox.__init__(self)
		
		Box_Controls = gtk.HBox()
		ProgressBar = gtk.ProgressBar()
		playButton = gtk.ToolButton(gtk.STOCK_MEDIA_PLAY)
		#playButton.connect("clicked", self.on_playButton_Click)

		Box_Controls.pack_start(playButton, False)
		Box_Controls.pack_start(ProgressBar)
		
		ZoneVideo = gtk.DrawingArea()

		ZoneVideo.add_events(gtk.gdk.BUTTON_PRESS_MASK)
		ZoneVideo.add_events(gtk.gdk.BUTTON_RELEASE_MASK)
		self.fullscreen = False
		self.DA_Parent = self
		#ZoneVideo.connect("button-press-event", self.on_DA_click)
		
		self.movie_window = ZoneVideo
		self.pack_start(ZoneVideo)
		self.pack_start(Box_Controls, False)
		self.show_all()
		
		#player.setUpGtkVideo(self.movie_window)
		self.movie_window.connect('map', self.player.setUpGtkVideo)