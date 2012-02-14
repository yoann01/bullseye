# -*- coding: utf-8 -*-
from PySide import QtGui, QtCore
from PySide.QtCore import Qt
import threading
import time
import gobject
import gettext
import logging


from common import messager, settings

from data.elements import QueuedTrack, BDD

import gui.modales
from gui.menus import TrackMenu
from qt.util.stardelegate.starrating import StarRating
from qt.util.stardelegate.stardelegate import StarDelegate
from qt.util import icons

IM = icons.IconManager()

logger = logging.getLogger(__name__)

class QueueManager(QtGui.QTabWidget):
	"""
        Cet objet correspond au gestionnaire de pistes à jouer, graphiquement c'est un NoteBook (onglets, etc...)
        TODO ponts (A -> B, B-> C), filtres
        TODO bouton stop = set stop track
        """
	def __init__(self, playerWidget):
		QtGui.QTabWidget.__init__(self)
		
		# *** Visual features ***
		self.setTabsClosable(True)
		self.tabCloseRequested.connect(self.removeQueue)
		addTabButton = QtGui.QPushButton('+')
		addTabButton.setFlat(True)
		addTabButton.released.connect(self.addQueue)
		self.setCornerWidget(addTabButton)
		
		# *** Data attributes
		self.playerWidget = playerWidget
		self.playerWidget.queueManager = self
		self.directList = [] #Liste de pistes à jouer en priorité
		self.bridges_src = {}
		self.bridges_dest = {}
		
		self.queue_jouee = None
		self.playing_iter = None
		self.dest_row = None
		
		q = Queue(self, 'Q0')
		q.model.append(QueuedTrack(1, q))
		q.model.append(QueuedTrack(2, q))
		q.model.append(QueuedTrack(3, q))
		self.addTab(q, 'Queue0')
		# On ajoute une liste pour commencer
		
		QtGui.QShortcut(QtGui.QKeySequence(self.tr("Ctrl+T", "File|New")), self, self.addQueue)
		QtGui.QShortcut(QtGui.QKeySequence(self.tr("Ctrl+W", "File|Close")), self, self.removeQueue)
		

	def getAddTabButtonPos(self):
		try:
			last_tab_label = self.get_tab_label(self.get_nth_page(self.get_n_pages() -1))
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
			q = self.currentWidget()
		except:
			q = None

		return q
		
	def addSelection(self, tracks):
		self.visibleQueue.addTracks(tracks)
		
		
	def addToDirectList(self, menuitem, row, temp=False):
		'''
		@param menuitem : osef
		@param row : TreeReference
		@param temp : if temp is true then after jumping return where player was before
		'''
		i = 0
		while((i < len(self.directList)) and not self.directList[i].equals(row)):
			i+=1

		if(i < len(self.directList) and self.directList[i].equals(row)):
			self.directList.insert(i, DirectIter(None, temp))
			i+=1
		else:
			self.directList.append(DirectIter(row, temp))
		if temp is True:
			image = icons.MANAGER.pixbuf_from_text(str(i+1), (18, 18), '#FFCC00', '#000', '#000')
		else:
			image = icons.MANAGER.pixbuf_from_text(str(i+1), (18, 18))
		row.get_model()[row.get_path()][1] = image


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
		nb_pages = self.count()
		if(label != None):
			#Cela veut dire qu'on a reçu une playlist du messager
			newQueue = Playlist(self, label)
		else:
			label = _("Queue ") + str(nb_pages)
			newQueue = Queue(self, label)
		
		self.addTab(newQueue, label)
		self.setCurrentIndex(nb_pages)
		return newQueue
		
		
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

	def demarquer_piste(self, forward=False):
		try:
			self.temp_queue_jouee.set_value(self.temp_playing_iter, 1, None)
			self.temp_queue_jouee.set_value(self.temp_playing_iter, 0, None)
			self.temp_queue_jouee = None
			self.temp_playing_iter = None
		except:
			logger.debug('No temporary jump track to unmark')
		try:
			print(self.queue_jouee.get_value(self.playing_iter, 5))
			self.queue_jouee.set_value(self.playing_iter, 1, None)
			self.queue_jouee.set_value(self.playing_iter, 0, None)
		except:
			logger.debug('No standard track to unmark')
		#if(forward):
				#if(self.numero + 1 < len(self.queue_jouee)):
					#self.numero +=1

	
	def removeQueue(self, i=-1):
		if i == -1: # triggered by shortcut
			i = self.currentIndex()
		if(self.widget(i).modified == True):
			print "TODO"
		self.removeTab(i)
		if(self.count() == 0):
			self.addQueue()
		
	def fermer_onglet(self, bouton=None, onglet=None):
		if(bouton == None):
			#La demande provient d'un raccourci clavier
			numero_page = self.get_current_page()
		else:
			numero_page = self.page_num(onglet)
		if(self.get_nth_page(numero_page).modified == True):
			dialog = gtk.Dialog(title=_("Closing non-saved playlist"), buttons=(gtk.STOCK_NO, gtk.RESPONSE_REJECT,
                      gtk.STOCK_YES, gtk.RESPONSE_ACCEPT))
			box = dialog.get_content_area()
			box.pack_start(gtk.Label(_("Save changes?")), False, 5, 5)
			box.show_all()
			reponse = dialog.run()
			dialog.destroy()
			if(reponse == -3): #Valider
				self.get_nth_page(numero_page).save()
		self.remove_page(numero_page)
		#Il n'y a plus d'onglet, on en crée un
		if(self.get_n_pages() == 0):
			self.addQueue()
			
	
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
		
	def getDefaultTrack(self):
		return self.visibleQueue.getTrackAt(0)
		
	def incrementPlayedTrack(self):
		messager.diffuser('incrementation', self, self.playing_track)
		try:
			compteur = self.temp_queue_jouee.get_value(self.temp_playing_iter, 9)
			self.temp_queue_jouee.set_value(self.temp_playing_iter, 9, compteur)
		except:
			compteur = self.queue_jouee.get_value(self.playing_iter, 9) + 1
			self.queue_jouee.set_value(self.playing_iter, 9, compteur)
		
	def initialisation_raccourcis(self):
		raccourcis = (
			('<Control>W', lambda *e: self.fermer_onglet()),
			('<Control>T', lambda *e: self.addQueue()),
		)
		accel_group = gtk.AccelGroup()
		for key, function in raccourcis:
			key, mod = gtk.accelerator_parse(key)
			accel_group.connect_group(key, mod, gtk.ACCEL_VISIBLE,
				function)
		messager.diffuser('desRaccourcis', self, accel_group)
		

        
        def load_state(self):
		def traiter_queues():
			bdd = BDD()
			queues = settings.get_option('session/queues', None)
			if(queues is not None):
				for key in queues.iterkeys():
					if type(key).__name__=='int':
						self.addQueue()
						for track_id in queues[key]:
							self.ajouter_selection(bdd.get_tracks_data({'track_ID':track_id}))
					else:
						playlist = self.addQueue(key)
						for track_id in queues[key]:
							self.ajouter_selection(bdd.get_tracks_data({'track_ID':track_id}))
						playlist.Liste.connect("row-changed", playlist.setModified)
			else:
				self.addQueue()
		a = threading.Thread(target=traiter_queues)
		a.start()
		
		
	def marquer_piste(self):#Ajoute un marqueur (pour la piste courante de la liste jouée)
		icon = gtk.gdk.pixbuf_new_from_file('icons/track.png')
		try:
			self.temp_queue_jouee.set_value(self.temp_playing_iter, 1, icon)
			self.temp_queue_jouee.set_value(self.temp_playing_iter, 0, 'bold')
		except:
			self.queue_jouee.set_value(self.playing_iter, 1, icon)
			self.queue_jouee.set_value(self.playing_iter, 0, 'bold')
		
		
	def on_zik_click(self, TreeView, i , c):
		#W = TV_zik, c = colonne, i = numero de ligne
		
		#On vire le marquage de piste en cours si il y en a un
		self.demarquer_piste()
		self.numero = i[0]
		self.queue_jouee = TreeView.get_model()
		self.playing_iter = self.queue_jouee.get_iter(i)
		#chemin = self.queue_jouee[i][4]
		self.playing_track = Track(self.queue_jouee[i][3])
		messager.diffuser('musique_a_lire', self, self.playing_track)
		self.marquer_piste()
		
		
	def on_tab_change(self, notebook, page, page_num):
			#Je rechoppe la page car ici elle est de type GPointer, non exploitable en PyGtk
			page = notebook.get_nth_page(page_num) # La page = le contenu = une liste de lecture = un TreeView
			if self.queue_jouee == None:
				self.queue_jouee = page.Liste
				self.numero = 0
		
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
		while( i < self.get_n_pages()):
			t = []
			queue =  self.get_nth_page(i)
			model = queue.Liste
			iter = model.get_iter_first()
			while(iter is not None):
				t.append(model.get_value(iter, 3))
				iter = model.iter_next(iter)
			if(type(queue).__name__=='Playlist'):
				queues[self.get_nth_page(i).tab_label.get_text()] = t
			else:
				queues[i] = t
			i += 1
		settings.set_option('session/queues', queues)
			


