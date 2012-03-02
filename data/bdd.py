# -*- coding: utf-8 -*-
import sqlite3
import os
from urllib import urlretrieve
from PIL import Image
from mutagen.easyid3 import EasyID3
from mutagen.oggvorbis import OggVorbis
from mutagen.mp3 import MP3
import gtk
import subprocess
from common import messager, settings, util, xdg
import threading
import time
from datetime import datetime
import elements
import unicodedata
import logging
from pylast import LastFMNetwork, NetworkError, WSError, md5


logger = logging.getLogger(__name__)


class BDD():
	def __init__(self):
		db_path = os.path.join(xdg.get_data_home(), 'data.db')
		if os.path.exists(db_path):
			self.conn = sqlite3.connect(db_path)
			self.conn.row_factory = sqlite3.Row
			self.c = self.conn.cursor()
		#else:
			#self.conn = sqlite3.connect('data.db')
			#self.conn.row_factory = sqlite3.Row
			#self.c = self.conn.cursor()
			#self.creer_tables()
			#self.scanner_dossier("/media/NOLIMIT")
	
	def execute_and_return(self, query):
		self.c.execute(query)
		row = self.c.fetchone()
		return row
		
	def execute(self, query, t=None):
		if(t != None):
			self.c.execute(query, t)
		else:
			self.c.execute(query)
		logger.debug(query)
		self.conn.commit()
	
	def execute_with_filters(self, query, section, params=[]):
		filters = settings.get_option(section + '/filters', {})
			
		for key in filters.iterkeys():
			if filters[key]['enabled']:
				try:
					where += ' OR '
				except NameError:
					where = 'WHERE '
				for t in filters[key]['criterions']:
					try:
						filter += filters[key]['link'] + t[0] + t[1] + '? '
					except NameError:
						filter = t[0] + t[1] + '? '
					params.append(t[2])
					
				where += '(' + filter + ')'
				del filter
		
		try:
			query += where
		except NameError:
			pass
		
		self.c.execute(query, params)

		
	def get_tracks(self, dic, filters={}):
		params = []
		for key in dic.iterkeys():
			try:
				query += ' AND ' + key + ' = ?'
			except NameError:
				query = 'SELECT track_ID FROM tracks WHERE ' + key + ' = ?'
			params.append(unicode(dic[key]))

			for t in filters['criterions']:
				query += ' ' + filters['link'] + t[0] + t[1] + '? '
				params.append(t[2])
		
		d = self.conn.cursor()
		d.execute(query, params)
		tracks = []
		for row in d:
			tracks.append(elements.Track(row[0]))
		return tracks
		
		
	def getTracks(self, dic):
		tracks = []
		tracksData = self.get_tracks_data(dic)
		for dataTuple in tracksData:
			tracks.append(elements.Track(dataTuple))
		return tracks
		
		
	def get_tracks_data(self, data):
		'''
			Créer une liste (tableau) de données sur les pistes correspondant aux critères passés en paramètre
			@param data : soit un dictionnaire (AND), soit une liste de dictionnaire (OU)
		'''
		t = []
		if type(data).__name__=='dict':
			for key in data.iterkeys():
				try:
					query += ' AND ' + key + ' = ?'
				except NameError:
					query = 'SELECT * FROM tracks WHERE ' + key + ' = ?'
				t.append(unicode(data[key]))
		else:
			for dic in data:
				try:
					query += ' OR ('
				except NameError:
					query = 'SELECT * FROM tracks WHERE ('
				for key in dic.iterkeys():
					try:
						part += ' AND ' + key + ' = ?'
					except NameError:
						part = key + ' = ?'
					t.append(unicode(dic[key]))
					
				query += part + ')'
				del part
				
				
		self.c.execute(query, t)
		table = []
		for row in self.c:
			table.append((row[0], row[1], row[2], row[3], row[4], row[6], row[7], row[8]))

		return table
		
	@staticmethod
	@util.threaded
	def initNetwork():
		BDD.network_is_connected = threading.Event()
		BDD.network_cache = []
		try:
			f = open(os.path.join(xdg.get_data_home(), 'network_cache.txt'), 'r')
			queue = f.readlines()
			f.close()
			for e in queue:
				BDD.network_cache.append(eval(e))
		except IOError:
			logger.debug("No network cache file")
		try:
			API_KEY = "04537e40b5501f85610cf4e4bbf1d97a" # this is a sample key
			API_SECRET = "b36376228a6e72314ffd503b8e3c9f5e"

			# In order to perform a write operation you need to authenticate yourself
			username = settings.get_option('music/audioscrobbler_login', '')
			password_hash = md5(settings.get_option('music/audioscrobbler_password', ''))

			BDD.network = LastFMNetwork(api_key = API_KEY, api_secret = 
			API_SECRET, username = username, password_hash = password_hash)
			logger.debug('Connection successfuly established with Last.fm')
			BDD.network_is_connected.set()
		except NetworkError:
			logger.debug('Connection to Last.fm failed')
			
	@staticmethod
	def saveCache():
		try:
			f = open(os.path.join(xdg.get_data_home(), 'network_cache.txt'), 'w')
			for e in BDD.network_cache:
				f.write(str(e) + "\n")
			f.close()
		except:
			logger.debug('Error saving scrobbling cache')


