# -*- coding: utf-8 -*-
import gst
import os
import gtk
import gobject

from common import messager

gobject.threads_init()
gtk.gdk.threads_init()

class Player(gobject.GObject):
	__gsignals__ = { "pause": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
	"unpause": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
	}
	
	def __init__(self, ProgressBar, Button):
		gobject.GObject.__init__(self)
		self._player = gst.element_factory_make('playbin2', \
			'player'+str(hash(self)))
		self._format = gst.Format(gst.FORMAT_TIME)
		
		
		self.bus = self._player.get_bus()
		self.bus.add_signal_watch()
		self.bus.connect("message", self.on_message)
		
		self.Button = Button
		
		#On met en route la barre de progression
		self.PBar = ProgressBar
		self.PBar.add_events(gtk.gdk.BUTTON_PRESS_MASK)
		self.PBar.add_events(gtk.gdk.BUTTON_RELEASE_MASK)
		self.PBar.set_sensitive(False)
		self.PBar.set_text(_("Pending..."))
		self.PBar.connect('button-release-event', self.seek_end)
		
		def update_position():
			self.PBar.set_fraction(self.pourcentage)
			self.PBar.set_text(self.etat)
			
		self._position_updater = Updater()
		self._position_updater.set_target(update_position)

	@property
	def duration(self):
		try:
			value, format = self._player.query_duration(self._format, None)
		except:
			value = -1

		return value
        
	@property
	def pourcentage(self):
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
		self._player.seek_simple(self._format, \
			gst.SEEK_FLAG_FLUSH, position)

	position = property(fset=set_position, fget=get_position)
		
	
	def lire_fichier(self, element):
		self.PBar.set_fraction(0.0)
		self.PBar.set_text("0:00")
		self._player.set_state(gst.STATE_NULL)
		#chemin.encode('latin-1')
		self.load(element.path)
		self.play()
		self.Button.set_stock_id(gtk.STOCK_MEDIA_PAUSE)

	def load(self, filename):
		if filename.startswith('http://'):
			uri = filename
		else:
			uri = 'file://' + os.path.abspath(filename)
		self._player.set_property('uri', uri)

	def play(self):
		#if self.liste != None:
		self._position_updater.start()
		self._player.set_state(gst.STATE_PLAYING)
		self.PBar.set_sensitive(True)

	def pause(self):
		self._position_updater.stop()
		self._player.set_state(gst.STATE_PAUSED)

	def stop(self, arret_total=None):
		self._position_updater.stop()
		self._player.set_state(gst.STATE_NULL)
		self.PBar.set_sensitive(False)
		self.PBar.set_fraction(0)
		self.Button.set_stock_id(gtk.STOCK_MEDIA_PLAY)
		if(arret_total != None):
			self.PBar.set_text('En attente')
		
	def is_paused(self):
		return self._player.get_state()[1] == gst.STATE_PAUSED
		
	def is_stopped(self):
		return self._player.get_state()[1] == gst.STATE_NULL
	
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
		
