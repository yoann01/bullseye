# -*- coding: utf-8 -*-

class AbstractPlayerWidget(object):
	'''
		A base class inherited by both Qt & Gtk Music Player Widget
	'''
	def __init__(self, player):
		# ------- Data attributes ---------
		self.jumpList = []
		self.bridgesSrc = {}
		self.bridgesDest = {}
		self.currentTrack = None
		self.currentQueue = None
		self.currentJumpTrack = None
		self.player = player
		self.player.addConnectedWidget(self)
		
	def addToJumpList(self, queue, track, temp=False):
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
		queue.refreshView(track)

		
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
		
	def getCurrents(self):
		return (self.currentQueue, self.currentTrack)

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
					if self.currentTrack.bridgeSrc != None:
						self.currentTrack = self.bridgesDest[self.currentTrack.bridgeSrc]
					else:
						self.currentTrack = self.currentQueue.getNextTrack(self.currentTrack)
					if self.currentTrack is None:
						self.stop()
					else:
						self.play()
			else:
				self.currentTrack.flags.remove('stop');
				self.currentQueue.refreshView(self.currentTrack)
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