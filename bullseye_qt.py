#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-
import sys
from PySide import QtCore, QtGui
from common import settings, util
from data.elements import Track

#Init translation
import gettext
filename = "locale/bullseye_Fr.mo"
trans = gettext.GNUTranslations(open( filename, "rb" ) )
# Param True : unicode
trans.install(True)
#gettext.install("bullseye")


class Frame(QtGui.QMainWindow):
	ready = QtCore.Signal()
	moduleLoaded = QtCore.Signal(str)
	
	def __init__(self, parent=None):
		QtGui.QMainWindow.__init__(self, parent)
		#print os.is_file(QtGui.QIcon.themeSearchPaths()[-1])
		if not QtGui.QIcon.hasThemeIcon("document-open"):
			import fallbackicons
			QtGui.QIcon.setThemeName('oxygen')
		self.move(settings.get_option('gui/window_x', 50), settings.get_option('gui/window_y', 50))
		self.resize(settings.get_option('gui/window_width', 700), settings.get_option('gui/window_height', 500))
		if(settings.get_option('gui/maximized', False)):
			self.maximized = True
			self.showMaximized()
		else:
			self.maximized = False

		self.setFont(QtGui.QFont("Verdana")) 

		self.setWindowTitle("Bullseye")

		try:
			self.setWindowIcon(QtGui.QIcon("icons/bullseye.png"))
		except:pass
		self.NB_Main = QtGui.QTabWidget(self)
		self.NB_Main.setTabPosition(QtGui.QTabWidget.West)
		
		
		from data.bdd import MainBDD
		self.BDD = MainBDD()
		self.loadedModules = []
		self.managers = {} # Managers are the big widget representing a module
		
		if(settings.get_option('music/preload', False)):
			self.loadMusic()
		else:
			button = QtGui.QPushButton('load')
			button.clicked.connect(self.loadMusic)
			self.NB_Main.addTab(button, _('Music'))
			
		if(settings.get_option('pictures/preload', False)):
			self.loadModule('pictures', True)
		else:
			button = QtGui.QPushButton('load')
			button.clicked.connect(lambda: self.loadModule('pictures'))
			self.NB_Main.addTab(button, _('Pictures'))
			
		
		if(settings.get_option('videos/preload', False)):
			self.loadSection('videos', True)
		else:
			button = QtGui.QPushButton('load')
			button.clicked.connect(lambda: self.loadModule('videos'))
			self.NB_Main.addTab(button, _('Videos'))
		
		
		from qt.gui.menubar import MenuBar, StatusBar
		#layout.addWidget(MenuBar())
		#layout.addWidget(self.NB_Main)
		#self.setLayout(layout)
		
		self.statusBar = StatusBar()
		
		self.setMenuBar(MenuBar(self))
		self.setCentralWidget(self.NB_Main)
		self.setStatusBar(self.statusBar)
		
		
		
		self.NB_Main.currentChanged.connect(self.onModuleChanged)
		self.ready.connect(self.loadMusic)

		@util.threaded
		def emitReady():
			import time
			time.sleep(0.5)
			self.ready.emit()
			
		#emitReady()


	def changeEvent(self, e):
		if e.type() == QtCore.QEvent.WindowStateChange:
			if self.windowState() == QtCore.Qt.WindowMaximized:
				self.maximized = True
			elif self.windowState() == QtCore.Qt.WindowNoState:
				self.maximized = False
	
	def closeEvent(self, e):
		from data.bdd import BDD
		BDD.saveCache()
		if 'music' in self.loadedModules:
			self.playerWidget.stop()
			self.queueManager.saveState()
		if 'videos' in self.loadedModules:
			self.managers['videos'].videoPlayerWidget.stop()
			
		settings.set_option('gui/maximized', self.maximized)
		settings.MANAGER.save()
		settings.MANAGER.saveTimer.cancel()
		print 'Good bye'
		
	
	def loadMusic(self):
		self.loadedModules.append('music')
		
		from qt.music.musicpanel import BrowserPanel
		from qt.music.playerwidget import PlayerWidget
		
		backend = settings.get_option('music/playback_lib', 'Phonon')
		if backend == 'Phonon':
			from media.phononplayer import Player
		elif backend == 'GStreamer':
			from media.player import Player
		elif backend == 'VLC':
			from media.vlcplayer import Player
		player = Player()
		from qt.music.queue import QueueManager
		
		playerWidget = PlayerWidget(player)
		self.playerWidget = playerWidget
		
		index = self.NB_Main.currentIndex()
		self.NB_Main.removeTab(index)
		
		self.HPaned_Music = QtGui.QSplitter(self)

		self.queueManager = QueueManager(playerWidget)
		self.browserPanel = BrowserPanel(self.BDD, self.queueManager)
		self.HPaned_Music.addWidget(self.browserPanel)
		
		
		
		
		rightLayout = QtGui.QVBoxLayout()
		rightLayout.addWidget(self.queueManager)
		
		#dockPlayer = QtGui.QDockWidget('Player')
		#dockPlayer.setFeatures(QtGui.QDockWidget.DockWidgetFloatable | QtGui.QDockWidget.DockWidgetMovable)
		#dockPlayer.setWidget(playerWidget)
		rightLayout.addWidget(playerWidget)
		rightWidget = QtGui.QWidget()
		rightWidget.setLayout(rightLayout)
		self.HPaned_Music.addWidget(rightWidget)
		
		self.HPaned_Music.setStretchFactor(0,0)
		self.HPaned_Music.setStretchFactor(1,1)
		
		self.NB_Main.insertTab(index, self.HPaned_Music, _('Music'))
		self.NB_Main.setCurrentIndex(index)
		
		self.moduleLoaded.emit('music')
		
	def loadModule(self, moduleKey, preload=False):
		self.loadedModules.append(moduleKey)
		
		from qt.uc_sections.manager import UCManager
		widget = UCManager(moduleKey)
		self.managers[moduleKey] = widget
		
		if not preload:
			index = self.NB_Main.currentIndex()
			self.NB_Main.removeTab(index)
		
		if(moduleKey == 'pictures'):
			if preload:
				self.NB_Main.addTab(widget, _('Pictures'))
			else:
				self.NB_Main.insertTab(index, widget, _('Pictures'))
		elif(moduleKey == 'videos'):
			self.NB_Main.addTab(widget, _('Videos'))
			#self.NB_Main.insertTab(index, widget, _('Pictures'))
			
			
		if not preload:
			self.NB_Main.setCurrentIndex(index)
		self.moduleLoaded.emit(moduleKey)
		
		
	def onModuleChanged(self, index):
		if(index == 0 and 'music' not in self.loadedModules):
			self.loadMusic()
		if(index == 1 and 'pictures' not in self.loadedModules):
			self.loadModule('pictures')
		elif(index == 2 and 'videos' not in self.loadedModules):
			self.loadModule('videos')
		
	def resizeEvent(self, e):
		if(not self.maximized):
			#pos = self.mapToGlobal(self.pos())
			settings.set_option('gui/window_x', self.pos().x())
			settings.set_option('gui/window_y', self.pos().y())
			settings.set_option('gui/window_width', e.size().width())
			settings.set_option('gui/window_height', e.size().height())
        

#Les quatre lignes ci-dessous sont impératives pour lancer l'application.
app = QtGui.QApplication(sys.argv)
app.setApplicationName('Bullseye');
print sys.argv
frame = Frame()
frame.show()
sys.exit(app.exec_())