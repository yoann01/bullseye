# -*- coding: utf-8 -*-
from PySide import QtGui, QtCore

class PropertiesPanel(QtGui.QWidget):
	def __init__(self):
		QtGui.QWidget.__init__(self)
		mainLayout = QtGui.QVBoxLayout()
		from qt.util.stardelegate.stareditor import StarEditor
		from qt.util.stardelegate.starrating import StarRating
		self.starWidget = StarEditor()
		self.starWidget.starRating = StarRating()
		self.starWidget.editingFinished.connect(self.updateRating)
		self.starWidget.setEnabled(False)
		
		self.titleLabel = QtGui.QLabel()
		self.sizeLabel = QtGui.QLabel()
		mainLayout.addWidget(self.titleLabel, 0)
		mainLayout.addWidget(self.sizeLabel, 0)
		mainLayout.addWidget(self.starWidget, 0)
		
		self.setLayout(mainLayout)
		
		
	@staticmethod
	def getFormatedSize(size):
		if size > 1000000:
			return str(size / 1000000) + ' Mo'
		elif size > 1000:
			return str(size / 1000) + ' Ko'
		else:
			return str(size) + ' o'
		
		
	def openElement(self, elt):
		self.currentElt = elt
		self.starWidget.setEnabled(True)
		self.starWidget.setCurrent(elt.rating)
		self.titleLabel.setText(elt.filename[:20] + (elt.filename[20:] and '..'))
		self.sizeLabel.setText(self.getFormatedSize(elt.size))
		
	def updateRating(self):
		self.currentElt.setRating(self.starWidget.current)