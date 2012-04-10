# -*- coding: utf-8 -*-
from PySide import QtGui, QtCore
from qt.gui import modales

from common import settings

class MenuBar(QtGui.QMenuBar):
	def __init__(self, parent):
		self.core = parent
		QtGui.QMenuBar.__init__(self, parent)
		toolsMenu = QtGui.QMenu(_('&Tools'))
		toolsMenu.addAction('settings', self.openSettings)
		self.addMenu(toolsMenu)
		
		parent.moduleLoaded.connect(self.loadModuleMenus)
		
		for module in self.core.loadedModules:
			self.loadModuleMenus(module)
		
		
	def loadModuleMenus(self, module):
		if(module == 'pictures' or module == 'videos'):
			pictures = QtGui.QMenu(_(module))
			#pictures.addAction(_("Check for doubloons"))
			pictures.addAction(_("Move to UC structure"))
			pictures.addSeparator()
			
			panelGroup = QtGui.QActionGroup(self)
			
			browserMode = settings.get_option(module + 's/browser_mode', 'panel')
			
			panes = pictures.addAction( _('Multi-panes'), lambda: self.core.managers[module].setBrowserMode('panes'))
			panes.setCheckable(True)
			if(browserMode == 'panes'):
				panes.setChecked(True)
			panes.setActionGroup(panelGroup)
			
			panel = pictures.addAction(_('All in one panel'), lambda: self.core.managers[module].setBrowserMode('panel'))
			panel.setCheckable(True)
			if(browserMode == 'panel'):
				panel.setChecked(True)
			panel.setActionGroup(panelGroup)

			self.addMenu(pictures)
		elif(module == 'music'):
			music = QtGui.QMenu(_('Music'))
			music.addAction(_('Reload covers'), self.core.BDD.reloadCovers)
			
			self.addMenu(music)
		

		
	def openSettings(self):
		dialog = modales.SettingsEditor()
		dialog.exec_()
