# -*- coding: utf-8 -*-
from common import messager, settings, util, xdg
from data.bdd import BDD
from data.elements import Container

class UCPanelInterface(object):
	'''
		A base class inherited by both Qt & Gtk U(niverses)C(ategories)Panels classes
	'''
	def __init__(self, type):
		self.data_type = type
		#self.elementSelector = elementSelector
		self.categories = {}
		self.universes = {}
		
	
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
			self.append(liste, None, Container([0, _('All'), 0, 0], container, type))
			
			dic[0] = {'label':None, 'children':[], 'parent':-1}
			for cont in containers:
				pere = self.append(liste, nodes[cont[2]], Container(cont, container, type))
				nodes[cont[0]] = pere
				
				dic[cont[0]] = {'label':cont[1], 'children':[], 'parent':cont[2]}

				dic[cont[2]]['children'].append(cont[0])
				
				if(show_antagonistic):
					#Add matching antagonistic (if category universe, if universe category) to node
					query = 'SELECT DISTINCT t.' + antagonist + '_ID, ' + antagonist + '_L, parent_ID, thumbnail_ID FROM ' + type + 's t JOIN ' + antagonist + '_' + type + 's u ON t.' + antagonist + '_ID = u.' + antagonist + '_ID WHERE ' + container + '_ID = ' + str(cont[0])
					for row in bdd.conn.execute(query):
						self.append(liste, pere, Container(row, antagonist, type))
			
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