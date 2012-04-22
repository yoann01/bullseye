# -*- coding: utf-8 -*-
import mplayer
import os

class Player(object):
	
	def __init__(self):
		self._player = mplayer.Player()

	@property
	def duration(self):
		try:
			value = self._player.length
		except:
			value = -1

		return value
        
	@property
	def pourcentage(self):
		try:
			duration = self._player.length
		except:
			duration = 1
		try:
			position = self._player.time_pos
		except:
			position = 1
		value = float(position) / float(duration)
		
		return value
			
	@property
	def etat(self):
		def transformer_position(secondes):
			minutes = 0
			while secondes > 59:
				minutes += 1
				secondes -= 60
				
			if secondes < 10:
				secondes = "0" + str(secondes)
			else:
				secondes = str(secondes)
			value = str(minutes) + ":" + secondes
			return value

		try:
			secondes = int(self.position)
			value = transformer_position(secondes)
				
		except:
			value = _("Nothing")
		return value

	def get_volume(self):
		return self._player.volume

	def set_volume(self, volume):
		self._player.volume = volume * 100

	volume = property(fget=get_volume, fset=set_volume)

	def get_position(self):
		try:
			value = self._player.time_pos
		except:
			value = -1
		return value

	def set_position(self, position):
		self._player.time_pos = position

	position = property(fset=set_position, fget=get_position)
		
	
	def lire_fichier(self, element):
		self.PBar.set_fraction(0.0)
		self.PBar.set_text("0:00")
		
		self.load(element.path)
		#self.play() load make it play with mplayer
		self.Button.set_stock_id(gtk.STOCK_MEDIA_PAUSE)

	def load(self, filename):
		filename = filename.replace(' ', '\ ')
		if filename.startswith('http://'):
			uri = filename
		else:
			uri = 'file://' + os.path.abspath(filename)
		self._position_updater.start()
		self._player.loadfile(filename)
		self.PBar.set_sensitive(True)

	def _on_destroy(self, *args):
		self._player.quit()
		
	def play(self):
		self._position_updater.start()
		self._player.pause()
		self.PBar.set_sensitive(True)

	def pause(self):
		self._position_updater.stop()
		self._player.pause()

		
	def stop(self, arret_total=None):
		self._position_updater.stop()
		self._player.stop()
		self.PBar.set_sensitive(False)
		self.PBar.set_fraction(0)
		self.Button.set_stock_id(gtk.STOCK_MEDIA_PLAY)
		if(arret_total != None):
			self.PBar.set_text('En attente')
		
	def is_paused(self):
		return bool(self._player.paused)
		
	def is_stopped(self):
		return self._player.stream_pos == None
	
	def is_playing(self):
		return self._player.get_state()[1] == gst.STATE_PLAYING
			
		
	def on_message(self, bus, message):
		t = message.type
		#EOS = End Of Song
		if t == gst.MESSAGE_EOS:
			messager.diffuser('need_piste_suivante', self, 'eos')
			#self.stop()
		elif t == gst.MESSAGE_ERROR:
			self.stop()
			err, debug = message.parse_error()
			print "Error: %s" % err, debug
	
	def on_volume_change(self, widget, value):
		self.volume = value
	
	def seek_end(self, widget, event):
		mouse_x, mouse_y = event.get_coords()
		progress_loc = self.PBar.get_allocation()
		value = mouse_x / progress_loc.width
		
		if value < 0: value = 0
		if value > 1: value = 1
		
		self.position = self.duration * value
		self.PBar.set_fraction(value)
		
	def toggle_pause(self):
		if self.is_paused():
			self.play()
			self.emit('unpause')
		elif self.is_stopped():
			self.emit('unpause')
			messager.diffuser('need_piste_suivante', self, 'click')
		else:
			self.pause()
			self.emit('pause')
			
	def getQtVideoWidget(self):
		from mplayer.qt4 import QPlayerView
		return QPlayerView()
		
	def getGtkVideoWidget(self):
		from mplayer.gtk2 import GtkPlayerView
		return GtkPlayerView()