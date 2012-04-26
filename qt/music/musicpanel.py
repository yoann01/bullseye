# -*- coding: utf-8 -*-
import os
from PySide import QtGui, QtCore
from PySide.QtCore import Qt

from PySide.QtCore import QModelIndex, QAbstractItemModel
from operator import attrgetter

from common import messager, settings, xdg
from qt.util import treemodel
from data.elements import Track
from qt.gui import menus, modales
import threading
import time

icon_track = QtGui.QPixmap('icons/track.png')
icon_artist = QtGui.QPixmap('icons/artist.png')
icon_album = QtGui.QPixmap('icons/star.png')
icon_genre = QtGui.QPixmap('icons/genre.png')
icon_year = QtGui.QPixmap('icons/year.png')
icon_rating = QtGui.QPixmap('icons/star.png')
icons = {"title":icon_track, "artist":icon_artist, "album":icon_album, "genre":icon_genre, "rating":icon_rating, "year":icon_year}
icon_size = settings.get_option('music/panel_icon_size', 32)

class BrowserPanel(QtGui.QTabWidget):
	def __init__(self, db, queueManager):
		QtGui.QTabWidget.__init__(self)
		self.addTab(LibraryPanel(db, queueManager), _('Library'))
		self.addTab(PlaylistBrowser(db, queueManager), _('Playlists'))
		self.resize(settings.get_option('music/paned_position', 200), 500)
		
