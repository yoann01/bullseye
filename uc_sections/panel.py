# -*- coding: utf-8 -*-
import threading
import os
import logging
import gtk
import glib
import subprocess

from PIL import Image

from common import messager, settings, util, xdg
from data.bdd import BDD
from gui import menus

from abstract.ucpanel import UCPanelInterface



logger = logging.getLogger(__name__)

class AbstractPanel(UCPanelInterface):
	
	icon_universe = gtk.gdk.pixbuf_new_from_file('icons/genre.png')
	icon_category = gtk.gdk.pixbuf_new_from_file('icons/artist.png')
	icon_size = settings.get_option('pictures/panel_icon_size', 32)
	icon_category = icon_category.scale_simple(icon_size, icon_size, gtk.gdk.INTERP_BILINEAR)
	thumbnail_path = xdg.get_thumbnail_dir('image' + '/128/')
	
	"""
		Base class for all differents Gtk UC Panel implementations
		TODO multi-panneaux
		TODO rewrite folders management
		TODO? possibilité de linker un univers à une catégorie : dès qu'on set l'univers, la catégorie est automatiquement settée. EX : dès que univers Piccolo alors caté perso
		INFO Categorie = forme, univers = fond
	"""
	def __init__(self, module):
		UCPanelInterface.__init__(self, module)
	
	
	def append(self, model, parentNode, container):
		def get_icon(ID, default):
			if(ID != 0):
				try:
					icon_path = self.thumbnail_path + str(ID) + ".jpg"
					#icon = gtk.gdk.pixbuf_new_from_file(icon_path)
					#icon = icon.scale_simple(icon_size, icon_size, gtk.gdk.INTERP_BILINEAR)
					icon = gtk.gdk.pixbuf_new_from_file_at_size(icon_path, self.icon_size, self.icon_size)
				except:
					icon = default
			else:
				icon = default
			return icon
			
		node = model.append(parentNode, [container.ID, container.container_type[0], container.label, get_icon(container.thumbnail_ID, None), None, None])
		return node
		
	def clear(self, model):
		model.clear()
		
	#@util.threaded
	#def processLoading(self, mode, liste, show_antagonistic=True):
		#'''
			#Remplit la liste fournie en fonction du type de données et du mode séléctionné
			#TODO? pixbufs are repeated, maybe I should keep their addresses and reuse them 
				#instead of using gtk.gdk.pixbuf_new_from_file_at_size every time
			#TODO? Option to collapse expanded on new collapse
		#'''
		

		#bdd = BDD()
		#type = self.data_type
		#liste.clear()
		#if(mode != 'folder'):
			#icon_universe = gtk.gdk.pixbuf_new_from_file('icons/genre.png')
			#icon_category = gtk.gdk.pixbuf_new_from_file('icons/artist.png')
			#icon_size = settings.get_option('pictures/panel_icon_size', 32)
			#icon_category = icon_category.scale_simple(icon_size, icon_size, gtk.gdk.INTERP_BILINEAR)
			#thumbnail_path = xdg.get_thumbnail_dir(self.data_type + '/128/')
			
			#def get_icon(ID, default):
				#if(ID != 0):
					#try:
						#icon_path = thumbnail_path + str(ID) + ".jpg"
						##icon = gtk.gdk.pixbuf_new_from_file(icon_path)
						##icon = icon.scale_simple(icon_size, icon_size, gtk.gdk.INTERP_BILINEAR)
						#icon = gtk.gdk.pixbuf_new_from_file_at_size(icon_path, icon_size, icon_size)
					#except:
						#icon = default
				#else:
					#icon = default
				#return icon
	

			#if(mode == 'category'):
				#container = 'categorie'
				#dic = self.categories
				#default_icon = icon_category
				#default_antagonist_icon = icon_universe
				#antagonist = 'univers'
			#elif(mode == 'universe'):
				#container = 'univers'
				#dic = self.universes
				#default_icon = icon_universe
				#default_antagonist_icon = icon_category
				#antagonist = 'categorie'
			
			#bdd.c.execute('SELECT DISTINCT * FROM ' + container + '_' + type + 's ORDER BY parent_ID')
			#containers = bdd.c.fetchall()
			#nodes = {0:None}
			
			#liste.append(None, [0, container[0], _('All'), None, None, None])
			
			#dic[0] = {'label':None, 'children':[], 'parent':-1}
			#for cont in containers:
				#icon = get_icon(cont[3], default_icon)
				#pere = liste.append(nodes[cont[2]], [cont[0], container[0], cont[1], icon, None, None])
				#nodes[cont[0]] = pere
				
				#dic[cont[0]] = {'label':cont[1], 'children':[], 'parent':cont[2]}

				#dic[cont[2]]['children'].append(cont[0])
				
				#if(show_antagonistic):
					##Add matching antagonistic (if category universe, if universe category) to node
					#query = 'SELECT DISTINCT t.' + antagonist + '_ID, ' + antagonist + '_L, parent_ID, thumbnail_ID FROM ' + type + 's t JOIN ' + antagonist + '_' + type + 's u ON t.' + antagonist + '_ID = u.' + antagonist + '_ID WHERE ' + container + '_ID = ' + str(cont[0])
					#for row in bdd.conn.execute(query):
						#icon = get_icon(row[3], default_antagonist_icon)
						#liste.append(pere, [row[0], antagonist[0], row[1], icon, None, None])
			
			##elif(mode == "dossier"):
				##self.c.execute('SELECT DISTINCT dossier FROM ' + type + 's ORDER BY dossier')
				##for dossier in self.c:
					##path = dossier[0].rpartition('/')
					##liste.append([dossier[0], path[2]])
		#else:
			#def add_node(path):
				#"""
					#Add a folder node, and all parent folder nodes if needed
				#"""
				#parts = path.split('/')
				#s = ''
				#node = None
				#for part in parts:
					#s += part
					#if(s not in nodes.keys()):
						#nodes[s] = liste.append(node, [0, 'f' + s, part, icon, None, None])
					#node = nodes[s]
					#s += '/'
					
			#icon = gtk.Image().render_icon(gtk.STOCK_DIRECTORY, gtk.ICON_SIZE_MENU)
			#bdd.c.execute('SELECT DISTINCT dossier FROM ' + self.data_type + 's ORDER BY dossier')
			#folders = bdd.c.fetchall()
			#nodes = {}
			#i = 0
			
			#while(i < len(folders)):
				#add_node(folders[i][0])
				#i += 1
		
	@util.threaded
	def loadFolders(self):
		def get_parent(path, level):
			"""
				Ex get_parent('/home/piccolo/Downloads/Pictures/DBZ, 2) = /home/piccolo/Downloads
			"""
			parts = path.split('/')
			parent = ''
			for i in xrange(len(parts) - level):
				parent += parts[i] + '/'
				
			return parent[:-1] # remove last slash
			
		def add_node(path):
			"""
				Add a folder node, and all parent folder nodes if needed
			"""
			parts = path.split('/')
			s = ''
			node = None
			for part in parts:
				s += part + '/'
				if(s not in nodes.keys()):
					nodes[s] = self.liste_dossiers.append(node, [s, part])
				node = nodes[s]
		
		bdd = BDD()
		bdd.c.execute('SELECT DISTINCT dossier FROM ' + self.data_type + 's ORDER BY dossier')
		
		folders = bdd.c.fetchall()
		#i = 0
		#node = None
		#parent = ''
		nodes = {}
		i = 0
		#node = self.liste_dossiers.append(None, [folders[0][0], folders[0][0]])
		#parent = folders[0][0]
		
		
		while(i < len(folders)):
			#print parent
			#print folders[i][0]
			#print folders[i][0].find(parent)
			
			# Recherche du plus proche dossier parent
			#j = 0
			#while(get_parent(folders[i][0], j) != get_parent(parent, j)):
				#j += 1
			
			#print(get_parent(folders[i][0], j))
			#if(folders[i][0].find(parent) != -1):
				#self.liste_dossiers.append(node, [folders[i][0], folders[i][0]])
			#else:
				#parent = folders[i][0]
				#node = self.liste_dossiers.append(None, [folders[i][0], folders[i][0]])
			#while(i < len(folders) and folders[i][0].find(parent) != -1):
				#self.liste_dossiers.append(node, [folders[i][0], folders[i][0]])
				#i += 1
			#parent = folders[i][0]
			#node = self.liste_dossiers.append(node, [folders[i][0], folders[i][0]])
			
			add_node(folders[i][0])
			i += 1
		
	
				

	@util.threaded
	def on_container_click(self, w, i, c):
		'''
			Séléctionne toutes les infos sur les fichiers du type donné (image ou video) et appartenant au conteneur data[1] (categorie_ID, univers_ID, dossier)
			
			Data[0] contient le type de données et définit donc les tables sur lesquelles on va s'appuyer
			Data[1] contient une chaîne permettant de savoir quelle(s) section(s) est (sont) visée(s)
		'''
		#def process():
		bdd = BDD()
		parameters = self.what_is(i, w.get_model()) #section, ID
		mode = self.mode
		
		level = len(i)
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
		
		query = "SELECT " + type + "_ID, fichier, dossier, note, categorie_ID, univers_ID FROM " + type + "s "

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
			try:
				thumbnail = gtk.gdk.pixbuf_new_from_file(thumbnail_path)
			except:
				thumbnail = gtk.gdk.pixbuf_new_from_file("icons/none.jpg")
			#On veut : ID, chemin, libellé,  apperçu, note, categorie_ID, univers_ID
			#table.append((row[0], path, row[1], thumbnail, row[3], row[4], row[5]))
			#self.elementSelector.append_element((row[0], path, row[1], thumbnail, row[3], row[4], row[5]))
			glib.idle_add(self.elementSelector.append_element, (row[0], path, row[1], thumbnail, row[3], row[4], row[5]))
		
		#task = threading.Thread(target=process)
		#task.start()
		#messager.diffuser("des_" + type +"s", self, table)
		#return table	

	
	def changer_mode(self, CB):
		#messager.diffuser('liste_sections', CB, [self.data_type, CB.get_active_text(), self.model])
		self.load()
		
	
	def on_drag_data_receive(self, TreeView, drag_context, x, y, selection_data, info, timestamp):
		#fin d'un DND
		T_elements_ID = eval(selection_data.get_text()) # eval => permet de retransformer la chaîne de caractères en tableau
		numero_tuple = TreeView.get_dest_row_at_pos(x, y)[0]
		dic = self.what_is(numero_tuple, TreeView.get_model())
		
		for key in dic.iterkeys():
			messager.diffuser('fileIN', self, [self.data_type, T_elements_ID, key, dic[key]])

	
	def on_folder_activated(self, w, i, c):
		dossier = self.liste_dossiers[i][0]
		messager.diffuser("need_data_of", self, [self.data_type, "dossier", dossier])
		
	def on_folder_click(self, TreeView, event):
		if(event.button == 2):
			path = TreeView.get_path_at_pos(int(event.x),int(event.y))[0]
			if(TreeView.row_expanded(path)):
				TreeView.collapse_row(path)
			else:
				TreeView.expand_row(path, False)
				
	def on_right_click(self, TreeView, event):
		if event.button == 3:
			try:
				path = TreeView.get_path_at_pos(int(event.x),int(event.y))[0]
				model = TreeView.get_model()
				id = model[path][0]
				type = model[path][1]
			except TypeError:
				id = 0
				type = 'unknown'
			
			m = menus.MenuCU(type, self.data_type, id)
			m.popup(None, None, None, event.button, event.time)
		elif event.button == 2:
			path = TreeView.get_path_at_pos(int(event.x),int(event.y))[0]
			if(TreeView.row_expanded(path)):
				TreeView.collapse_row(path)
			else:
				TreeView.expand_row(path, False)
			
	def reload_sections(self, new_section=None):
		self.load()
		#messager.diffuser('liste_sections', self, [self.data_type, self.CB.get_active_text(), self.model])
		
		
	def what_is(self, container_path, model):
		#Détermine le type de section (category ou universe) d'un chemin de l'arbre des sections, ainsi que son identifiant
		columns = {'c':'categorie_ID', 'u':'univers_ID', 'f':'dossier'}

		level = len(container_path)
		ID = model[container_path][0]
		print model[container_path][0]
		type = model[container_path][1][0] # A letter u, c, f
		
		if(type == 'f'):
			ID = model[container_path][1][1:] + '%'
		dic = {}
		
		if(len(container_path) > 1 and model[container_path[0:-1]][1][0] != type): # EX : universes matching category in same treeview
			parent_node_column = columns[model[container_path[0:-1]][1]]
			dic[parent_node_column] = model[container_path[0:-1]][0]
		
		
		dic.update(self.filters) # Update/Append current filters before [filters may say we're in category 2]...
		dic[columns[type]] = ID  # ...to potentially erase after [but if we drag on category 1 then we want 1 and not 2, thus updating with filters before the final destination]
		
		
		
		print dic
		
		# DEPRECATED
		#if(mode == "category"):
			#if(type == 'u'):
				#dic['univers_ID'] = ID
				#dic['categorie_ID'] = model[container_path[0:-1]][0]
			#else:
				#dic['categorie_ID'] = ID
			
		#elif(mode == "universe"):
			#if(type == 'c'):
				#dic['categorie_ID'] = ID
				#dic['univers_ID'] = model[container_path[0:-1]][0]
			#else:
				#dic['univers_ID'] = ID
		#elif(mode == "folder"):
			#ID = model[container_path][1] + '%'
			#dic['dossier'] = ID
		
		return dic
	
