# -*- coding: utf-8 -*-
import os
import logging



from common import settings, util, xdg
from data.elements import Container
from data.bdd import BDD


from PySide import QtGui, QtCore

from qt.util import treemodel
from abstract.ucpanel import UCPanelInterface 


logger = logging.getLogger(__name__)

icon_size = settings.get_option('pictures/panel_icon_size', 64)

class AbstractPanel(UCPanelInterface, QtGui.QWidget):

	expandRequested = QtCore.Signal(str, list)
	
	def __init__(self, moduleType):
		UCPanelInterface.__init__(self, moduleType)
		QtGui.QWidget.__init__(self)
		
		self.expandRequested.connect(self.expandNodes)
		
		
	def append(self, model, container, parentNode=None, backgroundColor='white'):
		if(parentNode == None):
			parentNode = model.rootItem
		return model.append(parentNode, UCItem(parentNode, container, backgroundColor))
		return parentNode.append(UCItem(parentNode, container))
		
	def clear(self, model):
		model.reset()
		
	def expand(self, view, nodes):
		self.expandRequested.emit(view, nodes)
		
	def expandNodes(self, view, nodes):
		tv = self.treeViews[view]
		model = tv.model()
		for node in nodes:
			index = model.createIndex(node.row(), 0, node)
			tv.setExpanded(index, True)
		
	@util.threaded
	def onContainerActivated(self, index, dontDigIfMelted=False):
		dic = self.filters.copy()
		dic.update(index.internalPointer().getFilter())
		
		if dontDigIfMelted:
			self.enqueue(dic, len(dic) == 1) # Dig only if one parameter = one container type = not melted
		else:
			self.enqueue(dic)
		print dic
		
	def showContextMenu(self, point):
		TreeView = self.sender()
		index =  TreeView.indexAt(point)
		if(TreeView.mode == 'Melted'):
			mode = self.mode
		else:
			mode = TreeView.mode
			
		if(index.isValid()):
			parentNode = index.internalPointer()
			parent = parentNode.container
		else:
			parentNode = TreeView.model().rootItem
			parent = Container([0, _('All'), 0, 0], mode, self.module)

		popupMenu = QtGui.QMenu( self )
		addCategory = popupMenu.addAction(QtGui.QIcon.fromTheme('list-add'), _('Add a ' + mode))
		deleteContainer = popupMenu.addAction(QtGui.QIcon.fromTheme('edit-delete'), _('Delete container'))
		action = popupMenu.exec_(TreeView.mapToGlobal(point))
		if action == addCategory:
			answer = QtGui.QInputDialog.getText(self, _('Add new container'), _('Name') + ' : ')
			if(answer[1] is True):
				newContainer = Container.create(mode, self.module, answer[0], parent.ID)
				self.append(TreeView.model(), newContainer, parentNode)
				if(mode == 'category'):
					self.categories[newContainer.ID] = {'label':newContainer.label, 'children':[], 'parent':newContainer.parent_ID}
				else:
					self.universes[newContainer.ID] = {'label':newContainer.label, 'children':[], 'parent':newContainer.parent_ID}
		elif action == deleteContainer:
			answer = QtGui.QMessageBox.question(self, _('Delete container'), _('Are you sure you want to delete') + ' ' + str(parent) + '?', QtGui.QMessageBox.StandardButton.Yes | QtGui.QMessageBox.StandardButton.No)
			if(answer == QtGui.QMessageBox.StandardButton.Yes):
				parent.delete()
				self.load()

	
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
		self.module = type
		self.elementSelector = elementSelector
		self.categories = {}
		self.universes = {}
		
		self.model = UCModel()
		TreeView = ContainerBrowser(self.model)
		self.TreeView = TreeView
		self.treeViews = {'folder':TreeView, 'category':TreeView, 'universe':TreeView}
		
		TreeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		TreeView.customContextMenuRequested.connect(self.showContextMenu)
		
		#filterModel = QtGui.QSortFilterProxyModel()
		#filterModel.setSourceModel(self.model)
		
		TreeView.setModel(self.model)
		TreeView.activated.connect(self.onContainerActivated)

		#TreeView.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
		
		self.modesCB = QtGui.QComboBox()
		modesModel = QtGui.QStandardItemModel()
		modesModel.appendRow([QtGui.QStandardItem('category'), QtGui.QStandardItem(_("Categories"))])
		modesModel.appendRow([QtGui.QStandardItem('universe'), QtGui.QStandardItem(_("Universes"))])
		modesModel.appendRow([QtGui.QStandardItem('folder'), QtGui.QStandardItem(_("Folders"))])
		self.modesCB.setModel(modesModel)
		self.modesCB.setModelColumn(1)
		self.modesCB.currentIndexChanged.connect(self.load)
		
		refreshButton = QtGui.QPushButton(QtGui.QIcon.fromTheme('view-refresh'), None)
		refreshButton.clicked.connect(self.load)
		
		self.showAntagonistic = QtGui.QCheckBox()
		self.showAntagonistic.setToolTip(_('Show antagonistic'))
		
		
		layout = QtGui.QVBoxLayout()
		modeBox = QtGui.QHBoxLayout()
		modeBox.addWidget(self.showAntagonistic, 0)
		modeBox.addWidget(self.modesCB, 1)
		modeBox.addWidget(refreshButton, 0)
		layout.addLayout(modeBox, 0)
		layout.addWidget(TreeView, 1)
		self.searchEntry = QtGui.QLineEdit()
		self.searchEntry.returnPressed.connect(self.load)
		layout.addWidget(self.searchEntry, 0)
		self.setLayout(layout)
		self.setMinimumWidth(300)
		
		self.load()
	
	def onContainerActivated(self, index):
		AbstractPanel.onContainerActivated(self, index, True)
	
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
		word = self.searchEntry.text()
		self.processLoading(mode, self.model, self.showAntagonistic.isChecked(), word)
		

	

	