class LibraryPanel(QtGui.QWidget):
	"""
		TODO check errors (arkenstone, little richard)
		TODO réimplémenter mousePressEvent pour avoir l'image lors du drag
	"""
	
	expandRequested = QtCore.Signal(list)
	
	def __init__(self, BDD, queueManager):
		QtGui.QWidget.__init__(self)
		self.BDD = BDD
		self.queueManager = queueManager
		self.tracks = {}
		self.mode = '("artist", "album", "title")'
		
		self.TreeView = QtGui.QTreeView()
		self.TreeView.setExpandsOnDoubleClick(False)
		self.TreeView.setSortingEnabled(True)
		self.TreeView.mouseReleaseEvent = self.mouseReleaseEvent
		
		self.model = LibraryModel()
		
		
		self.notLoading = threading.Event()
		self.notLoading.set()
		self.fill_model()
		
		#TreeNode(self.model, None, LibraryItem(None, 1, "ok", 1, 1, 1, 1, False))
		#self.model.append(LibraryItem(None, 1, "ok", 1, 1, 1, 1, False))
		self.TreeView.setModel(self.model)
		self.TreeView.activated.connect(self.enqueue)
		self.expandRequested.connect(self.expandIndexes)
		
		self.TreeView.setDragEnabled(True)
		self.TreeView.setAcceptDrops(True)
		self.TreeView.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
		
		# *** TreeView visual tweaks
		self.TreeView.setColumnWidth(1, settings.get_option('music/col_label_panel_width', 170))
		header = self.TreeView.header()
		header.setStretchLastSection(False)
		header.setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
		header.setResizeMode(1, QtGui.QHeaderView.Stretch)
		header.setResizeMode(2, QtGui.QHeaderView.ResizeToContents)
		header.setResizeMode(3, QtGui.QHeaderView.ResizeToContents)
		header.setResizeMode(4, QtGui.QHeaderView.ResizeToContents)
		self.TreeView.setAnimated(True)
		
		# --- Mode selector ---
		
		modesModel = QtGui.QStandardItemModel()
		modesModel.appendRow([QtGui.QStandardItem('("artist", "album", "title")'), QtGui.QStandardItem(_("Artist"))])
		modesModel.appendRow([QtGui.QStandardItem('("album", "title")'), QtGui.QStandardItem(_("Album"))])
		modesModel.appendRow([QtGui.QStandardItem('("rating", "title")'), QtGui.QStandardItem(_("Rating"))])
		modesModel.appendRow([QtGui.QStandardItem('("genre", "album", "title")'), QtGui.QStandardItem(_("Genre"))])
		modesModel.appendRow([QtGui.QStandardItem('("year", "artist", "album", "title")'), QtGui.QStandardItem(_("Year - Genre"))])
		modesModel.appendRow([QtGui.QStandardItem('("year", "genre", "artist", "album", "title")'), QtGui.QStandardItem(_("Year"))])
		modesModel.appendRow([QtGui.QStandardItem('("rating", "year", "genre", "artist", "album", "title")'), QtGui.QStandardItem(_("Rating - Year - Genre"))])


		self.modeCB = QtGui.QComboBox()
		self.modeCB.setModel(modesModel)
		self.modeCB.setModelColumn(1)
		self.modeCB.currentIndexChanged[int].connect(self.changeMode)
		
		
		refreshButton = QtGui.QPushButton(QtGui.QIcon.fromTheme('view-refresh'), _('Refresh'))
		refreshButton.clicked.connect(lambda: self.fill_model(None, True))
		modLayout = QtGui.QHBoxLayout()
		modLayout.addWidget(self.modeCB, 1)
		modLayout.addWidget(refreshButton)
		
		searchLine = QtGui.QLineEdit()
		searchLine.returnPressed.connect(lambda: self.searchFor(searchLine))
		
		layout = QtGui.QVBoxLayout()
		layout.addLayout(modLayout)
		layout.addWidget(self.TreeView)
		layout.addWidget(searchLine, 1)
		
		

		#self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding))
		self.setLayout(layout)
		
	def resizeEvent(self, event):
		settings.set_option('music/paned_position', event.size().width())
	
		
	def enqueue(self, i):
		dic = i.internalPointer().getFilter()
		
		self.queueManager.addSelection(self.BDD.getTracks(dic))
		
	#def enqueue(self, i): DEPRECATED
		#mode = eval(self.modeCB.model().item(self.modeCB.currentIndex(), 0).text()) #Ex : '("artist", "album")'
		
		#dic = {}
		#level = 0
		#params = []
		#while(i.isValid()): #On remonte la chaîne tant qu'on est pas arrivé à la racine
			#level += 1
			#params.append(i.internalPointer().label)
			#i = i.parent()
			
		#params.reverse()
		
		#i = 0
		#while(i < level):
			#dic[mode[i]] = params[i]
			#i += 1
		#self.queueManager.addSelection(self.BDD.getTracks(dic))
		
	def changeMode(self, i):
		model = self.modeCB.model()
		self.mode = model.data(model.index(i, 0))
		self.fill_model()
		
	def expandIndexes(self, indexes):
		for path in indexes:
			self.TreeView.setExpanded(path, True)
		
	
	def fill_model(self, garbageFromConnect=None, force_reload=False, mot='', e=None):
		'''
			Remplit la liste arborescente avec les pistes de la BDD selon l'arborescence du mode séléctionné
			
			@param data = [TreeStore, mode]
			@param e = threading event pour prévenir qu'on a fini
			TODO : ajouter le ratio d'écoutes par conteneur, qui s'applique uniquement sur les pistes notées
			ratio = total_ecoutes_conteneur / nb_pistes_notees_conteneur
		'''
		indices = {"title":2, "artist":4, "album":3, "genre":5, "rating":8, "year":9}
		
		global icon_size
		icon_size = settings.get_option('music/panel_icon_size', 32)
		
		
		def getValueOfLevel(track_line, level):
			'''
				@param track_line : la ligne de la piste dans le tableau self.tracks[mode]
				@level : le niveau de profondeur dans le mode d'affichage
					ex de mode ('artist, 'album', 'title') level 0 = artist, level 2 = title, etc...
			'''
			try:
				value = track_line[indices[mode[level]]]
			except IndexError:
				value = None
			return value
			
		def isSameContainer(track_line, niveau, cond):
			same = True
			for i in xrange(niveau+1):
				same = same and getValueOfLevel(track_line, i) == cond[i]

			return same
			
			
		def traiter_conteneur( niveau, ligne, selection, add_all=False, cond=[]):
			'''
				Cette méthode crée une selection des pistes intéressantes
				Pourquoi une séléction complète avant d'ajouter quoique ce soit? Parcequ'il faut d'abord vérifier les noeuds supérieurs avant d'ajouter un noeud inférieur.
				Cela impliquerait une suppresion de noeud inférieur sous condition, ce qui est très mal senti par le TreeView et son modèle étant donné que le thread n'est pas celui
				de sa naissance.
				
				@param ligne : la ligne à laquelle la fonction commence (intérêt de la localité de ce paramètre =  possibilité de multi-threading)
				@param selection : dictionnaire parent, chaque clé représente une ligne et est associée à un autre dictionnaire (sauf pour le dernier niveau) géré de la même manière
			'''

			if(niveau == profondeur_max): #Si on est au dernier niveau du mode d'affichage, c'est que c'est une piste
				if(add_all or tracks[ligne][2].lower().find(mot) != -1):
					selection['children'][ligne] = {'props':{'count':tracks[ligne][7], 'rating':tracks[ligne][8], 'rated':int(tracks[ligne][8] != 0)} }
						#self.expand.append(ligne)
					#fils = model.append(pere, [icon_track, tracks[ligne][0], tracks[ligne][2], 1, 1])
					#TreeView.expand_to_path(model.get_path(fils))
				#La ligne est traitée en intégralité, on passe à la suivante :
				i = ligne + 1

				
			else: #Il faut continuer de "creuser" et ajouter tous les fils de ce père
				
				elt = getValueOfLevel(tracks[ligne], niveau)
				cond = list(cond)
				cond.append(elt)
				
				#On ajoute le premier fils
				#fils = model.append(pere, [icon, 1, getValueOfLevel(tracks[ligne], niveau), 1, 1])
				
				if(add_all == False  and getValueOfLevel(tracks[ligne], niveau).lower().find(mot) != -1):
					add_all = True
					
				new = {'children':{}, 'props':{'count':0, 'rating':0, 'rated':0}}
				

				#Tant qu'il reste du monde et qu'on est toujours sur le même conteneur :
				#while(ligne < len(tracks) and elt == getValueOfLevel(tracks[ligne], niveau)):
				while(ligne < len(tracks) and isSameContainer(tracks[ligne], niveau, cond)):
					#Même valeur sur ce niveau, donc on descend d'un et on répète le schéma
					ligne = traiter_conteneur(niveau+1, ligne, new, add_all, cond)
					
				if(len(new['children']) > 0 or getValueOfLevel(tracks[ligne-1], niveau).lower().find(mot) != -1): #Si un père contient le mot ou a des fils
					selection['children'][ligne-1] = new
					if(add_all == False):
						self.expand[niveau].append(ligne-1)
				
					
					#selection[niveau] = {}
				#else:
					#del self.selection[niveau][-1]
				#if(len(sons[niveau]) > 0 or getValueOfLevel(tracks[ligne], niveau).find(mot) != -1):
					#pere = model.append(pere, [icon, 1, getValueOfLevel(tracks[ligne], niveau), 1, 1])
					#for son in sons[niveau]:
						#fils = model.append(pere, [icon, 1, getValueOfLevel(tracks[ligne], niveau), 1, 1])
					
				
				#On a pas traité en intégralité cette ligne donc on reste dessus :
				i = ligne
			
			try: #we add playcount to parent
				selection['props']['count'] += selection['children'][i-1]['props']['count']
				selection['props']['rating'] += selection['children'][i-1]['props']['rating']
				selection['props']['rated'] += selection['children'][i-1]['props']['rated']
					
			except KeyError:
				pass
			
			return i
				#On a enfin fini de boucler le premier père accroché à la racine, on passe donc au suivant si il y en a :
				#EN FAIT NON, C'EST FOIREUX :D
				#if(getValueOfLevel(tracks[ligne], niveau-1) != elt_pere):
					#traiter_conteneur(None, 0, None)
				
				
		
		
		#cle = 0
		#for c in mode:
			#cle += ord(c)
		
		#selection = [[], [], []]
			
		try:
			if(force_reload is True):
				self.tracks[self.mode] = self.BDD.loadTracks(self.mode)
				tracks = self.tracks[self.mode]
			else:
				tracks = self.tracks[self.mode]
		except KeyError:
			self.tracks[self.mode] = self.BDD.loadTracks(self.mode)
			tracks = self.tracks[self.mode]
		

		mode = eval(self.mode)
		profondeur_max = len(mode) - 1
		
		self.expand = []
		
		def getIcon(track_line, level):
			'''
				@param track_line : la ligne de la piste dans le tableau self.tracks[mode]
				@level : le niveau de profondeur dans le mode d'affichage
					ex de mode ('artist, 'album', 'title') level 0 = artist, level 2 = title, etc...
			'''
			try:
				path = os.path.join(xdg.get_thumbnail_dir(mode[level] + '/medium'),  track_line[indices[mode[level]]].replace ('/', ' ') + '.jpg')
				icon = QtGui.QIImage(path).scaled(icon_size)
			except:
				icon = icons[mode[level]]
			return icon

		def ajouter_selection(pere, niveau, selection):
			#icon = icons[mode[niveau]]
			
			for ligne in selection['children'].iterkeys():
				child = selection['children'][ligne]
				if(child['props']['rated'] == 0):
					burn = 0
				else:
					burn = float(child['props']['count']) / float(child['props']['rated'] +1)
				#icon = getIcon(tracks[ligne], niveau)
				
				
				child_node = pere.append(LibraryItem(pere, None, tracks[ligne][0], getValueOfLevel(tracks[ligne], niveau), child['props']['count'], child['props']['rating'], burn, "%.2f" % burn, False, mode[niveau]))
				
				if(niveau < len(mode)-1):
					if ligne in self.expand[niveau]:
						print('expand : ' + str(ligne) + ' - ' + getValueOfLevel(tracks[ligne], niveau))
						self.expand_paths.append(self.model.createIndex(child_node.row(), 0, child_node))
						#self.TreeView.expand_row(self.model.get_path(fils), False)
					ajouter_selection(child_node, niveau+1, child)
			#if(niveau == 1):
				#child_node = pere.append(LibraryItem(None, 0, None, 0, 0, 0, None, True))

			
			
		
		def expand():
			for path in self.expand_paths:
				self.TreeView.expand(path)

		def traiter_tous_les_conteneurs():
			#time.sleep(1)
			
			self.notLoading.wait()
			self.notLoading.clear()
			niveau = 0
			ligne = 0

			i = 0
			while(ligne < len(tracks)):
				
				self.expand = [[], []]
				self.expand_paths = []
				self.selection = {'children':{}, 'props':{'count':0, 'rating':0, 'rated':0}}
				ligne = traiter_conteneur(0, ligne, self.selection)
				
				self.model.beginInsertRows(QtCore.QModelIndex(), i, i+1)
				i+=1
				
				ajouter_selection(self.model.rootItem, 0, self.selection)
				#glib.idle_add(ajouter_selection, None, 0, self.selection)
				self.model.endInsertRows()
				self.expandRequested.emit(self.expand_paths)
				#expand()
				
			#self.TreeView.expand_all()
			if(e != None):
				e.set() #On a fini donc on prévient les autres threads qui nous attendaient
			self.notLoading.set()
			
			
		
		
		self.model.reset()
		a = threading.Thread(target=traiter_tous_les_conteneurs)
		a.start()
	
	
	


	def mouseReleaseEvent(self, e):
		if e.button() == Qt.MidButton:
			i = self.TreeView.indexAt(QtCore.QPoint(e.x(), e.y()))
			if(i.column() != 0):
				i= i.sibling(i.row(), 0)
			self.TreeView.setExpanded(i, not self.TreeView.isExpanded(i))
		else:
			QtGui.QTreeView.mouseReleaseEvent(self.TreeView, e)
			


		
	def searchFor(self, entry):
		word = entry.text()
		self.fill_model(mot=word)
		
		


		

        
