# -*- coding: utf-8 -*-
from PySide import QtGui, QtCore
from PySide.QtCore import Qt

from data import elements

class SpecialEltMenu(QtGui.QMenu):
	def __init__(self, elt, pos):
		QtGui.QMenu.__init__(self)
		self.addAction(elt.ID)
		catThumb = self.addAction(_('Set as category thumbnail'))
		uniThumb = self.addAction(_('Set as universe thumbnail'))
		
		action = self.exec_(pos)
		if(action == catThumb):
			container = elements.Container(elt.c_ID, 'categorie', elt.module)
		elif(action == uniThumb):
			container = elements.Container(elt.u_ID, 'univers', elt.module)
		container.set_thumbnail_ID(elt.ID)
		
		
	def show(self, pos):
		self.exec_(pos)