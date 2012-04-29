# -*- coding: utf-8 -*-
import logging
import os
import subprocess

from PIL import Image

from common import messager, settings, util, xdg
from data.bdd import BDD
from data.elements import Container, SpecialElement

logger = logging.getLogger(__name__)

class UCPanelInterface(object):
	'''
		A base class inherited by both Qt & Gtk U(niverses)C(ategories)Panels classes
		It also acts as a utility class for a module providing methods such as moveToUCStructure, checkForDoubloons
	'''
	
	def __init__(self, module):
		self.module = module
		#self.elementSelector = elementSelector
		self.categories = {}
		self.universes = {}
		self.filters = {}
		self.THUMBNAIL_DIR = xdg.get_thumbnail_dir(self.module + os.sep + '128' + os.sep)
		
		
	def checkForDoubloons(self):
		module = self.module
		self.bdd = BDD()
		self.bdd.c.execute('SELECT ' + module + '_ID, filename, folder, rating, categorie_ID, univers_ID, size FROM ' + module + 's GROUP BY size HAVING COUNT(size) > 1;')
		table = []
		rows = self.bdd.c.fetchall()
		for row in rows:
			t = (row[6],)
			self.bdd.c.execute('SELECT ' + module + '_ID, filename, folder, rating, categorie_ID, univers_ID, size FROM ' + module + 's WHERE size = ?', t)
			for row in self.bdd.c:
				path = unicode(row[1] + "/" + row[2])
				ID = str(row[0])
				thumbnail_path = self.createThumbnail(ID, path)

				self.elementSelector.append(SpecialElement(row, self.module, thumbnail_path))
				
				
	def createThumbnail(self, ID, path):
		
		thumbnail_path = self.THUMBNAIL_DIR + ID + ".jpg"

		if not os.path.exists(thumbnail_path):
			if(self.module == "picture"):
				try:
					im = Image.open(path)
					im.thumbnail((128, 128), Image.ANTIALIAS)
					im.save(thumbnail_path, "JPEG")
				except IOError:
					thumbnail_path = 'icons/none.png'
					logger.debug('IOError on thumbnail ' + path)
			elif(self.module == "video"):
				if(os.path.isfile(path)):
					try:
						cmd = ['totem-video-thumbnailer', path, thumbnail_path]
						ret = subprocess.call(cmd)
					except:
						thumbnail_path = "icons/none.png"
				else:
					thumbnail_path = "icons/none.png"
			else:
				thumbnail_path = "icons/none.png"
		return thumbnail_path
		
		
	def enqueue(self, parameters, dig=True):
		'''
			@param parameters : a dict containing a container_ID
			@dig : tell if we also enqueue children containers of containers in parameters
		'''
		bdd = BDD()
		mode = self.mode

		# DEPRECATED STUFF
		#level = len(i)
		#if(level == 2):
			#if(section == "universe"):
				#path_category = i[0]
				#ID_category = self.model[path_category][0]
				#messager.diffuser('need_data_of', self, [self.module, "category_and_universe", ID_category, ID])
			#elif(section == "category"):
				#path_universe = i[0]
				#ID_universe = self.model[path_universe][0]
				#messager.diffuser('need_data_of', self, [self.module, "category_and_universe", ID, ID_universe])
		#else: #level = 1
		#messager.diffuser('need_data_of', self, [self.module, section, ID])
		type = self.module
		#mode = data[1] # category, universe, category_and_universe or folder
		#critere = data[2] # category_ID, universe_ID or folder path
		
		#def fill_selector

		condition = ' = ? '
		
		t = []
		
		query = "SELECT " + type + "_ID, filename, folder, rating, categorie_ID, univers_ID, size FROM " + type + "s "

		def dig_in(ID, query):
			for c_ID in dic[ID]['children']:
				query += ' OR ' + column + ' = ?'
				t.append(c_ID)
				dig_in(c_ID, query)
			return query

		
		
		if(mode == "folder"):
			dig = False
			condition = ' LIKE ? '
			column = 'folder'
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
		query += " ORDER BY filename"
		
		
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

		for row in bdd.c:
			ID = str(row[0])
			path = unicode(row[2] + "/" + row[1])
			thumbnail_path = self.createThumbnail(ID, path)

			self.elementSelector.append(SpecialElement(row, self.module, thumbnail_path))
			
			
	def filter(self, container):
		'''
			Used by Panes to filter antagonists panes with clicked pane selection
		'''
		backgroundColor = '#A9E2F3'
		mode = self.mode
		bdd = BDD()
		self.filters.clear()
		if(mode == 'category'):
			containerType = 'categorie'
			dic = self.universes
			antagonist = 'univers'
			model = self.universesModel
		elif(mode == 'universe'):
			containerType = 'univers'
			dic = self.categories
			antagonist = 'categorie'
			model = self.categoriesModel
		
		
		self.clear(model)
		nodes = {0:None}
		
		self.append(model, Container((0, _('All'), 0, 0), antagonist, self.module), None, backgroundColor)
		
		query = 'SELECT DISTINCT t.' + antagonist + '_ID, ' + antagonist + '_L, parent_ID, thumbnail_ID FROM ' + self.module + 's t JOIN ' + antagonist + '_' + self.module + 's u ON t.' + antagonist + '_ID = u.' + antagonist + '_ID '
		if(container.ID != 0):
			query += ' WHERE ' + containerType + '_ID = ' + str(container.ID)
			self.filters[containerType + '_ID'] = container.ID
		query += ' ORDER BY parent_ID'
		for row in bdd.conn.execute(query):

			try:
				nodes[row[0]] = self.append(model, Container(row, antagonist, self.module), nodes[row[2]], backgroundColor)
			except KeyError:
				# parent node missing
				parent = row[2]
				parents = []
				while(parent != 0):
					parents.append(parent)
					parent = dic[parent]['parent']
				
				parents.reverse() # Sort them in the right order
				for parent in parents:
					# TODO icon in dic (thumbnail_ID)
					if(parent not in nodes.keys()):
						nodes[parent] = self.append(model, Container((parent, dic[parent]['label'], dic[parent]['parent'], 0),  antagonist, self.module), nodes[dic[parent]['parent']])
				# Now we can add the node that caused the exception
				nodes[row[0]] = self.append(model, Container(row, antagonist, self.module), nodes[row[2]], backgroundColor)
				
		if mode != 'folder':
			self.loadFolders(self.folderModel, container)
		
	
	def moveToUCStructure(self, *args):
		"""
			Move all indexed files to structured folders
		"""
		default_path = '/home/piccolo/Images/Bullseye/'
		mode = 'category'
		bdd = BDD()
		type = self.module
		
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
			query = 'SELECT ' + type + '_ID, folder, filename, size FROM ' + type + 's WHERE ' + container + '_ID = ?'
			if(show_antagonistic):
				query += ' AND ' + antagonist + '_ID = 1'
			bdd.c.execute(query, (container_ID,))
			directChildren = bdd.c.fetchall()
			for child in directChildren:
				new_name = child[2]
				if((child[1] + os.sep + child[2]) != (root_path + os.sep + new_name)): #Do not move if paths are the same
					i = 2
					same = False;
					while(os.path.isfile(root_path + os.sep + new_name) and not same):
						if(not os.path.isfile(child[1] + os.sep + child[2]) and os.path.getsize(root_path + os.sep + new_name) != child[3]): # Same size, assume database is not up to date, so lets move on the same place thus the database will update correctly
							(shortname, extension) = os.path.splitext(child[2])
							new_name = shortname + '_' + str(i) + extension
							i += 1
						else:
							same = True
					logger.debug('OLD path -> ' + child[1] + os.sep + child[2] + ' | NEW path -> ' + root_path + os.sep + new_name)
					try:
						os.renames(child[1] + os.sep + child[2], root_path + os.sep + new_name)
					except OSError:
						pass
					bdd.c.execute('UPDATE ' + type + 's SET folder = ?, filename = ? WHERE ' + type + '_ID = ?', (root_path, new_name, child[0]))
			
			if(show_antagonistic): #Elements of this container which are antagonist-setted (if category -> universe, if universe->category) will be placed in a subfolder
				bdd.c.execute('SELECT t.' + type + '_ID, folder, filename, ' + antagonist + '_L, t.' + antagonist + '_ID FROM ' + type + 's t JOIN ' + antagonist + '_' + type + 's u ON t.' + antagonist + '_ID = u.' + antagonist + '_ID WHERE ' + container + '_ID = ? AND t.' + antagonist + '_ID != 1', (container_ID,))
				children = bdd.c.fetchall()
				for child in children:
					new_name = child[2]
					if((child[1] + os.sep + child[2]) != (root_path + os.sep + child[3] + os.sep + new_name)): #move only if paths are different
						i = 2
						while(os.path.isfile(root_path + os.sep + child[3] + os.sep + new_name)):
							(shortname, extension) = os.path.splitext(child[2])
							new_name = shortname + '_' + str(i) + extension
							i += 1
						os.renames(child[1] + os.sep + child[2], root_path + os.sep + child[3] + os.sep + new_name)

						bdd.c.execute('UPDATE ' + type + 's SET folder = ?, filename = ? WHERE ' + type + '_ID = ?', (root_path + os.sep + child[3], new_name, child[0]))
			
			for subContainerID in dic[container_ID]['children']:
				bdd.c.execute('SELECT ' + container + '_L FROM ' + container + '_' + type + 's WHERE ' + container + '_ID = ?', (subContainerID,))
				label = bdd.c.fetchone()[0]
				processContainer(subContainerID, root_path + os.sep + label)
		
		
		bdd.c.execute('SELECT ' + container +'_ID, ' + container + '_L FROM ' + container + '_' + type + 's WHERE parent_ID = 0')
		rootContainers = bdd.c.fetchall()
		
		for cont in rootContainers:
			processContainer(cont[0], default_path + cont[1])
			
		bdd.conn.commit()
		
		
	
	@util.threaded
	def processLoading(self, mode, liste, show_antagonistic=True, word=''):
		'''
			Remplit la liste fournie en fonction du type de données et du mode séléctionné
			TODO? pixbufs are repeated, maybe I should keep their addresses and reuse them 
				instead of using gtk.gdk.pixbuf_new_from_file_at_size every time
			TODO? Option to collapse expanded on new collapse
		'''

		bdd = BDD()
		type = self.module
		
		if(mode != 'folder'):
			self.clear(liste)
			if(mode == 'category'):
				container = 'categorie'
				dic = self.categories
				antagonist = 'univers'
			elif(mode == 'universe'):
				container = 'univers'
				dic = self.universes
				antagonist = 'categorie'
			
			bdd.c.execute('SELECT DISTINCT c.' + container + '_ID, ' + container + '_L, parent_ID, thumbnail_ID, \
					IFNULL(SUM(rating), 0) FROM ' + container + '_' + type + 's c LEFT JOIN ' + type + 's t \
					ON c.' + container + '_ID = t.' + container + '_ID \
					GROUP BY c.' + container + '_ID \
					ORDER BY parent_ID')
			containers = bdd.c.fetchall()
			nodes = {0:None}
			
			#  ID, letter, label, iconID
			if word == '':
				self.append(liste, Container([0, _('All'), 0, 0], container, type), None)
			
			addAll = set() # container id list
			selection = set()
			neededButMaybeNotPresent = set()
			dic[0] = {'label':None, 'children':[], 'parent':-1}
			
			# First we filter
			for cont in containers:
				if(cont[2] in addAll or cont[1].lower().find(word) != -1):
					addAll.add(cont[0])
					neededButMaybeNotPresent.add(cont[2])
					selection.add(cont[0])

				
			selection = selection.union(neededButMaybeNotPresent)


			expand = []
			for cont in containers:
				if cont[0] in selection:
					
					dic[cont[0]] = {'label':cont[1], 'children':[], 'parent':cont[2]}
					dic[cont[2]]['children'].append(cont[0])
					pere = self.append(liste, Container(cont, container, type), nodes[cont[2]])
					if nodes[cont[2]] != None:
						#FIXME Qt Code in abstract!
						nodes[cont[2]].container.rating += cont[4]
					
					if(show_antagonistic):
						#Add matching antagonistic (if category universe, if universe category) to node
						query = 'SELECT DISTINCT t.' + antagonist + '_ID, ' + antagonist + '_L, parent_ID, thumbnail_ID, IFNULL(SUM(rating), 0) \
						FROM ' + type + 's t JOIN ' + antagonist + '_' + type + 's u ON t.' + antagonist + '_ID = u.' + antagonist + '_ID \
						WHERE ' + container + '_ID = ' + str(cont[0]) + ' GROUP BY t.' + antagonist + '_ID'
						for row in bdd.conn.execute(query):
							self.append(liste, Container(row, antagonist, type), pere)
					
					if cont[0] not in addAll:
						expand.append(pere)
						
					nodes[cont[0]] = pere
			
			self.expand(mode, expand)
			#elif(mode == "dossier"):
				#self.c.execute('SELECT DISTINCT dossier FROM ' + type + 's ORDER BY dossier')
				#for dossier in self.c:
					#path = dossier[0].rpartition(os.sep)
					#liste.append([dossier[0], path[2]])
		else:
			self.loadFolders(liste)
				
				
	def loadFolders(self, liste, container=None):
		self.clear(liste)
		def add_node(path, rating):
			"""
				Add a folder node, and all parent folder nodes if needed
			"""
			parts = path.split(os.sep)
			s = ''
			node = None
			for part in parts:
				s += part
				if(s not in nodes.keys()):
					nodes[s] = self.append(liste, Container((s + '%', part, 0, 0, rating), 'folder', self.module), node, backgroundColor) #[0, 'f' + s, part, icon, None, None])
				node = nodes[s]
				s += os.sep
				
		#icon = gtk.Image().render_icon(gtk.STOCK_DIRECTORY, gtk.ICON_SIZE_MENU)
		query = 'SELECT DISTINCT folder, IFNULL(SUM(rating), 0) FROM ' + self.module + 's'
		if(container != None and container.ID != 0):
			backgroundColor = '#A9E2F3'
			query += ' WHERE ' + container.container_type + '_ID = ' + str(container.ID)
		else:
			backgroundColor = 'white'
		query += ' GROUP BY folder ORDER BY folder'
		
		bdd = BDD()
		bdd.c.execute(query)
		folders = bdd.c.fetchall()
		nodes = {}
		i = 0
		
		while(i < len(folders)):
			add_node(folders[i][0], folders[i][1])
			i += 1