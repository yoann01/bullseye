class AbstractVideoPlayerWidget(object):
	def __init__(self, player):
		self.player = player
		self.player.addConnectedWidget(self)
		print 'TODO'
		
	def stop(self):
		#self.cleanPlayFlag()
		self.player.stop()
		
	def togglePause(self):
		if self.player.isStopped():
			self.playNextTrack()
		else:
			self.player.togglePause()