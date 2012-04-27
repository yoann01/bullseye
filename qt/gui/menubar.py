# -*- coding: utf-8 -*-
from PySide import QtGui, QtCore
from qt.gui import modales

from common import settings

class MenuBar(QtGui.QMenuBar):
	def __init__(self, parent):
		self.core = parent
		QtGui.QMenuBar.__init__(self, parent)
		toolsMenu = QtGui.QMenu(_('&Tools'))
		
		toolsMenu.addAction(_('Check for new files'), self.checkForNewFiles)
		toolsMenu.addAction(_('Settings'), self.openSettings)
		self.addMenu(toolsMenu)
		
		parent.moduleLoaded.connect(self.loadModuleMenus)
		
		for module in self.core.loadedModules:
			self.loadModuleMenus(module)
			
			
	def checkForNewFiles(self):
		progressNotifier = self.core.statusBar.addProgressNotifier()
		self.core.BDD.check_for_new_files(progressNotifier)
		
		
	def loadModuleMenus(self, module):
		if(module == 'pictures' or module == 'videos'):
			pictures = QtGui.QMenu(_(module))
			#pictures.addAction(_("Check for doubloons"))
			pictures.addAction(_('Check for doubloons'), self.core.managers[module].containerBrowser.checkForDoubloons)
			pictures.addAction(_("Move to UC structure"))
			pictures.addSeparator()
			
			panelGroup = QtGui.QActionGroup(self)
			
			browserMode = settings.get_option(module + '/browser_mode', 'panel')

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
			def reloadCovers():
				progressNotifier = self.core.statusBar.addProgressNotifier()
				self.core.BDD.reloadCovers(progressNotifier)
			music = QtGui.QMenu(_('Music'))
			music.addAction(_('Reload covers'), reloadCovers)
			
			
			self.addMenu(music)
		

		
	def openSettings(self):
		dialog = modales.SettingsEditor()
		dialog.exec_()
		
class StatusBar(QtGui.QStatusBar):
	def __init__(self):
		QtGui.QStatusBar.__init__(self)
		
	def addProgressNotifier(self):
		notifier = ProgressNotifier(self)
		notifier.done.connect(self.removeNotifier)
		self.addWidget(notifier)
		return notifier
		
	def removeNotifier(self):
		notifier = self.sender()
		self.removeWidget(notifier)

class ProgressNotifier(QtGui.QProgressBar):
	
	valueRequested = QtCore.Signal(int)
	done = QtCore.Signal()
	
	def __init__(self, statusBar):
		QtGui.QProgressBar.__init__(self)
		self.statusBar = statusBar
		self.valueRequested.connect(self.setValue)
		
	def emitDone(self):
		self.done.emit()
		
	def pulse(self):
		self.setRange(0, 0)
		
	def setFraction(self, val):
		val *= 100
		if(self.maximum != 100):
			self.setMaximum(100)
		self.valueRequested.emit(val)

			
