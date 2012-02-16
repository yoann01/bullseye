# -*- coding: utf-8 -*-
from PySide import QtGui, QtCore
from PySide.QtCore import Qt
from abstract.playerwidget import AbstractPlayerWidget 

class PlayerWidget(AbstractPlayerWidget, QtGui.QWidget):
	PLAY_ICON = QtGui.QIcon.fromTheme('media-playback-start')
	PAUSE_ICON = QtGui.QIcon.fromTheme('media-playback-pause')
	
	def __init__(self, player):
		QtGui.QWidget.__init__(self)
		AbstractPlayerWidget.__init__(self, player)
		
		# Widgets
		layout = QtGui.QHBoxLayout()
		
		#self.progressBar = QtGui.QProgressBar()
		self.progressBar = QtGui.QSlider(QtCore.Qt.Horizontal)
		self.progressBar.setTracking(False)
		self.progressBar.valueChanged.connect(self.seekTo)
		
		self.timer = QtCore.QTimer()
		self.timer.setInterval(1000)
		self.timer.timeout.connect(self.showProgress)
		
		prevButton = QtGui.QPushButton(QtGui.QIcon.fromTheme('media-skip-backward'), None)
		prevButton.clicked.connect(self.playPreviousTrack)
		self.playButton = QtGui.QPushButton(self.PLAY_ICON, None)
		self.playButton.clicked.connect(self.togglePause)
		nextButton = QtGui.QPushButton(QtGui.QIcon.fromTheme('media-skip-forward'), None)
		nextButton.clicked.connect(self.playNextTrack)
		stopButton = QtGui.QPushButton(QtGui.QIcon.fromTheme('media-playback-stop'), None)
		stopButton.clicked.connect(self.stop)
		layout.addWidget(prevButton)
		layout.addWidget(self.playButton)
		layout.addWidget(nextButton)
		layout.addWidget(stopButton)
		layout.addWidget(self.progressBar)
		self.setLayout(layout)
	


	def startUpdatingProgress(self):
		self.timer.start()
		self.playButton.setIcon(self.PAUSE_ICON)
	
	def stopUpdatingProgress(self, resetProgress=False):
		self.timer.stop()
		self.playButton.setIcon(self.PLAY_ICON)
		if resetProgress:
			self.progressBar.setSliderPosition(0)

	def seekTo(self, pos):
		self.player.seekTo(pos)
		
	def showProgress(self):
		self.progressBar.setSliderPosition(self.player.percentage * 100)	
	
			
