# -*- coding: utf-8 -*-
from PySide import QtGui, QtCore

class ImageWidget(QtGui.QGraphicsView):
	def __init__(self):
		QtGui.QGraphicsView.__init__(self)
		
		self.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
		scene = QtGui.QGraphicsScene(self)
		pic = QtGui.QPixmap('icons/8.jpg')
		#scene.addItem(QtGui.QGraphicsPixmapItem(pic))
		self.image = QtGui.QGraphicsPixmapItem(pic)
		scene.addItem(self.image)
		self.setScene(scene)
		self.show()
		
		# Data attributes
		self.zoom = 1
		
	def wheelEvent(self, e):
		pic = QtGui.QPixmap('icons/8.jpg')
		#scene.addItem(QtGui.QGraphicsPixmapItem(pic))
		#self.image.setPixmap(pic)
		
		if e.delta() > 0:
			factor = self.zoom / (self.zoom + 0.1)
			self.zoom += 0.1
		else:
			factor = self.zoom / (self.zoom - 0.1)
			self.zoom -= 0.1
		self.scale(factor, factor)
		
		self.centerOn(e.x(), e.y())
		print self.zoom
		print e.delta()
		print ''