# -*- coding: utf-8 -*-
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
	
	
	icon_size = settings.get_option('pictures/panel_icon_size', 32)
	DEFAULT_ICONS = {'univers': gtk.gdk.pixbuf_new_from_file('icons/genre.png').scale_simple(icon_size, icon_size, gtk.gdk.INTERP_BILINEAR), 'categorie': gtk.gdk.pixbuf_new_from_file('icons/artist.png').scale_simple(icon_size, icon_size, gtk.gdk.INTERP_BILINEAR), 'folder':gtk.Image().render_icon(gtk.STOCK_DIRECTORY, gtk.ICON_SIZE_MENU) }
	
	
	#icon_category = icon_category.scale_simple(icon_size, icon_size, gtk.gdk.INTERP_BILINEAR)
	thumbnail_path = xdg.get_thumbnail_dir('picture' + '/128/')
	
	"""
		Base class for all differents Gtk UC Panel implementations
		TODO multi-panneaux
		TODO rewrite folders management
		TODO? possibilité de linker un univers à une catégorie : dès qu'on set l'univers, la catégorie est automatiquement settée. EX : dès que univers Piccolo alors caté perso
		INFO Categorie = forme, univers = fond
	"""
	def __init__(self, module):
		UCPanelInterface.__init__(self, module)
	
	
	def append(self, model, container, parentNode):
		def get_icon(ID):
			if(ID != 0):
				try:
					icon_path = self.thumbnail_path + str(ID) + ".jpg"
					#icon = gtk.gdk.pixbuf_new_from_file(icon_path)
					#icon = icon.scale_simple(icon_size, icon_size, gtk.gdk.INTERP_BILINEAR)
					icon = gtk.gdk.pixbuf_new_from_file_at_size(icon_path, self.icon_size, self.icon_size)
				except:
					icon = self.DEFAULT_ICONS[container.container_type]
			else:
				icon = self.DEFAULT_ICONS[container.container_type]
			return icon

		
		node = model.append(parentNode, [container.ID, container.container_type[0], container.label, get_icon(container.thumbnail_ID), None, None])
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
		#type = self.module
		#liste.clear()
		#if(mode != 'folder'):
			#icon_universe = gtk.gdk.pixbuf_new_from_file('icons/genre.png')
			#icon_category = gtk.gdk.pixbuf_new_from_file('icons/artist.png')
			#icon_size = settings.get_option('pictures/panel_icon_size', 32)
			#icon_category = icon_category.scale_simple(icon_size, icon_size, gtk.gdk.INTERP_BILINEAR)
			#thumbnail_path = xdg.get_thumbnail_dir(self.module + '/128/')
			
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
			#bdd.c.execute('SELECT DISTINCT dossier FROM ' + self.module + 's ORDER BY dossier')
			#folders = bdd.c.fetchall()
			#nodes = {}
			#i = 0
			
			#while(i < len(folders)):
				#add_node(folders[i][0])
				#i += 1
		
	#@util.threaded
	#def loadFolders(self):
		#def get_parent(path, level):
			#"""
				#Ex get_parent('/home/piccolo/Downloads/Pictures/DBZ, 2) = /home/piccolo/Downloads
			#"""
			#parts = path.split('/')
			#parent = ''
			#for i in xrange(len(parts) - level):
				#parent += parts[i] + '/'
				
			#return parent[:-1] # remove last slash
			
		#def add_node(path):
			#"""
				#Add a folder node, and all parent folder nodes if needed
			#"""
			#parts = path.split('/')
			#s = ''
			#node = None
			#for part in parts:
				#s += part + '/'
				#if(s not in nodes.keys()):
					#nodes[s] = self.folderModel.append(node, [s, part])
				#node = nodes[s]
		
		#bdd = BDD()
		#bdd.c.execute('SELECT DISTINCT folder FROM ' + self.module + 's ORDER BY folder')
		
		#folders = bdd.c.fetchall()
		##i = 0
		##node = None
		##parent = ''
		#nodes = {}
		#i = 0
		##node = self.folderModel.append(None, [folders[0][0], folders[0][0]])
		##parent = folders[0][0]
		
		
		#while(i < len(folders)):
			##print parent
			##print folders[i][0]
			##print folders[i][0].find(parent)
			
			## Recherche du plus proche dossier parent
			##j = 0
			##while(get_parent(folders[i][0], j) != get_parent(parent, j)):
				##j += 1
			
			##print(get_parent(folders[i][0], j))
			##if(folders[i][0].find(parent) != -1):
				##self.folderModel.append(node, [folders[i][0], folders[i][0]])
			##else:
				##parent = folders[i][0]
				##node = self.folderModel.append(None, [folders[i][0], folders[i][0]])
			##while(i < len(folders) and folders[i][0].find(parent) != -1):
				##self.folderModel.append(node, [folders[i][0], folders[i][0]])
				##i += 1
			##parent = folders[i][0]
			##node = self.folderModel.append(node, [folders[i][0], folders[i][0]])
			
			#add_node(folders[i][0])
			#i += 1
		
	
				

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
		self.enqueue(parameters)

		


	
	def changer_mode(self, CB):
		#messager.diffuser('liste_sections', CB, [self.module, CB.get_active_text(), self.model])
		self.load()
		
	
	def on_drag_data_receive(self, TreeView, drag_context, x, y, selection_data, info, timestamp):
		#fin d'un DND
		T_elements_ID = eval(selection_data.get_text()) # eval => permet de retransformer la chaîne de caractères en tableau
		numero_tuple = TreeView.get_dest_row_at_pos(x, y)[0]
		dic = self.what_is(numero_tuple, TreeView.get_model())
		
		for key in dic.iterkeys():
			messager.diffuser('fileIN', self, [self.module, T_elements_ID, key, dic[key]])

	
	def on_folder_activated(self, w, i, c):
		dossier = self.folderModel[i][0]
		messager.diffuser("need_data_of", self, [self.module, "dossier", dossier])
		
	def on_folder_click(self, TreeView, event):
		if(event.button == 2):
			path = TreeView.get_path_at_pos(int(event.x),int(event.y))[0]
			if(TreeView.row_expanded(path)):
				TreeView.collapse_row(path)
			else:
				TreeView.expand_row(path, False)
				
	def on_right_click(self, TreeView, event):
		if event.button == 3:
			model = TreeView.get_model()
			try:
				path = TreeView.get_path_at_pos(int(event.x),int(event.y))[0]
				parentNode = model.get_iter(path)
				id = model[path][0]
				type = model[path][1]
			except TypeError:
				parentNode = None
				id = 0
				type = 'unknown'
			
			m = menus.MenuCU(type, self.module, id)
			m.popup(None, None, None, event.button, event.time)
			# WARNING connect_object remplace le premier premier user_param (ici model) par l'objet source du signal
			#Ce sera donc le premier paramètre de la méthode appelée. Ensuite seront ajoutés les arguments classiques du signal PUIS
			# viendra les VRAIS users params qui commencent ici avec parentNode
			m.connect_object('container-added', self.append, model, parentNode)
		elif event.button == 2:
			path = TreeView.get_path_at_pos(int(event.x),int(event.y))[0]
			if(TreeView.row_expanded(path)):
				TreeView.collapse_row(path)
			else:
				TreeView.expand_row(path, False)
			
	def reload_sections(self, new_section=None):
		self.load()
		#messager.diffuser('liste_sections', self, [self.module, self.CB.get_active_text(), self.model])
		
		
	def what_is(self, container_path, model):
		#Détermine le type de section (category ou universe) d'un chemin de l'arbre des sections, ainsi que son identifiant
		columns = {'c':'categorie_ID', 'u':'univers_ID', 'f':'folder'}

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
		self.module = type
		self.elementSelector = elementSelector
		self.categories = {}
		self.universes = {}
		
		TreeView = gtk.TreeView()
		TreeView.set_headers_visible(False)
		TVI = gtk.TreeView()
		TVI.set_headers_visible(False)
		CB = gtk.ComboBox()
		
		#Ini panel dossiers
		self.folderModel = gtk.TreeStore(str, str)
		self.loadFolders()
		#messager.diffuser('liste_sections', self, [self.module, "dossier", self.folderModel])
		TreeView.set_model(self.folderModel)
		colonne = gtk.TreeViewColumn('Column 0')
		TreeView.append_column(colonne)
		cell = gtk.CellRendererText()
		pb = gtk.CellRendererPixbuf()
		pb.set_property('stock-id', gtk.STOCK_DIRECTORY)
		colonne.pack_start(pb, True)
		colonne.pack_start(cell, True)
		colonne.add_attribute(cell, 'text', 1)
		TreeView.connect("row-activated", self.on_container_click)
		TreeView.connect("button-press-event", self.on_folder_click)
		
		#Ini panel catégories : container_ID, container_type, container_label, container_icon
		self.model = gtk.TreeStore(int, str, str, gtk.gdk.Pixbuf, str, str)
		#messager.diffuser('liste_sections', self, [self.module, "category", self.model])
		
		
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
				
