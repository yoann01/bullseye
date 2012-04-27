# -*- coding: utf-8 -*-
import gtk
import os
from common import messager, settings, xdg
from gui import menus, modales
import glib
import threading
import time
#from gui.menus import TrackMenu, TrackContainerMenu

class LibraryPanel(gtk.VBox):
	"""
		TODO check errors (arkenstone, little richard)
		Burn factor indicates container with playcount concentrated on fews children
	"""
	def __init__(self, BDD, queueManager):
		self.BDD = BDD
		self.queueManager = queueManager
		self.tracks = {}
		self.TreeView = gtk.TreeView()
		#self.TreeView.set_headers_visible(False)
		self.TreeView.enable_model_drag_source(gtk.gdk.MODIFIER_MASK,  [('text/plain', 0, 0)] ,
                  gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
		self.TreeView.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
		#self.TreeView.set_rubber_banding(True) #séléction multiple by dragging
		self.TreeView.connect('row-activated', self.ajouter_pistes)
		self.TreeView.connect("drag-begin", self.keep_true_selection)
		self.TreeView.connect("button-press-event", self.on_button_press)
		self.TreeView.connect("drag-data-get", self.on_drag_data_get)
		#icon, ID, titre
		self.mode = '("artist", "album", "title")'
		self.model = gtk.TreeStore(gtk.gdk.Pixbuf, int, str, int, int, float, str, bool) #icon, id, label, playcount, rating
		
		#messager.diffuser('TS_bibliotheque', self, [self.model, self.mode])
		
		def is_separator(model, iter):
			return model.get_value(iter, 7)
		self.TreeView.set_row_separator_func(is_separator)
		
		#self.TreeView.set_rules_hint(True)
		self.TreeView.set_model(self.model)
		
		pb = gtk.CellRendererPixbuf()
		#self.Col_Icon = BSColumn('col_icon_panel', _('Icon'), pb, pixbuf=0, default_width=80)
		self.Col_Icon = BSColumn('col_icon_panel', _('Icon'), default_width=80)
		self.Col_Icon.pack_start(pb, False)
		self.Col_Icon.set_attributes(pb, pixbuf=0)
		Col_Label = BSColumn('col_label_panel', _('Label'), expand=True, default_width=170)
		self.TreeView.append_column(self.Col_Icon)
		self.TreeView.append_column(Col_Label)
		cell = gtk.CellRendererText()
		
		#Col_Label.pack_start(pb, False)
		Col_Label.pack_start(cell, True)
		#Col_Label.set_attributes(pb, pixbuf=0)
		Col_Label.add_attribute(cell, 'text', 2)
		Col_Label.set_sort_column_id(2)
		Col_Label.connect("clicked", self.on_column_clicked)
		Col_Count = BSColumn('col_count_panel', _('Count'), cell, model_text=3, default_width=50)
		Col_Rating = gtk.TreeViewColumn(_('Rating'), cell, text=4)
		Col_Valor = gtk.TreeViewColumn(_('Burn'), cell, text=6)
		self.TreeView.append_column(Col_Count)
		self.TreeView.append_column(Col_Rating)
		self.TreeView.append_column(Col_Valor)
		Col_Count.set_sort_column_id(3)
		Col_Count.connect("clicked", self.on_column_clicked)
		Col_Rating.set_sort_column_id(4)
		Col_Rating.connect("clicked", self.on_column_clicked)
		Col_Valor.set_sort_column_id(5)
		Col_Valor.connect("clicked", self.on_column_clicked)
		
		self.notLoading = threading.Event()
		self.notLoading.set()
		self.fill_model()
		
		LS_CB = gtk.ListStore(str, str)
		LS_CB.append(['("artist", "album", "title")', _("Artist")])
		LS_CB.append(['("album", "title")', _("Album")])
		LS_CB.append(['("rating", "title")', _("Rating")])
		LS_CB.append(['("genre", "album", "title")', _("Genre")])
		LS_CB.append(['("year", "artist", "album", "title")', _("Year")])
		LS_CB.append(['("year", "genre", "artist", "album", "title")', _("Year - Genre")])
		LS_CB.append(['("rating", "year", "genre", "artist", "album", "title")', _("Rating - Year - Genre")])
		CB = gtk.ComboBox()
		cell = gtk.CellRendererText()
		CB.pack_start(cell)
		CB.add_attribute(cell, "text", 1)
		CB.set_model(LS_CB)
		CB.set_active(0)
		CB.connect("changed", self.changer_mode)
		self.CB = CB
		
		B_refresh = gtk.ToolButton(gtk.STOCK_REFRESH)
		B_refresh.connect('clicked', self.fill_model, True)
		
		gtk.VBox.__init__(self)
		Box_mode = gtk.HBox()
		Box_mode.pack_start(CB)
		Box_mode.pack_start(B_refresh, False)
		self.pack_start(Box_mode, False)
		SW = gtk.ScrolledWindow()
		SW.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		SW.add(self.TreeView)
		self.pack_start(SW)
		E_Search  = gtk.Entry()
		Search = SearchEntry(E_Search)
		Search.connect('activate', self.restreindre)
		self.pack_start(E_Search, False)
	
		
	def ajouter_pistes(self, w, i, c):
		mode = eval(self.CB.get_active_text()) #Ex : '("artist", "album")'
		level = len(i) #On choppe le niveau de profondeur de la séléction (ex : 1 = Artiste, 2 = Album, 3 = Piste)
		#if(level == len(mode)): #On est au plus bas : on veut une piste
			#messager.diffuser('queue_add_track', self, self.model[i][1])
		#else:
		
		dic = {}
		while(level > 0): #On remonte la chaîne tant qu'on est pas arrivé à la racine
			i = i[0:level] #On enlève l'étage de fin
			level -= 1
			dic[mode[level]] = self.model[i][2]
		#DEPRECATED messager.diffuser('need_tracks', self, dic)
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
		indices = {"title":2, "artist":4, "album":3, "genre":5, "rating":8, "year":9}
		
		icon_size = settings.get_option('music/panel_icon_size', 32)
		self.Col_Icon.set_min_width(icon_size + 16)
		
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
					count = tracks[ligne][7]
					rated = int(tracks[ligne][8] != 0)
					if rated:
						count_rated = count
					else:
						count_rated = 0
						
					selection['children'][ligne] = {'props':{'count':count, 'rating':tracks[ligne][8], 'rated':rated, 'count_rated':count_rated} }
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
					
				new = {'children':{}, 'props':{'count':0, 'rating':0, 'rated':0, 'count_rated':0}}
				

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
				selection['props']['count_rated'] += selection['children'][i-1]['props']['count_rated']
					
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
		
		icon_track = gtk.gdk.pixbuf_new_from_file('icons/track.png')
		icon_artist = gtk.gdk.pixbuf_new_from_file('icons/artist.png')
		icon_album = gtk.Image().render_icon(gtk.STOCK_CDROM, gtk.ICON_SIZE_MENU)
		icon_genre = gtk.gdk.pixbuf_new_from_file('icons/genre.png')
		icon_year = gtk.gdk.pixbuf_new_from_file('icons/year.png')
		icon_rating = gtk.gdk.pixbuf_new_from_file('icons/star.png')
		icons = {"title":icon_track, "artist":icon_artist, "album":icon_album, "genre":icon_genre, "rating":icon_rating, "year":icon_year}
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
				path = os.path.join(xdg.get_thumbnail_dir(mode[level] + '/medium'),  track_line[indices[mode[level]]].replace ('/', ' ')) # + '.jpg')
				icon = gtk.gdk.pixbuf_new_from_file_at_size(path, icon_size, icon_size)
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
					burn = float(child['props']['count_rated']) / float(child['props']['rated'] +1)
					#burn = float(child['props']['count_rated']) / float(child['props']['count'] +1)
				icon = getIcon(tracks[ligne], niveau)
				child_node = self.model.append(pere, [icon, tracks[ligne][0], getValueOfLevel(tracks[ligne], niveau), child['props']['count'], child['props']['rating'], burn, "%.2f" % burn, False ])
				
				if(niveau < len(mode)-1):
					if ligne in self.expand[niveau]:
						print('expand : ' + str(ligne) + ' - ' + getValueOfLevel(tracks[ligne], niveau))
						self.expand_paths.append(self.model.get_path(child_node))
						#self.TreeView.expand_row(self.model.get_path(fils), False)
					ajouter_selection(child_node, niveau+1, child)
			if(niveau == 1):
				child_node = self.model.append(pere, [None, 0, None, 0, 0, 0, None, True])

			
			
		
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
				
				ajouter_selection(None, 0, self.selection)
				#glib.idle_add(ajouter_selection, None, 0, self.selection)
				expand()
			#self.TreeView.expand_all()
			if(e != None):
				e.set() #On a fini donc on prévient les autres threads qui nous attendaient
			self.notLoading.set()
			
		
		
		self.model.clear()
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
		
		
class Playlists_Panel(gtk.VBox):
	
	FOLDER = os.path.join(xdg.get_data_home(), 'playlists' + os.sep)
	DYNAMIC_FOLDER = FOLDER + os.sep + 'dynamic' + os.sep
	
	def __init__(self, db, queueManager):
		#Attributs:
		self.mdb = db
		self.queueManager = queueManager
		
		self.TV = gtk.TreeView()
		self.model = gtk.TreeStore(gtk.gdk.Pixbuf, int, str) #icon, ID, titre
		
		
		pixbuf_dir = gtk.ToolButton().render_icon(gtk.STOCK_DIRECTORY, gtk.ICON_SIZE_BUTTON)
		self.pere = self.model.append(None, [pixbuf_dir, 0, "Static playlists"])
		for f in os.listdir(self.FOLDER):
			pixbuf = gtk.gdk.pixbuf_new_from_file('icons/playlist.png')
			if os.path.isfile(os.path.join(self.FOLDER, f)):
				self.model.append(self.pere, [pixbuf, 0, f])
		
		self.intelligent_pere = self.model.append(None, [pixbuf_dir, 0, _("Dynamic playlists")])

		for f in os.listdir(self.DYNAMIC_FOLDER):
			if os.path.isfile(os.path.join(self.DYNAMIC_FOLDER, f)):
				self.model.append(self.intelligent_pere, [pixbuf, 0, f])
		
				
				
		
		self.TV.set_model(self.model)
		colonne = gtk.TreeViewColumn('Column 0')
		self.TV.append_column(colonne)
		cell = gtk.CellRendererText()
		pb = gtk.CellRendererPixbuf()
		colonne.pack_start(pb, False)
		colonne.pack_start(cell, True)
		colonne.add_attribute(cell, 'text', 2)
		colonne.set_attributes(pb, pixbuf=0)
		
		self.TV.expand_all()
		
		#Signaux
		self.TV.connect('row-activated', self.charger_playlist)
		self.TV.connect("button-press-event", self.surClicDroit)
		
		#Abonnements
		messager.inscrire(self.ajouter_playlist, 'playlist_ajoutee')
		gtk.VBox.__init__(self)
		self.pack_start(self.TV)
		
	
	def ajouter_playlist(self, data):
		label = data[1]
		type = data[0]
		if(type == "intelligent"):
			pere = self.intelligent_pere
		else:
			pere = self.pere
			
		pixbuf = gtk.gdk.pixbuf_new_from_file('icons/playlist.png')	
		self.model.append(pere, [pixbuf, 0, label])
	
	def charger_playlist(self, w, i, colonne, stop_mod=False):
		level = len(i)
		if(level == 2): #On est bien sur une playlist
			nom = self.model[i][2]
			if(i[0] == 0): #On est sur une playlist perso
				fichier = open(self.FOLDER + nom,'r')
				liste = fichier.readlines()
				fichier.close()
				#On envoie la liste d'ID à la BDD, elle va la traiter et renvoyer les infos au queue_manager
				messager.diffuser('playlistData', self, [liste, nom, stop_mod])
			else: #On est sur une playlist intelligente
				fichier = open(self.DYNAMIC_FOLDER + nom,'r')
				data = fichier.readlines()
				fichier.close()
				self.queueManager.addQueue()
				self.queueManager.addSelection(self.mdb.getDynamicListTracks(eval(data[0])))

	
	def editer(self, bouton, uneLigne):
		path = self.model.get_path(uneLigne)
		nom = self.model.get_value(uneLigne, 2)
		if(path[0] == 0): #normal playlist
			print('temp rename')
		else: #intelligent playlist
			d = modales.IntelligentPlaylistCreator(nom)
		
		
	def supprimer(self, bouton, uneLigne):
		path = self.model.get_path(uneLigne)
		nom = self.model.get_value(uneLigne, 2)
		if(path[0] == 0):
			os.remove(self.FOLDER + nom)
		else:
			os.remove(self.DYNAMIC_FOLDER + nom)
		self.model.remove(uneLigne)
		
	def surClicDroit(self, TreeView, event):
		# On vérifie que c'est bien un clic droit:
		if event.button == 3:
			path = TreeView.get_path_at_pos(int(event.x),int(event.y))[0]
			level = len(path)
			if(level ==2):
				ligne = self.model.get_iter(path)
				m = menus.PlaylistMenu(self, ligne)
				#i.connect('activate', self.supprimer, playlist)
				#i.show() 
				#m.append(i) 
				m.popup(None, None, None, event.button, event.time)
			else:
				m = menus.CreatePlaylistMenu()
				m.popup(None, None, None, event.button, event.time)
				






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