# -*- coding: utf-8 -*-
from PySide import QtGui, QtCore
from abstract.videoplayerwidget import AbstractVideoPlayerWidget 

class VideoPlayerWidget(AbstractVideoPlayerWidget, QtGui.QWidget):
	def __init__(self, player):
		QtGui.QWidget.__init__(self)
		layout = QtGui.QVBoxLayout()
		
		self.player = player
		if player.backend  in ('Phonon', 'MPlayer'):
			layout.addWidget(self.player.getQtVideoWidget())
		else:
			videoArea = QtGui.QFrame()
			layout.addWidget(videoArea)
			self.player.setUpQtVideo(videoArea)
		
		
		self.setLayout(layout)