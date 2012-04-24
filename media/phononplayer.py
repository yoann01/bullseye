import os
import sys

from PySide import QtCore, QtGui
try:
	from PySide.phonon import Phonon
except ImportError:
	app = QtGui.QApplication(sys.argv)
	QtGui.QMessageBox.critical(None, "Music Player",
		"Your Qt installation does not have Phonon support.",
		QtGui.QMessageBox.Ok | QtGui.QMessageBox.Default,
		QtGui.QMessageBox.NoButton)
	sys.exit(1)
	
class Player(QtCore.QObject):
	def __init__(self):
		self.backend = 'Phonon'
		QtCore.QObject.__init__(self)
		self.audioOuptut = Phonon.AudioOutput(Phonon.MusicCategory, self)
		self.player = Phonon.MediaObject(self)
		Phonon.createPath(self.player, self.audioOuptut)
		
		self.connectedWidgets = []
		#self.aboutToFinish.connect(self.onPlaybackEnded)
		
	@property
	def percentage(self):
		value = float(self.player.currentTime()) / float(self.player.totalTime())
		return value
		
	
	def addConnectedWidget(self, playerWidget):
		''' This allow me to not used gsignal and qt signal'''
		self.connectedWidgets.append(playerWidget)
		
	def load(self, filename):
		if filename.startswith('http://'):
			uri = filename
		else:
			uri = 'file://' + os.path.abspath(filename)
		self.player.setCurrentSource(Phonon.MediaSource(uri))
		
	def playTrack(self, element):
		self.load(element.path)
		self.play()
		element.flags.add('play')
		
	def play(self):
		self.player.play()
		for pwidget in self.connectedWidgets:
			pwidget.startUpdatingProgress()

	def pause(self):
		self.player.pause()
		for pwidget in self.connectedWidgets:
			pwidget.stopUpdatingProgress()

	def stop(self):
		self.player.stop()
		for pwidget in self.connectedWidgets:
			pwidget.stopUpdatingProgress(True)
		
	def is_paused(self):
		return self.player.state() == Phonon.PausedState
		
	def isStopped(self):
		return self.player.state() == Phonon.StoppedState
	
	def is_playing(self):
		return self.player.state() == Phonon.PlayingState
		
		
	def onPlaybackEnded(self):
		for pwidget in self.connectedWidgets:
			pwidget.playNextTrack(True)
			
	def seekTo(self, pos):
		'''
			@param pos : float ranging from 0 to 1
		'''
		self.player.seek(int(self.player.totalTime() * (float(pos) / float(100))))
			
	def getQtVideoWidget(self):
		videoArea = Phonon.VideoWidget()
		Phonon.createPath(self.player, videoArea)
		return videoArea