class UC_Panel(AbstractPanel, gtk.Notebook):
	"""
		TODO multi-paneaux
		TODO init = hotSwap(obj) [delete, init]
		TODO rewrite folders management
		TODO? possibilité de linker un univers à une catégorie : dès qu'on set l'univers, la catégorie est automatiquement settée. EX : dès que univers Piccolo alors caté perso
		INFO Categorie = forme, univers = fond
	"""
	def __init__(self, type, elementSelector):
		AbstractPanel.__init__(self, type)
		self.data_type = type
		self.elementSelector = elementSelector
		self.categories = {}
		self.universes = {}
		
		TreeView = gtk.TreeView()
		TreeView.set_headers_visible(False)
		TVI = gtk.TreeView()
		TVI.set_headers_visible(False)
		CB = gtk.ComboBox()
		
		#Ini panel dossiers
		self.liste_dossiers = gtk.TreeStore(str, str)
		self.loadFolders()
		#messager.diffuser('liste_sections', self, [self.data_type, "dossier", self.liste_dossiers])
		TreeView.set_model(self.liste_dossiers)
		colonne = gtk.TreeViewColumn('Column 0')
		TreeView.append_column(colonne)
		cell = gtk.CellRendererText()
		pb = gtk.CellRendererPixbuf()
		pb.set_property('stock-id', gtk.STOCK_DIRECTORY)
		colonne.pack_start(pb, True)
		colonne.pack_start(cell, True)
		colonne.add_attribute(cell, 'text', 1)
		TreeView.connect("row-activated", self.on_folder_activated)
		TreeView.connect("button-press-event", self.on_folder_click)
		
		#Ini panel catégories : container_ID, container_type, container_label, container_icon
		self.model = gtk.TreeStore(int, str, str, gtk.gdk.Pixbuf, str, str)
		#messager.diffuser('liste_sections', self, [self.data_type, "category", self.model])
		
		
		TVI.set_model(self.model)
		colonne = gtk.TreeViewColumn('Column 27')
		TVI.append_column(colonne)
		cell = gtk.CellRendererText()
		pb = gtk.CellRendererPixbuf()
		colonne.pack_start(pb, False)
		colonne.pack_start(cell, True)
		colonne.add_attribute(cell, 'text', 2)
		colonne.add_attribute(pb, 'pixbuf', 3)
		TVI.connect("row-activated", self.on_container_click)
		TVI.connect("drag-data-received", self.on_drag_data_receive)
		TVI.connect("button-press-event", self.on_right_click)
		
		#Le TreeView sera la destination à toucher avec la souris
		TVI.enable_model_drag_dest([('text/plain', 0, 0)],
                  gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE)
                  
		
                  
		#Ini panel univers
		#liste_univers = gtk.ListStore(int, str)
		#messager.diffuser('liste_universI', self, liste_univers)
		#messager.inscrire(self.reload_sections, 'nouvelle_categorieI')
		
		LS_CB = gtk.ListStore(str, str)
		LS_CB.append(["category", "Categories"])
		LS_CB.append(["universe", _("Universes")])
		LS_CB.append(["folder", _("Folders")])
		cell = gtk.CellRendererText()
		CB.pack_start(cell)
		CB.add_attribute(cell, "text", 1)
		CB.set_model(LS_CB)
		CB.set_active(0)
		CB.connect("changed", self.changer_mode)
		self.CB = CB
		
		self.load()
		messager.inscrire(self.reload_sections, "new_category")
		messager.inscrire(self.reload_sections, "new_universe")
		
		B_refresh = gtk.ToolButton(gtk.STOCK_REFRESH)
		B_refresh.connect('clicked', self.load)
		
		#On assemble tout graphiquement
		gtk.Notebook.__init__(self)
		SW = gtk.ScrolledWindow()
		SW.add(TreeView)
		SW.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		label = gtk.Label(_("Folders"))
		self.append_page(SW, label)
		Box = gtk.VBox()
		Box_mode = gtk.HBox()
		Box_mode.pack_start(CB)
		Box_mode.pack_start(B_refresh, False)
		Box.pack_start(Box_mode, False)
		SW = gtk.ScrolledWindow()
		SW.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		SW.add(TVI)
		Box.pack_start(SW)
		self.set_size_request(300, -1)
		label = gtk.Label(_("Sections"))
		self.append_page(Box, label)
		self.filters = {}
		
	@property
	def mode(self):
		return self.CB.get_active_text()

				
	def load(self, *args):
		'''
			Remplit la liste fournie en fonction du type de données et du mode séléctionné
			TODO? pixbufs are repeated, maybe I should keep their addresses and reuse them 
				instead of using gtk.gdk.pixbuf_new_from_file_at_size every time
			TODO? Option to collapse expanded on new collapse
		'''
		mode = self.CB.get_active_text()
		liste = self.model
		self.processLoading(mode, liste)
				
