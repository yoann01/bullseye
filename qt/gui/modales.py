# -*- coding: utf-8 -*-
import os
from common import settings, xdg
from PySide import QtGui, QtCore
from qt.util import treemodel

class Criterion(QtGui.QWidget):
	FIELDS = (('artist', _('Artist')), ('album', _('Album')), ('rating', _('Rating')), ('playcount', _('Playcount')), ('path', _('Path')))
	NUMERIC_OPERATORS = ((" = ", _("equals")), (" < ", _("is inferior to")), (" > ", _("is superior to")), (" <= ", _("is lower than")), (" >= ", _("is at least")))
	OPERATORS = ((" = ", _('is')), (" != ", _('is not'), ), (" LIKE ", _("like")), (" NOT LIKE ", _("not like")))
	
	FIELDMODEL = QtGui.QStandardItemModel()
	for key, label in FIELDS:
		FIELDMODEL.appendRow([QtGui.QStandardItem(key), QtGui.QStandardItem(label)])
		
	OPERATORMODEL = QtGui.QStandardItemModel()
	for key, label in OPERATORS:
		OPERATORMODEL.appendRow([QtGui.QStandardItem(key), QtGui.QStandardItem(label)])
		
	NUMERIC_OPERATORSMODEL = QtGui.QStandardItemModel()
	for key, label in NUMERIC_OPERATORS:
		NUMERIC_OPERATORSMODEL.appendRow([QtGui.QStandardItem(key), QtGui.QStandardItem(label)])
		
	def __init__(self, config):
		'''
			config is a tuple containing a field, an operator and a value. eg ('artist', ' = ', 'AC/DC')
		'''
		QtGui.QWidget.__init__(self)
		layout = QtGui.QHBoxLayout()
		self.fieldCB = QtGui.QComboBox()
		self.fieldCB.setModel(self.FIELDMODEL)
		self.fieldCB.setModelColumn(1)
		
		pos = 0
		toMatch = config[0]
		while pos < len(self.FIELDS) and not self.FIELDS[pos][0] == toMatch :
			pos += 1
		if pos < len(self.FIELDS) and self.FIELDS[pos][0] == toMatch:
			self.fieldCB.setCurrentIndex(pos)
		
		self.fieldCB.currentIndexChanged[int].connect(self.setUpAccordingToField)
		
		self.operatorCB = QtGui.QComboBox()
		
		
		self.entryWidget = QtGui.QLineEdit()
		self.spinBox = QtGui.QSpinBox()
		self.spinBox.setMinimum(0)
		
		deleteButton = QtGui.QPushButton(QtGui.QIcon.fromTheme('list-remove'), None)
		deleteButton.clicked.connect(self.deleteLater)
		
		
		layout.addWidget(self.fieldCB, 0)
		layout.addWidget(self.operatorCB, 0)
		layout.addWidget(self.entryWidget)
		layout.addWidget(self.spinBox)
		layout.addWidget(deleteButton, 0)
		
		self.setLayout(layout)
		self.setUpAccordingToField()
		
		if config[0] in ('playcount', 'rating'):
			operators = self.NUMERIC_OPERATORS
			self.spinBox.setValue(config[2])
		else:
			operators = self.OPERATORS
			self.entryWidget.setText(config[2])
		
		pos = 0
		toMatch = config[1]
		while pos < len(operators) and not operators[pos][0] == toMatch :
			pos += 1
		if pos < len(operators) and operators[pos][0] == toMatch:
			self.operatorCB.setCurrentIndex(pos)
		
		
	def getConfig(self):
		field = self.FIELDS[self.fieldCB.currentIndex()]
		
		operatorModel = self.operatorCB.model()
		operatorKey = operatorModel.data(operatorModel.index(self.operatorCB.currentIndex(), 0))
		
		if field in ('playcount', 'rating'):
			value = self.spinBox.value()
		else:
			value = self.entryWidget.text()
		
		return field, operatorKey, value
		
		
	def setUpAccordingToField(self, pos=None):
		if pos is None:
			pos = self.fieldCB.currentIndex()

		if self.FIELDS[pos][0] in ('playcount', 'rating'):
			self.entryWidget.hide()
			self.spinBox.show()
			self.operatorCB.setModel(self.NUMERIC_OPERATORSMODEL)
		else:
			self.entryWidget.show()
			self.spinBox.hide()
			self.operatorCB.setModel(self.OPERATORMODEL)
		self.operatorCB.setModelColumn(1)
		
	
