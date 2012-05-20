# -*- coding: utf-8 -*-
import os
import logging
import gtk
import glib
import subprocess

from PIL import Image

from common import messager, settings, util, xdg
from data.bdd import BDD
from data.elements import Container
from gui import menus

from abstract.ucpanel import UCPanelInterface



logger = logging.getLogger(__name__)

class AbstractPanel(UCPanelInterface):
	
	
	icon_size = settings.get_option('pictures/panel_icon_size', 32)
	DEFAULT_ICONS = {'univers': gtk.gdk.pixbuf_new_from_file('icons/U.png').scale_simple(icon_size, icon_size, gtk.gdk.INTERP_BILINEAR), 'categorie': gtk.gdk.pixbuf_new_from_file('icons/C.png').scale_simple(icon_size, icon_size, gtk.gdk.INTERP_BILINEAR), 'folder':gtk.Image().render_icon(gtk.STOCK_DIRECTORY, gtk.ICON_SIZE_MENU) }
	
	
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
	
	def addRating(self, node, rating):
		print 'TODO'
		
	def append(self, model, container, parentNode, backgroundColor='white'):
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

		
		node = model.append(parentNode, [container.ID, container.container_type[0], container.label, container.rating, get_icon(container.thumbnail_ID), backgroundColor, None])
		return node
		
	def clear(self, model):
		model.clear()
		
	def expand(self, view, nodes):
		tv = self.treeViews[view]
		model = tv.get_model()

		for node in nodes:
			tv.expand_row(model.get_path(node), False)
		


	@util.threaded
	def onContainerActivated(self, w, i, c):
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
				
	def onContainerClicked(self, TreeView, event):
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
			ID = unicode(model[container_path][0])
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
	
class UC_Panel(AbstractPanel, gtk.VBox):
	"""
		TODO? possibilité de linker un univers à une catégorie : dès qu'on set l'univers, la catégorie est automatiquement settée. EX : dès que univers Piccolo alors caté perso
		INFO Categorie = forme, univers = fond
	"""
	def __init__(self, type, elementSelector):
		AbstractPanel.__init__(self, type)
		self.elementSelector = elementSelector

		
		#Ini panel catégories : container_ID, container_type, container_label, container_rating, container_icon
		self.model = gtk.TreeStore(int, str, str, int, gtk.gdk.Pixbuf, str, str)
		#messager.diffuser('liste_sections', self, [self.module, "category", self.model])
		
		TreeView = ContainerBrowser(self.model)
		TreeView.set_headers_visible(False)
		self.treeViews = {'folder':TreeView, 'category':TreeView, 'universe':TreeView}
		modeCB = gtk.ComboBox()
		

		
		
		
		TreeView.connect("row-activated", self.onContainerActivated)
		TreeView.connect("drag-data-received", self.on_drag_data_receive)
		TreeView.connect("button-press-event", self.onContainerClicked)
		
		#Le TreeView sera la destination à toucher avec la souris
		TreeView.enable_model_drag_dest([('text/plain', 0, 0)], gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE)
		
		modeModel = gtk.ListStore(str, str)
		modeModel.append(["category", "Categories"])
		modeModel.append(["universe", _("Universes")])
		modeModel.append(["folder", _("Folders")])
		cell = gtk.CellRendererText()
		modeCB.pack_start(cell)
		modeCB.add_attribute(cell, "text", 1)
		modeCB.set_model(modeModel)
		modeCB.set_active(0)
		modeCB.connect("changed", self.changer_mode)
		self.modeCB = modeCB
		
		
		messager.inscrire(self.reload_sections, "new_category")
		messager.inscrire(self.reload_sections, "new_universe")
		
		B_refresh = gtk.ToolButton(gtk.STOCK_REFRESH)
		B_refresh.connect('clicked', self.load)
		
		self.showAntagonistic = gtk.CheckButton(_("Show antagonistic"))
		self.showAntagonistic.set_active(settings.get_option(self.module + 's/show_antagonistic', False))
		self.showAntagonistic.connect('toggled', self.toggleAntagonisitc)
		
		#On assemble tout graphiquement
		gtk.VBox.__init__(self)
		
		Box_mode = gtk.HBox()
		Box_mode.pack_start(self.showAntagonistic, False)
		Box_mode.pack_start(modeCB)
		Box_mode.pack_start(B_refresh, False)
		self.pack_start(Box_mode, False)
		SW = gtk.ScrolledWindow()
		SW.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		SW.add(TreeView)
		self.pack_start(SW)
		
		self.searchEntry = gtk.Entry()
		self.searchEntry.connect('activate', self.load)
		self.pack_start(self.searchEntry, False)
		
		self.set_size_request(300, -1)
		self.filters = {}
		
		self.load()
		
	@property
	def mode(self):
		return self.modeCB.get_active_text()

				
	def load(self, *args):
		'''
			Remplit la liste fournie en fonction du type de données et du mode séléctionné
			TODO? pixbufs are repeated, maybe I should keep their addresses and reuse them 
				instead of using gtk.gdk.pixbuf_new_from_file_at_size every time
			TODO? Option to collapse expanded on new collapse
		'''
		word = self.searchEntry.get_text()
		mode = self.modeCB.get_active_text()
		liste = self.model
		self.processLoading(mode, liste, self.showAntagonistic.get_active(), word)
		
	def toggleAntagonisitc(self, button):
		settings.set_option(self.module + 's/show_antagonistic', self.showAntagonistic.get_active())
		self.load()
		
		
