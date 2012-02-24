# -*- coding: utf-8 -*-
from PySide import QtGui, QtCore
from qt.gui import modales

class MenuBar(QtGui.QMenuBar):
	def __init__(self):
		QtGui.QMenuBar.__init__(self)
		toolsMenu = QtGui.QMenu(_('&Tools'))
		toolsMenu.addAction('settings', self.openSettings)
		self.addMenu(toolsMenu)
		
	def openSettings(self):
		dialog = modales.SettingsEditor()
		dialog.exec_()
		