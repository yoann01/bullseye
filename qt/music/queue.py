# -*- coding: utf-8 -*-
from PySide import QtGui, QtCore
from PySide.QtCore import Qt
import threading, os
import time
import gettext
import logging
from operator import attrgetter


from common import settings, util, xdg

from data.elements import QueuedTrack, Track, BDD

from qt.gui.modales import TagsEditor
#from gui.menus import TrackMenu
from qt.util.stardelegate.starrating import StarRating
from qt.util.stardelegate.stardelegate import StarDelegate
from qt.util import icons

IM = icons.IconManager()

logger = logging.getLogger(__name__)

class QueueManager(QtGui.QWidget):
	"""
        Cet objet correspond au gestionnaire de pistes à jouer, graphiquement c'est un NoteBook (onglets, etc...)
        TODO ponts (A -> B, B-> C), filtres
        TODO bouton stop = set stop track
        TODO open external track files (mime + isLoaded(musicSection)) + handle drop event for that
        """
	def __init__(self, playerWidget):
		QtGui.QWidget.__init__(self)
		
		self.tabWidget = QtGui.QTabWidget()
		actionBox = QtGui.QHBoxLayout()
		scrollToCurrentButton = QtGui.QPushButton(QtGui.QIcon.fromTheme('go-jump'), None)
		scrollToCurrentButton.clicked.connect(self.scrollToCurrent)
		searchEntry = QtGui.QLineEdit()
		searchEntry.textChanged.connect(self.filter)
		actionBox.addWidget(scrollToCurrentButton, 0)
		actionBox.addWidget(searchEntry, 1)
		
		layout = QtGui.QVBoxLayout()
		layout.addWidget(self.tabWidget, 1)
		layout.addLayout(actionBox, 0)
		self.setLayout(layout)
		
		# *** Visual features ***
		self.tabWidget.setTabsClosable(True)
		self.tabWidget.tabCloseRequested.connect(self.removeQueue)
		addTabButton = QtGui.QPushButton(QtGui.QIcon.fromTheme('list-add'), None)
		addTabButton.setFlat(True)
		addTabButton.released.connect(self.addQueue)
		self.tabWidget.setCornerWidget(addTabButton)
		
		# *** Data attributes
		self.playerWidget = playerWidget
		self.playerWidget.queueManager = self
		
	
		
		# On ajoute une liste pour commencer
		self.loadState()
		
		QtGui.QShortcut(QtGui.QKeySequence(self.tr("Ctrl+T", "File|New")), self, self.addQueue)
		QtGui.QShortcut(QtGui.QKeySequence(self.tr("Ctrl+W", "File|Close")), self, self.removeQueue)
	
	


	@property
	def visibleQueue(self):
		try:
			q = self.tabWidget.currentWidget()
		except:
			q = None

		return q
		
	def addSelection(self, tracks, queue=None):
		if(queue == None):
			queue = self.visibleQueue
		queue.addTracks(tracks)
		

		
		
	def addPlaylist(self, label, IDList):
		bdd = BDD()
		playlist = self.addQueue(label)
		self.addSelection(bdd.getTracksFromIDs(IDList), playlist)
		playlist.watchForChange()
		
		
	def addQueue(self, label=None):
		nb_pages = self.tabWidget.count()
		if(label != None):
			#Cela veut dire qu'on a reçu une playlist du messager
			newQueue = Playlist(self, label)
		else:
			label = _("Queue ") + str(nb_pages)
			newQueue = Queue(self, label)
		
		self.tabWidget.addTab(newQueue, label)
		self.tabWidget.setCurrentIndex(nb_pages)
		return newQueue
			


	
	def removeQueue(self, i=-1):
		if i == -1: # triggered by shortcut
			i = self.currentIndex()
		if(self.tabWidget.widget(i).modified == True):
			if QtGui.QMessageBox.question (self, _("Closing non-saved playlist"), _("Save changes?"), QtGui.QMessageBox.Yes | QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
				self.tabWidget.widget(i).save()
		self.tabWidget.removeTab(i)
		if(self.tabWidget.count() == 0):
			self.addQueue()
	

	
	def filter(self, text):
		proxyModel = self.visibleQueue.filterModel
		proxyModel.setFilterRegExp(QtCore.QRegExp(text, QtCore.Qt.CaseInsensitive, QtCore.QRegExp.FixedString))
		proxyModel.setFilterKeyColumn(-1)
		print text
	
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
		
		
	
	def loadState(self):
		@util.threaded
		def addTracks(IDs, queue):
			bdd = BDD()
			self.addSelection(bdd.getTracksFromIDs(IDs), queue)
			

		queues = settings.get_option('session/queues', None)
		if(queues is not None):
			for key in queues.iterkeys():
				if type(key).__name__== 'int':
					addTracks(queues[key], self.addQueue())
				else:
					self.addPlaylist(key, queues[key])
		else:
			self.addQueue()
		

		
	def saveState(self):
		i = 0
		queues = {}
		while( i < self.tabWidget.count()):
			t = []
			queue =  self.tabWidget.widget(i)

			for track in queue.model.tracks:
				t.append(track.ID)

			if(type(queue).__name__ == 'Playlist'):
				queues[queue.label] = t
			else:
				queues[i] = t
			i += 1
		settings.set_option('session/queues', queues)
		
		
	def scrollToCurrent(self):
		currentQueue, currentTrack = self.playerWidget.getCurrents()
		index = currentQueue.model.tracks.index(currentTrack)
		self.tabWidget.setCurrentWidget(currentQueue)
		currentQueue.scrollTo(currentQueue.model.index(index, 0))
			


class Queue(QtGui.QTableView):
	'''
		Représente une queue (onglet) d'un gestionnaire de queue.
	'''
	def __init__(self, manager, label):
		QtGui.QTableView.__init__(self)
		
		self.starDelegate = StarDelegate() # Trick to prevent garbage collector issue
		#self.setItemDelegate(self.delegate) # The right way, but style option doesn't get initialized correctly causing no alternate colors for rows
		self.setItemDelegateForColumn(6, self.starDelegate)
		
		self.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked | QtGui.QAbstractItemView.SelectedClicked)
		# Visual tweaks
		self.setAlternatingRowColors(True)
		
		
		
		#self.setStyleSheet("{ border: none;}")
		self.setShowGrid(False)
		self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.verticalHeader().hide()
		self.setSortingEnabled(True)
		self.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
		self.setDragEnabled(True)
		self.setAcceptDrops(True)
		
		
		
		
		# *** Data attributes ***
		self.modified = False # pour les playlists enregistrées
		self.manager = manager
		
		#police, icon_playing, icon_stopping, ID, path, titre, album, artiste, length, count, pixbuf_note, note, bridge_src key
		self.model = QueueModel()
		filterModel = QtGui.QSortFilterProxyModel()
		filterModel.setSourceModel(self.model)
		self.filterModel = filterModel
		self.setModel(self.filterModel)
		
		
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
		#self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
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
		self.model.rowsMoved.connect(self.onReorder)
			
	def addTracks(self, tracks):
		self.model.append(tracks)
		
	def columnMoved(self, logicalIndex, oldVisualIndex, newVisualIndex):
		header = self.horizontalHeader()
		for i in range(header.count()):
			self.columnsPos[i] = header.visualIndex(i)
			
		settings.set_option('music/columns_order', self.columnsPos)
	
	
	def contextMenuEvent(self, event):
		track = self.getTrackAt(self.rowAt(event.y()))
		jumpListSize = str(len(self.manager.playerWidget.jumpList))
		self.popMenu = QtGui.QMenu( self )
		removeAction = self.popMenu.addAction(QtGui.QIcon.fromTheme('list-remove'), _('Remove from queue'))
		stopAction = self.popMenu.addAction(QtGui.QIcon.fromTheme('media-playback-stop'), _('Set stop cursor'))
		permAction = self.popMenu.addAction(QtGui.QIcon(icons.pixmapFromText(jumpListSize, (18, 18))), _('Add to perm jump list'))
		tempAction = self.popMenu.addAction(QtGui.QIcon(icons.pixmapFromText(jumpListSize, (18, 18), '#FFCC00', '#000', '#000')), _('Add to temp jump list'))
		self.popMenu.addSeparator()
		self.popMenu.addAction(u'José Long')
		tagsEdit = self.popMenu.addAction(QtGui.QIcon.fromTheme('list-edit'), _('Edit tags'))
		#self.popMenu.setStyleSheet(" QMenu {    icon-size: 128px; } " )
		
		# --- BRIDGES SOURCES ---
		dic = self.manager.playerWidget.bridgesSrc
		if(track.bridgeSrc != None):
			def remove_bridge_src(*args):
				dic.pop(track.bridgeSrc)
				track.bridgeSrc = None
				self.refreshView(track)
				
			self.popMenu.addAction(QtGui.QIcon(icons.pixmapFromText(track.bridgeSrc, (18, 18), '#FF0000')), _("Unset bridge source"), remove_bridge_src)
		else:
			def add_bridge_src(*args):
				self.manager.playerWidget.bridgesSrc[letter] = track
				track.bridgeSrc = letter
				self.refreshView(track)
			
			letter = chr(65 + len(dic))
			#bridgeSrcAction = self.popMenu.addAction(QtGui.QIcon(icons.pixmapFromText(letter + ' →', (24, 18), '#58FA58', '#000', '#000')), _("Add bridge source"), add_bridge_src)
			bridgeSrcAction = self.popMenu.addAction(QtGui.QIcon(icons.pixmapFromText(letter, (18, 18), '#58FA58', '#000', '#000')), _("Add bridge source"), add_bridge_src)
		
		
		
		# --- BRIDGES DESTINATIONS --- 
		dicDest = self.manager.playerWidget.bridgesDest
		
		if(track.bridgeDest != None):
			def remove_bridge_dest(*args):
				self.manager.playerWidget.bridgesDest.pop(track.bridgeDest)
				track.bridgeDest = None
				self.refreshView(track)
				
			self.popMenu.addAction(QtGui.QIcon(icons.pixmapFromText(track.bridgeDest, (18, 18), '#FF0000')), _("Unset bridge dest"), remove_bridge_dest)

		else:
			def add_bridge_dest(*args):
				self.manager.playerWidget.bridgesDest[letterDest] = track
				track.bridgeDest = letterDest
				self.refreshView(track)
			
			letterDest = chr(65 + len(dicDest))
			#self.popMenu.addAction(QtGui.QIcon(icons.pixmapFromText('← ' + letterDest, (24, 18), '#CC2EFA')), _("Add bridge dest"), add_bridge_dest)
			self.popMenu.addAction(QtGui.QIcon(icons.pixmapFromText(letterDest, (18, 18), '#CC2EFA')), _("Add bridge dest"), add_bridge_dest)
			
			
		action = self.popMenu.exec_(self.mapToGlobal(event.pos()))
		if action == removeAction:
			self.model.removeTrack(track)
		elif action == stopAction:
			self.toggleStopFlag(track)
		elif action == permAction:
			self.manager.playerWidget.addToJumpList(self, track, False)
		elif action == tempAction:
			self.manager.playerWidget.addToJumpList(self, track, True)
		elif action == tagsEdit:
			d = TagsEditor(track.ID)
			d.exec_()
			
	def dragEnterEvent(self, e):
		data = e.mimeData()
		print data.formats()
		if data.hasFormat('bullseye/library.items') or data.hasFormat('bullseye/queue.items'):
			e.accept()
			#e.acceptProposedAction()
		elif data.hasUrls():
			e.accept()
	
		
		print data.data('bullseye/library.items')
		#e.accept()
	
	def dragMoveEvent(self, e):
		QtGui.QTableView.dragMoveEvent(self, e)
		e.accept()
		#e.acceptProposedAction()
		# Must reimplement this otherwise the drag event is not spread
		# But at this point the event has already been checked by dragEnterEvent
		
	def rowMoved(self, row, oldIndex, newIndex):
		QtGui.QTableView.rowMoved(self, row, oldIndex, newIndex)
		
	def dropEvent(self, e):
		print "DROP EVENT"
		data = e.mimeData()
		print data.formats()
		
		
		if data.hasFormat('bullseye/library.items'):
			dic = eval(str(data.data('bullseye/library.items')))
			bdd = BDD()
			tracks = bdd.getTracks(dic)
			self.model.insert(tracks, self.rowAt(e.pos().y()))
		elif(data.hasFormat('bullseye/queue.items')):
			indexes = self.selectedIndexes()
			print indexes
			movedTracks = []
			if len(indexes) > 0:
				targetedTrack = self.getTrackAt(self.rowAt(e.pos().y()))
				print targetedTrack
				first = indexes[0]
				last = indexes[-1]
				
				row = -1
				for index in indexes:
					if(index.row() != row):
						track = self.getTrackAt(index)
						if(targetedTrack == track):
							return
						movedTracks.append(track)
						self.model.removeTrack(track)
						row = index.row()
				
				self.model.insertAfter(movedTracks, targetedTrack)
			QtGui.QTableView.dropEvent(self, e)
			
		elif data.hasUrls():
			tracks = []
			for url in data.urls():
				path = url.toLocalFile()
				track = Track.fromPath(path)
				
				if track is not None:
					tracks.append(track)
			self.model.insert(tracks, self.rowAt(e.pos().y()))
		
	
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
				self.set_stop_track(liste.get_iter(path))
		
	#def fermeture(self, widget):
		#numero_page = widget.get_parent().get_parent().get_parent().page_num(self.TreeView)
		#self.NB.remove_page(numero_page)
		##si aucun onglet, en créer un
		#if(self.NB.get_n_pages() == 0):
			#self.NB.addQueue()

	def getNextTrack(self, tr):
		return self.model.getNextTrack(tr)
		
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
				self.manager.playerWidget.addToJumpList(self, track, False)
			else:
				self.manager.playerWidget.addToJumpList(self, track, True)
				
	
	def onActivated(self, i):
		self.manager.playerWidget.cleanPlayFlag()
		self.manager.playerWidget.playTrack(self.getTrackAt(i), self)
	
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
				i.connect('activate', self.on_stop_track_button_click, self.Liste, False)
				m.append(i)
				m.show_all()
				m.popup(None, None, None, event.button, event.time)
			elif(event.button == 2):
				self.manager.fermer_onglet(None, self)
			else:
				return False
			
			
	def on_stop_track_button_click(self, button, queue, ligne):
		#Ajoute ou enlève un marqueur sur la piste séléctionnée
		self.set_stop_track(ligne)
		
	def onReorder(self, sourceParent, sourceStart, sourceEnd, destinationParent, destinationRow):
		print('ok')
	
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
		
	def save(self):
		f = open(os.path.join(xdg.get_data_home(), 'playlists') + os.sep + self.label, 'w')
		for track in self.model.tracks:
			f.write(str(track.ID) + "\n")
		f.close()
		
	
	def toggleStopFlag(self, track):
		flags = track.flags
		if 'stop' in flags:
			flags.remove('stop')
		else:
			flags.add('stop')

	