class UC_Panes(AbstractPanel, gtk.VBox):
	"""
		TODO? possibilité de linker un univers à une catégorie : dès qu'on set l'univers, la catégorie est automatiquement settée. EX : dès que univers Piccolo alors caté perso
		INFO Categorie = forme, univers = fond
	"""
	def __init__(self, module, elementSelector):
		AbstractPanel.__init__(self, module)
		self.elementSelector = elementSelector

		
		#Ini panel dossiers
		self.folderModel = gtk.TreeStore(str, str, str, int, gtk.gdk.Pixbuf, str, str)
		TreeView = ContainerBrowser(self.folderModel, 'folder')
		#TreeView.set_headers_visible(False)
		
		#Ini panel catégories : container_ID, container_type, container_label, container_icon, background, foreground
		self.categoriesModel = gtk.TreeStore(int, str, str, int, gtk.gdk.Pixbuf, str, str)
		self.universesModel = gtk.TreeStore(int, str, str, int, gtk.gdk.Pixbuf, str, str)
		TV_universes = ContainerBrowser(self.universesModel, 'universe')
		TV_categories = ContainerBrowser(self.categoriesModel, 'category')
		
		self.treeViews = {'universe':TV_universes, 'category':TV_categories, 'folder':TreeView}
		modeCB = gtk.ComboBox()
		
		
		tvLayout = gtk.HBox()
		for key in ('folder', 'category', 'universe'):
			tv = self.treeViews[key]
			if key != 'folder':
				tv.connect("drag-data-received", self.on_drag_data_receive)
				tv.connect("button-press-event", self.onContainerClicked)
				tv.enable_model_drag_dest([('text/plain', 0, 0)],gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE)
			
			else:
				tv.connect("button-press-event", self.on_folder_click)
				
			tv.connect("row-activated", self.onContainerActivated)
			
			SW = gtk.ScrolledWindow()
			SW.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
			SW.add(tv)
			tvLayout.pack_start(SW)
			
		

		
		# DEPRECATED
		#self.columns = {}
		#self.columns["universe"] = col
		#self.columns["category"] = col
		
		
		messager.inscrire(self.reload_sections, "new_category")
		messager.inscrire(self.reload_sections, "new_universe")
		
		B_refresh = gtk.ToolButton(gtk.STOCK_REFRESH)
		B_refresh.connect('clicked', self.load)
		
		modeModel = gtk.ListStore(str, str)
		modeModel.append([None, _('None')])
		modeModel.append(["category", _("Categories")])
		modeModel.append(["universe", _("Universes")])
		modeModel.append(["folder", _("Folders")])
		cell = gtk.CellRendererText()
		modeCB.pack_start(cell)
		modeCB.add_attribute(cell, "text", 1)
		modeCB.set_model(modeModel)
		modeCB.set_active(0)
		modeCB.connect("changed", self.filteringTreeViewChanged)
		
		self.filterLabel = gtk.Label(_('No active filters'))
		
		#On assemble tout graphiquement
		gtk.VBox.__init__(self)
		
		BB = gtk.HBox()
		BB.pack_start(B_refresh, False)
		BB.pack_start(modeCB, False)
		BB.pack_start(self.filterLabel, True)
		self.pack_start(BB, False)
		
		
		self.searchEntry = gtk.Entry()
		self.searchEntry.connect('activate', self.load)
		
		
		self.pack_start(tvLayout)
		self.pack_start(self.searchEntry, False)
		self.set_size_request(700, -1)

		self.toggled = {'category': False, 'universe': False, 'folder':False}
		self.filters = {}
		
		filterIndex = settings.get_option(self.module + 's/container_filter', 0)
		if filterIndex != 0:
			modeCB.set_active(filterIndex) # trigger filteringTreeViewChanged() and thus load
		else:
			self.load()
		
		
	def changeFilter(self, button):
		self.toggled['category'] = not self.toggled['category']
		self.toggled['universe'] = not self.toggled['universe']
		
	def filteringTreeViewChanged(self, modeCB):
		value = modeCB.get_active_text()
		
		for key in self.toggled.iterkeys():
			self.toggled[key] = False
			
		if value != None:
			self.toggled[value] = True
		
		for key in self.toggled.iterkeys():
			self.treeViews[key].modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
			
		settings.set_option(self.module + 's/container_filter', modeCB.get_active())
		self.load()

	
	def load(self, *args):
		word = self.searchEntry.get_text()
		self.processLoading('category', self.categoriesModel, False, word)
		self.processLoading('universe', self.universesModel, False, word)
		self.processLoading('folder', self.folderModel, False, word)
		
	def onContainerActivated(self, w, i, c):
		self.mode = w.mode
		AbstractPanel.onContainerActivated(self, w, i, c)
		
	def onContainerClicked(self, TreeView, event):
		self.mode = TreeView.mode
		AbstractPanel.onContainerClicked(self, TreeView, event)
		
		if(event.button == 1):
			if self.toggled[self.mode]:
				model = TreeView.get_model()
				try:
					path = TreeView.get_path_at_pos(int(event.x),int(event.y))[0]
					model = TreeView.get_model()
					id = model[path][0]
					type = model[path][1]
				except TypeError:
					id = 0
					
				container = Container(id, type, self.module)
				self.filterLabel.set_text(_('Filtering') + ' : ' + container.label + ' (' + self.mode + ')')
				for key in self.toggled.iterkeys():
					if not self.toggled[key]:
						self.treeViews[key].modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse("#A9E2F3"))
						#self.treeViews[key].show()

				self.filter(container)


		
		
