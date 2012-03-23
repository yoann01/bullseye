# -*- coding: utf-8 -*-
import threading
import os
import logging
import gtk

import glib
import subprocess

from PIL import Image

from common import messager, settings, util, xdg
from data.bdd import BDD
from gui import menus


from PySide import QtGui, QtCore

from qt.util import treemodel
from abstract.ucpanel import UCPanelInterface 


class IconSelector(QtGui.QListView):
	def __init__(self, moduleType):
		QtGui.QListView.__init__(self)
		#self.setMovement(QtGui.QListView.Free)
		self.setViewMode(QtGui.QListView.IconMode)
		self.model = ThumbnailModel()
		self.setModel(self.model)

		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
		self.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
		self.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
		self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
		#self.setSelectionRectVisible(True)
		#self.setBatchSize(3)
		#self.setLayoutMode(QtGui.QListView.Batched)
		
		self.setSpacing(10)
		self.setStyleSheet(' QListView::item::selected::active {border-radius:5px; background-color: palette(highlight)}')
		#self.setStyleSheet('QListView::icon { border-radius:10px; background-color:orange;}');
		self.setMinimumHeight(170)

		self.setWrapping(False)
		self.activated.connect(self.onActivated)
		
	def onActivated(self, index):
		self.openElement(self.getEltAt(index.row()))
		
	def append(self, elt):
		self.model.append(elt)
		print self.contentsSize().height()
		print self.verticalScrollBar().sizeHint().height()
		
	def getEltAt(self, i):
		return self.model.items[i]
		
class ImageSelector(IconSelector):
	"""
		TODO intégrer Box_Controls
	"""
	def __init__(self, imageWidget):
		IconSelector.__init__(self, 'image')
		self.imageWidget = imageWidget
		
	def openElement(self, elt):
		self.imageWidget.loadFile(elt.path)
		
		
class ThumbnailModel(QtCore.QAbstractListModel):
	def __init__(self):
		QtCore.QAbstractListModel.__init__(self)
		self.items = []
		
	def append(self, elt):
		self.beginInsertRows(QtCore.QModelIndex(), 0, 1)
		self.items.append(elt)
		self.endInsertRows()
		
		
	def data(self, index, role):
		item = self.items[index.row()]
		if not index.isValid():
			return None
		elif role == QtCore.Qt.DisplayRole:
			return item.file
			if index.column() == 1:
				return self.tracks[index.row()].title
			elif index.column() == 2:
				return self.tracks[index.row()].album
			elif index.column() == 3:
				return self.tracks[index.row()].artist
			elif index.column() == 4:
				return self.tracks[index.row()].length
			elif index.column() == 5:
				return self.tracks[index.row()].playcount
			elif index.column() == 6:
				return self.tracks[index.row()].rating
		elif role == QtCore.Qt.DecorationRole:
			try:
				if(item.icon is None):
					item.icon = QtGui.QPixmap(item.thumbnail_path)
			except:
				item.icon = QtGui.QPixmap(item.thumbnail_path)
				
			return item.icon
	
	def flags(self, index):
		return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled
	
	def rowCount(self, parent):
		return len(self.items)