class CriterionManager(QtGui.QWidget):
	"""
		Widget to handle SQL Query creation with GUI
	"""
	def __init__(self):
		QtGui.QWidget.__init__(self)
		layout = QtGui.QVBoxLayout()
		
		BB = QtGui.QHBoxLayout()
		self.whatever = QtGui.QCheckBox(_("Whatever criterion matches"))
		BB.addWidget(self.whatever)
		
		self.randomOrder = QtGui.QCheckBox(_("Random order"))
		BB.addWidget(self.randomOrder)
		
		addButton = QtGui.QPushButton(QtGui.QIcon.fromTheme('list-add'), None)
		addButton.clicked.connect(self.addCriterion)
		BB.addWidget(addButton)
		
		self.criterionBox = QtGui.QVBoxLayout()
		layout.addLayout(self.criterionBox)
		layout.addLayout(BB, 0)
		
		self.setLayout(layout)
		
		
	def addCriterion(self, field=None, operator=None, condition=None):
		'''
			Ajoute un nouveau critère de séléction (à configurer graphiquement) qui sera traité lors de la validation
		'''
		self.criterionBox.addWidget(Criterion((field, operator, condition)), 0)
		

		
	def getConfig(self):
		"""
			Return all parameter in dict
		"""
		config = {}
		if self.randomOrder.isChecked():
			config['random'] = True
		else:
			config['random'] = False
			
		if self.whatever.isChecked():
			config['link'] = ' OR '
		else:
			config['link'] = ' AND '
		
		config['criterions'] = []
		for i in range(self.criterionBox.count()):
			config['criterions'].append(self.criterionBox.itemAt(i).widget().getConfig())
			
		return config
		
	def loadCriterions(self, dic):
		random = dic['random']
		logic_operator = dic['link']
		if(random):
			self.randomOrder.setCheckState(QtCore.Qt.Checked)
		if(logic_operator == " OR "):
			self.whatever.setCheckState(QtCore.Qt.Checked)
		
		crits = dic['criterions']
		for crit in crits:
			criterion = crit[0]
			operator = crit[1]
			condition = crit[2]
			self.addCriterion(criterion, operator, condition)
			
	def reset(self):
		self.randomOrder.setCheckState(QtCore.Qt.Unchecked)
		self.whatever.setCheckState(QtCore.Qt.Unchecked)

		for i in range(self.criterionBox.count()):
			self.criterionBox.itemAt(i).widget().deleteLater()


class DynamicPlaylistCreator(QtGui.QDialog):
	'''
		Créateur de fichiers contenant des paramètres pour créer une requête SQL séléctionnant des pistes y correspondant
	'''	
	def __init__(self, name=None):
		QtGui.QDialog.__init__(self)
		layout = QtGui.QVBoxLayout()
		nameLayout = QtGui.QHBoxLayout()
		self.nameEntry = QtGui.QLineEdit()
		nameLayout.addWidget(QtGui.QLabel(_('Name') + ' : '), 0)
		nameLayout.addWidget(self.nameEntry, 1)
		
		self.previousName = name
		if(name == None):
			self.setWindowTitle(_("Add a dynamic playlist"))
		else:
			self.setWindowTitle(_("Edit a dynamic playlist"))
			
		self.criterionManager = CriterionManager()
		
		layout.addLayout(nameLayout, 0)
		layout.addWidget(self.criterionManager, 1)
		buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
		buttonBox.accepted.connect(self.accept)
		buttonBox.rejected.connect(self.reject)
		layout.addWidget(buttonBox)
		
		if name == None:
			self.criterionManager.addCriterion()
		else:
			self.nameEntry.setText(name)
			self.loadCriterions(name)
			
		self.setLayout(layout)
		
	def accept(self):
		name = self.nameEntry.text()
		f = open(os.path.join(xdg.get_data_home(), 'playlists') + os.sep + 'dynamic' + os.sep  + name, 'w')
		f.write(str(self.criterionManager.getConfig()))
		
		QtGui.QDialog.accept(self)
		
	def exec_(self):
		if QtGui.QDialog.exec_(self) and QtGui.QDialogButtonBox.Ok:
			return self.nameEntry.text()
		else:
			return None
		
		
	def loadCriterions(self, name):
		f = open(os.path.join(xdg.get_data_home(), 'playlists') + os.sep + 'dynamic' + os.sep  + name, 'r')
		data = f.readlines()
		f.close()
		self.criterionManager.loadCriterions(eval(data[0]))
		
			
			
