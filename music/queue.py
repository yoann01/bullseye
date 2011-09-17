# -*- coding: utf-8 -*-
import gtk
import glib
import threading
import time
import gobject
import gettext
import logging


from common import messager, settings

from data.elements import Track, BDD

import gui.modales
from gui.menus import TrackMenu
from gui.util import icons, etoiles

IM = icons.IconManager()

logger = logging.getLogger(__name__)

class QueueManager(gtk.Notebook):
	"""
        Cet objet correspond au gestionnaire de pistes à jouer, graphiquement c'est un NoteBook (onglets, etc...)
        TODO ponts (A -> B, B-> C), filtres
        TODO bouton stop = set stop track 
        """
	def __init__(self, player):
		#gtk.rc_parse_string("style \"ephy-tab-close-button-style\"\n"
			     #"{\n"
			       #"GtkWidget::focus-padding = 0\n"
			       #"GtkWidget::focus-line-width = 0\n"
			       #"xthickness = 0\n"
			       #"ythickness = 0\n"
			     #"}\n"
			     #"widget \"*.ephy-tab-close-button\" style \"ephy-tab-close-button-style\"")
		gtk.Notebook.__init__(self)
		self.player = player
		self.directList = [] #Liste de pistes à jouer en priorité
		self.bridges_src = {}
		self.bridges_dest = {}
		
		#Abonnement à certains types de messages auprès du messager
		#messager.inscrire(self.charger_playlist, 'playlist')
		messager.inscrire(self.ajouter_selection, 'desPistes')
		messager.inscrire(self.charger_playlist, 'playlistData')
		messager.inscrire(self.avance_ou_arrete, 'need_piste_suivante')
		messager.inscrire(self.recule, 'need_piste_precedente')
		messager.inscrire(self.demarquer_piste, 'MusicPlayerStopped')
		
		self.numero = 0 #Le numéro de piste à jouer
		
		
		self.connect("switch-page", self.on_tab_change)
		
		self.IM = icons.IconManager()
		self.queue_jouee = None
		self.playing_iter = None
		self.dest_row = None
		# On ajoute une liste pour commencer
		self.load_state()
		self.initialisation_raccourcis()
		glib.timeout_add_seconds(300, self.save_state)
		
		
		self.connect('expose-event', self.redrawAddTabButton)
		self.connect('button-release-event', self.onButtonRelease)
		

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
				self.ajouter_un_onglet()
		
	def redrawAddTabButton(self, w, e):
		icon = gtk.Image().render_icon(gtk.STOCK_ADD, gtk.ICON_SIZE_MENU)
		#icon = gtk.gdk.pixbuf_new_from_file('icons/track.png')
		
		alloc = self.getAddTabButtonPos()
		self.window.draw_pixbuf(None, icon, 0, 0, alloc[0], alloc[1])

	@property
	def queue_visible(self):
		try:
			liste = self.get_nth_page(self.get_current_page()).Liste
		except:
			liste = None

		return liste
		
	def addToDirectList(self, menuitem, queue, ligne, temp=False):
		'''
		@param menuitem : osef
		@param ligne : l'iter à ajouter à la directList
		@param temp : if temp is true then after jumping return where player was before
		'''
		self.directList.append(DirectIter(queue, ligne, temp))
		if temp is True:
			image = icons.MANAGER.pixbuf_from_text(str(len(self.directList)), (18, 18), '#FFCC00', '#000', '#000')
		else:
			image = icons.MANAGER.pixbuf_from_text(str(len(self.directList)), (18, 18))
		queue.set_value(ligne, 1, image)


	def ajouter_selection(self, selection): 
		''' 
			Ajoute la séléction envoyée par le Panel à la queue visible
			@param selection : t de list content les informations des pistes à ajouter
				rappel de l'ordre: police, icon_playing, icon_stopping, ID, path, titre, album, artiste, length, count, pixbuf_note, note, bridge_src key
		'''
		liste = self.queue_visible
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
		
	def ajouter_un_onglet(self, button=None, label=None):
		nb_pages = self.get_n_pages()
		if(label != None):
			#Cela veut dire qu'on a reçu une playlist du messager
			nouvelleQueue = Playlist(self, label)
		else:
			label = _("List ") + str(nb_pages)
			nouvelleQueue = Queue(self, label)
			
		self.set_current_page(nb_pages)
		return nouvelleQueue
		
		
	def avance_ou_arrete(self, motif):
		'''
			Méthode primordiale permettant au MusicPlayer d'avoir sa piste sur demande (démarrage ou enchaînement)
		'''
		# Tout d'abord on vire le marquage de l'ancienne piste courante et on incrémente si fin de piste atteinte
		self.demarquer_piste()
		if(motif == "eos"):
			#ID_courant = self.queue_jouee.get_value(self.playing_iter, 3)
			messager.diffuser('incrementation', self, self.playing_track)
			compteur = self.queue_jouee.get_value(self.playing_iter, 9) + 1
			self.queue_jouee.set_value(self.playing_iter, 9, compteur)
			
		try:	
			if (self.queue_jouee.get_value(self.playing_iter, 2) is None):
				not_a_stop_track = True
			else:
				not_a_stop_track = False
		except:
			not_a_stop_track = True
			
		try:
			di = self.directList[0]
		except IndexError:
			di = None
			
		if(not_a_stop_track): #On vérifie d'abord qu'on ne doit pas s'arrêter avant de mouliner
			#Quelle est la piste à jouer? 3 possibilités :
			if(di != None): # 1/ une piste prioritaire
				self.playing_track = Track(di.queue.get_value(di.ligne, 3))
				
				if di.temp:
					self.temp_queue_jouee = di.queue
					self.temp_playing_iter = di.ligne
				else:
					self.queue_jouee = di.queue
					self.playing_iter = di.ligne
				self.directList.remove(di)
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
					self.queue_jouee = self.queue_visible
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
		queue = self.ajouter_un_onglet(data[1])
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
			self.ajouter_un_onglet()
			
	
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
		
	def initialisation_raccourcis(self):
		raccourcis = (
			('<Control>W', lambda *e: self.fermer_onglet()),
			('<Control>T', lambda *e: self.ajouter_un_onglet()),
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
						self.ajouter_un_onglet()
						for track_id in queues[key]:
							self.ajouter_selection(bdd.get_tracks_data({'track_ID':track_id}))
					else:
						playlist = self.ajouter_un_onglet(key)
						for track_id in queues[key]:
							self.ajouter_selection(bdd.get_tracks_data({'track_ID':track_id}))
						playlist.Liste.connect("row-changed", playlist.setModified)
			else:
				self.ajouter_un_onglet()
		a = threading.Thread(target=traiter_queues)
		a.start()
		
		
	def marquer_piste(self):#Ajoute un marqueur (pour la piste courante de la liste jouée)
		icon = gtk.gdk.pixbuf_new_from_file('track.png')
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
			


class Queue(gtk.ScrolledWindow):
	'''
		Représente une queue (onglet) d'un gestionnaire de queue.
	'''
	def __init__(self, gestionnaire, label):
		self.modified = False #pour les playlists enregistrées
		self.gestionnaire = gestionnaire
		#police, icon_playing, icon_stopping, ID, path, titre, album, artiste, length, count, pixbuf_note, note, bridge_src key
		self.Liste = gtk.ListStore(str, gtk.gdk.Pixbuf, gtk.gdk.Pixbuf, int, str, str, str, str, str, int, gtk.gdk.Pixbuf, int, str)
		self.TreeView = gtk.TreeView(self.Liste)
		self.TreeView.set_rules_hint(True)
		self.TreeView.set_reorderable(True)
		self.TreeView.connect("row-activated", gestionnaire.on_zik_click)
		self.TreeView.connect("button-press-event", self.surClicDroit)
		self.TreeView.connect("key-press-event", self.executerRaccourci)
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
		close_button.connect('clicked', gestionnaire.fermer_onglet, self)
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

		
		
		cols = [Col_Titre, Col_Artiste, Col_Album, Col_Count, Col_Note]
		
		for col in cols:
			col.connect('clicked', self.on_column_clicked)
		
		
		#Col_Titre.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
		#Col_Titre.set_fixed_width(40)
		
		messager.inscrire(self.refresh_view, 'track_data_changed')
		
		
		gtk.ScrolledWindow.__init__(self)
		self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.add(self.TreeView)
		gestionnaire.append_page(self, tab_label_box)
		gestionnaire.show_all()
		
                  
	def enlever_piste(self, button, ligne):
		self.Liste.remove(ligne)
	
		
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
			#self.NB.ajouter_un_onglet()
		
		
		
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
		
		# On vérifie que c'est bien un clic droit:
		if event.button == 3:
			path = TreeView.get_path_at_pos(int(event.x),int(event.y))[0]
			if(path != None):
				queue = TreeView.get_model()
				piste_ID = queue[path][3]
				ligne = queue.get_iter(path)
			if (path != None):
				iter = queue.get_iter(path)
				
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
				i.connect('activate', self.gestionnaire.addToDirectList, queue, ligne)
				m.append(i)
				
				#image = icons.MANAGER.pixbuf_from_text(str(len(self.directList)), (18, 18), '#FFCC00', '#000', '#000')
				#image = icons.MANAGER.pixbuf_from_text(str(len(self.directList)), (18, 18))
				i = gtk.ImageMenuItem(_("Add to temp jump list"))
				i.set_image(gtk.image_new_from_pixbuf(icons.MANAGER.pixbuf_from_text(str(len(self.gestionnaire.directList)), (18, 18), '#FFCC00', '#000', '#000')))
				i.connect('activate', self.gestionnaire.addToDirectList, queue, ligne, True)
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
				piste_ID = queue[path][3]
				ligne = queue.get_iter(path)
			self.gestionnaire.addToDirectList(None, queue, ligne, True)
				

class Playlist(Queue):
	def __init__(self, gestionnaire, label):
		Queue.__init__(self, gestionnaire, label)
		print('OH YEAH')
		
	def setModified(self, model, path, i):
		if(self.modified == False):
			self.modified = True
			self.tab_label.set_text('*' + self.tab_label.get_text())
			

class DirectIter():
	'''
		Représente une piste qui sera lue en priorité
	'''
	def __init__(self, queue, ligne, temp=False):
		self.queue = queue
		self.ligne = ligne
		self.temp = temp



	
	
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