class MusicPlayer(Player):
	def __init__(self, Box):
		ProgressBar = gtk.ProgressBar()
		B_Play = gtk.ToolButton(gtk.STOCK_MEDIA_PLAY)
		Player.__init__(self, ProgressBar, B_Play)
		
		BB = gtk.HButtonBox()
		B_Prev = gtk.ToolButton(gtk.STOCK_MEDIA_PREVIOUS)
		
		self.connect('pause', self.set_play_icon, B_Play)
		self.connect('unpause', self.set_pause_icon, B_Play)
		
		B_Next = gtk.ToolButton(gtk.STOCK_MEDIA_NEXT)
		B_Stop = gtk.ToolButton(gtk.STOCK_MEDIA_STOP)
		B_Prev.connect("clicked", self.on_B_Prev_Click)
		B_Play.connect("clicked", self.on_B_Play_Click)
		B_Next.connect("clicked", self.on_B_Next_clicked)
		B_Stop.connect("clicked", self.stop)
		Box.pack_start(B_Prev, False)
		Box.pack_start(B_Play, False)
		Box.pack_start(B_Next, False)
		Box.pack_start(B_Stop, False)
		BB.set_spacing(10)
		B_Volume = gtk.VolumeButton()
		B_Volume.connect("value-changed", self.on_volume_change)
		Box.pack_start(B_Volume, False)
		#Box.pack_start(BB, False)
		
		
		Box.pack_start(ProgressBar)
		Box.show_all()
		
		#on "coupe" la sortie vidéo
		fakesink = gst.element_factory_make("fakesink", "my-fakesink")
		self._player.set_property("video-sink", fakesink)
		messager.inscrire(self.lire_fichier, 'musique_a_lire')
		messager.inscrire(self.stop, 'arret_musique')
		
	def on_B_Next_clicked(self, w):
		#Joue la piste suivante de la queue courante, seulement si il y en a une (de piste hein)
		messager.diffuser('need_piste_suivante', self, 'demarre')

	def on_B_Play_Click(self, b):
		#FAUX (SIGNAL) J'envoie le bouton pour que son icône puisse changer en fonction de l'état trouvé
		self.toggle_pause()
	
	def on_B_Prev_Click(self, w):
		messager.diffuser('need_piste_precedente', self, None)
	
	def set_play_icon(self, player, button):
		button.set_stock_id(gtk.STOCK_MEDIA_PLAY)
		
	def set_pause_icon(self, player, button):
		button.set_stock_id(gtk.STOCK_MEDIA_PAUSE)
		
	def stop(self, b=None):
		super(MusicPlayer, self).stop(b)
		messager.diffuser('MusicPlayerStopped', self, True)
	
		
		
class VideoPlayer(Player):
	def __init__(self, Box):
		Box_Controls = gtk.HBox()
		ProgressBar = gtk.ProgressBar()
		B_Play = gtk.ToolButton(gtk.STOCK_MEDIA_PLAY)
		B_Play.connect("clicked", self.on_B_Play_Click)

		Box_Controls.pack_start(B_Play, False)
		Box_Controls.pack_start(ProgressBar)
		
		ZoneVideo = gtk.DrawingArea()
		ZoneVideo.add_events(gtk.gdk.BUTTON_PRESS_MASK)
		ZoneVideo.add_events(gtk.gdk.BUTTON_RELEASE_MASK)
		self.fullscreen = False
		self.DA_Parent = Box
		ZoneVideo.connect("button-press-event", self.on_DA_click)
		
		Box.pack_start(ZoneVideo)
		Box.pack_start(Box_Controls, False)
		Box.show_all()
		Player.__init__(self, ProgressBar, B_Play)
		self.movie_window = ZoneVideo
		self.bus.enable_sync_message_emission()
		self.bus.connect("sync-message::element", self.on_sync_message)
		messager.inscrire(self.lire_fichier, 'video_a_lire')
		
		
	def on_sync_message(self, bus, message):
		if message.structure is None:
			return
		message_name = message.structure.get_name()
		if message_name == "prepare-xwindow-id":
			imagesink = message.src
			imagesink.set_property("force-aspect-ratio", True)
			gtk.gdk.threads_enter()
			imagesink.set_xwindow_id(self.movie_window.window.xid)
			gtk.gdk.threads_leave()
			
	def on_DA_click(self, widget, event):
		if event.type == gtk.gdk._2BUTTON_PRESS:
			if self.fullscreen:
				parent = widget.get_parent()
				widget.reparent(self.DA_Parent)
				parent.destroy()
				self.fullscreen = False

			else:
				fenetre = gtk.Window()
				fenetre.fullscreen()
				fenetre.show()

				widget.reparent(fenetre)
				self.fullscreen = True
				

			print('doubleclick')
			
	def on_B_Play_Click(self, b):
		#J'envoie le bouton pour que son icône puisse changer en fonction de l'état trouvé
		self.toggle_pause()
	
	
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