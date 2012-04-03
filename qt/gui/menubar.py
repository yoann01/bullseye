# -*- coding: utf-8 -*-
from PySide import QtGui, QtCore
from qt.gui import modales

class MenuBar(QtGui.QMenuBar):
	def __init__(self, parent):
		self.core = parent
		QtGui.QMenuBar.__init__(self, parent)
		toolsMenu = QtGui.QMenu(_('&Tools'))
		toolsMenu.addAction('settings', self.openSettings)
		self.addMenu(toolsMenu)
		
		parent.moduleLoaded.connect(self.loadModuleMenus)
		
		
	def loadModuleMenus(self, module):
		if(module == 'pictures' or module == 'videos'):
			pictures = QtGui.QMenu(_(module))
			#pictures.addAction(_("Check for doubloons"))
			pictures.addAction(_("Move to UC structure"))
			pictures.addSeparator()
			
			panelGroup = QtGui.QActionGroup(self)
			
			panes = pictures.addAction( _('Multi-panes'), lambda: self.temp(module, panes, 'panes'))
			panes.setCheckable(True)
			panes.setActionGroup(panelGroup)
			
			panel = pictures.addAction(_('All in one panel'), lambda: self.temp(module, panel, 'panel'))
			panel.setCheckable(True)
			panel.setActionGroup(panelGroup)

			self.addMenu(pictures)
		
	def openSettings(self):
		dialog = modales.SettingsEditor()
		dialog.exec_()
		
	def temp(self, module, action, viewType):
		self.core.managers[module].setBrowserMode(viewType)