class MainBDD():
	"""
		A class used for utility purpose and GUI access to database
		TODO Optimiser l'analayse des nouveaux fichiers
		TODO centraliser une méthode pour chopper les elements avec filtres (cf retrieve, load, etc)
		TODO Merge MainBDD & BDD
		TODO Make a utility class (static)
	"""
	def __init__(self):
		db_path = os.path.join(xdg.get_data_home(), 'data.db')
		if os.path.exists(db_path):
			self.conn = sqlite3.connect(db_path)
			self.conn.row_factory = sqlite3.Row
			self.c = self.conn.cursor()
		else:
			self.conn = sqlite3.connect(db_path)
			self.conn.row_factory = sqlite3.Row
			self.c = self.conn.cursor()
			self.creer_tables()
			#self.scanner_dossier("/home/piccolo/Musique")
		
		xdg.make_missing_dirs()
		
		
			
			
		
		#BDD.initNetwork()
		#Abonnement à certains types de messages auprès du messager
		messager.inscrire(self.charger_playlist, 'ID_playlist')
		messager.inscrire(self.fill_library_browser, 'TS_bibliotheque')
		#messager.inscrire(self.remplir_liste_sections, 'liste_sections')
		messager.inscrire(self.get_tracks_data , 'need_tracks')
		messager.inscrire(self.get_track_data , 'queue_add_track')
		#messager.inscrire(self.get_data_of, 'need_data_of')
		messager.inscrire(self.add_file_in, 'fileIN')
		messager.inscrire(self.add_file_in, 'fileINuniverse', None, "univers_ID")
		messager.inscrire(self.ajouter_section, 'new_category', None, "categorie")
		messager.inscrire(self.ajouter_section, 'new_universe', None, "univers")
		messager.inscrire(self.create_intelligent_playlist, 'intelligent_playlist_request')
		
		print('BDD initialisée')
		
	

	def add_file_in(self, data):
		'''
		Détails paramètres : data[0] = type (~ table a modifier), data[1] = tableau contenant des ID, data[2] = nom champ conteneur (univers_ID ou categorie_ID), data[3] = valeur identifiant conteneur
		
		Ajoute les enregistrements dont l'ID est contenue dans le tableau data[1] au conteneur dont l'ID est contenu dans data[3]
		
		Les ID de sections étant des entiers pour tous les types de sections, une chaîne (type) est fournie en fonction du message reçu par la BDD
		'''
		##self.c.execute('INSERT INTO lien_IC VALUES (?, ?)', t) abandonné
		type = data[0]
		query = 'UPDATE ' + type +  's SET ' + data[2] + ' = ? WHERE ' + type + '_ID = ?'
		for ID in data[1]:
			t = (data[3], ID)
			self.c.execute(query, t)
		self.conn.commit()
		messager.diffuser("notification_etat", self, data[2] + " des " + type + "(s) modifié avec succès")
	


	
	def ajouter_section(self, data, type_section):
		'''
		Ajoute une nouvelle section (dont le libellé et le type sont passés en paramètres) pour un type de fichier
		'''
		type_fichier = data[0]
		libelle_section = data[1]
		parent_id = data[2]
		t = (unicode(libelle_section), parent_id,)
		query = "INSERT INTO " + type_section + "_" + type_fichier + "s (" + type_section + "_L, parent_ID) VALUES(?, ?)"
		#ex = INSERT INTO categorie_images (categorie_L) VALUES(?)
		self.c.execute(query, t)
		self.conn.commit()
		
		
	def charger_musiques(self, liste, selection):
		#Ajoute à la playlist les musiques séléctionnées dans le panel
		for track in selection:
			liste.append([track[1], track[0], "not set", "not set", '0'] )
			
	
	def create_intelligent_playlist(self, filter):
		'''
			Crée une requête pour séléctionner des pistes selon les paramètres envoyés
		'''
		params = []
		for t in filter['criterions']:
			try:
				query += ' ' + filter['link'] + t[0] + t[1] + '? '
			except NameError:
				query = 'SELECT * FROM tracks WHERE ' + t[0] + t[1] + '? '
			params.append(t[2])
		
		
		#COLLATE NOCASE'
		
		if(filter['random']):
			query += " ORDER BY RANDOM()"

		logger.debug(query)
		logger.debug(params)
		self.c.execute(query, params)
		table = []
		for row in self.c:
			table.append((row[0], row[1], row[2], row[3], row[4], row[6], row[7], row[8]))
		messager.diffuser('desPistes', self, table)
			
		
		
	def charger_playlist(self, data):
		ID_list = data[0] # data[1] = l'instance de queue
		# Charge une playlist
		table = []
		for ID in ID_list:
			table.append(self.get_track_data(int(ID)))
		messager.diffuser('desPistes', self, table, False)
		data[1].Liste.connect("row-changed", data[1].setModified)
	
	
	def check_for_new_files(self, folders, P_Bar):
		'''
			Méthode principale pour remplir la base
			- Est executée dans un thread secondaire
			@param dossier : le dossier père qui sera scanné
			@param P_Bar : la barre de progrès pour informer de l'état d'avancement du scan
			TODO walk + list (see Bluemindo)
			TODO use trigger to check existence - not needed with current process
			TODO PERF trick : essayer de checker l'existence avec un trigger mais sans récupérer les tags
			TODO prompter les fichiers mal nommés
		'''
		
		#Redéfinition d'une connexion puisque cette fonction tourne dans un thread secondaire :
		conn = sqlite3.connect(os.path.join(xdg.get_data_home(), 'data.db'))
		conn.row_factory = sqlite3.Row
		c = conn.cursor()
		
		recovered_paths = []
		error_paths = []
		
		def add_files(files):
			'''
				Ajoute des nouveaux fichiers à la BDD
				
				@param files : liste de tuples(type, dossier, fichier, extension)
				@param P_Bar : barre de progrès représentant l'avancement
			'''
			
			registered_paths = []
			c.execute('SELECT path FROM tracks')
			for row in c:
				registered_paths.append(row[0])
				
			c.execute('SELECT dossier, fichier, dossier FROM images')
			for row in c:
				registered_paths.append(row[0] + '/' + row[1])
				
			c.execute('SELECT dossier, fichier, dossier FROM videos')
			for row in c:
				registered_paths.append(row[0] + '/' + row[1])
			
			
			new_paths = list(set(recovered_paths) - set(registered_paths))
			
			new_files = {'music':[], 'image':[], 'video':[]}
			# *** REQUETE PARAMETREE AVEC CLAUSE IN -> for row in conn.execute('SELECT path FROM tracks WHERE path IN (%s)' % ("?," * len(tracks_path))[:-1], tracks_path):
			
			longueur = float(len(files['music_files']))
			P_Bar.set_fraction(0)
			i = 0
			for track in files['music_files']:
				path = track[0] + '/' + track[1]
				if(path in new_paths):
					new_files['music'].append(get_track_data(path, track[2]))
				i += 1
				P_Bar.set_fraction((float(i) / longueur))
			
			longueur = float(len(files['image_files']))
			P_Bar.set_fraction(0)
			i = 0
			for element in files['image_files']:
				path = element[0] + '/' + element[1]
				if(path in new_paths):
					new_files['image'].append(get_UC_element_data('image', element[0], element[1]))
				i += 1
				P_Bar.set_fraction((float(i) / longueur))
				
			longueur = float(len(files['video_files']))
			P_Bar.set_fraction(0)
			i = 0
			for element in files['video_files']:
				path = element[0] + '/' + element[1]
				if(path in new_paths):
					new_files['video'].append(get_UC_element_data('video', element[0], element[1]))
				i += 1
				P_Bar.set_fraction((float(i) / longueur))
				
			
			for section in new_files.iterkeys():
				if(section == 'music'):
					conn.executemany('INSERT INTO tracks (path, title, album, artist, genre, length, note, compteur, year) VALUES (?,?,?,?,?, ?, ?, ?, ?)', new_files[section])
				else:
					conn.executemany('INSERT INTO ' + section + 's (dossier, fichier, note, categorie_ID, univers_ID, size) VALUES (?, ?, ?, ?, ?, ?)', new_files[section])
			
			P_Bar.set_fraction(0)
			conn.commit()
				
		def get_UC_element_data(type, dossier, fichier):
			t = (unicode(dossier), unicode(fichier), 0, 1, 1, os.path.getsize(os.path.join(dossier, fichier)))
			return t
			
		
		def get_track_data(fichier, extension):
			if(extension == ".mp3"):
				try:
					audio = EasyID3(fichier)
				except:
						audio = "Unset"
			elif(extension == ".ogg"):
				try:
					audio = OggVorbis(fichier)
				except:
						audio = "Unset"
			try:
				#titre = unicode(audio['TIT2'])
				titre = audio['title'][0]
			except:
				titre = _("Unknown")
			
			try:
				#album = unicode(audio['TALB'])
				album = audio['album'][0]
			except:
				album = _("Unknown")
			try:
				#artiste = unicode(audio['TPE1'])
				artiste = audio['artist'][0]
			except:
				artiste = _("Unknown")
				
			try:
				genre = audio['genre'][0]
			except:
				genre = _("Unknown")
				
			try:
				year = audio['date'][0][0:4]
			except:
				year = _("Unknown")
			
			if(extension == ".mp3"):
				length = int(MP3(fichier).info.length)
			else:
				length =  int(audio.info.length)
			print fichier
			fichier = unicode(fichier)
			t = (fichier, titre, album, artiste, genre, length, 0, 0, year)
			#conn.execute('INSERT INTO tracks (path, title, album, artist, genre, length, note, compteur, year) VALUES (?,?,?,?,?, ?, ?, ?, ?)', t)
			return t
			
			
		def scanner_dossier(dossier, dig=False, files={'music_files':[], 'image_files':[], 'video_files':[]}):
			'''
				Scanne récursivement un dossier et ses sous-dossiers pour repérer les fichiers intéressants
				@param dossier : le dossier qui sera scanné
				@param files : un dictionnaire contenant des listes de tuples contenant les infos des nouveaux fichiers
			'''
			
			
			def add_new_CU(type, dossier, fichier, extension):
				try:
					t = (unicode(dossier), unicode(fichier))
					c.execute('SELECT COUNT(' + type + '_ID) FROM ' + type + 's WHERE dossier = ? AND fichier = ?', t)
					if(c.fetchone()[0] == 0): #Si le fichier n'est pas déjà dans la base
						files.append((type, dossier, fichier, extension))
				except UnicodeDecodeError:
					logger.debug('Fichier avec nom foireux : ' + dossier + fichier)
						
			def check_interest(dossier, fichier, extension):
				if extension == ".mp3" or extension == ".ogg":
					try:
						t = (unicode(dossier + "/" + fichier),)
						#c.execute('SELECT COUNT(track_ID) FROM tracks WHERE path = ?', t)
						#if(c.fetchone()[0] == 0): #Si le fichier n'est pas déjà dans la base
						files['music_files'].append((dossier, fichier, extension))
						recovered_paths.append(unicode(dossier + "/" + fichier))
					except UnicodeDecodeError:
						error_paths.append(dossier + '/' + fichier)
				elif extension == ".flv" or extension == ".mkv" or extension == ".avi":
					try :
						files['video_files'].append((dossier, fichier))
						recovered_paths.append(unicode(dossier + "/" + fichier))
					except UnicodeDecodeError:
						error_paths.append(dossier + '/' + fichier)
				elif extension in (".jpg", '.gif', ".png", ".bmp"):
					try :
						if(dossier != "thumbnails/images"): # *** A COMPLETER ***
							files['image_files'].append((dossier, fichier))
							recovered_paths.append(unicode(dossier + "/" + fichier))
					except UnicodeDecodeError:
						error_paths.append(dossier + '/' + fichier)
				#elif extension == '.pdf':
					#add_new_CU('document', dossier, fichier, extension)

			P_Bar.pulse()
			for f in os.listdir(dossier):
				if f[0] != ".":
					if os.path.isfile(os.path.join(dossier, f)):
						(shortname, extension) = os.path.splitext(f)
						check_interest(dossier, f, extension)
					else:
						if(dig):
							scanner_dossier(dossier + "/" + f, files)
			return (files)
		
		for folder in folders:
			new_files = scanner_dossier(folder[0], folder[1])
			add_files(new_files)
			
		for path in error_paths:
			logging.debug('Chemin foireux : ' + path)
			
		
	def creer_tables(self):
		'''
			Crée la base de données
		'''
		# ***** Musique *****
		self.c.execute('''CREATE TABLE tracks
		(track_ID INTEGER PRIMARY KEY AUTOINCREMENT, path text, title text, album text,
		artist text, genre text, length int, compteur int, note int, year text)''')
		
		
		self.c.execute('''CREATE TRIGGER insert_track BEFORE INSERT ON tracks
			FOR EACH ROW BEGIN
				SELECT  RAISE(IGNORE)
				WHERE (SELECT track_ID from tracks WHERE path = NEW.path) IS NOT NULL;
			END;''')
		
		
		# ***** Vidéos *****
		self.creer_tablesUC("video")
		
		
		# ***** Images *****
		self.creer_tablesUC("image")
		
		#self.c.execute('''CREATE TABLE lien_IC
		#(categorie_ID int, image_ID int, PRIMARY KEY(categorie_ID, image_ID))''')
		
		#self.creer_tablesUC("document")
		
	def creer_tablesUC(self, type):
		queries = []
		queries.append( 'CREATE TABLE univers_' + type + 's (univers_ID INTEGER PRIMARY KEY AUTOINCREMENT, univers_L text, parent_ID INTEGER DEFAULT 0, thumbnail_ID INTEGER DEFAULT 0)')
		
		queries.append('CREATE TABLE categorie_' + type + 's (categorie_ID INTEGER PRIMARY KEY AUTOINCREMENT, categorie_L text, parent_ID INTEGER DEFAULT 0, thumbnail_ID INTEGER DEFAULT 0)')
		
		queries.append( 'INSERT INTO categorie_' + type + 's VALUES(1, "Divers",0 , 0)')
		queries.append ( 'INSERT INTO univers_' + type + 's VALUES(1, "Divers", 0, 0)')
		
		query = 'CREATE TABLE ' + type + 's ('+ type + '_ID INTEGER PRIMARY KEY AUTOINCREMENT, dossier text, fichier text, note int, categorie_ID, univers_ID, size int,'
		query += 'FOREIGN KEY(categorie_ID) REFERENCES categorie_' + type + 's(categorie_ID),'
		query += 'FOREIGN KEY(univers_ID) REFERENCES univers_' + type + 's(univers_ID))'
		queries.append(query)
		for query in queries:
			self.c.execute(query)
		
		
	def fill_library_browser(self, data, e=None):
		'''
			Remplit la liste arborescente avec les pistes de la BDD selon l'arborescence du mode séléctionné
			
			@param data = [TreeStore, mode]
			@param e = threading event pour prévenir qu'on a fini
			TODO : ajouter le ratio d'écoutes par conteneur, qui s'applique uniquement sur les pistes notées
			ratio = total_ecoutes_conteneur / nb_pistes_notees_conteneur
		'''
		indices = {"title":2, "artist":4, "album":3, "genre":5, "note":8, "year":9}

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
			
		def traiter_conteneur(pere, niveau, ligne):
			'''
				@param ligne : la ligne à laquelle la fonction commence (intérêt de la localité de ce paramètre =  possibilité de threading)
				@param mot : le mot que doit contenir chaque noeud pour être présent
			'''
		
			if(niveau == profondeur_max): #Si on est au dernier niveau du mode d'affichage, c'est que c'est une piste
				#if(tracks[ligne][2].lower().find(mot) != -1):
				model.append(pere, [icon_track, tracks[ligne][0], tracks[ligne][2], 1, 1])
				#La ligne est traitée en intégralité, on passe à la suivante :
				i = ligne + 1

				
			else: #Il faut continuer de "creuser" et ajouter tous les fils de ce père
				icon = icons[mode[niveau]]
				elt = getValueOfLevel(tracks[ligne], niveau)
				#On ajoute le premier fils
				fils = model.append(pere, [icon, 1, getValueOfLevel(tracks[ligne], niveau), 1, 1])
				#Tant qu'il reste du monde et qu'on est toujours sur le même conteneur :
				while(ligne < len(tracks) and elt == getValueOfLevel(tracks[ligne], niveau)):
					#Si les deux lignes n'ont pas la même valeur sur ce niveau on ajoute la nouvelle ligne :
					if(ligne < len(tracks) and elt != getValueOfLevel(tracks[ligne], niveau)):
						fils = model.append(pere, [icon, 1, getValueOfLevel(tracks[ligne], niveau), 1, 1])
						elt = getValueOfLevel(tracks[ligne], niveau)
					#Même valeur sur ce niveau, donc on descend d'un et on répète le schéma
					else:
						ligne = traiter_conteneur(fils, niveau+1, ligne)
				#On a pas traité en intégralité cette ligne donc on reste dessus :
				i = ligne
			return i
				#On a enfin fini de boucler le premier père accroché à la racine, on passe donc au suivant si il y en a :
				#EN FAIT NON, C'EST FOIREUX :D
				#if(getValueOfLevel(tracks[ligne], niveau-1) != elt_pere):
					#traiter_conteneur(None, 0, None)
				
				
		
		model = data[0]
		mode = data[1]
		
		#cle = 0
		#for c in mode:
			#cle += ord(c)
			
		try:
			tracks = self.tracks[mode]
		except KeyError:
			self.loadTracks(mode)
			tracks = self.tracks[mode]
		
		icon_track = gtk.gdk.pixbuf_new_from_file('track.png')
		icon_artist = gtk.gdk.pixbuf_new_from_file('icons/artist.png')
		icon_album = gtk.Image().render_icon(gtk.STOCK_CDROM, gtk.ICON_SIZE_MENU)
		icon_genre = gtk.gdk.pixbuf_new_from_file('icons/genre.png')
		icon_year = gtk.gdk.pixbuf_new_from_file('icons/year.png')
		icon_rating = gtk.gdk.pixbuf_new_from_file('icons/star.png')
		icons = {"title":icon_track, "artist":icon_artist, "album":icon_album, "genre":icon_genre, "note":icon_rating, "year":icon_year}
		mode = eval(mode)
		profondeur_max = len(mode) - 1
		
		model.clear()
		


			
			
		

		def traiter_tous_les_conteneurs():
			niveau = 0
			ligne = 0
			while(ligne < len(tracks)):
				ligne = traiter_conteneur(None, 0, ligne)
			if(e != None):
				e.set() #On a fini donc on prévient les autres threads qui nous attendaient
		a = threading.Thread(target=traiter_tous_les_conteneurs)
		a.start()
		

			
		#def traiter_conteneurs(conteneurs, pere, i, condition_antecedente=""):
			#conn = sqlite3.connect('data.db')
			#conn.row_factory = sqlite3.Row
			#c = conn.cursor()
			#if(i < profondeur_max): #Il faut encore "creuser"
				#for conteneur in conteneurs:
					##print("Traitement de " + mode[i])
					#pere_icon = gtk.gdk.pixbuf_new_from_file('icons/' + mode[i-1] + '.png')
					#query = 'SELECT DISTINCT ' + mode[i] + ', SUM(compteur), SUM(note) FROM tracks WHERE ' + mode[i-1] + ' = ?' + condition_antecedente + ' GROUP BY ' + mode[i] + ' ORDER BY ' + mode[i]
					#antecedent = condition_antecedente + ' AND ' + mode[i-1] + ' = "' + str(conteneur[0]) + '"'
					##print(query)
					
					#c.execute(query, (conteneur[0],))
					
					#conteneurs = c.fetchall()
					#fils = treestore.append(pere, [pere_icon, 0, conteneur[0], conteneur[1], conteneur[2]])
					##traiter_conteneurs(conteneurs, fils, i+1, antecedent)
					#a = threading.Thread(target=traiter_conteneurs, args=(conteneurs, fils, i+1, antecedent))
					#a.start()
					
			#else: #On est en bas de la "chaîne", il ne reste plus qu'à traiter les pistes du dernier conteneur
				#for conteneur in conteneurs:
					#fils = treestore.append(pere, [icon_album, 0, conteneur[0], conteneur[1], conteneur[2]])
					#c.execute('SELECT DISTINCT track_ID, title, compteur, note FROM tracks WHERE ' + mode[i-1] + ' = ?' + condition_antecedente +' ORDER BY title', (conteneur[0],))
					#for titre in c:
						#treestore.append(fils, [icon_track, titre[0], titre[1], titre[2], titre[3]])
				##Fin de branche
				#i += 1
		
		#treestore = data[0]
		#mode = eval(data[1])
		#print(mode)
		#profondeur_max = len(mode) -1
		#icon_track = gtk.gdk.pixbuf_new_from_file('track.png')
		#icon_artist = gtk.gdk.pixbuf_new_from_file('icons/artist.png')
		#icon_album = gtk.Image().render_icon(gtk.STOCK_CDROM, gtk.ICON_SIZE_MENU)
		#icon_genre = gtk.gdk.pixbuf_new_from_file('icons/genre.png')
		#icon_year = gtk.gdk.pixbuf_new_from_file('icons/year.png')
		
		#treestore.clear()
		
		## On traite les conteneurs de bases (ex : Artiste, Genre):
		#self.c.execute('SELECT DISTINCT ' + mode[0] + ', SUM(compteur), SUM(note) FROM tracks GROUP BY ' + mode[0] + ' ORDER BY ' + mode[0])
		#pere_icon = gtk.gdk.pixbuf_new_from_file('icons/' + mode[0] + '.png')
		#pere = None  #Un conteneur de base n'a pas de père
		#conteneurs = self.c.fetchall()
		#i = 1 #On se place sur le second niveau de conteneurs

		##traiter_conteneurs(conteneurs, pere, i)
		#a = threading.Thread(target=traiter_conteneurs, args=(conteneurs, pere, i))
		#a.start()
		
		return model
		
		
	def fill_library_browserBOURRIN(self, data):
		'''
			DEPRECATED Used way to much SQL queries
			Remplit la liste arborescente avec les pistes de la BDD selon l'arborescence du mode séléctionné
			
			data = [TreeStore, mode]
			
			Cette version a été abandonnée car elle utilise beaucoup trop de requêtes, ce qui est terrible au niveau des perfs.
		'''
		def traiter_conteneurs(conteneurs, pere, i, condition_antecedente=""):
			conn = sqlite3.connect('data.db')
			conn.row_factory = sqlite3.Row
			c = conn.cursor()
			if(i < profondeur_max): #Il faut encore "creuser"
				for conteneur in conteneurs:
					#print("Traitement de " + mode[i])
					pere_icon = gtk.gdk.pixbuf_new_from_file('icons/' + mode[i-1] + '.png')
					query = 'SELECT DISTINCT ' + mode[i] + ', SUM(compteur), SUM(note) FROM tracks WHERE ' + mode[i-1] + ' = ?' + condition_antecedente + ' GROUP BY ' + mode[i] + ' ORDER BY ' + mode[i]
					antecedent = condition_antecedente + ' AND ' + mode[i-1] + ' = "' + str(conteneur[0]) + '"'
					#print(query)
					
					c.execute(query, (conteneur[0],))
					
					conteneurs = c.fetchall()
					fils = treestore.append(pere, [pere_icon, 0, conteneur[0], conteneur[1], conteneur[2]])
					#traiter_conteneurs(conteneurs, fils, i+1, antecedent)
					a = threading.Thread(target=traiter_conteneurs, args=(conteneurs, fils, i+1, antecedent))
					a.start()
					
			else: #On est en bas de la "chaîne", il ne reste plus qu'à traiter les pistes du dernier conteneur
				for conteneur in conteneurs:
					fils = treestore.append(pere, [icon_album, 0, conteneur[0], conteneur[1], conteneur[2]])
					c.execute('SELECT DISTINCT track_ID, title, compteur, note FROM tracks WHERE ' + mode[i-1] + ' = ?' + condition_antecedente +' ORDER BY title', (conteneur[0],))
					for titre in c:
						treestore.append(fils, [icon_track, titre[0], titre[1], titre[2], titre[3]])
				#Fin de branche
				i += 1
		
		treestore = data[0]
		mode = eval(data[1])
		print(mode)
		profondeur_max = len(mode) -1
		icon_track = gtk.gdk.pixbuf_new_from_file('track.png')
		icon_artist = gtk.gdk.pixbuf_new_from_file('icons/artist.png')
		icon_album = gtk.Image().render_icon(gtk.STOCK_CDROM, gtk.ICON_SIZE_MENU)
		icon_genre = gtk.gdk.pixbuf_new_from_file('icons/genre.png')
		icon_year = gtk.gdk.pixbuf_new_from_file('icons/year.png')
		
		treestore.clear()
		
		# On traite les conteneurs de bases (ex : Artiste, Genre):
		self.c.execute('SELECT DISTINCT ' + mode[0] + ', SUM(compteur), SUM(note) FROM tracks GROUP BY ' + mode[0] + ' ORDER BY ' + mode[0])
		pere_icon = gtk.gdk.pixbuf_new_from_file('icons/' + mode[0] + '.png')
		pere = None  #Un conteneur de base n'a pas de père
		conteneurs = self.c.fetchall()
		i = 1 #On se place sur le second niveau de conteneurs

		#traiter_conteneurs(conteneurs, pere, i)
		a = threading.Thread(target=traiter_conteneurs, args=(conteneurs, pere, i))
		a.start()
		
		return treestore

			
			
		##Exemple : pour chaque album, on traite les pistes
		#for conteneur in conteneurs:
			#fils = treestore.append(pere, [icon_album, 0, conteneur[0]])
			#self.c.execute('SELECT DISTINCT track_ID, title FROM tracks WHERE ' + mode[i-1] + ' = ? ORDER BY title', (conteneur[0],))
			#for titre in self.c:
				#treestore.append(fils, [icon_track, titre[0], titre[1]])
					
					
		#elif(mode == "Album"):
			#self.c.execute('SELECT DISTINCT album FROM tracks ORDER BY album')
			#for album in self.c:
				#pere = treestore.append(None, [icon_album, 0, album[0]])
				#d = self.conn.cursor()
				#d.execute('SELECT DISTINCT track_ID, title FROM tracks WHERE album = ? ORDER BY title', (album[0],))
				#for titre in d:
						#treestore.append(pere, [icon_track, titre[0], titre[1]])
		#elif(mode == "Genre"):
			#self.c.execute('SELECT DISTINCT genre FROM tracks ORDER BY genre')
			##Pour chaque genre, on traite les albums
			#for genre in self.c:
				#pere = treestore.append(None, [icon_genre, 0, genre[0]])
				#d = self.conn.cursor()
				#d.execute('SELECT DISTINCT artist FROM tracks WHERE genre = ? ORDER BY album', (genre[0],))
				##Pour chaque artiste, on traite les albums
				#for artist in d:
					#fils = treestore.append(pere, [icon_artist, 0, artist[0]])
					#e = self.conn.cursor()
					#e.execute('SELECT DISTINCT album FROM tracks WHERE artist = ? ORDER BY album', (artist[0],))
					#for album in e:
						#petit_fils = treestore.append(fils, [icon_album, 0, album[0]])
						#f = self.conn.cursor()
						#f.execute('SELECT DISTINCT track_ID, title FROM tracks WHERE album = ? ORDER BY title', (album[0],))
						#for titre in f:
							#treestore.append(petit_fils, [icon_track, titre[0], titre[1]])
		#elif(mode == "Année"):
			#self.c.execute('SELECT DISTINCT year FROM tracks ORDER BY year')
			#for year in self.c:
				#pere = treestore.append(None, [icon_year, 0, year[0]])

	
			
	def get_data_of(self, data):
		'''
			Séléctionne toutes les infos sur les fichiers du type donné (image ou video) et appartenant à la section data[1] (categorie_ID, univers_ID, dossier)
			
			Data[0] contient le type de données et définit donc les tables sur lesquelles on va s'appuyer
			Data[1] contient une chaîne permettant de savoir quelle(s) section(s) est (sont) visée(s)
		'''
		type = data[0]
		mode = data[1] # category, universe, category_and_universe or folder
		critere = data[2] # category_ID, universe_ID or folder path
		dig = True
		
		t = []
		
		query = "SELECT " + type + "_ID, fichier, dossier, note, categorie_ID, univers_ID FROM " + type + "s "

		def dig_in(ID, query):
			for c_ID in self.categories[ID]:
				query += ' OR categorie_ID = ?'
				t.append(c_ID)
				dig_in(c_ID, query)
				
		
		
		
		if(mode == "dossier"):
			t = (unicode(critere),)
			query += "WHERE dossier = ? ORDER BY fichier"
		elif(mode == "category"):
			t.append(int(critere))
			query += "WHERE categorie_ID = ?"
			if(dig is True):
				dig_in(int(critere), query)
			query += " ORDER BY fichier"
		elif(mode == "universe"):
			t = (int(critere),)
			query += "WHERE univers_ID = ? ORDER BY fichier"
		elif(mode == "category_and_universe"):
			universe_ID = data[3]
			t = (int(critere), universe_ID,)
			query += "WHERE categorie_ID = ? AND univers_ID = ? ORDER BY fichier"
		else:
			t = (unicode(critere),)
			query += "ORDER BY fichier"
			
		self.c.execute(query, t)
		table = []
		for row in self.c:
			path = unicode(row[2] + "/" + row[1])
			print(path)
			ID = str(row[0])
			thumbnail_path = "thumbnails/" + type + "s/" + ID + ".jpg"
			if not os.path.exists(thumbnail_path):
				if(type == "image"):
					im = Image.open(path)
					im.thumbnail((128, 128), Image.ANTIALIAS)
					im.save(thumbnail_path, "JPEG")
				elif(type == "video"):
					cmd = ['totem-video-thumbnailer', path, thumbnail_path]
					ret = subprocess.call(cmd)
				else:
					thumbnail_path = "thumbnails/none.jpg"
					
			#if os.path.exists(thumbnail_path):
				#thumbnail = gtk.gdk.pixbuf_new_from_file(thumbnail_path)
			#else:
			thumbnail = gtk.gdk.pixbuf_new_from_file(thumbnail_path)
			#On veut : ID, chemin, libellé,  apperçu, note, categorie_ID, univers_ID
			table.append((row[0], path, row[1], thumbnail, row[3], row[4], row[5]))
		logger.debug(query)
		messager.diffuser("des_" + type +"s", self, table)
		return table
		
	
	def getTracks(self, dic):
		tracks = []
		tracksData = self.get_tracks_data(dic, False)
		for dataTuple in tracksData:
			tracks.append(elements.Track(dataTuple))
		return tracks
		
	def get_track_data(self, track_ID):
	#Renvoie un tableau contentant les informations de la piste dont l'ID est track_ID
		t = (track_ID,)
		self.c.execute('SELECT * FROM tracks WHERE track_ID = ?', t)
		for row in self.c:
			table = (row[0], row[1], row[2], row[3], row[4], row[6], row[7], row[8])
		#messager.diffuser('desPistes', self, table)
		return table
	
	def get_tracks_data(self, data, send_message=True):
		'''
			Créer une liste (tableau) de données sur les pistes correspondant aux critères passés en paramètre
			@param data : soit un dictionnaire (AND), soit une liste de dictionnaire (OU)
			@param send_message : si vrai envoie un message avec le résultat, si faux retourne directement le résultat
		'''
		t = []
		if type(data).__name__=='dict':
			for key in data.iterkeys():
				try:
					query += ' AND ' + key + ' = ?'
				except NameError:
					query = 'SELECT * FROM tracks WHERE ' + key + ' = ?'
				t.append(unicode(data[key]))
		else:
			for dic in data:
				try:
					query += ' OR ('
				except NameError:
					query = 'SELECT * FROM tracks WHERE ('
				for key in dic.iterkeys():
					try:
						part += ' AND ' + key + ' = ?'
					except NameError:
						part = key + ' = ?'
					t.append(unicode(dic[key]))
					
				query += part + ')'
				del part
				
				
		print(query)
		self.c.execute(query, t)
		table = []
		for row in self.c:
			table.append((row[0], row[1], row[2], row[3], row[4], row[6], row[7], row[8]))
		if(send_message):
			messager.diffuser('desPistes', self, table)
		else:
			return table
		
	#def get_tracks_data(self, data):
		#if type(data).__name__=='dict':
			#for key in data.iterkeys():
				#try:
					#query += ' AND ' + key + ' = "' + data[key] + '"'
				#except NameError:
					#query = 'SELECT * FROM tracks WHERE ' + key + ' = "' + data[key] + '"'
		#else:
			#for dic in data:
				#try:
					#query += ' OR ('
				#except NameError:
					#query = 'SELECT * FROM tracks WHERE ('
				#for key in dic.iterkeys():
					#try:
						#part += ' AND ' + key + ' = "' + dic[key] + '"'
					#except NameError:
						#part = key + ' = "' + dic[key] + '"'
					
				#query += part + ')'
				#del part
				
				
		#print(query)
		#self.c.execute(query)
		#table = []
		#for row in self.c:
			#table.append((row[0], row[1], row[2], row[3], row[4], row[6], row[7], row[8]))
		#messager.diffuser('desPistes', self, table)
			
	#def get_album_data(self, album):
		#t = (album,)
		#self.c.execute('SELECT * FROM tracks WHERE album = ?', t)
		#table = []
		#for row in self.c:
			#table.append((row[0], row[1], row[2], row[3], row[4], row[6], row[7], row[8]))
		#messager.diffuser('desPistes', self, table)
		
	#def get_artiste_data(self, artiste):
		#t = (artiste,)
		#table = []
		#self.c.execute('SELECT * FROM tracks WHERE artist = ?', t)
		#for row in self.c:
			#table.append((row[0], row[1], row[2], row[3], row[4], row[6], row[7], row[8]))
		##On envoie la séléction au queue_manager
		#messager.diffuser('desPistes', self, table)
		
	#def incrementer(self, track):
		#""" Increment track playcount and scrobble the play"""
		#t = (track.ID,)
		#self.c.execute('UPDATE tracks SET compteur = compteur + 1 WHERE track_ID = ?', t)
		#self.conn.commit()
		
		#def scrobble(track):
			#time_elapsed = int( time.mktime( datetime.utcnow().timetuple())) - track.time_started
			#if(time_elapsed > 120):
				#try:
					#BDD.network.scrobble(track.artist, track.title, int(track.time_started))
					#if len(self.network_cache) > 0:
						#for tup in self.network_cache:
							#BDD.network.scrobble(tup[0], tup[1], tup[2])
						#self.network_cache = []
					#self.quit() # update cache
				#except:
					#self.network_cache.append((track.artist, track.title, int(track.time_started)))
					
		#task = threading.Thread(target=scrobble, args=(track,))
		#task.start()
		
		
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
		
	
	def loadTracks(self, mode):
		'''
			Charge les données de toutes les pistes selon une structure donnée
		'''

		query = 'SELECT * FROM tracks '
		
		filters = settings.get_option('music/filters', {})
		params = []

		for key in filters.iterkeys():
					if filters[key]['enabled']:
						try:
							where += ' OR '
						except NameError:
							where = 'WHERE '
						for t in filters[key]['criterions']:
							try:
								filter += filters[key]['link'] + t[0] + t[1] + '? '
							except NameError:
								filter = t[0] + t[1] + '? '
							params.append(t[2])
							
						where += '(' + filter + ')'
						del filter

		try:
			query += where
		except NameError:
			pass
		query += ' ORDER BY ';
		liste = eval(mode)
		for e in liste:
			query += e + ', '
		print(query)
		self.c.execute(query[:-2], params)
		return self.c.fetchall()
		
		
		
	def modifier_note(self, data):
		"""
			DEPRECATED now handled in elements objects
		"""
		# data = [type, ID, note]
		type_cible = data[0]
		t = (data[2], data[1],)
		if(type_cible == "image"):
			self.c.execute('UPDATE images SET note = ? WHERE image_ID = ?', t)
		elif(type_cible == "track"):
			self.c.execute('UPDATE tracks SET note = ? WHERE track_ID = ?', t)
		elif(type_cible == "video"):
			self.c.execute('UPDATE videos SET note = ? WHERE video_ID = ?', t)
		self.conn.commit()
	
	def quit(self):
		f = open(os.path.join(xdg.get_data_home(), 'network_cache.txt'), 'w')
		for e in BDD.network_cache:
			f.write(str(e) + "\n")
		f.close()
	
	@util.threaded
	def reloadCovers(self, *args):
		forceReload = False
		artist_dir = xdg.get_thumbnail_dir('artist')
		album_dir = xdg.get_thumbnail_dir('album')
		
		
		if(BDD.network_is_connected.isSet()):
			bdd = BDD()
			
			bdd.execute_with_filters('SELECT DISTINCT artist, album FROM tracks ', 'music')
			
			rows = bdd.c.fetchall()
			length = float(len(rows))
			
			i = 0
			while(i < len(rows)):
				artist_name = rows[i][0]
				dest_path = os.path.join(artist_dir + '/medium', artist_name.replace ('/', ' ')) # + '.jpg')
				if(forceReload or not os.path.isfile(dest_path)):
					artist = BDD.network.get_artist(artist_name)
					cover = artist.get_cover_image(1)
					os.path
					
					if(cover is not None):
						#extension = os.path.splitext(f)[1]
						urlretrieve(cover, dest_path)
					else:
						logger.debug('No cover url for artist ' + artist_name)
				
				while(i < len(rows) and artist_name == rows[i][0]):
					album_name = rows[i][1]
					dest_path = os.path.join(album_dir + '/medium', album_name.replace ('/', ' ')) # + '.jpg')
					if(forceReload or not os.path.isfile(dest_path)):
						try:
							album = BDD.network.get_album(artist_name, album_name)
							cover = album.get_cover_image(1)
						except WSError:
							logger.debug('Error : No album ' + album_name)
						
						if(cover is not None):
							urlretrieve(cover, dest_path)
						else:
							logger.debug('No cover url for album ' + album_name)
					i += 1

		else:
			logger.debug("Can't retrieve covers : Network not connected")
	
			
			

	def retrieveFromLastFMOLD(self, P_Bar):
		"""
			DEPRECATED
			TODO? Other account support?
			TODO? Compte-rendu
			TODO? Album optionnel ou noté ***
		"""
		def process():
			bdd = BDD()
			account = settings.get_option('music/audioscrobbler_login', None)
			if account is not None:
				
				library = BDD.network.get_user("Maitre_Piccolo").get_library()
				
				query = 'SELECT DISTINCT artist, album FROM tracks '
				
				filters = settings.get_option('music/filters', {})
				params = []

				for key in filters.iterkeys():
					if filters[key]['enabled']:
						try:
							where += ' OR '
						except NameError:
							where = 'WHERE '
						for t in filters[key]['criterions']:
							try:
								filter += filters[key]['link'] + t[0] + t[1] + '? '
							except NameError:
								filter = t[0] + t[1] + '? '
							params.append(t[2])
							
						where += '(' + filter + ')'
						del filter
				
				try:
					query += where
				except NameError:
					pass
				
				bdd.c.execute(query, params) 
				couples = bdd.c.fetchall()
				length = float(len(couples))
				nb_errors = 0
				i = 0
				P_Bar.set_fraction(i)
				
				for row in couples:
					try:
						tracks = library.get_tracks(row[0], row[1])
						#if tracks empty check with only artist
						d = bdd.conn.cursor()
						for track in tracks:
							title = track.item.get_title()
							bdd.c.execute('SELECT COUNT(title) FROM tracks WHERE artist = ? AND title = ? COLLATE NOCASE', (row[0], title))
							matchingTracksCount = bdd.c.fetchone()[0]
							if( matchingTracksCount == 1): #We assume it's the good one (useful if the album is somthing like "Greatest Hits", etc...)
								t = (track.playcount, row[0], title)
								d.execute('UPDATE tracks SET compteur = ? WHERE artist = ? AND title = ? COLLATE NOCASE', t)
							elif(matchingTracksCount > 1): #In doubt, we update only the ones with matching album
								t = (track.playcount, row[0], row[1], title)
								d.execute('UPDATE tracks SET compteur = ? WHERE artist = ? AND album = ? AND title = ? COLLATE NOCASE', t)
						i += 1
						P_Bar.set_fraction(float(i) / length)
					except WSError:
						logger.debug('Error with artist ' + row[0] + ' and album ' + row[1])
						nb_errors += 1
						P_Bar.set_text(str(nb_errors) + ' ' + _('errors'))
				
				bdd.conn.commit()
				P_Bar.set_text( _('Sync ended with') + ' ' + str(nb_errors) + _('errors'))
				
		task = threading.Thread(target=process)
		task.start()
	
	def retrieveFromLastFM(self, P_Bar):
		"""
			TODO? Other account support?
			TODO? Compte-rendu
			TODO? Album optionnel ou noté ***
		"""
		def process():
			bdd = BDD()
			account = settings.get_option('music/audioscrobbler_login', None)
			if account is not None:
				
				library = BDD.network.get_user("Maitre_Piccolo").get_library()
				
				bdd.execute_with_filters('SELECT DISTINCT artist FROM tracks ', 'music')
				artists = bdd.c.fetchall()
				
				bdd.execute_with_filters('SELECT COUNT(DISTINCT artist, album) FROM tracks ', 'music')
				length = float(len(bdd.c.fetchone()[0]))
				nb_errors = 0
				i = 0
				P_Bar.set_fraction(i)
				
				for artist in artists:
					try:
						albums = library.get_albums(artist[0])
						#if tracks empty check with only artist
						d = bdd.conn.cursor()
						for album in albums:
							album_title = album.item.get_title()
							
							tracks = library.get_tracks(artist[0], album_title)
							for track in tracks:
								title = track.item.get_title()
								bdd.c.execute('SELECT COUNT(title) FROM tracks WHERE artist = ? AND album != ? COLLATE NOCASE AND title = ? COLLATE NOCASE', (artist[0], album_title, title))
								#Ex : ZZ Top -> Eliminator -> Legs [Last.fm count 50][otherAlbumCount 0] and ZZ Top -> Greatest Hits -> Legs [Last.fm count 2][otherAlbumCount 1]
								# We don't want the second to erase the first BUT if we only have Greatest Hits we want the big score
								otherAlbumCount = bdd.c.fetchone()[0]
								
								if( otherAlbumCount > 0): #If song is in another album, we have to set the album
									t = (track.playcount, artist[0], album_title, title)
									d.execute('UPDATE tracks SET compteur = ? WHERE artist = ? AND album = ? COLLATE NOCASE AND title = ? COLLATE NOCASE', t)
								else: # There is no song with anoter album so we apply on all albums (useful if we have ONLY "Greatest Hits" album like, etc...)
									t = (track.playcount, artist[0], title)
									d.execute('UPDATE tracks SET compteur = ? WHERE artist = ? AND title = ? COLLATE NOCASE', t)
									
							i += 1
							P_Bar.set_fraction(float(i) / length)
					except WSError:
						logger.debug('Error with artist ' + artist[0] + ' and album ' + album_title)
						nb_errors += 1
						P_Bar.set_text(str(nb_errors) + ' ' + _('errors'))
				
				bdd.conn.commit()
				P_Bar.set_text( _('Sync ended with') + ' ' + str(nb_errors) + ' ' + _('errors'))
				
		task = threading.Thread(target=process)
		task.start()
		
	def retrieveFromSave(self, file_path, dic):
		query = ''
		params = []
		for param in dic['criterions']:
				query += ' AND ' + param[0] + param[1] + ' ? '
				params.append(param[2])

		conn = sqlite3.connect(file_path)
		conn.row_factory = sqlite3.Row
		c = conn.cursor()
		c.execute('SELECT artist, album, title, note, compteur FROM tracks')
		for row in c:
			t = [row[3], row[0], row[1], row[2]]
			t.extend(params)
			self.c.execute('UPDATE tracks SET note = ? WHERE artist = ? AND album = ? AND title = ?', t)