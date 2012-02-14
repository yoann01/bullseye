# -*- coding: utf-8 -*-
from common import settings
from PySide import QtGui, QtCore
from qt.util import treemodel

class SettingsEditor(QtGui.QDialog):
	def __init__(self):
		QtGui.QDialog.__init__(self)
		layout = QtGui.QHBoxLayout()
		
		TreeView = QtGui.QTreeView()
		self.sections = treemodel.TreeModel()
		TreeView.setModel(self.sections)
		TreeView.activated.connect(self.sectionActivated)
		
		self.widgets = {}
		
		generalLayout = QtGui.QFormLayout()
		self.CB_gui_framework = QtGui.QComboBox()
		self.CB_gui_framework.addItem('Gtk 2')
		self.CB_gui_framework.addItem('Qt 4')
		generalLayout.addRow(_('GUI framework'), self.CB_gui_framework)
		
		self.pictures_enabled = QtGui.QCheckBox(_('Enable pictures manager'))
		self.pictures_enabled.setChecked(settings.get_option('pictures/enabled', False))
		generalLayout.addRow(self.pictures_enabled)
		
		generalWidget = QtGui.QWidget()
		generalWidget.setLayout(generalLayout)
		self.widgets['general'] = generalWidget
		#generalWidget.hide()

		layout.addWidget(generalWidget)
		
		self.setLayout(layout)
		
		
		
	def sectionActivated(self, index):
		print index
		
	def loadSection(self, section):
		self.activeWidget = self.widgets[section]
		self.activeWidget.show()