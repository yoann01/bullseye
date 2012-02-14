# -*- coding: utf-8 -*-
from PySide import QtGui, QtCore
from qt.gui import modales

class MenuBar(QtGui.QMenuBar):
	def __init__(self):
		QtGui.QMenuBar.__init__(self)
		self.addAction('settings', self.triggered)
		
	def triggered(self, action):
		print action
		dialog = modales.SettingsEditor()
		dialog.exec_()
		