class UC_Panes(AbstractPanel):
	"""
		NOTE Categorie = forme, univers = fond
	"""
	
	def __init__(self, module, elementSelector):
		AbstractPanel.__init__(self, module)
		self.module = module
		self.elementSelector = elementSelector
		
		
		
		# --- TreeView work ---
		
		self.categoriesModel = UCModel()
		self.universesModel = UCModel()
		self.folderModel = UCModel()
		
		
		self.treeViews = {
				'folder': ContainerBrowser(self.folderModel, 'folder'), 
				'category': ContainerBrowser(self.categoriesModel, 'category'),
				'universe': ContainerBrowser(self.universesModel, 'universe')
				}
				
	
		tvLayout = QtGui.QHBoxLayout()
		for key in ('folder', 'category', 'universe'):
			tv = self.treeViews[key]
			if key != 'folder':
				tv.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
				tv.customContextMenuRequested.connect(self.showContextMenu)
		
			tv.activated.connect(self.onContainerActivated)
		
			tv.clicked.connect(self.onContainerClicked)
				
			tvLayout.addWidget(tv)
	
	
		# --- Other work ---
		
		self.modesCB = QtGui.QComboBox()
		modesModel = QtGui.QStandardItemModel()
		modesModel.appendRow([QtGui.QStandardItem(None), QtGui.QStandardItem(_("None"))])
		modesModel.appendRow([QtGui.QStandardItem('category'), QtGui.QStandardItem(_("Categories"))])
		modesModel.appendRow([QtGui.QStandardItem('universe'), QtGui.QStandardItem(_("Universes"))])
		modesModel.appendRow([QtGui.QStandardItem('folder'), QtGui.QStandardItem(_("Folders"))])
		self.modesCB.setModel(modesModel)
		self.modesCB.setModelColumn(1)
		self.modesCB.currentIndexChanged[int].connect(self.filteringTreeViewChanged)
		
		self.filterLabel = QtGui.QLabel(_('No active filters'))
		
		self.searchEntry = QtGui.QLineEdit()
		self.searchEntry.returnPressed.connect(self.load)
	
		
		
		# --- On assemble tout graphiquement ---
		
		
		mainLayout = QtGui.QVBoxLayout()
		
		buttonBar = QtGui.QToolBar()
		buttonBar.addAction(QtGui.QIcon.fromTheme('view-refresh'), None, self.load)
		buttonBar.addWidget(self.modesCB)
		buttonBar.addSeparator()
		buttonBar.addWidget(self.filterLabel)
		
		
		mainLayout.addWidget(buttonBar, 0)
		mainLayout.addLayout(tvLayout, 1)
		mainLayout.addWidget(self.searchEntry, 0)
		
		self.setLayout(mainLayout)
		
		self.toggled = {'category': False, 'universe': False, 'folder':False}
		self.load()
		
	def changeFilter(self, button):
		self.toggled['category'] = not self.toggled['category']
		self.toggled['universe'] = not self.toggled['universe']
		

	def expandNodes(self, view, nodes):
		tv = self.treeViews[view]
		model = tv.model()
		for node in nodes:
			index = model.createIndex(node.row(), 0, node)
			tv.setExpanded(index, True)
			
	def filteringTreeViewChanged(self, index):
		model = self.modesCB.model()
		value = model.data(model.index(index, 0))
		
		for key in self.toggled.iterkeys():
			self.toggled[key] = False
			
		if value != None:
			self.toggled[value] = True
			
		self.load()
		
	
	def load(self, *args):
		self.filterLabel.setText(_('No active filters'))
		for key in self.toggled.iterkeys():
			if not self.toggled[key]:
				self.treeViews[key].setStyleSheet("background-color:white;")
			else:
				self.treeViews[key].setStyleSheet("")
		word = self.searchEntry.text()
		self.processLoading('category', self.categoriesModel, False, word)
		self.processLoading('universe', self.universesModel, False, word)
		self.processLoading('folder', self.folderModel, False, word)
		
	def onContainerActivated(self, index):
		self.mode = self.sender().mode
		AbstractPanel.onContainerActivated(self, index)
	
	
	def onContainerClicked(self, index):
		self.mode = self.sender().mode
		#AbstractPlanel.onContainerClicked(self, index)
		if self.toggled[self.mode]:
			container = index.internalPointer().container
			#index.internalPointer().background = 'yellow'
			self.filterLabel.setText(_('Filtering') + ' : ' + container.label + ' (' + self.mode + ')')
			for key in self.toggled.iterkeys():
				if not self.toggled[key]:
					self.treeViews[key].setStyleSheet("background-color:#A9E2F3;")
				else:
					self.treeViews[key].setStyleSheet('')
			self.filter(container)
			