class LibraryItem(treemodel.TreeItem):
	def __init__(self, parent, icon, ID, label, playcount, rating, burn, rounded_burn, is_separator, type):
		treemodel.TreeItem.__init__(self, label, parent)
		self.icon = icon
		self.ID = ID
		self.label = label
		self.playcount = playcount
		self.rating = rating
		self.burn = burn
		self.rounded_burn = rounded_burn
		self.is_separator = is_separator
		self.type = type
		
		self.subelements = []
		
	def __str__( self ):
		return self.label
		
	def __repr__(self):
		return self.label
		
	def getFilter(self):
		'''
			ex : {"artist":"AC/DC", "album":"Back In Black", "title":"You Shook Me All Night Long"}
		'''
		dic = {}
		item = self
		while(item.parent() != None): # Don't  eval rootItem 
			dic[item.type] = item.label
			item = item.parent()
		return dic



		
		
		
		

		
		
class LibraryModel(treemodel.TreeModel):
	def __init__(self):
		treemodel.TreeModel.__init__(self)
		self.columnsFields = ('label', 'label', 'playcount', 'rating', 'burn')


	def columnCount(self, parent):
		return 5

	def data(self, index, role):
		if not index.isValid():
			return None
		item = index.internalPointer()
		if role == Qt.DisplayRole:
			if index.column() == 1:
				return item.label
			elif index.column() == 2:
				return item.playcount
			elif index.column() == 3:
				return item.rating
			elif index.column() == 4:
				return item.rounded_burn
				
		elif role == Qt.DecorationRole and index.column() == 0:
			if(item.icon is None):
				try:
					path = os.path.join(xdg.get_thumbnail_dir(item.type + '/medium'),  item.label.replace ('/', ' ')) # + '.jpg')
					item.icon = QtGui.QPixmap(path)
					if(item.icon.isNull()):
						item.icon = icons[item.type]
					else:
						item.icon = item.icon.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation) #scaledToHeight(icon_size)
						
				except:
					item.icon = icons[item.label]
				
			return item.icon
		return None

	def flags(self, index):
		return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled
	
	def headerData(self, section, orientation, role):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			if section == 0:
				return 'Icon'
			elif section == 1:
				return 'Label'
			elif section == 2:
				return _('Count')
			elif section == 3:
				return _('Rating')
			elif section == 4:
				return _('Burn')
			
		return None
		
	def mimeData(self, indexes):
		'''
			What is passed during drag operations
		'''
		data = QtCore.QMimeData()
		selection = []
		for i in indexes:
			selection.append(i.internalPointer().getFilter())
		data.setData('bullseye/library.items', str(selection))
		return data
		
	def mimeTypes(self):
		'''
			FIXME Not used, didn't manage to find out how to automatically serialize items (thus overrided mimeData instead)
		'''
		return ('bullseye/library.items',)
		
	def sort(self, columnIndex, order):
		self.layoutAboutToBeChanged.emit()
		if(order == Qt.AscendingOrder):
			reverse = False
		else:
			reverse = True
			
		def sort(elt, reverse):
			elt.childItems = sorted(elt.childItems, key=attrgetter(self.columnsFields[columnIndex]), reverse=reverse)
			for childElt in elt.childItems:
				sort(childElt, reverse)
				
		sort(self.rootItem, reverse)
		
		self.layoutChanged.emit()
		
            

