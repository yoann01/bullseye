# -*- coding: utf-8 -*-
import vlc
import os
import glib
import sys

from common import messager

#instance = vlc.Instance()
class Player(object):
	
	def __init__(self):
		#self._player = instance.media_player_new()
		self.backend = 'VLC'
		self._player = vlc.MediaPlayer()
		#Ne fonctionne pas, va savoir pourquoi. Bypass = trick sur le get pourcentage
		#self._player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, self.on_message)
		
		
		#On met en route la barre de progression

		#self.PBar.connect('button-release-event', self.seek_end)
		
		#def update_position():
			#self.PBar.set_fraction(self.pourcentage)
			#self.PBar.set_text(self.etat)
		#self._position_updater = Updater()
		#self._position_updater.set_target(update_position)

	@property
	def duration(self):
		try:
			value = self._player.get_length()
		except:
			value = -1

		return value
        
	@property
	def pourcentage(self):
		pos = round(self._player.get_position(), 2)
		if(pos == 1.0):
			messager.diffuser('need_piste_suivante', self, 'eos')
		return pos
			
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
			secondes = self.position / 1000
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
		return self._player.get_time()

	def set_position(self, position):
		self._player.set_position(position)

	position = property(fset=set_position, fget=get_position)
		
	
	def playTrack(self, element):
		#element.path.encode('latin-1')
		self.load(element.path.encode( "utf8" ))
		self.play()

	def load(self, filename):
		self._player.set_mrl(filename)

	def play(self):
		#self._position_updater.start()
		self._player.play()

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
		return (not self._player.is_playing() and self.position != -1)
		
	def is_stopped(self):
		return (not self._player.is_playing() and self.position == -1)
	
	def is_playing(self):
		return self._player.is_playing()
	
	def on_message(self, event):
		messager.diffuser('need_piste_suivante', self, 'eos')
		
	def on_volume_change(self, widget, value):
		self.volume = value
	
	def seek_end(self, widget, event):
		mouse_x, mouse_y = event.get_coords()
		progress_loc = self.PBar.get_allocation()
		value = mouse_x / progress_loc.width
		
		if value < 0: value = 0
		if value > 1: value = 1
		

		self.position = value
		self.PBar.set_fraction(value)
		
	def setUpGtkVideo(self, widget):
		self.movie_window = widget
		if sys.platform == 'win32':
			self._player.set_hwnd(self.movie_window.window.handle)
		else:
			self._player.set_xwindow(self.movie_window.window.xid)
		return True
		
	def setUpQtVideo(self, widget):
		if sys.platform == "linux2": # for Linux using the X Server
			self._player.set_xwindow(widget.winId())
		elif sys.platform == "win32": # for Windows
			self._player.set_hwnd(widget.winId())
		elif sys.platform == "darwin": # for MacOS
			self._player.set_agl(widget.windId())
		
	def toggle_pause(self, button):
		if self.is_paused():
			button.set_stock_id(gtk.STOCK_MEDIA_PAUSE)
			self.play()
		elif self.is_stopped():
			messager.diffuser('need_piste_suivante', self, 'click')
		else:
			button.set_stock_id(gtk.STOCK_MEDIA_PLAY)
			self.pause()
			
class MusicPlayer(Player):
	def __init__(self, Box):
		BB = gtk.HButtonBox()
		B_Prev = gtk.ToolButton(gtk.STOCK_MEDIA_PREVIOUS)
		B_Play = gtk.ToolButton(gtk.STOCK_MEDIA_PLAY)
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
		
		ProgressBar = gtk.ProgressBar()
		Box.pack_start(ProgressBar)
		Box.show_all()
		Player.__init__(self, ProgressBar, B_Play)
		#on "coupe" la sortie vidéo
		messager.inscrire(self.lire_fichier, 'musique_a_lire')
		messager.inscrire(self.stop, 'arret_musique')
		
	def on_B_Next_clicked(self, w):
		#Joue la piste suivante de la queue courante, seulement si il y en a une (de piste hein)
		messager.diffuser('need_piste_suivante', self, 'demarre')

	def on_B_Play_Click(self, b):
		#J'envoie le bouton pour que son icône puisse changer en fonction de l'état trouvé
		self.toggle_pause(b)
	
	def on_B_Prev_Click(self, w):
		messager.diffuser('need_piste_precedente', self, None)
	
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
		self.movie_window.realize()
		self._player.set_xwindow(self.movie_window.window.xid)
		#self.bus.enable_sync_message_emission()
		#self.bus.connect("sync-message::element", self.on_sync_message)
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
		self.toggle_pause(b)



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