# -*- coding: utf-8 -*-
from PySide import QtGui, QtCore

class ImageWidget(QtGui.QGraphicsView):
	def __init__(self):
		QtGui.QGraphicsView.__init__(self)
		
		self.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
		scene = QtGui.QGraphicsScene(self)
		self.pic = QtGui.QPixmap('icons/8.jpg')
		#scene.addItem(QtGui.QGraphicsPixmapItem(pic))
		self.image = QtGui.QGraphicsPixmapItem(self.pic)
		scene.addItem(self.image)
		self.setScene(scene)
		self.show()
		
		# Data attributes
		self.zoom = 1
		self.scaleFactor = 1.0
		
	def wheelEvent(self, e):
		#scene.addItem(QtGui.QGraphicsPixmapItem(pic))
		#self.image.setPixmap(pic)
		
		if e.delta() > 0:
			self.scaleFactor *= 1.25
			self.scale(1.25, 1.25)
			return
			self.image.setPixmap(self.pic.scaled(self.scaleFactor * self.pic.size()))
			#self.scaleImage(1.25)
			
			return
			factor = self.zoom / (self.zoom + 0.1)
			self.zoom += 0.1
		else:
			self.scaleFactor *= 0.8
			self.scale(0.8, 0.8)
			return
			self.image.setPixmap(self.pic.scaled(self.scaleFactor * self.pic.size()))
			#self.scaleImage(0.8)
			return
			factor = self.zoom / (self.zoom - 0.1)
			self.zoom -= 0.1
		self.scale(factor, factor)
		
		self.centerOn(e.x(), e.y())
		print self.zoom
		print e.delta()
		print ''
	
	def scaleImage(self, factor):
		self.scaleFactor *= factor
		self.scale(factor, factor)
		
class SimpleImageWidget(QtGui.QScrollArea):
	def __init__(self):
		QtGui.QScrollArea.__init__(self)
		pic = QtGui.QPixmap('icons/8.jpg')
		self.image = QtGui.QLabel()
		self.image.setSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)
		self.image.setScaledContents(True)
		self.image.setPixmap(pic)
		
		self.setWidget(self.image)
		self.scaleFactor = 1.0
		
	def wheelEvent(self, e):
		print e.delta()
		#scene.addItem(QtGui.QGraphicsPixmapItem(pic))
		#self.image.setPixmap(pic)
		
		if e.delta() > 0:
			self.scaleImage(1.25)
			return
			factor = self.zoom / (self.zoom + 0.1)
			self.zoom += 0.1
		else:
			self.scaleImage(0.8)
			return
			factor = self.zoom / (self.zoom - 0.1)
			self.zoom -= 0.1
		#self.scale(factor, factor)
		
		print self.zoom
		print e.delta()
		print ''
		
	def scaleImage(self, factor):
		self.scaleFactor *= factor
		self.image.resize(self.scaleFactor * self.image.pixmap().size())
		#self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
		#self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)
		#self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
		#self.zoomOutAct.setEnabled(self.scaleFactor > 0.333)