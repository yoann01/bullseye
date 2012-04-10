# -*- coding: utf-8 -*-
import gtk
import glib
import threading
import time
import gobject
import gettext
import logging

from operator import attrgetter


from common import messager, settings, util

from data.elements import Track, BDD

import gui.modales
from gui.menus import TrackMenu
from gui.util import icons, etoiles

IM = icons.IconManager()

logger = logging.getLogger(__name__)

class QueueManager(gtk.VBox):
	"""
        Cet objet correspond au manager de pistes à jouer, graphiquement c'est un NoteBook (onglets, etc...)
        TODO ponts (A -> B, B-> C), filtres
        TODO bouton stop = set stop track 
        """
	def __init__(self, playerWidget):
		#gtk.rc_parse_string("style \"ephy-tab-close-button-style\"\n"
			     #"{\n"
			       #"GtkWidget::focus-padding = 0\n"
			       #"GtkWidget::focus-line-width = 0\n"
			       #"xthickness = 0\n"
			       #"ythickness = 0\n"
			     #"}\n"
			     #"widget \"*.ephy-tab-close-button\" style \"ephy-tab-close-button-style\"")
		gtk.VBox.__init__(self)
		self.NoteBook = gtk.Notebook()
		
		self.playerWidget = playerWidget
		self.playerWidget.queueManager = self

		
		#DEPRECATED Abonnement à certains types de messages auprès du messager
		#messager.inscrire(self.charger_playlist, 'playlist')
		messager.inscrire(self.ajouter_selection, 'desPistes')
		messager.inscrire(self.charger_playlist, 'playlistData')


		
		self.IM = icons.IconManager()
		self.queue_jouee = None
		self.playing_iter = None
		self.dest_row = None
		# On ajoute une liste pour commencer
		self.loadState()
		self.initialisation_raccourcis()
		glib.timeout_add_seconds(300, self.save_state)
		
		actionBox = gtk.HBox()
		scrollToCurrentButton = gtk.ToolButton(gtk.STOCK_JUMP_TO)
		scrollToCurrentButton.connect('clicked', self.scrollToCurrent)
		actionBox.pack_start(scrollToCurrentButton, False)
		
		self.pack_start(self.NoteBook)
		self.pack_start(actionBox, False)
			
		self.NoteBook.connect('expose-event', self.redrawAddTabButton)
		self.NoteBook.connect('button-release-event', self.onButtonRelease)
		

	def addSelection(self, tracks):
		self.visibleQueue.addTracks(tracks)
		
	def getAddTabButtonPos(self):
		try:
			last_tab_label = self.NoteBook.get_tab_label(self.NoteBook.get_nth_page(self.NoteBook.get_n_pages() -1))
			alloc = last_tab_label.get_allocation()
		except:
			print 'TODO'
		
		return (alloc.x + alloc.width + 10, alloc.y + 4)
			
	def onButtonRelease(self, widget, event):
		if(event.button == 1):
			x, y = self.getAddTabButtonPos()
			x_root, y_root = self.window.get_root_origin()
			x = x + x_root - 5
			y = y + y_root + 16
			if(event.x_root > x and event.x_root < x + 32 and event.y_root > y and event.y_root < y + 32):
				self.addQueue()
		
	def redrawAddTabButton(self, w, e):
		icon = gtk.Image().render_icon(gtk.STOCK_ADD, gtk.ICON_SIZE_MENU)
		#icon = gtk.gdk.pixbuf_new_from_file('icons/track.png')
		
		alloc = self.getAddTabButtonPos()
		self.window.draw_pixbuf(None, icon, 0, 0, alloc[0], alloc[1])

	@property
	def visibleQueue(self):
		try:
			queue = self.NoteBook.get_nth_page(self.NoteBook.get_current_page())
		except:
			queue = None

		return queue


	def ajouter_selection(self, selection): 
		''' 
			Ajoute la séléction envoyée par le Panel à la queue visible
			@param selection : t de list content les informations des pistes à ajouter
				rappel de l'ordre: police, icon_playing, icon_stopping, ID, path, titre, album, artiste, length, count, pixbuf_note, note, bridge_src key
		'''
		liste = self.visibleQueue
		try:
			iter_pos = liste.get_iter(self.dest_row[0])
			pos_type = self.dest_row[1]
		except:
			iter_pos = None
			pos_type = None
			
		if liste != None:
			for track in selection:
				length = self.format_length(track[5])
				rating= self.IM.rating_pixbufs[track[7]]
				if(pos_type == gtk.TREE_VIEW_DROP_BEFORE or pos_type == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE):
					liste.insert_before(iter_pos, [None, None, None, track[0], track[1], track[2], track[3], track[4], length, track[6], rating, track[7], None] )
				elif(pos_type == gtk.TREE_VIEW_DROP_AFTER or pos_type == gtk.TREE_VIEW_DROP_INTO_OR_AFTER):
					liste.insert_after(iter_pos, [None, None, None, track[0], track[1], track[2], track[3], track[4], length, track[6], rating, track[7], None] )
				else:
					liste.append([None, None, None, track[0], track[1], track[2], track[3], track[4], length, track[6], rating, track[7], None] )
		self.dest_row = None
		
	def addQueue(self, button=None, label=None):
		nb_pages = self.NoteBook.get_n_pages()
		if(label != None):
			#Cela veut dire qu'on a reçu une playlist du messager
			nouvelleQueue = Playlist(self, label)
		else:
			label = _("List ") + str(nb_pages)
			nouvelleQueue = Queue(self, label)
			
		self.NoteBook.set_current_page(nb_pages)
		return nouvelleQueue
		
		
	def avance_ou_arrete(self, motif):
		'''
			Méthode primordiale permettant au MusicPlayer d'avoir sa piste sur demande (démarrage ou enchaînement)
		'''
		# Tout d'abord on incrémente si fin de piste atteinte et on vire le marquage de l'ancienne piste courante
		
		if(motif == "eos"):
			#ID_courant = self.queue_jouee.get_value(self.playing_iter, 3)
			self.incrementPlayedTrack()
			
		self.demarquer_piste()
			
		try:	
			if (self.queue_jouee.get_value(self.playing_iter, 2) is None):
				not_a_stop_track = True
			else:
				not_a_stop_track = False
		except:
			not_a_stop_track = True
			
		try:
			di = self.directList[0]
			self.directList.remove(di)
			if(di.row == None):
				di = None
		except IndexError:
			di = None
			
		if(not_a_stop_track): #On vérifie d'abord qu'on ne doit pas s'arrêter avant de mouliner
			#Quelle est la piste à jouer? 3 possibilités :
			if(di != None): # 1/ une piste prioritaire
				self.playing_track = Track(di.get_model()[di.get_path()][3])
				
				if di.temp:
					self.temp_queue_jouee = di.get_model()
					self.temp_playing_iter = self.temp_queue_jouee.get_iter(di.get_path())
				else:
					self.queue_jouee = di.get_model()
					self.playing_iter = self.queue_jouee.get_iter(di.get_path())
				
				messager.diffuser('musique_a_lire', self, self.playing_track)
				self.marquer_piste()
			else:
				if(self.playing_iter): # 2/ la piste qui suit la dernière piste lue
					bridge_key = self.queue_jouee.get_value(self.playing_iter, 12)
					if(bridge_key != None):
						try:
							ref = self.bridges_dest[bridge_key]
							queue = ref.get_model()
							next_iter = queue.get_iter(ref.get_path())
							self.queue_jouee = queue
						except:
							next_iter = self.queue_jouee.iter_next(self.playing_iter)
					else:
						next_iter = self.queue_jouee.iter_next(self.playing_iter)
				else: # 3/ la première piste de la queue visible
					self.queue_jouee = self.visibleQueue
					next_iter = self.queue_jouee.get_iter_first()
					
				
				if(next_iter): # Après recherche, on a obtenu une piste
					self.playing_iter = next_iter
					self.playing_track = Track(self.queue_jouee.get_value(self.playing_iter, 3))
					messager.diffuser('musique_a_lire', self, self.playing_track)
					self.marquer_piste()
				else: # Il n'y a pas de suivant
					self.queue_jouee.set_value(self.playing_iter, 2, None)
					messager.diffuser('arret_musique', self, True)
					print("Liste de lecture terminée ou stoppée")

		else: # On s'arrête simplement
			self.queue_jouee.set_value(self.playing_iter, 2, None)
			messager.diffuser('arret_musique', self, True)
			print("Liste de lecture terminée ou stoppée")
			
			
			
	def charger_playlist(self, data):
		#data[0] = tracks ID, data[1] = playlist name
		queue = self.addQueue(data[1])
		messager.diffuser('ID_playlist', self, [data[0], queue], False)
	
	def cleanDirectList(self):
		"""
			Remove all DirectIter that is no longer present
		"""
		for di in self.directList:
			if(di.queue.get_path(di.ligne) == None):
				self.directList.remove(di)

	
	def closeQueue(self, bouton=None, onglet=None):
		if(bouton == None):
			#La demande provient d'un raccourci clavier
			numero_page = self.NoteBook.get_current_page()
		else:
			numero_page = self.NoteBook.page_num(onglet)
		if(self.NoteBook.get_nth_page(numero_page).modified == True):
			dialog = gtk.Dialog(title=_("Closing non-saved playlist"), buttons=(gtk.STOCK_NO, gtk.RESPONSE_REJECT,
                      gtk.STOCK_YES, gtk.RESPONSE_ACCEPT))
			box = dialog.get_content_area()
			box.pack_start(gtk.Label(_("Save changes?")), False, 5, 5)
			box.show_all()
			reponse = dialog.run()
			dialog.destroy()
			if(reponse == -3): #Valider
				self.get_nth_page(numero_page).save()
		self.NoteBook.remove_page(numero_page)
		#Il n'y a plus d'onglet, on en crée un
		if(self.NoteBook.get_n_pages() == 0):
			self.addQueue()

		
	def getDefaultTrack(self):
		return self.visibleQueue.getTrackAt(0)
	
	def incrementPlayedTrack(self):
		self.playing_track.incrementPlayCount()
		try:
			compteur = self.temp_queue_jouee.get_value(self.temp_playing_iter, 9)
			self.temp_queue_jouee.set_value(self.temp_playing_iter, 9, compteur)
		except:
			compteur = self.queue_jouee.get_value(self.playing_iter, 9) + 1
			self.queue_jouee.set_value(self.playing_iter, 9, compteur)
		
	def initialisation_raccourcis(self):
		raccourcis = (
			('<Control>W', lambda *e: self.closeQueue()),
			('<Control>T', lambda *e: self.addQueue()),
		)
		accel_group = gtk.AccelGroup()
		for key, function in raccourcis:
			key, mod = gtk.accelerator_parse(key)
			accel_group.connect_group(key, mod, gtk.ACCEL_VISIBLE,
				function)
		messager.diffuser('desRaccourcis', self, accel_group)
		

        @util.threaded
        def loadState(self):
		"""
			TODO Use one sql query by queue (using parametized IN clause) and thread this
			self.memcursor.execute('''SELECT id, matbefore, matafter, name, date 
                            FROM main 
                           WHERE name IN (%s)''' % 
                       ','.join('?'*len(offset)), (offset,))
		"""
		bdd = BDD()
		queues = settings.get_option('session/queues', None)
		if(queues is not None):
			for key in queues.iterkeys():
				if type(key).__name__=='int':
					self.addQueue()
					self.addSelection(bdd.getTracksFromIDs(queues[key]))
				else:
					playlist = self.addQueue(key)
					for track_id in queues[key]:
						self.addSelection(bdd.getTracks({'track_ID':track_id}))
					playlist.Liste.connect("row-changed", playlist.setModified)
		else:
			self.addQueue()
		
		
	def marquer_piste(self):#Ajoute un marqueur (pour la piste courante de la liste jouée)
		icon = gtk.gdk.pixbuf_new_from_file('icons/track.png')
		try:
			self.temp_queue_jouee.set_value(self.temp_playing_iter, 1, icon)
			self.temp_queue_jouee.set_value(self.temp_playing_iter, 0, 'bold')
		except:
			self.queue_jouee.set_value(self.playing_iter, 1, icon)
			self.queue_jouee.set_value(self.playing_iter, 0, 'bold')

		
	def recule(self, data):
		if self.numero > 0:
			self.demarquer_piste()
			self.numero -= 1
			self.playing_iter = self.queue_jouee.get_iter(self.numero)
			chemin = self.queue_jouee[self.numero][4]
			messager.diffuser('musique_a_lire', self, chemin)
			self.marquer_piste()
			
	def save_state(self):
		i = 0
		queues = {}
		while( i < self.NoteBook.get_n_pages()):
			t = []
			queue =  self.NoteBook.get_nth_page(i)
			model = queue.model
			iter = model.get_iter_first()
			while(iter is not None):
				t.append(model.get_value(iter, 3))
				iter = model.iter_next(iter)
			if(type(queue).__name__=='Playlist'):
				queues[self.NoteBook.get_nth_page(i).tab_label.get_text()] = t
			else:
				queues[i] = t
			i += 1
		settings.set_option('session/queues', queues)
		
	def scrollToCurrent(self, button=None):
		currentQueue, currentTrack = self.playerWidget.getCurrents()
		index = currentQueue.tracks.index(currentTrack)
		self.NoteBook.set_current_page(self.NoteBook.page_num(currentQueue))
		currentQueue.TreeView.scroll_to_cell(index)
			