class ContainerBrowser(gtk.TreeView):
	def __init__(self, model, mode='Melted'):
		gtk.TreeView.__init__(self)
		self.mode = mode
		self.set_model(model)
		
		col = gtk.TreeViewColumn(_(mode))
		self.append_column(col)
		cell = gtk.CellRendererText()
		pb = gtk.CellRendererPixbuf()
		col.pack_start(pb, False)
		col.pack_start(cell, True)
		col.add_attribute(cell, 'text', 2)
		col.add_attribute(cell, 'cell-background', 5)
		col.add_attribute(pb, 'cell-background', 5)
		col.add_attribute(cell, 'foreground', 6)
		col.add_attribute(pb, 'pixbuf', 4)
		col.set_sort_column_id(2)
		col.connect("clicked", self.on_column_clicked)
		
		col = gtk.TreeViewColumn(_('Rating'))
		self.append_column(col)
		cell = gtk.CellRendererText()
		col.pack_start(cell, True)
		col.add_attribute(cell, 'text', 3)
		col.set_sort_column_id(3)
		col.connect("clicked", self.on_column_clicked)
		
	def on_column_clicked(self, column):
		def disable_sorting_state():
			time.sleep(2.0)
			self.model.set_sort_column_id(-2, 0)
			
		a = threading.Thread(target=disable_sorting_state)
		a.start()