class ContainerBrowser(QtGui.QTreeView):
	def __init__(self, model, mode='Melted'):
		QtGui.QTreeView.__init__(self)
		self.setAcceptDrops(True)
		self.setDropIndicatorShown(True)
		self.setAnimated(True)
		self.setExpandsOnDoubleClick(False)
		
		self.mode = mode
		self.setModel(model)
		self.header().setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
		
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
	def __init__(self, parent, container, background='white'):
		treemodel.TreeItem.__init__(self, container.label, parent)
		self.container = container
		self.subelements = []
		self.icon = None
		self.background = background
		
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
		if self.container.container_type == 'folder':
			dic['folder'] = self.container.ID
		else:
			while(item.parent() != None): # Don't  eval rootItem 
				fieldKey = item.container.container_type + '_ID'
				if(not dic.has_key(fieldKey)):
					dic[fieldKey] = item.container.ID
				item = item.parent()
		return dic

class UCModel(treemodel.TreeModel):
	
	DEFAULT_ICONS = {
		'univers': QtGui.QPixmap(xdg.get_data_dir() + os.sep + 'icons' + os.sep + 'genre.png'),
		'categorie': QtGui.QPixmap(xdg.get_data_dir() + os.sep + 'icons' + os.sep + 'artist.png'),
		'folder': QtGui.QPixmap(xdg.get_data_dir() + os.sep + 'icons' + os.sep + 'folder.png')
		}
		
	
		
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
				return item.container.rating
		elif role == QtCore.Qt.DecorationRole and index.column() == 0:
			if(item.icon is None):
				path = item.container.getThumbnailPath()

				if path is not None:
					item.icon = QtGui.QPixmap(item.container.getThumbnailPath())
					#item.icon = item.icon.scaled(icon_size, icon_size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation) #scaledToHeight(icon_size)
				else:
					item.icon = self.DEFAULT_ICONS[item.container.container_type]
				# FIXME delete the next line, uncomment the previous line and maintain good aspect ratio for DEFAULT_ICONS
				item.icon = item.icon.scaled(icon_size, icon_size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation) #scaledToHeight(icon_size)
				
			return item.icon
		elif role == QtCore.Qt.BackgroundColorRole:
			return QtGui.QColor(item.background)
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
				return _('Rating')
			
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
		
