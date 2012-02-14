# -*- coding: utf-8 -*-
from PySide import QtGui, QtCore
from PySide.QtCore import Qt

class PlayerWidget(QtGui.QWidget):
	PLAY_ICON = QtGui.QIcon.fromTheme('media-playback-start')
	PAUSE_ICON = QtGui.QIcon.fromTheme('media-playback-pause')
	
	def __init__(self, player):
		QtGui.QWidget.__init__(self)
		self.player = player
		self.player.addConnectedWidget(self)
		
		layout = QtGui.QHBoxLayout()
		
		#self.progressBar = QtGui.QProgressBar()
		self.progressBar = QtGui.QSlider(QtCore.Qt.Horizontal)
		self.progressBar.setTracking(False)
		self.progressBar.valueChanged.connect(self.seekTo)
		
		self.timer = QtCore.QTimer()
		self.timer.setInterval(1000)
		self.timer.timeout.connect(self.showProgress)
		
		# Data attributes
		self.jumpList = []
		self.currentTrack = None
		self.currentQueue = None
		self.currentJumpTrack = None
		
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
	
	def addToJumpList(self, queue, track, temp):
		# First we check that the jumpTrack is not already here
		jt = JumpTrack(queue, track, temp)
		i = 0
		while i < len(self.jumpList) and not self.jumpList[i].equals(jt):
			i+=1
		if i < len(self.jumpList) and self.jumpList[i].equals(jt): # jumpTrack already here, we delay it...
			self.jumpList.insert(i, JumpTrack(None, None, temp)) # ... by adding a dummy jump right before its position
			i+=1
		else:
			self.jumpList.append(jt) # Not there, just add it
			if temp:
				track.flags.add('tempjump')
			else:
				track.flags.add('permjump')
			
		track.priority = i+1
				
	def cleanPlayFlag(self):
		if self.currentJumpTrack != None and self.currentJumpTrack.temp:
			self.currentJumpTrack.track.flags.remove('play')
			self.currentJumpTrack.queue.refreshView(self.currentJumpTrack.track)
		elif self.currentTrack != None:
			try:
				self.currentTrack.flags.remove('play')
				self.currentQueue.refreshView(self.currentTrack)
			except KeyError:
				pass
		


	def play(self):
		if self.currentJumpTrack == None:
			self.player.playTrack(self.currentTrack)
			self.currentQueue.refreshView(self.currentTrack)
		else:
			self.player.playTrack(self.currentJumpTrack.track)
			self.currentJumpTrack.queue.refreshView(self.currentJumpTrack.track)
		
		
	def playDefaultTrack(self):
		self.currentTrack = self.queueManager.getDefaultTrack()
		self.currentQueue = self.queueManager.visibleQueue
		if(self.currentTrack != None):
			self.play()
	
	def playJumpTrack(self):
		self.currentJumpTrack = self.popJumpList()
		
		if self.currentJumpTrack != None:
			if self.currentJumpTrack.isDummy(): # Dummy jump used to delay a real jump
				self.currentJumpTrack = None
				return False
			else:
				if self.currentJumpTrack.temp:
					self.play()
				else: # Perm jump, retains data (currentQueue & currentTrack) and play
					self.currentTrack = self.currentJumpTrack.track
					if(self.currentQueue != self.currentJumpTrack.queue):
						self.currentQueue = self.currentJumpTrack.queue
					self.play()
				try:
					self.currentJumpTrack.track.flags.remove('tempjump')
				except:
					pass
				try:
					self.currentJumpTrack.track.flags.remove('permjump')
				except:
					pass
				return True
		return False;


	def playNextTrack(self, songFinished=False):
		if songFinished:
			self.currentTrack.incrementPlayCount()
			
		if(self.currentTrack is None):
			self.playDefaultTrack()
		else:
			self.cleanPlayFlag()
			if 'stop' not in self.currentTrack.flags:
				# First, process potential jump track
				if not self.playJumpTrack(): # No jump track, just play next track under this one 
					self.currentTrack = self.currentQueue.model.getNextTrack(self.currentTrack)
					if self.currentTrack is None:
						self.stop()
					else:
						self.play()
			else:
				self.currentTrack.flags.remove('stop');
				self.stop()
	
	def playPreviousTrack(self):
		self.cleanPlayFlag()
		self.currentTrack = self.currentQueue.model.getPreviousTrack(self.currentTrack)
		if self.currentTrack is None:
			self.stop()
		else:
			self.play()
		
	def playTrack(self, track, queue):
		self.currentQueue = queue
		self.currentTrack = track
		self.play()
		
	def popJumpList(self):
		if len(self.jumpList) != 0:
			jt = self.jumpList[0]
			self.jumpList.remove(jt)
		else:
			jt = None
		
		# Update priority
		for elt in self.jumpList:
			elt.track.priority -= 1
		return jt
	
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
		
	def stop(self):
		self.cleanPlayFlag()
		self.player.stop()
		
		
	def togglePause(self):
		if self.player.isStopped():
			self.playNextTrack()
		else:
			self.player.togglePause()
			
class JumpTrack:
	def __init__(self, queue, track, temp):
		self.queue = queue
		self.track = track
		self.temp = temp
	
	def equals(self, jt):
		return jt.track == self.track and jt.queue == self.queue
		
	def isDummy(self):
		return self.track == None