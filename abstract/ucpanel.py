# -*- coding: utf-8 -*-
import logging
import os
import subprocess

from common import messager, settings, util, xdg
from data.bdd import BDD
from data.elements import Container, SpecialElement

logger = logging.getLogger(__name__)

class UCPanelInterface(object):
	'''
		A base class inherited by both Qt & Gtk U(niverses)C(ategories)Panels classes
	'''
	def __init__(self, type):
		self.data_type = type
		#self.elementSelector = elementSelector
		self.categories = {}
		self.universes = {}
		
	def enqueue(self, parameters):
	
		bdd = BDD()
		mode = self.mode
		
		# DEPRECATED STUFF
		#level = len(i)
		#if(level == 2):
			#if(section == "universe"):
				#path_category = i[0]
				#ID_category = self.model[path_category][0]
				#messager.diffuser('need_data_of', self, [self.data_type, "category_and_universe", ID_category, ID])
			#elif(section == "category"):
				#path_universe = i[0]
				#ID_universe = self.model[path_universe][0]
				#messager.diffuser('need_data_of', self, [self.data_type, "category_and_universe", ID, ID_universe])
		#else: #level = 1
		#messager.diffuser('need_data_of', self, [self.data_type, section, ID])
		type = self.data_type
		#mode = data[1] # category, universe, category_and_universe or folder
		#critere = data[2] # category_ID, universe_ID or folder path
		
		#def fill_selector
		dig = True
		condition = ' = ? '
		
		t = []
		
		query = "SELECT " + type + "_ID, fichier, dossier, note, categorie_ID, univers_ID, size FROM " + type + "s "

		def dig_in(ID, query):
			for c_ID in dic[ID]['children']:
				query += ' OR ' + column + ' = ?'
				t.append(c_ID)
				dig_in(c_ID, query)
			return query

		
		
		if(mode == "folder"):
			dig = False
			condition = ' LIKE ? '
			column = 'dossier'
			#t = (unicode(critere),)
			#query += "WHERE dossier LIKE ? ORDER BY fichier"
		elif(mode == "category"):
			dic = self.categories
			column = 'categorie_ID'
		elif(mode == "universe"):
			dic = self.universes
			column = 'univers_ID'
			
		
		first = True
		if(parameters[column] != 0): #No need to process this if ID = 0, which means select all
			
			for param in parameters.iterkeys():
				t.append(parameters[param])
				print parameters[param]
				if(first == True):
					query += "WHERE (" + param + condition
					first = False
				else:
					query += ' AND ' + param + condition 
			if(dig is True and parameters[column] != 0): 
				query = dig_in(parameters[column], query)
			query += ')'
		
		# DELETE
		#print self.filters
		#for key in self.filters.iterkeys():
			#t.append(self.filters[key])
			#if(first == True):
				#query += "WHERE " + key + condition
				#first = False
			#else:
				#query += ' AND ' + key + condition 
		query += " ORDER BY fichier"
		
		
		#elif(mode == "category_and_universe"):
			#universe_ID = data[3]
			#t = (int(critere), universe_ID,)
			#query += "WHERE categorie_ID = ? AND univers_ID = ? ORDER BY fichier"
		#else:
			#t = (unicode(critere),)
			#query += "ORDER BY fichier"
		
		logger.debug(query)
		print(t)
		bdd.c.execute(query, t)
		#table = []
		thumbnail_dir = xdg.get_thumbnail_dir(self.data_type + '/128/')
		for row in bdd.c:
			path = unicode(row[2] + "/" + row[1])
			print(path)
			ID = str(row[0])
			thumbnail_path = thumbnail_dir + ID + ".jpg"
			
			if not os.path.exists(thumbnail_path):
				if(type == "image"):
					try:
						im = Image.open(path)
						im.thumbnail((128, 128), Image.ANTIALIAS)
						im.save(thumbnail_path, "JPEG")
					except IOError:
						thumbnail_path = 'icons/none.jpg'
						logger.debug('IOError on thumbnail ' + path)
				elif(type == "video"):
					if(os.path.isfile(path)):
						cmd = ['totem-video-thumbnailer', path, thumbnail_path]
						ret = subprocess.call(cmd)
					else:
						thumbnail_path = "thumbnails/none.jpg"
				else:
					thumbnail_path = "thumbnails/none.jpg"
					
			#if os.path.exists(thumbnail_path):
				#thumbnail = gtk.gdk.pixbuf_new_from_file(thumbnail_path)
			#else:
			# TODO thumbnail loading in selector class
			#try:
				#thumbnail = gtk.gdk.pixbuf_new_from_file(thumbnail_path)
			#except:
				#thumbnail = gtk.gdk.pixbuf_new_from_file("icons/none.jpg")
			#On veut : ID, chemin, libellé,  apperçu, note, categorie_ID, univers_ID
			#table.append((row[0], path, row[1], thumbnail, row[3], row[4], row[5]))
			#self.elementSelector.append_element((row[0], path, row[1], thumbnail, row[3], row[4], row[5]))
			self.elementSelector.append(SpecialElement(row, self.data_type, thumbnail_path))
			#glib.idle_add(self.elementSelector.append_element, (row[0], path, row[1], thumbnail, row[3], row[4], row[5]))
		
	
	def moveToUCStructure(self, *args):
		"""
			Move all indexed files to structured folders
		"""
		default_path = '/home/piccolo/Images/Bullseye/'
		mode = 'category'
		bdd = BDD()
		type = self.data_type
		
		show_antagonistic = True


		if(mode == 'category'):
			container = 'categorie'
			dic = self.categories
			antagonist = 'univers'
		elif(mode == 'universe'):
			container = 'univers'
			dic = self.universes
			antagonist = 'categorie'
		

		
		def processContainer(container_ID, root_path):
			print root_path
			query = 'SELECT ' + type + '_ID, dossier, fichier, size FROM ' + type + 's WHERE ' + container + '_ID = ?'
			if(show_antagonistic):
				query += ' AND ' + antagonist + '_ID = 1'
			bdd.c.execute(query, (container_ID,))
			directChildren = bdd.c.fetchall()
			for child in directChildren:
				new_name = child[2]
				if((child[1] + '/' + child[2]) != (root_path + '/' + new_name)): #Do not move if paths are the same
					i = 2
					same = False;
					while(os.path.isfile(root_path + '/' + new_name) and not same):
						if(not os.path.isfile(child[1] + '/' + child[2]) and os.path.getsize(root_path + '/' + new_name) != child[3]): # Same size, assume database is not up to date, so lets move on the same place thus the database will update correctly
							(shortname, extension) = os.path.splitext(child[2])
							new_name = shortname + '_' + str(i) + extension
							i += 1
						else:
							same = True
					logger.debug('OLD path -> ' + child[1] + '/' + child[2] + ' | NEW path -> ' + root_path + '/' + new_name)
					try:
						os.renames(child[1] + '/' + child[2], root_path + '/' + new_name)
					except OSError:
						pass
					bdd.c.execute('UPDATE ' + type + 's SET dossier = ?, fichier = ? WHERE ' + type + '_ID = ?', (root_path, new_name, child[0]))
			
			if(show_antagonistic): #Elements of this container which are antagonist-setted (if category -> universe, if universe->category) will be placed in a subfolder
				bdd.c.execute('SELECT t.' + type + '_ID, dossier, fichier, ' + antagonist + '_L, t.' + antagonist + '_ID FROM ' + type + 's t JOIN ' + antagonist + '_' + type + 's u ON t.' + antagonist + '_ID = u.' + antagonist + '_ID WHERE ' + container + '_ID = ? AND t.' + antagonist + '_ID != 1', (container_ID,))
				children = bdd.c.fetchall()
				for child in children:
					new_name = child[2]
					if((child[1] + '/' + child[2]) != (root_path + '/' + child[3] + '/' + new_name)): #move only if paths are different
						i = 2
						while(os.path.isfile(root_path + '/' + child[3] + '/' + new_name)):
							(shortname, extension) = os.path.splitext(child[2])
							new_name = shortname + '_' + str(i) + extension
							i += 1
						os.renames(child[1] + '/' + child[2], root_path + '/' + child[3] + '/' + new_name)
						bdd.c.execute('UPDATE ' + type + 's SET dossier = ?, fichier = ? WHERE ' + type + '_ID = ?', (root_path + '/' + child[3], new_name, child[0]))
			
			for subContainerID in dic[container_ID]['children']:
				bdd.c.execute('SELECT ' + container + '_L FROM ' + container + '_' + type + 's WHERE ' + container + '_ID = ?', (subContainerID,))
				label = bdd.c.fetchone()[0]
				processContainer(subContainerID, root_path + '/' + label)
		
		
		bdd.c.execute('SELECT ' + container +'_ID, ' + container + '_L FROM ' + container + '_' + type + 's WHERE parent_ID = 0')
		rootContainers = bdd.c.fetchall()
		
		for cont in rootContainers:
			processContainer(cont[0], default_path + cont[1])
			
		bdd.conn.commit()
		
		
	
	@util.threaded
	def processLoading(self, mode, liste, show_antagonistic=True):
		'''
			Remplit la liste fournie en fonction du type de données et du mode séléctionné
			TODO? pixbufs are repeated, maybe I should keep their addresses and reuse them 
				instead of using gtk.gdk.pixbuf_new_from_file_at_size every time
			TODO? Option to collapse expanded on new collapse
		'''

		bdd = BDD()
		type = self.data_type
		self.clear(liste)
		
		if(mode != 'folder'):
			if(mode == 'category'):
				container = 'categorie'
				dic = self.categories
				antagonist = 'univers'
			elif(mode == 'universe'):
				container = 'univers'
				dic = self.universes
				antagonist = 'categorie'
			
			bdd.c.execute('SELECT DISTINCT * FROM ' + container + '_' + type + 's ORDER BY parent_ID')
			containers = bdd.c.fetchall()
			nodes = {0:None}
			
			#  ID, letter, label, iconID
			self.append(liste, Container([0, _('All'), 0, 0], container, type), None)
			
			dic[0] = {'label':None, 'children':[], 'parent':-1}
			for cont in containers:
				pere = self.append(liste, Container(cont, container, type), nodes[cont[2]])
				nodes[cont[0]] = pere
				
				dic[cont[0]] = {'label':cont[1], 'children':[], 'parent':cont[2]}

				dic[cont[2]]['children'].append(cont[0])
				
				if(show_antagonistic):
					#Add matching antagonistic (if category universe, if universe category) to node
					query = 'SELECT DISTINCT t.' + antagonist + '_ID, ' + antagonist + '_L, parent_ID, thumbnail_ID FROM ' + type + 's t JOIN ' + antagonist + '_' + type + 's u ON t.' + antagonist + '_ID = u.' + antagonist + '_ID WHERE ' + container + '_ID = ' + str(cont[0])
					for row in bdd.conn.execute(query):
						self.append(liste, Container(row, antagonist, type), pere)
			
			#elif(mode == "dossier"):
				#self.c.execute('SELECT DISTINCT dossier FROM ' + type + 's ORDER BY dossier')
				#for dossier in self.c:
					#path = dossier[0].rpartition('/')
					#liste.append([dossier[0], path[2]])
		else:
			def add_node(path):
				"""
					Add a folder node, and all parent folder nodes if needed
				"""
				parts = path.split('/')
				s = ''
				node = None
				for part in parts:
					s += part
					if(s not in nodes.keys()):
						nodes[s] = liste.append(node, [0, 'f' + s, part, icon, None, None])
					node = nodes[s]
					s += '/'
					
			icon = gtk.Image().render_icon(gtk.STOCK_DIRECTORY, gtk.ICON_SIZE_MENU)
			bdd.c.execute('SELECT DISTINCT dossier FROM ' + self.data_type + 's ORDER BY dossier')
			folders = bdd.c.fetchall()
			nodes = {}
			i = 0
			
			while(i < len(folders)):
				add_node(folders[i][0])
				i += 1