class Playlist(Queue):
	def __init__(self, manager, label):
		Queue.__init__(self, manager, label)
		self.label = label
		

	def setModified(self, *args):
		if(self.modified == False):
			self.modified = True
			#self.tab_label.set_text('*' + self.tab_label.get_text())
			
	def watchForChange(self):
		self.model.rowsInserted.connect(self.setModified)
		self.model.rowsRemoved.connect(self.setModified)

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
		self.setSupportedDragActions(QtCore.Qt.MoveAction)
		self.tracks = []
		self.columnsFields = {1:'title', 6:'album', 7:'artist', 9:'playcount', 11:'rating'}

	def append(self, data):
		self.insert(data, len(self.tracks))
		
	def insert(self, data, pos):
		if type(data).__name__=='list':
			self.beginInsertRows(QtCore.QModelIndex(), pos, pos + len(data)-1)
			if(pos == len(self.tracks)):
				self.tracks.extend(data)
			else:
				for track in data:
					self.tracks.insert(pos, track)
		else:
			self.beginInsertRows(QtCore.QModelIndex(), pos, pos +1)
			self.tracks.insert(data, pos)
			
		self.endInsertRows()
		#self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
		
	def insertAfter(self, data, track):
		if(track != None):
			self.insert(data, self.tracks.index(track) +1)
		else:
			self.append(data)
		
	def rowCount(self, parent):
		return len(self.tracks)

	def columnCount(self, parent):
		return 7
		return len(self.tracks[0])

	def data(self, index, role):
		if not index.isValid():
			return None
		track = self.tracks[index.row()]
		if role == Qt.DisplayRole:
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
				return icons.pixmapFromText(str(self.tracks[index.row()].priority), (18, 18))
			elif 'tempjump' in self.tracks[index.row()].flags:
				return icons.pixmapFromText(str(self.tracks[index.row()].priority), (18, 18), '#FFCC00', '#000', '#000')
			elif track.bridgeSrc != None:
				if(track.bridgeDest != None):
					return icons.pixmapFromText(u'← ' + track.bridgeDest + ' - ' + track.bridgeSrc + u' →', (64, 18), ('#58FA58', '#CC2EFA'), '#000', '#000')
				else:
					return icons.pixmapFromText(track.bridgeSrc + u' →', (32, 18), '#58FA58', '#000', '#000')
			elif track.bridgeDest != None:
				return icons.pixmapFromText(u'← ' + track.bridgeDest, (32, 18), '#CC2EFA')
			elif 'stop' in self.tracks[index.row()].flags:
				return QtGui.QIcon.fromTheme('media-playback-stop')
		return None
	
	def flags(self, index):
		if(index.column() == 6):
			return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled
		else:
			return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled
			
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

	def mimeTypes(self):
		return ('bullseye/queue.items',)
	
	def refreshView(self, track):
		index = self.createIndex(self.tracks.index(track), 0)
		self.dataChanged.emit(index, index)
		
	def removeTrack(self, track):
		index = self.createIndex(self.tracks.index(track), 0)
		self.beginRemoveRows(index, 0, 1)
		self.tracks.remove(track)
		self.endRemoveRows()
		
	def remove(self, indexes):
		self.beginRemoveRows(indexes[0], 0, len(indexes))
		#self.tracks.
	
	def setData(self, index, value, role=QtCore.Qt.EditRole):
		if(index.column() == 6):
			self.tracks[index.row()].rating = value
		return True
		print 'TODO';
		
	def sort(self, columnIndex, order):
		self.layoutAboutToBeChanged.emit()
		if(order == Qt.AscendingOrder):
			reverse = False
		else:
			reverse = True
		self.tracks = sorted(self.tracks, key=attrgetter(self.columnsFields[columnIndex]), reverse=reverse)
		self.layoutChanged.emit()
		
	def supportedDropActions(self):
		return Qt.CopyAction | Qt.MoveAction

