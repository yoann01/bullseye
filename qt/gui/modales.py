# -*- coding: utf-8 -*-
from common import settings
from PySide import QtGui, QtCore
from qt.util import treemodel

class SettingsEditor(QtGui.QDialog):
	def __init__(self):
		QtGui.QDialog.__init__(self)
		self.setWindowTitle(_("Settings editor"))
		mainLayout = QtGui.QVBoxLayout()
		buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
		buttonBox.accepted.connect(self.accept)
		buttonBox.rejected.connect(self.reject)
		layout = QtGui.QHBoxLayout()
		mainLayout.addLayout(layout)
		mainLayout.addWidget(buttonBox)
		
		
		# --- Sections selector
		TreeView = QtGui.QTreeView(self)
		TreeView.header().setResizeMode(QtGui.QHeaderView.ResizeToContents)
		self.sections = QtGui.QStandardItemModel(self)
		def addSection(key, text, iconPath=None, parent=self.sections.invisibleRootItem()):
			node = QtGui.QStandardItem(QtGui.QIcon(iconPath), _(text))
			node.setEditable(False)
			parent.appendRow([node, QtGui.QStandardItem(key)])
			return node
			
		addSection('general', 'General')
		addSection('folders', 'Indexed folders')
		musicNode = addSection('music', 'Music')
		node = addSection('music_filters', 'Filters', None, musicNode)
		
		TreeView.setModel(self.sections)
		#TreeView.header().setSectionHidden(1, True)
		TreeView.activated.connect(self.sectionActivated)
		layout.addWidget(TreeView)
		layout.setStretchFactor(TreeView, 0)
		
		
		self.widgets = {}
		
		generalLayout = QtGui.QFormLayout()
		self.CB_gui_framework = QtGui.QComboBox()
		self.CB_gui_framework.addItem('Gtk 2')
		self.CB_gui_framework.addItem('Qt 4')
		generalLayout.addRow(_('GUI framework' + ' : '), self.CB_gui_framework)
		
		self.pictures_enabled = QtGui.QCheckBox(_('Enable pictures manager'))
		self.pictures_enabled.setChecked(settings.get_option('pictures/enabled', False))
		generalLayout.addRow(self.pictures_enabled)
		
		generalWidget = QtGui.QWidget()
		generalWidget.setLayout(generalLayout)
		self.widgets['general'] = generalWidget
		self.activeWidget = generalWidget

		layout.addWidget(generalWidget)
		layout.setStretchFactor(generalWidget, 1)
		
		foldersLayout = QtGui.QVBoxLayout()
		foldersView = QtGui.QTableView()
		foldersView.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
		self.foldersModel = QtGui.QStandardItemModel(0, 2)
		foldersView.setModel(self.foldersModel)
		addFolderButton = QtGui.QPushButton(_('Add'))
		def add_folder():
				folderPath = QtGui.QFileDialog.getExistingDirectory(self)
				checkBox = QtGui.QStandardItem()
				checkBox.setCheckable(True)
				self.foldersModel.appendRow([QtGui.QStandardItem(folderPath), checkBox])
		addFolderButton.clicked.connect(add_folder)
		
		removeFolderButton = QtGui.QPushButton(_('Remove'))
		buttonsLayout = QtGui.QHBoxLayout()
		buttonsLayout.addWidget(addFolderButton)
		buttonsLayout.addWidget(removeFolderButton)
		
		foldersLayout.addWidget(foldersView)
		foldersLayout.addLayout(buttonsLayout)
		foldersWidget = QtGui.QWidget()
		foldersWidget.setLayout(foldersLayout)
		self.widgets['folders'] = foldersWidget
		foldersWidget.hide()
		layout.addWidget(foldersWidget)
		
		self.setLayout(mainLayout)
		
	def accept(self):
		print 'TODO'
		QtGui.QDialog.accept(self)
		
	def loadSection(self, section):
		self.activeWidget.hide()
		self.activeWidget = self.widgets[section]
		self.activeWidget.show()
		
	
		
	def sectionActivated(self, index):
		print index.data()
		print self.sections.itemFromIndex(index).data()
		section = self.sections.data(self.sections.index(index.row(), 1))
		self.loadSection(section)
		print section
		