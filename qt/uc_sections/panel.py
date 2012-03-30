# -*- coding: utf-8 -*-
import threading
import os
import logging
import gtk

import glib
import subprocess

from PIL import Image

from common import settings, util, xdg
from data.elements import Container
from data.bdd import BDD


from PySide import QtGui, QtCore

from qt.util import treemodel
from abstract.ucpanel import UCPanelInterface 


logger = logging.getLogger(__name__)

icon_size = settings.get_option('pictures/panel_icon_size', 32)

class AbstractPanel(UCPanelInterface, QtGui.QWidget):
	def __init__(self, moduleType):
		UCPanelInterface.__init__(self, moduleType)
		QtGui.QWidget.__init__(self)
		
		
	def append(self, model, container, parentNode):
		if(parentNode == None):
			parentNode = model.rootItem
		return model.append(parentNode, UCItem(parentNode, container))
		return parentNode.append(UCItem(parentNode, container))
		
	def clear(self, model):
		model.reset()
		
	def onContainerActivated(self, index):
		dic = index.internalPointer().getFilter()
		self.enqueue(dic)
		print dic
		
class AbstractPlanel():
	"""
		TODO multi-panneaux
		TODO rewrite folders management
		TODO? possibilité de linker un univers à une catégorie : dès qu'on set l'univers, la catégorie est automatiquement settée. EX : dès que univers Piccolo alors caté perso
		INFO Categorie = forme, univers = fond
	"""
	


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
				#ID_category = self.liste_sections[path_category][0]
				#messager.diffuser('need_data_of', self, [self.data_type, "category_and_universe", ID_category, ID])
			#elif(section == "category"):
				#path_universe = i[0]
				#ID_universe = self.liste_sections[path_universe][0]
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
		#messager.diffuser('liste_sections', CB, [self.data_type, CB.get_active_text(), self.liste_sections])
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
		#messager.diffuser('liste_sections', self, [self.data_type, self.CB.get_active_text(), self.liste_sections])
		
		
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
		
		
		dic.update(self.filters) # Update before [filters may say we're in category 2]...
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
	