class PlaylistBrowser(QtGui.QWidget):
	
	FOLDER = os.path.join(xdg.get_data_home(), 'playlists')
	PLAYLIST_ICON = QtGui.QPixmap(xdg.get_data_dir() + 'icons/playlist.png')
	FOLDER_ICON = QtGui.QIcon.fromTheme('folder')
	
	def __init__(self, db, queueManager):
		self.mdb = db
		self.queueManager = queueManager
		
		QtGui.QWidget.__init__(self)
		treeView = QtGui.QTreeView()
		treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		treeView.customContextMenuRequested.connect(self.showContextMenu)
		self.model = treemodel.SimpleTreeModel()
		self.reloadModel()
		treeView.setModel(self.model)
		treeView.activated.connect(self.onActivated)
		
		layout = QtGui.QVBoxLayout()
		layout.addWidget(treeView)
		self.setLayout(layout)
		
	def addPlaylist(self, key, text, iconPath=xdg.get_data_dir() + 'icons/playlist.png', parent=None):
		node = treemodel.SimpleTreeItem(parent, key, iconPath, text)
		self.model.append(parent, node)
		return node
		
	def deletePlaylist(self, index):
		item = index.internalPointer()
		name = item.key
		if item.parent().key == '42static':
			os.remove(self.FOLDER + os.sep +  name)
		else:
			os.remove(self.FOLDER + os.sep + 'dynamic' + os.sep + name)
		#self.model.removeRow(index.row(), index.parent())
		self.reloadModel()
		
	def onActivated(self, index):
		item = index.internalPointer()
		if item.parent().key == '42static':
			f = open(self.FOLDER + os.sep +  item.key, 'r')
			IDList = f.readlines()
			f.close()
			self.queueManager.addPlaylist(item.key, IDList)
		elif item.parent().key == '42dynamic':
			f = open(self.FOLDER + os.sep + 'dynamic' + os.sep + item.key, 'r')
			data = f.readlines()
			f.close()
			self.queueManager.addQueue()
			self.queueManager.addSelection(self.mdb.getDynamicListTracks(eval(data[0])))
		
	def reloadModel(self):
		self.model.reset()
		self.staticNode = self.addPlaylist('42static', _("Static playlists"))
		for f in os.listdir(self.FOLDER):
			if os.path.isfile(os.path.join(self.FOLDER, f)):
				self.addPlaylist(f, f, None, self.staticNode)
		
		self.dynamicNode = self.addPlaylist('42dynamic', _("Dynamic playlists"))
		dossier = self.FOLDER + os.sep + 'dynamic' + os.sep
		for f in os.listdir(dossier):
			if os.path.isfile(os.path.join(dossier, f)):
				self.addPlaylist(f, f, None, self.dynamicNode)
				
	def showContextMenu(self, pos):
		item = self.sender().indexAt(pos).internalPointer()
		popMenu = QtGui.QMenu(self)
		if item.key == '42static' or item.key == '42dynamic':
			addStatic = popMenu.addAction(QtGui.QIcon.fromTheme('list-add'), _("Add a static playlist"))
			addDynamic = popMenu.addAction(QtGui.QIcon.fromTheme('list-add'), _("Add a dynamic playlist"))
			
			action = popMenu.exec_(self.sender().mapToGlobal(pos))
			if action == addStatic:
				print 'todo'
			elif action == addDynamic:
				d = modales.DynamicPlaylistCreator()
				newName = d.exec_()
				if newName != None:
					self.addPlaylist(newName, newName, None, self.dynamicNode)
		else:
			edit = popMenu.addAction(QtGui.QIcon.fromTheme('list-edit'), _("Edit playlist"))
			delete = popMenu.addAction(QtGui.QIcon.fromTheme('list-remove'), _("Delete playlist"))
			
			action = popMenu.exec_(self.sender().mapToGlobal(pos))
			if action == edit:
				d = modales.DynamicPlaylistCreator(item.key)
				d.exec_()
			elif action == delete:
				self.deletePlaylist(self.sender().indexAt(pos))