class UC_Panes(AbstractPanel, gtk.HBox):
	"""
		TODO multi-paneaux
		TODO rewrite folders management
		TODO? possibilité de linker un univers à une catégorie : dès qu'on set l'univers, la catégorie est automatiquement settée. EX : dès que univers Piccolo alors caté perso
		INFO Categorie = forme, univers = fond
	"""
	def __init__(self, type, elementSelector):
		AbstractPanel.__init__(self, type)
		self.data_type = type
		self.elementSelector = elementSelector
		self.categories = {}
		self.universes = {}
		
		TreeView = gtk.TreeView()
		TreeView.set_headers_visible(False)
		
		TV_universes = gtk.TreeView()
		TV_categories = gtk.TreeView()
		CB = gtk.ComboBox()
		
		#Ini panel dossiers
		self.liste_dossiers = gtk.TreeStore(str, str)
		self.loadFolders()
		#messager.diffuser('liste_sections', self, [self.data_type, "dossier", self.liste_dossiers])
		TreeView.set_model(self.liste_dossiers)
		colonne = gtk.TreeViewColumn('Column 0')
		TreeView.append_column(colonne)
		cell = gtk.CellRendererText()
		pb = gtk.CellRendererPixbuf()
		pb.set_property('stock-id', gtk.STOCK_DIRECTORY)
		colonne.pack_start(pb, True)
		colonne.pack_start(cell, True)
		colonne.add_attribute(cell, 'text', 1)
		TreeView.connect("row-activated", self.on_folder_activated)
		TreeView.connect("button-press-event", self.on_folder_click)
		
		#Ini panel catégories : container_ID, container_type, container_label, container_icon, background, foreground
		self.categories_model = gtk.TreeStore(int, str, str, gtk.gdk.Pixbuf, str, str)
		self.universes_model = gtk.TreeStore(int, str, str, gtk.gdk.Pixbuf, str, str)
		#messager.diffuser('liste_sections', self, [self.data_type, "category", self.model])
		
		
		TV_universes.set_model(self.universes_model)
		TV_categories.set_model(self.categories_model)
		
		col = gtk.TreeViewColumn(_('Categories'))
		TV_categories.append_column(col)
		cell = gtk.CellRendererText()
		pb = gtk.CellRendererPixbuf()
		col.pack_start(pb, False)
		col.pack_start(cell, True)
		col.add_attribute(cell, 'text', 2)
		col.add_attribute(cell, 'cell-background', 4)
		col.add_attribute(pb, 'cell-background', 4)
		col.add_attribute(cell, 'foreground', 5)
		col.add_attribute(pb, 'pixbuf', 3)
		
		self.columns = {}
		self.columns["universe"] = col
		
		col = gtk.TreeViewColumn(_('Universes'))
		TV_universes.append_column(col)
		cell = gtk.CellRendererText()
		pb = gtk.CellRendererPixbuf()
		col.pack_start(pb, False)
		col.pack_start(cell, True)
		col.add_attribute(cell, 'text', 2)
		col.add_attribute(pb, 'pixbuf', 3)
		col.add_attribute(cell, 'cell-background', 4)
		col.add_attribute(pb, 'cell-background', 4)
		
		self.columns["category"] = col
		
		TV_categories.connect("row-activated", self.on_container_click, 'category')
		TV_universes.connect("row-activated", self.on_container_click, 'universe')
		
		
		TV_categories.connect("drag-data-received", self.on_drag_data_receive)
		TV_universes.connect("drag-data-received", self.on_drag_data_receive)
		
		TV_categories.connect("button-press-event", self.on_right_click, 'category')
		TV_universes.connect("button-press-event", self.on_right_click, 'universe')
		
		#Le TreeView sera la destination à toucher avec la souris
		TV_categories.enable_model_drag_dest([('text/plain', 0, 0)],
                  gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE)
                  
		TV_universes.enable_model_drag_dest([('text/plain', 0, 0)],
                  gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE)
		
                  
		#Ini panel univers
		#liste_univers = gtk.ListStore(int, str)
		#messager.diffuser('liste_universI', self, liste_univers)
		#messager.inscrire(self.reload_sections, 'nouvelle_categorieI')
		
		LS_CB = gtk.ListStore(str, str)
		LS_CB.append(["category", "Categories"])
		LS_CB.append(["universe", _("Universes")])
		LS_CB.append(["folder", _("Folders")])
		cell = gtk.CellRendererText()
		CB.pack_start(cell)
		CB.add_attribute(cell, "text", 1)
		CB.set_model(LS_CB)
		CB.set_active(0)
		CB.connect("changed", self.changer_mode)
		self.CB = CB
		
		self.load()
		messager.inscrire(self.reload_sections, "new_category")
		messager.inscrire(self.reload_sections, "new_universe")
		
		B_refresh = gtk.ToolButton(gtk.STOCK_REFRESH)
		B_refresh.connect('clicked', self.load)
		
		#On assemble tout graphiquement
		gtk.HBox.__init__(self)
		SW = gtk.ScrolledWindow()
		SW.add(TreeView)
		SW.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		label = gtk.Label(_("Folders"))
		self.pack_start(SW)
		Box = gtk.VBox()
		Box_mode = gtk.HBox()
		Box_mode.pack_start(CB)
		Box_mode.pack_start(B_refresh, False)
		Box.pack_start(Box_mode, False)
		
		Box = gtk.VBox()
		SW = gtk.ScrolledWindow()
		B = gtk.ToggleButton('Left')
		B.connect('clicked', self.changeFilter)
		SW.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		SW.add(TV_categories)
		Box.pack_start(SW)
		Box.pack_start(B, False)
		self.pack_start(Box)
		
		SW = gtk.ScrolledWindow()
		SW.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		SW.add(TV_universes)
		self.pack_start(SW)
		
		self.set_size_request(600, -1)
		label = gtk.Label(_("Sections"))
		#self.append_page(Box, label)
		self.toggled = {'category': True, 'universe': False}
		self.filters = {}
		
	def changeFilter(self, button):
		self.toggled['category'] = not self.toggled['category']
		self.toggled['universe'] = not self.toggled['universe']
		

	
	def load(self, *args):
		self.processLoading('category', self.categories_model, False)
		self.processLoading('universe', self.universes_model, False)
		
	def on_container_click(self, w, i, c, mode):
		self.mode = mode
		AbstractPanel.on_container_click(self, w, i, c)
		
	def on_right_click(self, TreeView, event, mode):
		self.mode = mode
		AbstractPanel.on_right_click(self, TreeView, event)
		
		if(event.button == 1):
			if(self.toggled[self.mode]):
				path = TreeView.get_path_at_pos(int(event.x),int(event.y))[0]
				self.categories_model[path][4] = 'yellow'
				for item in self.universes_model:
					item[4] = 'yellow'
				col = self.columns[self.mode]
				model = TreeView.get_model()
				col.set_title('Universes of' + ' ' + model[path][2])
				try:
					path = TreeView.get_path_at_pos(int(event.x),int(event.y))[0]
					model = TreeView.get_model()
					id = model[path][0]
					type = model[path][1]
				except TypeError:
					id = 0
					
				icon_universe = gtk.gdk.pixbuf_new_from_file('icons/genre.png')
				icon_category = gtk.gdk.pixbuf_new_from_file('icons/artist.png')
				icon_size = settings.get_option('pictures/panel_icon_size', 32)
				icon_category = icon_category.scale_simple(icon_size, icon_size, gtk.gdk.INTERP_BILINEAR)
				thumbnail_path = xdg.get_thumbnail_dir(self.data_type + '/128/')
				
				def get_icon(ID, default):
					if(ID != 0):
						try:
							icon_path = thumbnail_path + str(ID) + ".jpg"
							#icon = gtk.gdk.pixbuf_new_from_file(icon_path)
							#icon = icon.scale_simple(icon_size, icon_size, gtk.gdk.INTERP_BILINEAR)
							icon = gtk.gdk.pixbuf_new_from_file_at_size(icon_path, icon_size, icon_size)
						except:
							icon = default
					else:
						icon = default
					return icon
					
				bdd = BDD()
				self.filters.clear()
				if(mode == 'category'):
					container = 'categorie'
					dic = self.universes
					default_icon = icon_category
					default_antagonist_icon = icon_universe
					antagonist = 'univers'
					model = self.universes_model
				elif(mode == 'universe'):
					container = 'univers'
					dic = self.categories
					default_icon = icon_universe
					default_antagonist_icon = icon_category
					antagonist = 'categorie'
					model = self.categories_model
				
				
				model.clear()
				nodes = {0:None}
				
				model.append(None, [0, antagonist[0], _('All'), None, None, None])
				
				query = 'SELECT DISTINCT t.' + antagonist + '_ID, ' + antagonist + '_L, parent_ID, thumbnail_ID FROM ' + self.data_type + 's t JOIN ' + antagonist + '_' + self.data_type + 's u ON t.' + antagonist + '_ID = u.' + antagonist + '_ID '
				if(id != 0):
					query += ' WHERE ' + container + '_ID = ' + str(id)
					self.filters[container + '_ID'] = id
				query += ' ORDER BY parent_ID'
				for row in bdd.conn.execute(query):
					icon = get_icon(row[3], default_antagonist_icon)

					try:
						nodes[row[0]] = model.append(nodes[row[2]], [row[0], antagonist[0], row[1], icon, None, None])
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
								nodes[parent] = model.append(nodes[dic[parent]['parent']], [parent, antagonist[0], dic[parent]['label'], default_antagonist_icon, None, None])
						# Now we can add the node that caused the exception
						nodes[row[0]] = model.append(nodes[row[2]], [row[0], antagonist[0], row[1], icon, None, None])

		