class Queue(gtk.ScrolledWindow):
	'''
		Représente une queue (onglet) d'un manager de queue.
	'''
	def __init__(self, manager, label):
		self.modified = False #pour les playlists enregistrées
		self.manager = manager
		#police, icon_playing, icon_stopping, ID, path, titre, album, artiste, length, count, pixbuf_note, note, bridge_src key
		self.model = gtk.ListStore(str, gtk.gdk.Pixbuf, gtk.gdk.Pixbuf, int, str, str, str, str, str, int, gtk.gdk.Pixbuf, int, str)
		self.TreeView = gtk.TreeView(self.model)
		self.TreeView.set_rules_hint(True)
		self.TreeView.set_reorderable(True)
		self.TreeView.connect("row-activated", self.activated)
		self.TreeView.connect("button-press-event", self.onButtonClick)
		self.TreeView.connect("key-press-event", self.executerRaccourci)
		self.model.connect('row-deleted', self.onRowDeleted)
		self.model.connect('row-inserted', self.onRowInserted)
		self.model.connect('rows-reordered', self.onRowsReordered)
		self.isMoving = False #Tell if there is currently a drag operation initiated by this TreeView
		#On s'occupe du "label" de l'onglet
		tab_label_box = gtk.EventBox()
		tab_label_box.set_visible_window(False) #make event box don't change anything lookwise
		tab_label_box.connect('event', self.on_tab_click, self.TreeView)
		self.tab_label = gtk.Label(label)
		self.tab_label.set_max_width_chars(20)
		hbox = gtk.HBox(False, 2)
		hbox.pack_start(self.tab_label, False, False)
		close_icon = gtk.Image()
		close_icon.set_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
		close_button = gtk.Button()
		close_button.set_relief(gtk.RELIEF_NONE)
		close_button.set_focus_on_click(False)
		close_button.set_tooltip_text(_("Close Tab"))
		close_button.add(close_icon)
		close_button.set_size_request(24,24) # avoid big padding
		close_button.connect('clicked', manager.closeQueue, self)
		hbox.pack_end(close_button, False, False)
		tab_label_box.add(hbox)
		tab_label_box.show_all()
		
		cell = gtk.CellRendererText()
		pb = gtk.CellRendererPixbuf()
		pb2 = gtk.CellRendererPixbuf()
		cellr = etoiles.RatingCellRenderer()
		cellr.connect('rating-changed', self.on_cell_rating_changed)
		#col = gtk.TreeViewColumn('header', cell, text=0, font=1)
		Col_Titre = BSColumn('col_title', _('Title'), expand=True)
		Col_Artiste = BSColumn('col_artist', _('Artist'), expand=True)
		Col_Album = BSColumn('col_album', _('Album'), expand=True)
		Col_Duree = BSColumn('col_length', _('Length'))
		Col_Count = BSColumn('col_playcount', _('Playcount'), cell, model_text=9)
		Col_Note = BSColumn('col_rating', _('Rating'), cellr, pixbuf=10, default_width=85)
		Col_Titre.name = 'col_title'
		Col_Artiste.name = 'col_artist'
		self.TreeView.append_column(Col_Titre)
		self.TreeView.append_column(Col_Album)
		self.TreeView.append_column(Col_Artiste)
		self.TreeView.append_column(Col_Duree)
		self.TreeView.append_column(Col_Count)
		self.TreeView.append_column(Col_Note)
		
		self.TreeView.set_enable_search(False)
		self.TreeView.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
		#self.TreeView.set_rubber_banding(True) #séléction multiple by dragging
		#Le TreeView accepte les données droppées
		self.TreeView.enable_model_drag_dest([('text/plain', 0, 0), ('GTK_TREE_MODEL_ROW', 0, 0)],
                  gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE)
		self.TreeView.connect("drag-data-received", self.on_drag_data_received)
		self.TreeView.connect("drag-begin", self.on_drag_begin)
		
		Col_Titre.pack_start(pb, False)
		Col_Titre.pack_start(pb2, False)
		Col_Titre.pack_start(cell, True)
		Col_Artiste.pack_start(cell, True)
		Col_Album.pack_start(cell, True)
		Col_Duree.pack_start(cell, True)
		
		Col_Titre.set_attributes(cell, text=5, font=0)
		Col_Titre.add_attribute(pb, 'pixbuf', 1)
		Col_Titre.add_attribute(pb2, 'pixbuf', 2)
		Col_Artiste.add_attribute(cell, 'text', 7)
		Col_Album.add_attribute(cell, 'text', 6)
		Col_Duree.add_attribute(cell, 'text', 8)
		
		Col_Titre.set_sort_column_id(5)
		Col_Album.set_sort_column_id(6)
		Col_Artiste.set_sort_column_id(7)
		Col_Count.set_sort_column_id(9)
		Col_Note.set_sort_column_id(11)

		
		self.columnsFields = {5:'title', 6:'album', 7:'artist', 9:'playcount', 11:'rating'}
		
		cols = [Col_Titre, Col_Artiste, Col_Album, Col_Count, Col_Note]
		
		for col in cols:
			col.connect('clicked', self.on_column_clicked)
		
		
		#Col_Titre.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
		#Col_Titre.set_fixed_width(40)
		
		messager.inscrire(self.updateView, 'track_data_changed')
		
		self.tracks = []
		
		
		gtk.ScrolledWindow.__init__(self)
		self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.add(self.TreeView)
		manager.NoteBook.append_page(self, tab_label_box)
		manager.show_all()
		
	def activated(self, TreeView, i , c):
		#W = TreeView, c = colonne, i = numero de ligne
		self.manager.playerWidget.cleanPlayFlag()
		self.manager.playerWidget.playTrack(self.tracks[i[0]], self)
		
	def addTracks(self, tracks):
		if type(tracks).__name__!='list': # One track
			tracks = [tracks,]
			
		self.tracks.extend(tracks)
		
		try:
			iter_pos = liste.get_iter(self.dest_row[0])
			pos_type = self.dest_row[1]
		except:
			iter_pos = None
			pos_type = None
			
		for track in tracks:
			length = self.format_length(track.length)
			rating= self.manager.IM.rating_pixbufs[track.rating]
			if(pos_type == gtk.TREE_VIEW_DROP_BEFORE or pos_type == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE):
				self.model.insert_before(iter_pos, [None, None, None, track[0], track[1], track[2], track[3], track[4], length, track[6], rating, track[7], None] )
			elif(pos_type == gtk.TREE_VIEW_DROP_AFTER or pos_type == gtk.TREE_VIEW_DROP_INTO_OR_AFTER):
				self.model.insert_after(iter_pos, [None, None, None, track[0], track[1], track[2], track[3], track[4], length, track[6], rating, track[7], None] )
			else:
				self.model.append([None, None, None, int(track.ID), track.path, track.tags['title'], track.tags['album'], track.tags['artist'], length, track.playcount, rating, track.rating, None] )
		
		
	def removeTrack(self, iter):
		self.model.remove(iter)
		path = self.model.get_path(iter)
		self.tracks.remove(path[0])
	
		
	def enregistrer(self, button):
		DN = gtk.Dialog()
		Entry = gtk.Entry()
		hbox = gtk.HBox()
		hbox.pack_start(gtk.Label(_("Name") + " : "), False, 5, 5)
		hbox.pack_end(Entry)
		DN.vbox.add(hbox)
		
		DN.add_button('OK', 1)
		DN.add_button(_("Cancel"), 0)
		DN.show_all()
		action = DN.run()
		nom = Entry.get_text()
		DN.destroy()
		if(action == 1):
			self.save(nom)
			messager.diffuser('playlist_ajoutee', self, ['personalised', nom])
	
	
	def executerRaccourci(self, widget, event):
		if(event.keyval == gtk.gdk.keyval_from_name("Delete")):
			selection = self.TreeView.get_selection()
			liste, paths = selection.get_selected_rows()
			paths.reverse() # Start from tail in order to be sure next paths to delete are still referring to the same tracks as before
			for path in paths:
				liste.remove(liste.get_iter(path))
				#next = liste.iter_next(iter)
				#if(next):
					#selection.select_iter(next)
				#liste.remove(iter)
			self.manager.cleanDirectList()
				
		elif(event.keyval == gtk.gdk.keyval_from_name("s")):
			selection = self.TreeView.get_selection()
			liste, paths = selection.get_selected_rows()
			for path in paths:
				self.toggleStopFlag(self.tracks[path[0]])
		
	#def fermeture(self, widget):
		#numero_page = widget.get_parent().get_parent().get_parent().page_num(self.TreeView)
		#self.NB.remove_page(numero_page)
		##si aucun onglet, en créer un
		#if(self.NB.get_n_pages() == 0):
			#self.NB.addQueue()
		
	def format_length(self, length):
		minutes = 0
		while length > 59:
			length -= 60
			minutes += 1
		if length < 10:
			length = "0" + str(length)
		else:
			length = str(length)
		length = str(minutes) + ":" + length
		
		return length
		
	def getNextTrack(self, tr):
		try:
			return self.tracks[self.tracks.index(tr) + 1]
		except IndexError:
			return None
			
	def getTrackAt(self, i):
		try:
			return self.tracks[i]
		except IndexError:
			return None
			
			
	def onButtonClick(self, TreeView, event):
		# On vérifie que c'est bien un clic droit:
		if event.button == 3:
			from abstract.playerwidget import AbstractPlayerWidget
			path = TreeView.get_path_at_pos(int(event.x),int(event.y))[0]
			if(path != None):
				queue = TreeView.get_model()
				piste_ID = queue[path][3]
				ligne = queue.get_iter(path)
			if (path != None):
				track = self.tracks[path[0]]
				iter = queue.get_iter(path)
				row = gtk.TreeRowReference(queue, path)
				m = TrackMenu(piste_ID)
				m.append(gtk.SeparatorMenuItem())
				i = gtk.ImageMenuItem(_("Remove from queue"))
				i.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_MENU))
				i.connect_object('activate', self.removeTrack, ligne)
				m.append(i)
				
				i = gtk.ImageMenuItem(_("Set stop cursor"))
				i.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_STOP, gtk.ICON_SIZE_MENU))
				i.connect_object('activate', self.toggleStopFlag, track)
				m.append(i)
				
				jumpListSize = str(len(self.manager.playerWidget.jumpList))
				i = gtk.ImageMenuItem(_("Add to perm jump list"))
				i.set_image(gtk.image_new_from_pixbuf(icons.MANAGER.pixbuf_from_text(jumpListSize, (18, 18))))
				i.connect_object('activate', AbstractPlayerWidget.addToJumpList, self.manager.playerWidget, self, track)
				m.append(i)
				
				#image = icons.MANAGER.pixbuf_from_text(str(len(self.directList)), (18, 18), '#FFCC00', '#000', '#000')
				#image = icons.MANAGER.pixbuf_from_text(str(len(self.directList)), (18, 18))
				i = gtk.ImageMenuItem(_("Add to temp jump list"))
				i.set_image(gtk.image_new_from_pixbuf(icons.MANAGER.pixbuf_from_text(jumpListSize, (18, 18), '#FFCC00', '#000', '#000')))
				i.connect_object('activate', AbstractPlayerWidget.addToJumpList, self.manager.playerWidget, self, track, True)
				m.append(i)
				
				
				# *** BRIDGES ***
				dic = self.manager.playerWidget.bridgesSrc
				
				
				if(track.bridgeSrc != None):
					def remove_bridge_src(*args):
						dic.pop(track.bridgeSrc)
						track.bridgeSrc = None
						self.refreshView(track)
						
					i = gtk.ImageMenuItem(_("Unset bridge source"))
					i.set_image(gtk.image_new_from_pixbuf(icons.MANAGER.pixbuf_from_text(track.bridgeSrc, (18, 18), '#FF0000')))
					i.connect('activate', remove_bridge_src)
				else:
					def add_bridge_src(*args):
						self.manager.playerWidget.bridgesSrc[letter] = track # gtk.TreeRowReference(self.model, path)
						track.bridgeSrc = letter
						self.refreshView(track)
					
					letter = chr(65 + len(dic))
					icon = icons.MANAGER.pixbuf_from_text(letter + ' →', (24, 18), '#58FA58', '#000', '#000')
					i = gtk.ImageMenuItem(_("Add bridge source"))
					i.set_image(gtk.image_new_from_pixbuf(icon))
					i.connect('activate', add_bridge_src)
				m.append(i)
				
				# --- BRIDGES DESTINATIONS --- 
				dicDest = self.manager.playerWidget.bridgesDest
				

				if(track.bridgeDest != None):
					def remove_bridge_dest(*args):
						self.manager.playerWidget.bridgesDest.pop(track.bridgeDest)
						track.bridgeDest = None
						self.refreshView(track)
						
					i = gtk.ImageMenuItem(_("Unset bridge dest"))
					i.set_image(gtk.image_new_from_pixbuf(icons.MANAGER.pixbuf_from_text(track.bridgeDest, (18, 18), '#FF0000')))
					i.connect('activate', remove_bridge_dest)
				else:
					def add_bridge_dest(*args):
						self.manager.playerWidget.bridgesDest[letterDest] = track #gtk.TreeRowReference(self.model, path)
						track.bridgeDest = letterDest
						self.refreshView(track)
					
					letterDest = chr(65 + len(dicDest))
					icon = icons.MANAGER.pixbuf_from_text('← ' + letterDest, (24, 18), '#CC2EFA')
					i = gtk.ImageMenuItem(_("Add bridge dest"))
					i.set_image(gtk.image_new_from_pixbuf(icon))
					i.connect('activate', add_bridge_dest)
					
				
					
				#if(iter in self.manager.bridges_src.values):

				#else:
					#i = gtk.ImageMenuItem(_("Add to temp jump list"))
					#i.set_image(gtk.image_new_from_pixbuf(icons.MANAGER.pixbuf_from_text('A'), (18, 18), '#FFCC00', '#000', '#000')))
					#i.connect('activate', self.manager.addToDirectList, queue, ligne, True)
				m.append(i)
				
				m.show_all()
				m.popup(None, None, None, event.button, event.time)
				
		elif event.button == 2:
			path = TreeView.get_path_at_pos(int(event.x),int(event.y))[0]
			if(path != None):
				track = self.tracks[path[0]]
				from gtk.gdk import CONTROL_MASK, SHIFT_MASK
				if event.state & CONTROL_MASK:
					self.manager.playerWidget.addToJumpList(self, track, False)
				else:
					self.manager.playerWidget.addToJumpList(self, track, True)
					
					
					
	def on_cell_rating_changed(self, widget, path, rating):
		#self.model[path][10] = IM.pixbuf_from_rating(rating)
		self.tracks[path[0]].change_rating(widget, rating)
		#messager.diffuser('modification_note', self, ["track", self.model[path][3], rating])
	
	def on_column_clicked(self, column):
		def disable_sorting_state():
			time.sleep(2.0)
			self.model.set_sort_column_id(-2, 0)
			
		a = threading.Thread(target=disable_sorting_state)
		a.start()
		
	def on_drag_begin(self, treeview, dragcontext):
		self.isMoving = True
	
	def on_drag_data_received(self, TV, drag_context, x, y, selection_data, info, timestamp):
		if(selection_data.get_target() == 'text/plain'):
			#fin d'un DND
			self.manager.dest_row = self.TreeView.get_dest_row_at_pos(x, y)
			
			T = eval(selection_data.get_text()) # eval => permet de retransformer la chaîne de caractères en tableau de dictionnaires
			#for dic in T:
			messager.diffuser('need_tracks', self, T)
		
	def on_tab_click(self, widget, event, child):
		if event.type == gtk.gdk.BUTTON_PRESS:
			if(event.button == 1): 
				print("click gauche")
			elif(event.button  == 3):
				m = gtk.Menu() 
				i = gtk.MenuItem(_("Save as...")) 
				i.connect('activate', self.enregistrer)
				m.append(i) 
				i = gtk.MenuItem(_("Set all track to stop"))
				i.connect('activate', self.on_stop_track_button_click, self.model, False)
				m.append(i)
				m.show_all()
				m.popup(None, None, None, event.button, event.time)
			elif(event.button == 2):
				self.manager.closeQueue(None, self)
			else:
				return False
			

	def onRowDeleted(self, model, path):
		if(self.isMoving):
			previousPos = path[0]
			trackMoved = self.tracks.pop(previousPos)
			self.tracks.insert(self.newPos, trackMoved)
			self.isMoving = False # Done moving
		
	def onRowInserted(self, model, path, iter):
		if(self.isMoving):
			self.newPos = path[0] - 1
			
	def onRowsReordered(self, model, path, iter, newOrder):
		column, order = self.model.get_sort_column_id()
		if(order == gtk.SORT_ASCENDING):
			reverse = False
		else:
			reverse = True
		self.tracks = sorted(self.tracks, key=attrgetter(self.columnsFields[column]), reverse=reverse)
	
	def refreshView(self, track):
		'''
			Method called by PlayerWidget, mainly to update flags icons
		'''
		font = 'normal'
		
		if('play' in track.flags):
			icon = gtk.gdk.pixbuf_new_from_file('icons/track.png')
			font = 'bold'
		elif 'permjump' in track.flags:
			icon = icons.MANAGER.pixbuf_from_text(str(track.priority), (18, 18))
		elif 'tempjump' in track.flags:
			icon = icons.MANAGER.pixbuf_from_text(str(track.priority), (18, 18), '#FFCC00', '#000', '#000')
		elif track.bridgeSrc != None:
			if(track.bridgeDest != None):
				icon = icons.MANAGER.pixbuf_from_text('← ' + track.bridgeDest + ' - ' + track.bridgeSrc + ' →', (36, 18), '#58FA58', '#000', '#000')
			else:
				icon = icons.MANAGER.pixbuf_from_text(track.bridgeSrc + ' →', (24, 18), '#58FA58', '#000', '#000')
		elif track.bridgeDest != None:
			icon = icons.MANAGER.pixbuf_from_text('← ' + track.bridgeDest, (24, 18), '#CC2EFA')
		else :
			icon = None
			
		if 'stop' in track.flags:
			stop_icon = gtk.ToolButton()
			stop_icon = stop_icon.render_icon(gtk.STOCK_MEDIA_STOP, gtk.ICON_SIZE_BUTTON, detail=None)
			font = 'italic'
		else:
			stop_icon = None
		
		index = self.tracks.index(track)
		iter = self.model.get_iter(index)
		self.model.set(iter, 0, font, 1, icon, 2, stop_icon, 4, track.path, 5, track.tags['title'], 6, track.tags['album'], 7, track.tags['artist'], 9, track.playcount, 10, IM.pixbuf_from_rating(track.rating))
		
		
	def save(self, name=None):
		if(name == None):
			name = self.tab_label.get_text()[1:]
		fichier = open('playlists/' + name,'w')
		for piste in self.model:
			print(piste[3])
			fichier.write(str(piste[3]) + "\n")
		fichier.close()
	
	
	
	
	
	def toggleStopFlag(self, track):
		flags = track.flags
		if 'stop' in flags:
			flags.remove('stop')
		else:
			flags.add('stop')
		self.refreshView(track)
	
	
	def updateView(self, track):
		"""
			A track data has just changed in the whole system. Checks if we have this track and update accordingly
			#model order :police, icon_playing, icon_stopping, ID, path, titre, album, artiste, length, count, pixbuf_note, note
		"""
		iter = self.model.get_iter_first()
		while(iter is not None):
			if(self.model.get_value(iter, 3) == int(track.ID)):
				self.model.set(iter, 4, track.path, 5, track.tags['title'], 6, track.tags['album'], 7, track.tags['artist'], 10, IM.pixbuf_from_rating(track.rating))
			iter = self.model.iter_next(iter)


class Playlist(Queue):
	def __init__(self, manager, label):
		Queue.__init__(self, manager, label)
		
	def setModified(self, model, path, i):
		if(self.modified == False):
			self.modified = True
			self.tab_label.set_text('*' + self.tab_label.get_text())
			

class DirectIter():
	'''
		Représente une piste qui sera lue en priorité
	'''
	def __init__(self, row, temp=False):
		self.row = row
		self.temp = temp
	
	def equals(self, ref):
		if(self.row == None):
			return False
		return (ref.get_path() == self.get_path() and ref.get_model() == self.get_model())
		
	def get_model(self):
		return self.row.get_model()
	
	def get_path(self):
		return self.row.get_path()


		
	
class BSColumn(gtk.TreeViewColumn):
	'''
		Bullseye Special Column
	'''
	def __init__(self, name, label, cell=None, model_text=None, pixbuf=None, default_width=50, expand=False):
		kwargs = {}
		if(model_text is not None):
			kwargs['text'] = model_text
		if(pixbuf is not None):
			kwargs['pixbuf'] = pixbuf
		gtk.TreeViewColumn.__init__(self, label, cell, **kwargs)
		self.name = name
		width = settings.get_option('music/' + self.name + '_width', default_width)
		self.set_min_width(default_width)
		#self.set_max_width(width)
		self.set_expand(expand)
		self.set_resizable(True)
		self.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
		self.connect('notify::width', self.on_width_change)
		
	def on_width_change(self, *args):
		settings.set_option('music/' + self.name + '_width', self.get_width())


