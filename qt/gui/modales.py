# -*- coding: utf-8 -*-
from common import settings
from PySide import QtGui, QtCore
from qt.util import treemodel

class Criterion(QtGui.QWidget):
	FIELDS = (('artist', _('Artist')), ('album', _('Album')), ('note', _('Rating')), ('compteur', _('Playcount')), ('path', _('Path')))
	def __init__(self):
		QtGui.QWidget.__init__(self)
		layout = QtGui.QHBoxLayout()
		self.setLayout(layout)
		
	
class CriterionManager(QtGui.QWidget):
	"""
		Widget to handle SQL Query creation with GUI
	"""
	def __init__(self):
		QtGui.QWidget.__init__(self)
		
		fieldsModel = QtGui.QStandardItemModel()
		for (key, label) in FIELDS:
			fieldsModel.appendRow([QtGui.QStandardItem(key), QtGui.QStandardItem(label)])
		self.liste = gtk.ListStore(str, str)
		self.liste.append(["artist", _("Artist")])
		self.liste.append(["album", _("Album")])
		self.liste.append(["note", _("Rating")])
		self.liste.append(["compteur", _("Play count")])
		self.liste.append(["path", _("Path")])
		
		self.liste_operateurs = gtk.ListStore(str, str)
		self.liste_operateurs.append([" = ", _("is")])
		self.liste_operateurs.append([" != ", _("is not")])
		self.liste_operateurs.append([" LIKE ", _("like")])
		self.liste_operateurs.append([" NOT LIKE ", _("not like")])
		
		self.liste_operateurs_note = gtk.ListStore(str, str)
		self.liste_operateurs_note.append([" = ", _("equals")])
		self.liste_operateurs_note.append([" < ", _("is inferior to")])
		self.liste_operateurs_note.append([" > ", _("is superior to")])
		self.liste_operateurs_note.append([" <= ", _("is lower than")])
		self.liste_operateurs_note.append([" >= ", _("is at least")])
		
		BB = gtk.HButtonBox()
		self.RB_Criterion = gtk.CheckButton(_("Whatever criterion matches"))
		self.RB_Random = gtk.CheckButton(_("Random order"))
		B_Add = gtk.ToolButton(gtk.STOCK_ADD)
		B_Add.connect("clicked", self.add_criterion)
		BB.add(self.RB_Criterion)
		BB.add(self.RB_Random)
		BB.add(B_Add)
		self.pack_end(BB, False)
		self.Box_Criteres = gtk.VBox()
		self.pack_start(self.Box_Criteres)
		
	def add_criterion(self, button=None, criterion=None, operator=None, condition=None):
		'''
			Ajoute un nouveau critère de séléction (à configurer graphiquement) qui sera traité lors de la validation
		'''
		Box_Critere = gtk.HBox(spacing=12)
		Box_Critere.set_border_width(2)
		
		CB_Critere = gtk.ComboBox()
		CB_Critere.set_model(self.liste)
		cell = gtk.CellRendererText()
		CB_Critere.pack_start(cell)
		CB_Critere.add_attribute(cell, "text", 1)
		if(criterion == None):
			CB_Critere.set_active(0)
			liste_op = self.liste_operateurs
		else:
			i = 0
			while(self.liste[i][0] != criterion and i < len(self.liste)):
				i += 1
			if(self.liste[i][0] == criterion):
				CB_Critere.set_active(i)
			else:
				print("error : bad criterion")
			if(criterion in ('note', 'compteur')):
				liste_op = self.liste_operateurs_note
			else:
				liste_op = self.liste_operateurs
				
		CB_Operateur = gtk.ComboBox()
		CB_Operateur.set_model(liste_op)
		CB_Operateur.pack_start(cell)
		CB_Operateur.add_attribute(cell, "text", 1)
		if(operator == None):
			CB_Operateur.set_active(0)
		else:
			i = 0
			while(i < len(liste_op) and liste_op[i][0] != operator):
				i += 1
			try:
				if(liste_op[i][0] == operator):
					CB_Operateur.set_active(i)
				else:
					logger.debug("error : bad operator")
			except IndexError:
				logger.debug('exception : bad operator ' + operator)
		
		E_Condition = gtk.Entry()
		if(condition != None):
			E_Condition.set_text(condition)
			
		B_Delete = gtk.ToolButton(gtk.STOCK_REMOVE)
		B_Delete.connect("clicked", self.delete_criterion, Box_Critere)
		Box_Critere.pack_start(CB_Critere, False)
		Box_Critere.pack_start(CB_Operateur, False)
		Box_Critere.pack_start(E_Condition)
		Box_Critere.pack_end(B_Delete, False)
		Box_Critere.show_all()
		self.Box_Criteres.pack_start(Box_Critere, False)
		CB_Critere.connect("changed", self.format_widgets, Box_Critere)
		
	def delete_criterion(self, button, Box_Critere):
		Box_Critere.destroy()
		
	def format_widgets(self, CB, Box):
		'''
			Formatte une ligne de critères pour que les widgets soient conformes au type
		'''
		children = Box.get_children()
		if (children[0].get_active_text() == "note" or children[0].get_active_text() == "compteur"):
			children[1].set_model(self.liste_operateurs_note)
			children[1].set_active(0)
			children[2].destroy()
			SB = gtk.SpinButton(climb_rate=1)
			SB.set_increments(1, 2)
			SB.set_range(0, 5)
			Box.pack_start(SB, False)
		else:
			children[1].set_model(self.liste_operateurs)
			children[1].set_active(0)
			children[2].destroy()
			E_Condition = gtk.Entry()
			Box.pack_start(E_Condition)
		Box.show_all()
		
	def get_config(self):
		"""
			Return all parameter in dict
		"""
		config = {}
		if(self.RB_Random.get_active()):
			config['random'] = True
		else:
			config['random'] = False
			
		if(self.RB_Criterion.get_active()):
			config['link'] = ' OR '
		else:
			config['link'] = ' AND '
		
		config['criterions'] = []
		for critere in self.Box_Criteres:
			children = critere.get_children()
			criterion = children[0].get_active_text()
			operator = children[1].get_active_text()
			condition =  children[2].get_text()
			t = (criterion, operator, condition)
			#column, operator, condition = criterion
			config['criterions'].append(t)
			
		return config
		
	def load_criterions(self, dic):
		random = dic['random']
		logic_operator = dic['link']
		if(random):
			self.RB_Random.set_active(True)
		if(logic_operator == " OR "):
			self.RB_Criterion.set_active(True)
		
		crits = dic['criterions']
		for crit in crits:
			criterion = crit[0]
			operator = crit[1]
			condition = crit[2]
			self.add_criterion(None, criterion, operator, condition)
			
	def reset(self):
		self.RB_Random.set_active(False)
		self.RB_Criterion.set_active(False)
		for critere in self.Box_Criteres:
			critere.destroy()

class SettingsEditor(QtGui.QDialog):
	def __init__(self):
		QtGui.QDialog.__init__(self)
		self.setWindowTitle(_('Settings editor'))
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
		self.sections = treemodel.SimpleTreeModel()
		def addSection(key, text, iconPath=None, parent=None):
			node = treemodel.SimpleTreeItem(parent, key, iconPath, text)
			self.sections.append(parent, node)
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
		section = index.internalPointer().key
		self.loadSection(section)

