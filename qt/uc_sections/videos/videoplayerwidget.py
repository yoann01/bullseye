# -*- coding: utf-8 -*-
from PySide import QtGui, QtCore
from abstract.videoplayerwidget import AbstractVideoPlayerWidget 

class VideoPlayerWidget(AbstractVideoPlayerWidget, QtGui.QWidget):
	def __init__(self, player):
		QtGui.QWidget.__init__(self)
		layout = QtGui.QVBoxLayout()
		#videoArea = QtGui.QFrame()
		self.player = player
		#layout.addWidget(videoArea)
		#if in ('Phonon', 'MPlayer')
		layout.addWidget(self.player.getQtVideoWidget())
		
		self.setLayout(layout)
		
		
		#self.player.setUpQtVideo(videoArea)