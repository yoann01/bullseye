# -*- coding: utf-8 -*-
import gst
import os

class Player(object):
	def __init__(self):
		self._player = gst.element_factory_make('playbin2', 'player'+str(hash(self)))
		self._format = gst.Format(gst.FORMAT_TIME)

		self.bus = self._player.get_bus()
		self.bus.add_signal_watch()
		self.bus.connect("message", self.on_message)
		
		self.connectedWidgets = []

	@property
	def duration(self):
		try:
			value, format = self._player.query_duration(self._format, None)
		except:
			value = -1

		return value
        
	@property
	def percentage(self):
		try:
			duration, format = self._player.query_duration(gst.FORMAT_TIME)
		except:
			duration = 1
		try:
			position, format = self._player.query_position(gst.FORMAT_TIME)
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
			secondes = self.position / 1000000000
			value = transformer_position(secondes)
				
		except:
			value = "Nothing"
		return value

	def get_volume(self):
		return self._player.get_property('volume')

	def set_volume(self, volume):
		self._player.set_property('volume', volume)

	volume = property(fget=get_volume, fset=set_volume)

	def get_position(self):
		try:
			value, format = self._player.query_position(self._format, None)
		except:
			value = -1

		return value

	def set_position(self, position):
		self._player.seek_simple(self._format, gst.SEEK_FLAG_FLUSH, position)

	position = property(get_position, set_position)
	
	
	def addConnectedWidget(self, playerWidget):
		''' This allow me to not used gsignal and qt signal'''
		self.connectedWidgets.append(playerWidget)
	
	def playTrack(self, element):
		self._player.set_state(gst.STATE_NULL)
		#chemin.encode('latin-1')
		self.load(element.path)
		self.play()
		element.flags.add('play')

	def load(self, filename):
		if filename.startswith('http://'):
			uri = filename
		else:
			uri = 'file://' + os.path.abspath(filename)
		self._player.set_property('uri', uri)

	def play(self):
		self._player.set_state(gst.STATE_PLAYING)
		for pwidget in self.connectedWidgets:
			pwidget.startUpdatingProgress()

	def pause(self):
		self._player.set_state(gst.STATE_PAUSED)
		for pwidget in self.connectedWidgets:
			pwidget.stopUpdatingProgress()

	def stop(self):
		self._player.set_state(gst.STATE_NULL)
		for pwidget in self.connectedWidgets:
			pwidget.stopUpdatingProgress(True)
		
	def is_paused(self):
		return self._player.get_state()[1] == gst.STATE_PAUSED
		
	def isStopped(self):
		return self._player.get_state()[1] == gst.STATE_NULL
	
	def is_playing(self):
		return self._player.get_state()[1] == gst.STATE_PLAYING
			
		
	def on_message(self, bus, message):
		t = message.type
		#EOS = End Of Song
		if t == gst.MESSAGE_EOS:
			for pwidget in self.connectedWidgets:
				pwidget.playNextTrack(True)
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
		
	def seekTo(self, pos):
		'''
			@param pos : float ranging from 0 to 1
		'''
		self.position = int(self.duration * (float(pos) / float(100)))
		#self._player.seek_simple(self._format, gst.SEEK_FLAG_FLUSH, )
		
	def togglePause(self):
		if self.is_paused():
			self.play()
		elif self.isStopped():
			messager.diffuser('need_piste_suivante', self, 'click')
		else:
			self.pause()