class FilterManager(QtGui.QWidget):
	"""
		Widget that handles filter managment with a CriterionManager
	"""
	def __init__(self, config):
		QtGui.QWidget.__init__(self)
		
		self.config = config
		model = QtGui.QStandardItemModel()
		for key in self.config.iterkeys():
			model.appendRow(QtGui.QStandardItem(key))
		self.filterCB = QtGui.QComboBox()
		self.filterCB.setModel(model)
		self.filterCB.currentIndexChanged[int].connect(self.loadFilter)
		addButton = QtGui.QPushButton(QtGui.QIcon.fromTheme('list-add'), None)
		addButton.clicked.connect(self.addFilter)
		deleteButton = QtGui.QPushButton(QtGui.QIcon.fromTheme('list-remove'), None)
		deleteButton.clicked.connect(self.deleteFilter)
		self.enabled = QtGui.QCheckBox(_('Enabled'))
		
		actionBox = QtGui.QHBoxLayout()
		actionBox.addWidget(self.enabled, 0)
		actionBox.addWidget(deleteButton, 0)
		actionBox.addWidget(self.filterCB, 1)
		actionBox.addWidget(addButton, 0)
		
		
		
		
		self.criterionManager = CriterionManager()
		
		layout = QtGui.QVBoxLayout()
		layout.addLayout(actionBox, 0)
		layout.addWidget(self.criterionManager, 1)
		self.setLayout(layout)
		
		try:
			self.filterCB.setCurrentIndex(0)
			self.activeFilter = self.filterCB.currentText()
		except:
			pass
		
	def addFilter(self):
		name = QtGui.QInputDialog.getText(self, _('New filter name'), _('Enter a name') + ' : ')[0]
		
		model = self.filterCB.model()
		model.appendRow(QtGui.QStandardItem(name))
		
		
	def deleteFilter(self):
		model = self.filterCB.model()
		filterName = self.filterCB.currentText()
		del self.config[filterName]
		self.activeFilter = None
		model.removeRows(self.filterCB.currentIndex(), 1)
		
		
	def getConfig(self):
		filter = self.filterCB.currentText()
		if(filter != None): # saving current
			self.config[filter] = self.criterionManager.getConfig()
			self.config[filter]['enabled'] = self.enabled.isChecked()
		return self.config
	
	def loadFilter(self):
		try:
			if(self.activeFilter != None): # saving previous
				self.config[self.activeFilter] = self.criterionManager.getConfig()
				self.config[self.activeFilter]['enabled'] = self.enabled.isChecked()
		except:
			pass
		
		filter = self.filterCB.currentText()
		self.activeFilter = filter
		self.criterionManager.reset()
		self.enabled.setCheckState(QtCore.Qt.Unchecked)
		try:
			self.criterionManager.loadCriterions(self.config[filter])
			if(self.config[filter]['enabled']):
				self.enabled.setCheckState(QtCore.Qt.Checked)
		except KeyError:
			pass


