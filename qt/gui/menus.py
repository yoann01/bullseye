# -*- coding: utf-8 -*-
from PySide import QtGui, QtCore
from PySide.QtCore import Qt

class SpecialEltMenu(QtGui.QMenu):
	def __init__(self, elt):
		QtGui.QMenu.__init__(self)
		self.addAction(elt.ID)
		
		
	def show(self, pos):
		self.exec_(pos)