class UC_Panel(AbstractPanel):
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
		
		TreeView = ContainerBrowser()
		self.TreeView = TreeView
		
		TreeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		TreeView.customContextMenuRequested.connect(self.showContextMenu)
		self.model = UCModel()
		TreeView.setModel(self.model)
		TreeView.activated.connect(self.onContainerActivated)

		#TreeView.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
		
		self.modesCB = QtGui.QComboBox()
		modesModel = QtGui.QStandardItemModel()
		modesModel.appendRow([QtGui.QStandardItem('category'), QtGui.QStandardItem(_("Categories"))])
		modesModel.appendRow([QtGui.QStandardItem('universe'), QtGui.QStandardItem(_("Universes"))])
		self.modesCB.setModel(modesModel)
		self.modesCB.setModelColumn(1)
		self.modesCB.currentIndexChanged.connect(self.load)
		
		refreshButton = QtGui.QPushButton(QtGui.QIcon.fromTheme('view-refresh'), None)
		refreshButton.clicked.connect(self.load)
		
		self.load()
		
		layout = QtGui.QVBoxLayout()
		modeBox = QtGui.QHBoxLayout()
		modeBox.addWidget(self.modesCB, 1)
		modeBox.addWidget(refreshButton)
		layout.addLayout(modeBox)
		layout.addWidget(TreeView)
		self.setLayout(layout)
		self.setMinimumWidth(300)
		
	def append(self, model, container, parentNode):
		if(parentNode == None):
			parentNode = model.rootItem
		return model.append(parentNode, UCItem(parentNode, container))
		return parentNode.append(UCItem(parentNode, container))
		
	def clear(self, model):
		model.reset()
		
	
		
	@property
	def mode(self):
		model = self.modesCB.model()
		return model.data(model.index(self.modesCB.currentIndex(), 0))

				
	def load(self, *args):
		'''
			Remplit la liste fournie en fonction du type de données et du mode séléctionné
			TODO? pixbufs are repeated, maybe I should keep their addresses and reuse them 
				instead of using gtk.gdk.pixbuf_new_from_file_at_size every time
			TODO? Option to collapse expanded on new collapse
		'''
		mode = self.mode
		print mode
		self.processLoading(mode, self.model)
		
	
		
	
		
	
	def showContextMenu(self, point):
		TreeView = self.sender()
		index =  TreeView.indexAt(point)
		if(index.isValid()):
			parentNode = index.internalPointer()
			parent = parentNode.container
		else:
			parentNode = self.model.rootItem
			parent = Container([0, _('All'), 0, 0], 'category', self.data_type)

		popupMenu = QtGui.QMenu( self )
		addCategory = popupMenu.addAction(QtGui.QIcon.fromTheme('list-add'), _('Add a category'))
		deleteContainer = popupMenu.addAction(QtGui.QIcon.fromTheme('edit-delete'), _('Delete container'))
		action = popupMenu.exec_(TreeView.mapToGlobal(point))
		if action == addCategory:
			answer = QtGui.QInputDialog.getText(self, _('Add new container'), _('Name') + ' : ')
			if(answer[1] is True):
				newContainer = Container.create('categorie', self.data_type, answer[0], parent.ID)
				self.append(TreeView.model(), newContainer, parentNode)
				self.categories[newContainer.ID] = {'label':newContainer.label, 'children':[], 'parent':newContainer.parent_ID}
		elif action == deleteContainer:
			answer = QtGui.QMessageBox.question(self, _('Dele container'), _('Are you sure you want to delete') + ' ' + str(parent) + '?', QtGui.QMessageBox.StandardButton.Yes | QtGui.QMessageBox.StandardButton.No)
			if(answer == QtGui.QMessageBox.StandardButton.Yes):
				parent.delete()
				self.load()
		
		

	

	
class UC_Panes(AbstractPanel):
	"""
		NOTE Categorie = forme, univers = fond
	"""
	def __init__(self, type, elementSelector):
		AbstractPanel.__init__(self, type)
		self.data_type = type
		self.elementSelector = elementSelector
		
		TV_folders = ContainerBrowser()
		TV_universes = ContainerBrowser('universe')
		TV_categories = ContainerBrowser('category')
		
		self.categoriesModel = UCModel()
		self.universesModel = UCModel()
		
		TV_categories.setModel(self.categoriesModel)
		TV_universes.setModel(self.universesModel)


		#self.loadFolders()
		


		
		TV_categories.activated.connect(self.onContainerActivated)
		TV_universes.activated.connect(self.onContainerActivated)
		#TV_universes.activated.connect(lambada: self.on_container_click('universe'))
		
		#TV_categories.connect("button-press-event", self.on_right_click, 'category')
		#TV_universes.connect("button-press-event", self.on_right_click, 'universe')
	
	
		self.load()
		
		# --- On assemble tout graphiquement ---
		layout = QtGui.QHBoxLayout()
		
		layout.addWidget(TV_folders)
		layout.addWidget(TV_categories)
		layout.addWidget(TV_universes)
		
		self.setLayout(layout)
		
		self.toggled = {'category': True, 'universe': False}
		self.filters = {}
		
	def changeFilter(self, button):
		self.toggled['category'] = not self.toggled['category']
		self.toggled['universe'] = not self.toggled['universe']
		

		
	
	def load(self, *args):
		self.processLoading('category', self.categoriesModel, False)
		self.processLoading('universe', self.universesModel, False)
		
	def onContainerActivated(self, index):
		self.mode = self.sender().mode
		AbstractPanel.onContainerActivated(self, index)
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


