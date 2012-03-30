# -*- coding: utf-8 -*-
from PySide import QtGui, QtCore

class PropertiesPanel(QtGui.QWidget):
	def __init__(self):
		QtGui.QWidget.__init__(self)
		mainLayout = QtGui.QVBoxLayout()
		from qt.util.stardelegate.stareditor import StarEditor
		from qt.util.stardelegate.starrating import StarRating
		starEditor = StarEditor()
		starEditor.starRating = StarRating()
		mainLayout.addWidget(starEditor, 0)
		
		self.setLayout(mainLayout)