class Queue(QtGui.QTableView):
	'''
		Représente une queue (onglet) d'un gestionnaire de queue.
	'''
	def __init__(self, gestionnaire, label):
		QtGui.QTableView.__init__(self)
		
		self.setItemDelegate(StarDelegate())
		#self.setItemDelegateForColumn(3, StarDelegate())
		
		self.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked | QtGui.QAbstractItemView.SelectedClicked)
		# Visual tweaks
		self.setAlternatingRowColors(True);
		
		
		
		#self.setStyleSheet("{ border: none;}")
		self.setShowGrid(False)
		self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.verticalHeader().hide()
		self.setSortingEnabled(True)
		
		
		
		# *** Data attributes ***
		self.modified = False #pour les playlists enregistrées
		self.gestionnaire = gestionnaire
		
		#police, icon_playing, icon_stopping, ID, path, titre, album, artiste, length, count, pixbuf_note, note, bridge_src key
		self.model = QueueModel()
		self.setModel(self.model)
		
		header = self.horizontalHeader()
		
		# Give the visual index for each logical index
		self.columnsPos = settings.get_option('music/columns_order', [0, 1, 2, 3, 4, 5, 6])
		logical = 0
		while logical < 7:
			current = header.visualIndex(logical)
			if current != self.columnsPos[logical]:
				header.moveSection(current, self.columnsPos[logical])
				self.columnsPos[logical] = current
			logical += 1
		#self.setContextMenuPolicy(Qt.CustomContextMenu)
		#self.customContextMenuRequested.connect(self.showContextMenu)
		
		# Column tweaks - need to be done after model is setted
		self.setColumnWidth(1, settings.get_option('music/col_artist_width', 50))
		self.setColumnWidth(2, settings.get_option('music/col_album_width', 50))
		
		header = self.horizontalHeader()
		header.setMovable(True)
		header.sectionMoved.connect(self.columnMoved)
		#header.setStretchLastSection(True)
		#self.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
		header.setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
		header.setResizeMode(1, QtGui.QHeaderView.Stretch)
		header.setResizeMode(6, QtGui.QHeaderView.Fixed)
		
		self.activated.connect(self.onActivated)
		
	
		
	def onActivated(self, i):
		self.gestionnaire.playerWidget.playTrack(self.getTrackAt(i), self)
		
	def addTracks(self, tracks):
		self.model.append(tracks)
		
	def columnMoved(self, logicalIndex, oldVisualIndex, newVisualIndex):
		header = self.horizontalHeader()
		for i in range(header.count()):
			self.columnsPos[i] = header.visualIndex(i)
			
		settings.set_option('music/columns_order', self.columnsPos)
	
	
	def contextMenuEvent(self, event):
		track = self.getTrackAt(self.rowAt(event.y()))
		jumpListSize = str(len(self.gestionnaire.playerWidget.jumpList))
		self.popMenu = QtGui.QMenu( self )
		removeAction = self.popMenu.addAction(QtGui.QIcon.fromTheme('list-remove'), _('Remove from queue'))
		stopAction = self.popMenu.addAction(QtGui.QIcon.fromTheme('media-playback-stop'), _('Set stop cursor'))
		permAction = self.popMenu.addAction(QtGui.QIcon(icons.pixmapFromText(jumpListSize, (18, 18))), _('Add to perm jump list'))
		tempAction = self.popMenu.addAction(QtGui.QIcon(icons.pixmapFromText(jumpListSize, (18, 18), '#FFCC00', '#000', '#000')), _('Add to temp jump list'))
		self.popMenu.addSeparator()
		self.popMenu.addAction('José Long')
		action = self.popMenu.exec_(self.mapToGlobal(event.pos()))
		if action == removeAction:
			self.model.removeTrack(track)
		elif action == stopAction:
			self.toggleStopFlag(track)
		elif action == permAction:
			self.gestionnaire.playerWidget.addToJumpList(self, track, False)
		elif action == tempAction:
			self.gestionnaire.playerWidget.addToJumpList(self, track, True)
			
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
			self.gestionnaire.cleanDirectList()
				
		elif(event.keyval == gtk.gdk.keyval_from_name("s")):
			selection = self.TreeView.get_selection()
			liste, paths = selection.get_selected_rows()
			for path in paths:
				self.set_stop_track(liste.get_iter(path))
		
	#def fermeture(self, widget):
		#numero_page = widget.get_parent().get_parent().get_parent().page_num(self.TreeView)
		#self.NB.remove_page(numero_page)
		##si aucun onglet, en créer un
		#if(self.NB.get_n_pages() == 0):
			#self.NB.addQueue()
		
	def getTrackAt(self, i):
		if type(i).__name__ == 'int':
			try:
				return self.model.tracks[i]
			except IndexError:
				return None
		else:
			return self.model.tracks[i.row()]
		
	def keyPressEvent(self, e):
		if e.key() == Qt.Key.Key_S:
			indexes = self.selectedIndexes()
			if len(indexes) > 0:
				first = indexes[0]
				last = indexes[-1]
				for index in indexes:
					self.toggleStopFlag(self.getTrackAt(index))
				self.model.dataChanged.emit(first, last)
		else:
			QtGui.QTableView.keyPressEvent(self, e)
	
	def mouseReleaseEvent(self, e):
		if e.button() == Qt.MidButton:
			track = self.getTrackAt(self.rowAt(e.y()))
			if Qt.ControlModifier and e.modifiers():
				self.gestionnaire.playerWidget.addToJumpList(self, track, False)
			else:
				self.gestionnaire.playerWidget.addToJumpList(self, track, True)
				
	
	def on_cell_rating_changed(self, widget, path, rating):
		#self.Liste[path][10] = IM.pixbuf_from_rating(rating)
		Track(self.Liste[path][3]).change_rating(widget, rating)
		#messager.diffuser('modification_note', self, ["track", self.Liste[path][3], rating])
	
	def on_column_clicked(self, column):
		def disable_sorting_state():
			time.sleep(2.0)
			self.Liste.set_sort_column_id(-2, 0)
			
		a = threading.Thread(target=disable_sorting_state)
		a.start()
		
	
	def on_drag_data_received(self, TV, drag_context, x, y, selection_data, info, timestamp):
		if(selection_data.get_target() == 'text/plain'):
			#fin d'un DND
			self.gestionnaire.dest_row = self.TreeView.get_dest_row_at_pos(x, y)
			
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
				i.connect('activate', self.on_stop_track_button_click, self.Liste, False)
				m.append(i)
				m.show_all()
				m.popup(None, None, None, event.button, event.time)
			elif(event.button == 2):
				self.gestionnaire.fermer_onglet(None, self)
			else:
				return False
			
			
	def on_stop_track_button_click(self, button, queue, ligne):
		#Ajoute ou enlève un marqueur sur la piste séléctionnée
		self.set_stop_track(ligne)
	
	def refreshView(self, track):
		self.model.refreshView(track)
		
	def refresh_view(self, track):
		"""
			A track data has just changed. Checks if we have this track and update accordingly
			#model order :police, icon_playing, icon_stopping, ID, path, titre, album, artiste, length, count, pixbuf_note, note
		"""
		iter = self.Liste.get_iter_first()
		while(iter is not None):
			if(self.Liste.get_value(iter, 3) == int(track.ID)):
				self.Liste.set(iter, 4, track.path, 5, track.tags['title'], 6, track.tags['album'], 7, track.tags['artist'], 10, IM.pixbuf_from_rating(track.rating))
			iter = self.Liste.iter_next(iter)
		
	def save(self, name=None):
		if(name == None):
			name = self.tab_label.get_text()[1:]
		fichier = open('playlists/' + name,'w')
		for piste in self.Liste:
			print(piste[3])
			fichier.write(str(piste[3]) + "\n")
		fichier.close()
		
	
	def toggleStopFlag(self, track):
		flags = track.flags
		if 'stop' in flags:
			flags.remove('stop')
		else:
			flags.add('stop')
		
	def set_stop_track(self, ligne):
		icon = gtk.ToolButton()
		icon = icon.render_icon(gtk.STOCK_MEDIA_STOP, gtk.ICON_SIZE_BUTTON, detail=None)
		if(ligne != False):
			if(self.Liste.get_value(ligne, 2) is None):
				
				self.Liste.set_value(ligne, 2, icon)
				self.Liste.set_value(ligne, 0, 'italic')
			else:
				self.Liste.set_value(ligne, 2, None)
				self.Liste.set_value(ligne, 0, 'normal')
		else:
			for i in xrange(len(self.Liste)):
				ligne = self.Liste.get_iter(i)
				self.Liste.set_value(ligne, 2, icon)
				self.Liste.set_value(ligne, 0, 'italic')
					
	
	def surClicDroit(self, TreeView, event):
		print event
		# On vérifie que c'est bien un clic droit:
		if event.button == 3:
			path = TreeView.get_path_at_pos(int(event.x),int(event.y))[0]
			if(path != None):
				queue = TreeView.get_model()
				piste_ID = queue[path][3]
				ligne = queue.get_iter(path)
			if (path != None):
				iter = queue.get_iter(path)
				row = gtk.TreeRowReference(queue, path)
				m = TrackMenu(piste_ID)
				m.append(gtk.SeparatorMenuItem())
				i = gtk.ImageMenuItem(_("Remove from queue"))
				i.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_MENU))
				i.connect('activate', self.enlever_piste, ligne)
				m.append(i)
				
				i = gtk.ImageMenuItem(_("Set stop cursor"))
				i.set_image(gtk.image_new_from_stock(gtk.STOCK_MEDIA_STOP, gtk.ICON_SIZE_MENU))
				i.connect('activate', self.on_stop_track_button_click, queue, ligne)
				m.append(i)
				
				i = gtk.ImageMenuItem(_("Add to perm jump list"))
				i.set_image(gtk.image_new_from_pixbuf(icons.MANAGER.pixbuf_from_text(str(len(self.gestionnaire.directList)), (18, 18))))
				i.connect('activate', self.gestionnaire.addToDirectList, row)
				m.append(i)
				
				#image = icons.MANAGER.pixbuf_from_text(str(len(self.directList)), (18, 18), '#FFCC00', '#000', '#000')
				#image = icons.MANAGER.pixbuf_from_text(str(len(self.directList)), (18, 18))
				i = gtk.ImageMenuItem(_("Add to temp jump list"))
				i.set_image(gtk.image_new_from_pixbuf(icons.MANAGER.pixbuf_from_text(str(len(self.gestionnaire.directList)), (18, 18), '#FFCC00', '#000', '#000')))
				i.connect('activate', self.gestionnaire.addToDirectList, row, True)
				m.append(i)
				
				
				# *** BRIDGES ***
				j = 0
				done = False
				dic = self.gestionnaire.bridges_src
				
				while(not done and j < len(dic.keys())):
					
					ref = dic[dic.keys()[j]]

					if(ref.get_path() == path and ref.get_model() == self.Liste): 
						done = True
					else:
						j += 1
				if(done):
					def remove_bridge_src(*args):
						self.gestionnaire.bridges_src.pop(key)
						self.Liste[path][12] = None
						self.Liste[path][1] = None
					key = dic.keys()[j]
					i = gtk.ImageMenuItem(_("Unset bridge source"))
					i.set_image(gtk.image_new_from_pixbuf(icons.MANAGER.pixbuf_from_text(key, (18, 18), '#FF0000')))
					i.connect('activate', remove_bridge_src)
				else:
					def add_bridge_src(*args):
						self.gestionnaire.bridges_src[letter] = gtk.TreeRowReference(self.Liste, path)
						self.Liste[path][12] = letter
						self.Liste[path][1] = icons.MANAGER.pixbuf_from_text(letter + ' →', (24, 18), '#58FA58', '#000', '#000')
					
					letter = chr(65 + len(dic))
					icon = icons.MANAGER.pixbuf_from_text(letter + ' →', (24, 18), '#58FA58', '#000', '#000')
					i = gtk.ImageMenuItem(_("Add bridge source"))
					i.set_image(gtk.image_new_from_pixbuf(icon))
					i.connect('activate', add_bridge_src)
				m.append(i)
				
				j = 0
				done = False
				dic = self.gestionnaire.bridges_dest
				
				while(not done and j < len(dic.keys())):
					
					ref = dic[dic.keys()[j]]

					if(ref.get_path() == path and ref.get_model() == self.Liste): 
						done = True
					else:
						j += 1
				if(done):
					def remove_bridge_dest(*args):
						self.gestionnaire.bridges_dest.pop(key)
						self.Liste[path][1] = None
						
					key = dic.keys()[j]
					i = gtk.ImageMenuItem(_("Unset bridge dest"))
					i.set_image(gtk.image_new_from_pixbuf(icons.MANAGER.pixbuf_from_text(key, (18, 18), '#FF0000')))
					i.connect('activate', remove_bridge_dest)
				else:
					def add_bridge_dest(*args):
						self.gestionnaire.bridges_dest[letter] = gtk.TreeRowReference(self.Liste, path)
						self.Liste[path][1] = icon
					
					letter = chr(65 + len(dic))
					icon = icons.MANAGER.pixbuf_from_text('← ' + letter, (24, 18), '#CC2EFA')
					i = gtk.ImageMenuItem(_("Add bridge dest"))
					i.set_image(gtk.image_new_from_pixbuf(icon))
					i.connect('activate', add_bridge_dest)
					
				
					
				#if(iter in self.gestionnaire.bridges_src.values):

				#else:
					#i = gtk.ImageMenuItem(_("Add to temp jump list"))
					#i.set_image(gtk.image_new_from_pixbuf(icons.MANAGER.pixbuf_from_text('A'), (18, 18), '#FFCC00', '#000', '#000')))
					#i.connect('activate', self.gestionnaire.addToDirectList, queue, ligne, True)
				m.append(i)
				
				m.show_all()
				m.popup(None, None, None, event.button, event.time)
		elif event.button == 2:
			path = TreeView.get_path_at_pos(int(event.x),int(event.y))[0]
			if(path != None):
				queue = TreeView.get_model()
				row = gtk.TreeRowReference(queue, path)
				from gtk.gdk import CONTROL_MASK, SHIFT_MASK
				if event.state & CONTROL_MASK:
					self.gestionnaire.addToDirectList(None, row, False)
				else:
					self.gestionnaire.addToDirectList(None, row, True)