class ContainerBrowser(QtGui.QTreeView):
	def __init__(self, mode='Melted'):
		QtGui.QTreeView.__init__(self)
		self.setAcceptDrops(True)
		self.setDropIndicatorShown(True)
		self.setAnimated(True)
		self.setExpandsOnDoubleClick(False)
		
		self.mode = mode
		
	def dragEnterEvent(self, e):
		QtGui.QTreeView.dragEnterEvent(self, e)
		data = e.mimeData()
		print data.formats()
		if data.hasFormat('bullseye/ucelements'):
			e.accept()

		
	def dragLeaveEvent(self, e):
		self.clearFocus()
		
	def dragMoveEvent(self, e):
		QtGui.QTreeView.dragMoveEvent(self, e)
		index = self.indexAt(e.pos())
		if(index.isValid()):
			self.setFocus(QtCore.Qt.MouseFocusReason)
			self.setCurrentIndex(index)
		e.accept()
		#e.acceptProposedAction()
		# Must reimplement this otherwise the drag event is not spread
		# But at this point the event has already been checked by dragEnterEvent
		
	def dropEvent(self, e):
		print "DROP EVENT"
		data = e.mimeData()
		print data.formats()
		
		if data.hasFormat('bullseye/ucelements'):
			dic = eval(str(data.data('bullseye/ucelements')))
			self.indexAt(e.pos()).internalPointer().container.addElements(dic)
			
	
	def mouseReleaseEvent(self, e):
		if e.button() == QtCore.Qt.MidButton:
			i = self.indexAt(QtCore.QPoint(e.x(), e.y()))
			if(i.column() != 0):
				i= i.sibling(i.row(), 0)
			self.setExpanded(i, not self.isExpanded(i))
		else:
			QtGui.QTreeView.mouseReleaseEvent(self, e)

class UCItem(treemodel.TreeItem):
	def __init__(self, parent, container):
		treemodel.TreeItem.__init__(self, container.label, parent)
		self.container = container
		self.subelements = []
		self.icon = None
		
	def __str__( self ):
		return self.label
		
	def __repr__(self):
		return self.label
		
	def getFilter(self):
		'''
			ex : {"artist":"AC/DC", "album":"Back In Black", "title":"You Shook Me All Night Long"}
		'''
		dic = {}
		item = self
		while(item.parent() != None): # Don't  eval rootItem 
			fieldKey = item.container.container_type + '_ID'
			if(not dic.has_key(fieldKey)):
				dic[fieldKey] = item.container.ID
			item = item.parent()
		return dic

class UCModel(treemodel.TreeModel):
	def __init__(self):
		treemodel.TreeModel.__init__(self)


	def columnCount(self, parent):
		return 3

	def data(self, index, role):
		if not index.isValid():
			return None
		item = index.internalPointer()
		if role == QtCore.Qt.DisplayRole:
			if index.column() == 1:
				return item.container.label
			elif index.column() == 2:
				return item.container.label
		elif role == QtCore.Qt.DecorationRole and index.column() == 0:
			if(item.icon is None):
				item.icon = QtGui.QPixmap(item.container.getThumbnailPath())
				item.icon = item.icon.scaled(icon_size, icon_size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation) #scaledToHeight(icon_size)
				
			return item.icon
		return None

	def dropMimeData(self, data, action, row, column, parent):
		print 'ERIA'
                  
	def flags(self, index):
		return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled
	
	def headerData(self, section, orientation, role):
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
			if section == 0:
				return 'Icon'
			elif section == 1:
				return 'Label'
			elif section == 2:
				return _('Count')
			
		return None
		
	def mimeData(self, indexes):
		'''
			What is passed during drag operations
		'''
		data = QtCore.QMimeData()
		selection = []
		for i in indexes:
			selection.append(i.internalPointer().getFilter())
		data.setData('bullseye/library.items', str(selection))
		return data
		
	def mimeTypes(self):
		'''
			FIXME Not used, didn't manage to find out how to automatically serialize items (thus overrided mimeData instead)
		'''
		return ('bullseye/library.items',)
		
	def supportedDropActions(self):
		return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction