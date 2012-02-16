# -*- coding: utf-8 -*-
import gtk
import gobject
from abstract.playerwidget import AbstractPlayerWidget 

class PlayerWidget(AbstractPlayerWidget, gtk.HBox):
	
	def __init__(self, player):
		AbstractPlayerWidget.__init__(self, player)
		gtk.HBox.__init__(self)

		
		# -------- Widgets ---------
		self.progressBar = gtk.ProgressBar()
		self.progressBar.add_events(gtk.gdk.BUTTON_PRESS_MASK)
		self.progressBar.add_events(gtk.gdk.BUTTON_RELEASE_MASK)
		self.progressBar.set_sensitive(False)
		self.progressBar.set_text(_("Pending..."))
		self.progressBar.connect('button-release-event', self.seekTo)
			
		self.timer = Updater()
		self.timer.set_target(self.showProgress)
		
		
		#BB = gtk.HButtonBox()
		#BB.set_spacing(10)
		prevButton = gtk.ToolButton(gtk.STOCK_MEDIA_PREVIOUS)
		prevButton.connect("clicked", self.onPrevClick)
		
		self.playButton = gtk.ToolButton(gtk.STOCK_MEDIA_PLAY)
		self.playButton.connect("clicked", self.togglePause)
		
		nextButton = gtk.ToolButton(gtk.STOCK_MEDIA_NEXT)
		stopButton = gtk.ToolButton(gtk.STOCK_MEDIA_STOP)
		
		
		nextButton.connect("clicked", self.onNextClick)
		stopButton.connect("clicked", self.stop)
		self.pack_start(prevButton, False)
		self.pack_start(self.playButton, False)
		self.pack_start(nextButton, False)
		self.pack_start(stopButton, False)

		volumeButton = gtk.VolumeButton()
		#volumeButton.connect("value-changed", self.on_volume_change)
		self.pack_start(volumeButton, False)
		self.pack_start(self.progressBar)
	
	def onNextClick(self, button):
		self.playNextTrack()
	
	def onPrevClick(self, button):
		self.playPreviousTrack()
		
	def startUpdatingProgress(self):
		self.timer.start()
		self.playButton.set_stock_id(gtk.STOCK_MEDIA_PAUSE)
	
	def stopUpdatingProgress(self, resetProgress=False):
		self.timer.stop()
		self.playButton.set_stock_id(gtk.STOCK_MEDIA_PLAY)
		if resetProgress:
			self.progressBar.set_fraction(0)
	
	def seekTo(self, widget, event):
		mouse_x, mouse_y = event.get_coords()
		progress_loc = self.progressBar.get_allocation()
		value = mouse_x / progress_loc.width
		
		if value < 0: value = 0
		if value > 1: value = 1
		
		self.player.seekTo(value * 100)
		self.progressBar.set_fraction(value)
		
	def showProgress(self):
		self.progressBar.set_fraction(self.player.percentage)
		self.progressBar.set_text(self.player.etat)
		
	def stop(self, button):
		AbstractPlayerWidget.stop(self)
		

class Updater(object):
	TIMEOUT = 1000

	def __init__(self):
		self._source_id = None
		self._target = None

	def set_target(self, callback):
		self._target = callback

	def start(self):
		self.stop()
		self._source_id = gobject.timeout_add(self.TIMEOUT, self._callback)

	def stop(self):
		if self._source_id:
			gobject.source_remove(self._source_id)

	def _callback(self):
		if self._target:
			self._target()
		return True