class Playlist(Queue):
	def __init__(self, gestionnaire, label):
		Queue.__init__(self, gestionnaire, label)
		
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


	
	
class QueueModel(QtCore.QAbstractTableModel):
	def __init__(self, parent=None, *args):
		QtCore.QAbstractTableModel.__init__(self, parent, *args)
		self.tracks = []

	def append(self, data):
		
		if type(data).__name__=='list':
			self.beginInsertRows(QtCore.QModelIndex(), 0, len(data))
			self.tracks.extend(data)
		else:
			self.beginInsertRows(QtCore.QModelIndex(), 0, 1)
			self.tracks.append(data)
			
		self.endInsertRows()
		#self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
		
	def rowCount(self, parent):
		return len(self.tracks)

	def columnCount(self, parent):
		return 7
		return len(self.tracks[0])

	def data(self, index, role):
		if not index.isValid():
			return None
		elif role == Qt.DisplayRole:
			if index.column() == 1:
				return self.tracks[index.row()].title
			elif index.column() == 2:
				return self.tracks[index.row()].album
			elif index.column() == 3:
				return self.tracks[index.row()].artist
			elif index.column() == 4:
				return self.tracks[index.row()].length
			elif index.column() == 5:
				return self.tracks[index.row()].playcount
			elif index.column() == 6:
				return self.tracks[index.row()].rating
		elif role == Qt.FontRole:
			if 'play' in self.tracks[index.row()].flags:
				font = QtGui.QFont()
				font.setBold(True)
				return font
		elif role == Qt.DecorationRole and index.column() == 0:
			if 'play' in self.tracks[index.row()].flags:
				return QtGui.QIcon.fromTheme('media-playback-start')
			elif 'permjump' in self.tracks[index.row()].flags:
				return QtGui.QIcon(icons.pixmapFromText(str(self.tracks[index.row()].priority), (18, 18)))
			elif 'tempjump' in self.tracks[index.row()].flags:
				return QtGui.QIcon(icons.pixmapFromText(str(self.tracks[index.row()].priority), (18, 18), '#FFCC00', '#000', '#000'))
			elif 'stop' in self.tracks[index.row()].flags:
				return QtGui.QIcon.fromTheme('media-playback-stop')
		return None
	
	def flags(self, index):
		if(index.column() == 6):
			return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable
		else:
			return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
			
	def getNextTrack(self, tr):
		try:
			return self.tracks[self.tracks.index(tr) + 1]
		except IndexError:
			return None
			
	def getPreviousTrack(self, tr):
		try:
			return self.tracks[self.tracks.index(tr) - 1]
		except IndexError:
			return None
		
	def headerData(self, section, orientation, role):
		if section == 0:
			return '#'
		elif section == 1:
			return _('Title')
		elif section == 2:
			return _('Album')
		elif section == 3:
			return _('Artist')
		elif section == 4:
			return _('Length')
		elif section == 5:
			return _('Playcount')
		#elif section == 6:
			#return _('Rating')
			
	
	def refreshView(self, track):
		index = self.createIndex(self.tracks.index(track), 0)
		self.dataChanged.emit(index, index)
		
	def removeTrack(self, track):
		index = self.createIndex(self.tracks.index(track), 0)
		self.beginRemoveRows(index, 0, 1)
		self.tracks.remove(track)
		self.endRemoveRows()
	
	def setData(self, index, value, role=QtCore.Qt.EditRole):
		if(index.column() == 6):
			self.tracks[index.row()].rating = value
		return True
		print 'TODO';