class SettingsEditor(QtGui.QDialog):
	def __init__(self):
		QtGui.QDialog.__init__(self)
		self.setWindowTitle(_('Settings editor'))
		mainLayout = QtGui.QVBoxLayout()
		buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
		buttonBox.accepted.connect(self.accept)
		buttonBox.rejected.connect(self.reject)
		layout = QtGui.QHBoxLayout()
		self.widgetLayout = layout
		mainLayout.addLayout(layout)
		mainLayout.addWidget(buttonBox)
		
		
		# --- Sections selector
		TreeView = QtGui.QTreeView(self)
		TreeView.setMinimumWidth(200)
		TreeView.header().setResizeMode(QtGui.QHeaderView.ResizeToContents)
		self.sections = treemodel.SimpleTreeModel()
		def addSection(key, text, iconPath=None, parent=None):
			node = treemodel.SimpleTreeItem(parent, key, iconPath, text)
			self.sections.append(parent, node)
			return node
			
		addSection('general', _('General'))
		addSection('folders', _('Indexed folders'))
		musicNode = addSection('music', _('Music'))
		addSection('music_scrobbler', _('Audioscrobbler'), None, musicNode)
		addSection('music_filters', _('Filters'), None, musicNode)
		addSection('videos', _('Videos'))
		
		
		TreeView.setModel(self.sections)
		#TreeView.header().setSectionHidden(1, True)
		TreeView.clicked.connect(self.sectionActivated)
		layout.addWidget(TreeView, 0)
		
		
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

		layout.addWidget(generalWidget, 1)
		
		foldersLayout = QtGui.QVBoxLayout()
		foldersView = QtGui.QTableView()
		foldersView.setMinimumWidth(400)

		foldersView.verticalHeader().hide()
		self.foldersModel = QtGui.QStandardItemModel(0, 2)
		self.foldersModel.setHorizontalHeaderLabels([_("Path"), _("Dig")])
		for path, dig in settings.get_option('music/folders', []):
				checkBox = QtGui.QStandardItem()
				checkBox.setCheckable(True)
				if dig:
					checkBox.setCheckState(QtCore.Qt.Checked)
				self.foldersModel.appendRow([QtGui.QStandardItem(path), checkBox])
			
		foldersView.setModel(self.foldersModel)
		foldersView.horizontalHeader().setResizeMode (0, QtGui.QHeaderView.Stretch)
		foldersView.horizontalHeader().setResizeMode (1, QtGui.QHeaderView.Fixed)
		
		
		addFolderButton = QtGui.QPushButton(QtGui.QIcon.fromTheme('list-add'), _('Add'))
		def add_folder():
				folderPath = QtGui.QFileDialog.getExistingDirectory(self)
				checkBox = QtGui.QStandardItem()
				checkBox.setCheckable(True)
				self.foldersModel.appendRow([QtGui.QStandardItem(folderPath), checkBox])
		addFolderButton.clicked.connect(add_folder)
		
		removeFolderButton = QtGui.QPushButton(QtGui.QIcon.fromTheme('list-remove'), _('Remove'))
		def remove_folder():
			selected = foldersView.selectedIndexes()
			selected.reverse()
			for index in selected:
				self.foldersModel.removeRows(index.row(), 1)
			
		removeFolderButton.clicked.connect(remove_folder)
		buttonsLayout = QtGui.QHBoxLayout()
		buttonsLayout.addWidget(addFolderButton)
		buttonsLayout.addWidget(removeFolderButton)
		
		foldersLayout.addWidget(foldersView)
		foldersLayout.addLayout(buttonsLayout)

		foldersWidget = QtGui.QWidget()
		foldersWidget.setLayout(foldersLayout)
		self.widgets['folders'] = foldersWidget
		foldersWidget.hide()
		layout.addWidget(foldersWidget, 1)
		
		
		
		# --- Music section ---
		musicLayout = QtGui.QFormLayout()
		
		self.CB_music_playback_lib = QtGui.QComboBox()
		libs = {'GStreamer':0, 'MPlayer':1, 'VLC':2, 'Phonon':3}
		self.CB_music_playback_lib.addItem('GStreamer')
		#self.CB_music_playback_lib.addItem('MPlayer')
		self.CB_music_playback_lib.addItem('VLC')
		self.CB_music_playback_lib.addItem('Phonon')
		self.CB_music_playback_lib.setCurrentIndex(libs[settings.get_option('music/playback_lib', 'Phonon')])
		musicLayout.addRow(_('Playback library')  + ' : ', self.CB_music_playback_lib)
		
		self.CB_icon_size_panel_music = QtGui.QComboBox()
		self.CB_icon_size_panel_music.addItem('16')
		self.CB_icon_size_panel_music.addItem('24')
		self.CB_icon_size_panel_music.addItem('32')
		self.CB_icon_size_panel_music.addItem('48')
		self.CB_icon_size_panel_music.addItem('64')
		self.CB_icon_size_panel_music.setCurrentIndex(settings.get_option('music/panel_icon_size', 32) / 16)
		musicLayout.addRow(_('Panel icon size') + ' : ', self.CB_icon_size_panel_music)
		musicWidget = QtGui.QWidget()
		musicWidget.setLayout(musicLayout)
		self.widgets['music'] = musicWidget
		musicWidget.hide()
		layout.addWidget(musicWidget, 1)
		
		# --- Audioscrobbler section ---
		self.audioscrobbler_login = QtGui.QLineEdit()
		self.audioscrobbler_login.setText(settings.get_option('music/audioscrobbler_login', ''))
		
		self.audioscrobbler_password = QtGui.QLineEdit()
		self.audioscrobbler_password.setEchoMode(QtGui.QLineEdit.Password)
		self.audioscrobbler_password.setText(settings.get_option('music/audioscrobbler_password', ''))
		scrobblerLayout = QtGui.QFormLayout()
		
		scrobblerLayout.addRow(_('Login') + ' : ', self.audioscrobbler_login)
		scrobblerLayout.addRow(_('Password') + ' : ', self.audioscrobbler_password)
		
		self.addWidgetFor('music_scrobbler', scrobblerLayout)
		
		# --- Music filters ---
		mfiltersWidget = FilterManager(settings.get_option('music/filters', {}))
		self.widgets['music_filters'] = mfiltersWidget
		mfiltersWidget.hide()
		layout.addWidget(mfiltersWidget, 1)
		
		
		
		# --- Videos section ---
		videosLayout = QtGui.QFormLayout()
		
		self.CB_video_playback_lib = QtGui.QComboBox()
		self.CB_video_playback_lib.addItem('GStreamer')
		#self.CB_video_playback_lib.addItem('MPlayer')
		self.CB_video_playback_lib.addItem('VLC')
		self.CB_video_playback_lib.addItem('Phonon')
		self.CB_video_playback_lib.setCurrentIndex(libs[settings.get_option('videos/playback_lib', 'Phonon')])
		videosLayout.addRow(_('Playback library')  + ' : ', self.CB_video_playback_lib)
		
		
		self.addWidgetFor('videos', videosLayout)
		
		
		
		self.setLayout(mainLayout)
		
	def accept(self):
		print 'TO COMPLETE'
		folders = []
		for i in range(self.foldersModel.rowCount()):
			folders.append((self.foldersModel.item(i, 0).text(), self.foldersModel.item(i, 1).checkState() == QtCore.Qt.Checked))
		settings.set_option('music/folders', folders)
		
		# --- Music settings --- :
		settings.set_option('music/playback_lib', self.CB_music_playback_lib.currentText())
		settings.set_option('music/panel_icon_size', int(self.CB_icon_size_panel_music.currentText()))
		settings.set_option('music/filters', self.widgets['music_filters'].getConfig())
		
		#Audioscrobbler settings :
		settings.set_option('music/audioscrobbler_login', self.audioscrobbler_login.text())
		settings.set_option('music/audioscrobbler_password', self.audioscrobbler_password.text())
		
		#Videos settings
		settings.set_option('videos/playback_lib', self.CB_video_playback_lib.currentText())
		
		#for UCmodule in ('videos',):
			#settings.set_option(UCmodule + '/indexed_extensions', self.widgets[UCmodule].extensions.text())
			#settings.set_option(UCmodule + '/preload', self.widgets[UCmodule].preload.isChecked())
			#settings.set_option(UCmodule + '/panel_icon_size', int(self.widgets[UCmodule].CB_icon_size_panel.currentText()))
		
		QtGui.QDialog.accept(self)
		
		
	def addWidgetFor(self, section, layout):
		widget = QtGui.QWidget()
		widget.setLayout(layout)
		self.widgets[section] = widget
		widget.hide()
		self.widgetLayout.addWidget(widget, 1)
		
	def loadSection(self, section):
		self.activeWidget.hide()
		self.activeWidget = self.widgets[section]
		self.activeWidget.show()
		
	
		
	def sectionActivated(self, index):
		section = index.internalPointer().key
		self.loadSection(section)

