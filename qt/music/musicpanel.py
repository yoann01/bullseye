# -*- coding: utf-8 -*-
import os
from PySide import QtGui, QtCore
from PySide.QtCore import Qt

from PySide.QtCore import QModelIndex, QAbstractItemModel

from common import messager, settings, xdg
from qt.util import treemodel
from data.elements import Track
from gui import menus, modales
import threading
import time
#from gui.menus import TrackMenu, TrackContainerMenu

icon_track = QtGui.QPixmap('icons/track.png')
icon_artist = QtGui.QPixmap('icons/artist.png')
icon_album = QtGui.QPixmap('icons/star.png')
icon_genre = QtGui.QPixmap('icons/genre.png')
icon_year = QtGui.QPixmap('icons/year.png')
icon_rating = QtGui.QPixmap('icons/star.png')
icons = {"title":icon_track, "artist":icon_artist, "album":icon_album, "genre":icon_genre, "note":icon_rating, "year":icon_year}
icon_size = settings.get_option('music/panel_icon_size', 32)

class LibraryPanel(QtGui.QWidget):
	"""
		TODO check errors (arkenstone, little richard)
	"""
		
	def __init__(self, BDD, queueManager):
		QtGui.QWidget.__init__(self)
		self.BDD = BDD
		self.queueManager = queueManager
		self.tracks = {}
		self.mode = '("artist", "album", "title")'
		
		self.TreeView = QtGui.QTreeView()
		
		self.model = LibraryModel()
		
		
		self.notLoading = threading.Event()
		self.notLoading.set()
		self.fill_model()
		
		#TreeNode(self.model, None, LibraryItem(None, 1, "ok", 1, 1, 1, 1, False))
		#self.model.append(LibraryItem(None, 1, "ok", 1, 1, 1, 1, False))
		self.TreeView.setModel(self.model)
		self.TreeView.activated.connect(self.ajouter_pistes)
		
		# *** TreeView visual tweaks
		self.TreeView.setColumnWidth(1, settings.get_option('music/col_label_panel_width', 170))
		
		# *** Mode selector ***
		modsModel = QtGui.QStandardItemModel()
		modsModel.appendRow([QtGui.QStandardItem('("artist", "album", "title")'), QtGui.QStandardItem(_("Artist"))])
		modsModel.appendRow([QtGui.QStandardItem('("genre", "album", "title")'), QtGui.QStandardItem(_("Genre"))])
		self.CB_mod = QtGui.QComboBox()
		self.CB_mod.setModelColumn(1)
		self.CB_mod.setModel(modsModel)
		
		refreshButton = QtGui.QPushButton(QtGui.QIcon.fromTheme('view-refresh'), _('Refresh'))
		refreshButton.clicked.connect(self.fill_model)
		modLayout = QtGui.QHBoxLayout()
		modLayout.addWidget(self.CB_mod)
		modLayout.addWidget(refreshButton)
		modLayout.setStretch(0, 1)
		modLayout.setStretch(1, 0)
		
		layout = QtGui.QVBoxLayout()
		layout.addLayout(modLayout)
		layout.addWidget(self.TreeView)
		
		

		#self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding))
		self.setLayout(layout)
		self.setMinimumSize(settings.get_option('music/paned_position', 200), 500)
		
	def resizeEvent(self, event):
		print  event.size().width()
		settings.set_option('music/paned_position', event.size().width())
	
		
	def ajouter_pistes(self, i):
		mode = eval(self.CB_mod.model().item(self.CB_mod.currentIndex(), 0).text()) #Ex : '("artist", "album")'
		
		dic = {}
		level = 0
		params = []
		while(i.isValid()): #On remonte la chaîne tant qu'on est pas arrivé à la racine
			level += 1
			params.append(i.internalPointer().label)
			i = i.parent()
			
		params.reverse()
		
		i = 0
		while(i < level):
			dic[mode[i]] = params[i]
			i += 1
		
		self.queueManager.addSelection(self.BDD.getTracks(dic))
		
	def changer_mode(self, mode):
		self.mode = self.CB.get_active_text()
		self.fill_model()
		#messager.diffuser('TS_bibliotheque', self, [self.model, mode])
		
	
	def fill_model(self, garbageFromConnect=None, force_reload=False, mot='', e=None):
		'''
			Remplit la liste arborescente avec les pistes de la BDD selon l'arborescence du mode séléctionné
			
			@param data = [TreeStore, mode]
			@param e = threading event pour prévenir qu'on a fini
			TODO : ajouter le ratio d'écoutes par conteneur, qui s'applique uniquement sur les pistes notées
			ratio = total_ecoutes_conteneur / nb_pistes_notees_conteneur
		'''
		indices = {"title":2, "artist":4, "album":3, "genre":5, "note":8, "year":9}
		
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
						self.expand_paths.append(self.model.get_path(child_node))
						#self.TreeView.expand_row(self.model.get_path(fils), False)
					ajouter_selection(child_node, niveau+1, child)
			#if(niveau == 1):
				#child_node = pere.append(LibraryItem(None, 0, None, 0, 0, 0, None, True))

			
			
		
		def expand():
			for path in self.expand_paths:
				self.TreeView.expand_row(path, False)

		def traiter_tous_les_conteneurs():
			self.notLoading.wait()
			self.notLoading.clear()
			niveau = 0
			ligne = 0

			while(ligne < len(tracks)):
				self.expand = [[], []]
				self.expand_paths = []
				self.selection = {'children':{}, 'props':{'count':0, 'rating':0, 'rated':0}}
				ligne = traiter_conteneur(0, ligne, self.selection)
				
				ajouter_selection(self.model.rootItem, 0, self.selection)
				#glib.idle_add(ajouter_selection, None, 0, self.selection)
				expand()
			#self.TreeView.expand_all()
			if(e != None):
				e.set() #On a fini donc on prévient les autres threads qui nous attendaient
			self.notLoading.set()
			
		
		
		self.model.reset()
		a = threading.Thread(target=traiter_tous_les_conteneurs)
		a.start()
	
	
	
	
	def keep_true_selection(self, TV, drag_context):
		'''
			Trick pour dragger plusieurs items car lors du drag la séléction devient l'item draggé
		'''
		#Début d'un DND
		selection = TV.get_selection()
		if(selection.get_selected_rows()[1][0] in self.selection):
			for path in self.selection:
				selection.select_path(path)
		else:
			self.selection = selection.get_selected_rows()[1]
		
	def on_button_press(self, TV, event):
		if event.button == 1: #Clic gauche
			model, self.selection = TV.get_selection().get_selected_rows()
		elif event.button == 3: #Clic droit
			path = TV.get_path_at_pos(int(event.x),int(event.y))[0]
			if (path != None):
				mode = eval(self.mode)
				model = TV.get_model()
				if(len(path) != len(mode)): #Conteneur
					dic = {}
					i = 0
					while (i != len(path)):
						dic[mode[i]] = model[path[0:i+1]][2]
						i += 1
					m = menus.TrackContainerMenu(dic)
					m.show_all()
					m.popup(None, None, None, event.button, event.time)
				else: #Piste
					piste_ID = model[path][1]
					ligne = model.get_iter(path)
					m = menus.TrackMenu(piste_ID)
					m.append(gtk.SeparatorMenuItem())
					i = gtk.ImageMenuItem(_("Remove from queue"))
					i.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_MENU))
					#i.connect('activate', self.enlever_piste, ligne)
					m.append(i)

					i = gtk.ImageMenuItem(_("Add to direct list"))
					i.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_MENU))
					#i.connect('activate', self.gestionnaire.addToDirectList, queue, ligne)
					m.append(i)
					m.show_all()
					m.popup(None, None, None, event.button, event.time)
		elif event.button == 2:
			path = TV.get_path_at_pos(int(event.x),int(event.y))[0]
			if(TV.row_expanded(path)):
				TV.collapse_row(path)
			else:
				TV.expand_row(path, False)
	
	def on_column_clicked(self, column):
		def disable_sorting_state():
			time.sleep(2.0)
			self.model.set_sort_column_id(-2, 0)
			
		a = threading.Thread(target=disable_sorting_state)
		a.start()
		
	def on_drag_data_get(self, widget, drag_context, selection_data, info, timestamp):
		def get_dic(path, mode):
			#renvoie un dictionnaire contenant les données nécessaires à l'identifcation d'un item draggé
			level = len(path)
			dic = {}
			while (level > 0):
				dic[mode[level -1]] = self.model[path[0:level]][2]
				level -= 1
			return dic
		#Début d'un DND
		model, paths = widget.get_selection().get_selected_rows() #Cela correspond en fait à l'index de l'unique item cliqué (auto séléctionné par l'événement button-press)
		if paths[0] in self.selection: #On vérifie que cet index ne figure pas dans l'ancienne séléction multiple
			paths = self.selection #Si c'est le cas, cela veut dire que l'on voulait DND la séléction multiple et non l'unique item cliqué
		T = []
		mode = eval(self.mode)
		for path in paths:
			T.append(get_dic(path, mode))
		selection_data.set_text(str(T))

		
	def restreindre(self, entry):
		word = entry.get_text()
		mode = self.CB.get_active_text()
		e = threading.Event()
		self.fill_model(mot=word)
		
		#self.model = self.BDD.fill_library_browser([self.model, mode], e)
		
		
		#def suite_travail(e):
			#t = e.wait() #On attend que l'autre thread ait fini puisqu'on est la suite de son travail
			
			#self.TreeView.collapse_all()
			#if (word == ""):
				#print('vide')
				##self.TreeView.set_model(self.model)
			#else:
				#liste_a_virer = []
				#liste_a_garder = []
				
				#def traiter(modele, chemin, iter, data=None):
					#nom = modele[chemin][2].lower()
					#recherche = data[2].lower()
					#if(nom.find(recherche) == -1):
						#data[0].append(chemin)
					#else:
						#data[1].append(chemin)
				
				#self.model.foreach(traiter, [liste_a_virer, liste_a_garder, word])
				
				#for chemin in liste_a_garder:
					##On "développe" ce qu'on veut avant de virer ce qu'on ne veut pas (car les chemins réels auront alors changé)
					#i = 1
					#longueur = len(chemin)
					#while(i < longueur):
						#chemin_pere = chemin[0:i]
						#self.TreeView.expand_to_path(chemin_pere)
						#i+=1
					##self.TreeView.expand_to_path(chemin)
				

				#liste_a_virer.reverse()
				#for chemin in liste_a_virer:
					#iter = self.model.get_iter(chemin)
					#i = 0
					##Tant qu'on essaye pas d'évaluer un niveau inexistant (au delà de la racine) et qu'aucun père n'a été trouvé
					#while(i < len(chemin) and not(chemin[0:i] in liste_a_garder)): 
						#i += 1
					#pere_present = (chemin[0:i] in liste_a_garder)
					#has_child = self.model.iter_has_child(iter)
		
					#if(not(pere_present) and not(has_child)): 
					##L'élément est sur la liste à virer et qu'il n'a ni fils et ni père: on le supprime
						#self.model.remove(iter)
		
		#a = threading.Thread(target=suite_travail, args=(e,))
		#a.start()
		#suite_travail()
		
		
	#def ajouter_pistes(self, i):
		#level = len(i) #On choppe le niveau de profondeur de la séléction ( 1 = Artiste, 2 = Album, 3 = Piste)
		#selection = []
		#if level == 3:
			#track_ID = self.model[i][0]
			#track_data = self.BDD.get_track_data(track_ID)
			#selection.append((track[0], track[2], track[3], track[4],))
		#elif level == 2:
			#j = 0
			#numero = i + (j,)
			#track = self.model[numero]
			#while track != None:
				##On ajoute les infos de la piste à la séléction
				#selection.append((track[0], track[2], track[3], track[4],))
				#j += 1
				#numero = i + (j,)
				#try:
					#track = self.model[numero]
				#except:
					#track = None
				
			#print(selection)
			
		#self.playlist.ajouter_selection(selection)

		#print(self.model[i][0])
		
		






		

        
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



		
	
            
class LibraryModel(treemodel.TreeModel):
	def __init__(self):
		treemodel.TreeModel.__init__(self)


	def columnCount(self, parent):
		return 3

	def data(self, index, role):
		if not index.isValid():
			return None
		item = index.internalPointer()
		if role == Qt.DisplayRole:
			if index.column() == 1:
				return item.label
			elif index.column() == 2:
				return item.playcount
		elif role == Qt.DecorationRole and index.column() == 0:
			if(item.icon is None):
				try:
					path = os.path.join(xdg.get_thumbnail_dir(item.type + '/medium'),  item.label.replace ('/', ' ') + '.jpg')
					item.icon = QtGui.QPixmap(path)
					if(item.icon.isNull()):
						item.icon = icons[item.type]
					else:
						item.icon = item.icon.scaledToHeight(icon_size)
				except:
					item.icon = icons[item.label]
				
			return item.icon
		return None

	def headerData(self, section, orientation, role):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			if section == 0:
				return 'Icon'
			elif section == 1:
				return 'Label'
			elif section == 2:
				return _('Count')
			
		return None
            
class SearchEntry(object):
	"""
		A gtk.Entry that emits the "activated" signal when something has
		changed after the specified timeout
	"""
	def __init__(self, entry=None, timeout=500):
		"""
		Initializes the entry
		"""
		self.entry = entry
		self.timeout = timeout
		self.change_id = None

		if self.entry is None:
			self.entry = gtk.Entry()

		#self.entry.connect('changed', self.on_entry_changed)
		self.entry.connect('icon-press', self.on_entry_icon_press)

	def on_entry_changed(self, *e):
		"""
		Called when the entry changes
		"""
		if self.change_id:
			glib.source_remove(self.change_id)

		self.change_id = glib.timeout_add(self.timeout, self.entry_activate)

	def on_entry_icon_press(self, entry, icon_pos, event):
		"""
		Clears the entry
		"""
		self.entry.set_text('')

	def entry_activate(self, *e):
		"""
		Emit the activate signal
		"""
		self.entry.activate()

	def __getattr__(self, attr):
		"""
		Tries to pass attribute requests
		to the internal entry item
		"""
		return getattr(self.entry, attr)