class UC_Panes(AbstractPanel, gtk.VBox):
	"""
		TODO multi-paneaux
		TODO rewrite folders management
		TODO? possibilité de linker un univers à une catégorie : dès qu'on set l'univers, la catégorie est automatiquement settée. EX : dès que univers Piccolo alors caté perso
		INFO Categorie = forme, univers = fond
	"""
	def __init__(self, module, elementSelector):
		AbstractPanel.__init__(self, module)
		self.module = module
		self.elementSelector = elementSelector
		self.categories = {}
		self.universes = {}
		
		TreeView = gtk.TreeView()
		TreeView.set_headers_visible(False)
		
		TV_universes = gtk.TreeView()
		TV_categories = gtk.TreeView()
		CB = gtk.ComboBox()
		
		#Ini panel dossiers
		self.folderModel = gtk.TreeStore(str, str, str, gtk.gdk.Pixbuf, str, str)

		#messager.diffuser('liste_sections', self, [self.module, "dossier", self.folderModel])
		TreeView.set_model(self.folderModel)
		colonne = gtk.TreeViewColumn('Column 0')
		TreeView.append_column(colonne)
		cell = gtk.CellRendererText()
		pb = gtk.CellRendererPixbuf()
		pb.set_property('stock-id', gtk.STOCK_DIRECTORY)
		colonne.pack_start(pb, True)
		colonne.pack_start(cell, True)
		colonne.add_attribute(cell, 'text', 2)
		TreeView.connect("row-activated", self.on_container_click, 'folder')
		TreeView.connect("button-press-event", self.on_folder_click)
		
		#Ini panel catégories : container_ID, container_type, container_label, container_icon, background, foreground
		self.categories_model = gtk.TreeStore(int, str, str, gtk.gdk.Pixbuf, str, str)
		self.universes_model = gtk.TreeStore(int, str, str, gtk.gdk.Pixbuf, str, str)
		#messager.diffuser('liste_sections', self, [self.module, "category", self.model])
		
		
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
		gtk.VBox.__init__(self)
		
		BB = gtk.HButtonBox()
		BB.pack_start(B_refresh, False)
		self.pack_start(BB, False)
		
		hbox = gtk.HBox()
		SW = gtk.ScrolledWindow()
		SW.add(TreeView)
		SW.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		label = gtk.Label(_("Folders"))
		hbox.pack_start(SW)
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
		hbox.pack_start(Box)
		
		SW = gtk.ScrolledWindow()
		SW.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		SW.add(TV_universes)
		hbox.pack_start(SW)
		
		searchEntry = gtk.Entry()
		
		
		self.pack_start(hbox)
		self.pack_start(searchEntry, False)
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
		self.processLoading('folder', self.folderModel, False)
		
	def on_container_click(self, w, i, c, mode):
		self.mode = mode
		AbstractPanel.on_container_click(self, w, i, c)
		
	def on_right_click(self, TreeView, event, mode):
		# TODO should use Interface filter() method
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
					
				icon_universe = self.DEFAULT_ICONS['univers']
				icon_category = self.DEFAULT_ICONS['categorie']
				thumbnail_path = xdg.get_thumbnail_dir(self.module + '/128/')
				
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
				
				query = 'SELECT DISTINCT t.' + antagonist + '_ID, ' + antagonist + '_L, parent_ID, thumbnail_ID FROM ' + self.module + 's t JOIN ' + antagonist + '_' + self.module + 's u ON t.' + antagonist + '_ID = u.' + antagonist + '_ID '
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

		