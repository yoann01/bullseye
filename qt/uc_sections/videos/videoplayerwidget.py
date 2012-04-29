# -*- coding: utf-8 -*-
from PySide import QtGui, QtCore
from abstract.videoplayerwidget import AbstractVideoPlayerWidget 

class VideoPlayerWidget(AbstractVideoPlayerWidget, QtGui.QWidget):
	
	PLAY_ICON = QtGui.QIcon.fromTheme('media-playback-start')
	PAUSE_ICON = QtGui.QIcon.fromTheme('media-playback-pause')
	
	def __init__(self, player):
		QtGui.QWidget.__init__(self)
		layout = QtGui.QVBoxLayout()
		self.setLayout(layout) # Important to set layout before, so that video attachment is made correctly
		self.player = player
		if player.backend  in ('Phonon', 'MPlayer'):
			layout.addWidget(self.player.getQtVideoWidget(), 1)
		else:
			videoArea = QtGui.QFrame()
			layout.addWidget(videoArea, 1)
			self.player.setUpQtVideo(videoArea)
		
		self.progressBar = QtGui.QSlider(QtCore.Qt.Horizontal)
		self.progressBar.setTracking(False)
		self.progressBar.valueChanged.connect(self.seekTo)
		self.progressBar.setEnabled(False)
		
		self.timer = QtCore.QTimer()
		self.timer.setInterval(1000)
		self.timer.timeout.connect(self.showProgress)
		
		prevButton = QtGui.QPushButton(QtGui.QIcon.fromTheme('media-skip-backward'), None)
		prevButton.clicked.connect(self.playPrevious)
		self.playButton = QtGui.QPushButton(self.PLAY_ICON, None)
		self.playButton.clicked.connect(self.togglePause)
		nextButton = QtGui.QPushButton(QtGui.QIcon.fromTheme('media-skip-forward'), None)
		nextButton.clicked.connect(self.playNext)
		stopButton = QtGui.QPushButton(QtGui.QIcon.fromTheme('media-playback-stop'), None)
		stopButton.clicked.connect(self.stop)
		controlLayout = QtGui.QHBoxLayout()
		controlLayout.addWidget(prevButton)
		controlLayout.addWidget(self.playButton)
		controlLayout.addWidget(nextButton)
		controlLayout.addWidget(stopButton)
		controlLayout.addWidget(self.progressBar)
		layout.addLayout(controlLayout, 0)
		
		self.player.addConnectedWidget(self)
		
	def playPrevious(self):
		print 'todo'
		
	def playNext(self):
		print 'todo'
		
		
	def startUpdatingProgress(self):
		self.timer.start()
		self.progressBar.setEnabled(True)
		self.playButton.setIcon(self.PAUSE_ICON)
	
	def stopUpdatingProgress(self, resetProgress=False):
		self.timer.stop()
		self.playButton.setIcon(self.PLAY_ICON)
		if resetProgress:
			self.progressBar.setSliderPosition(0)
			self.progressBar.setEnabled(False)

	def seekTo(self, pos):
		self.player.seekTo(pos)
		
	def showProgress(self):
		self.progressBar.setSliderPosition(self.player.percentage * 100)
		
	def stop(self):
		self.player.stop()
		
	def togglePause(self):
		if self.player.isStopped():
			self.playNext()
		else:
			self.player.togglePause()
		