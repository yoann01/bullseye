# -*- coding: utf-8 -*-
from PySide import QtGui, QtCore

from common import settings

class UCManager(QtGui.QWidget):
	'''
		The package widget that contains all the others
	'''
	def __init__(self, moduleKey):
		QtGui.QWidget.__init__(self)
		
		self.fullScreen = False
		
		if(moduleKey == 'pictures'):
			self.module = 'picture'
			from qt.uc_sections.iconselector import ImageSelector
			from qt.uc_sections.pictures.imagewidget import SimpleImageWidget
			from qt.uc_sections.panel import UC_Panel, UC_Panes
			
			mainLayout = QtGui.QVBoxLayout()
			layout = QtGui.QHBoxLayout()
			imageWidget = SimpleImageWidget()
			self.elementSelector = ImageSelector(imageWidget)
			if(settings.get_option(self.module + 's/browser_mode', 'panel') == 'panes'):
				self.containerBrowser = UC_Panes(self.module, self.elementSelector)
			else:
				self.containerBrowser = UC_Panel(self.module, self.elementSelector)
			layout.addWidget(self.containerBrowser, 0)
			layout.addWidget(imageWidget, 1)
			mainLayout.addLayout(layout, 1)
			mainLayout.addWidget(self.elementSelector, 0)
			
			imageWidget.mouseDoubleClickEvent = self.toggleFullScreen
			imageWidget.keyPressEvent = self.onViewWidgetKeyPress


			
		if(moduleKey == 'videos'):
			self.module = 'video'
			from qt.uc_sections.iconselector import VideoSelector
			
			from qt.uc_sections.panel import UC_Panel
			backend = settings.get_option('videos/playback_lib', 'Phonon')
			
			from qt.uc_sections.videos.videoplayerwidget import VideoPlayerWidget
			if(backend == 'VLC'):
				from media import vlcplayer
				self.videoPlayerWidget = VideoPlayerWidget(vlcplayer.Player())
			elif(backend == 'MPlayer'):
				from media import mplayers
				self.videoPlayerWidget = VideoPlayerWidget(mplayers.Player())
			elif(backend == 'Phonon'):
				from media import phononplayer
				self.videoPlayerWidget = VideoPlayerWidget(phononplayer.Player())
			else:
				from media import player
				self.videoPlayerWidget = VideoPlayerWidget(player.Player())
				
			mainLayout = QtGui.QVBoxLayout()
			layout = QtGui.QHBoxLayout()
			self.elementSelector = VideoSelector(self.videoPlayerWidget)
			
			if(settings.get_option(self.module + 's/browser_mode', 'panel') == 'panes'):
				self.containerBrowser = UC_Panes(self.module, self.elementSelector)
			else:
				self.containerBrowser = UC_Panel(self.module, self.elementSelector)
				
			layout.addWidget(self.containerBrowser, 0)
			layout.addWidget(self.videoPlayerWidget, 1)
			mainLayout.addLayout(layout, 1)
			mainLayout.addWidget(self.elementSelector, 0)
			
			self.videoPlayerWidget.mouseDoubleClickEvent = self.toggleFullScreen
			
			
		self.setLayout(mainLayout)
		self.upLayout = layout
		

	def onViewWidgetKeyPress(self, e):
		if self.fullScreen:
			if e.key() == QtCore.Qt.Key_Right:
				self.elementSelector.loadNext()
			elif e.key() == QtCore.Qt.Key_Left:
				self.elementSelector.loadPrevious()
			
	def setBrowserMode(self, viewType):
		'''
			Change the widget used to display containers
		'''
		from qt.uc_sections.panel import UC_Panel, UC_Panes
		

		
		if(viewType == 'panel'):
			newObj = UC_Panel(self.module, self.elementSelector)
		else:
			newObj = UC_Panes(self.module, self.elementSelector)
		settings.set_option(self.module + 's/browser_mode', viewType)
			
		index = self.upLayout.indexOf(self.containerBrowser)
		self.containerBrowser.deleteLater()
		self.upLayout.insertWidget(index, newObj, 0)
		
		self.containerBrowser = newObj
	
	
	def toggleFullScreen(self, *args):
		if self.fullScreen:
			self.containerBrowser.show()
			self.elementSelector.show()
		else:
			self.containerBrowser.hide()
			self.elementSelector.hide()
		self.fullScreen = not self.fullScreen