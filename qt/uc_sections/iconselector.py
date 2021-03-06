# -*- coding: utf-8 -*-
import threading
import os
import logging
from PIL import Image

from common import messager, settings, util, xdg
from data.bdd import BDD

from PySide import QtGui, QtCore

from qt.util import treemodel
from abstract.ucpanel import UCPanelInterface 


class IconViewer(QtGui.QListView):
	def __init__(self, moduleType):
		QtGui.QListView.__init__(self)
		#self.setMovement(QtGui.QListView.Free)
		self.setViewMode(QtGui.QListView.IconMode)
		#self.setUniformItemSizes(True)
		self.model = ThumbnailModel()
		self.setModel(self.model)

		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		#self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
		self.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
		self.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
		self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
		#self.setSelectionRectVisible(True)
		#self.setBatchSize(3)
		#self.setLayoutMode(QtGui.QListView.Batched)
		
		self.setSpacing(10)
		self.setStyleSheet('QListView::item::selected::active {border-radius:5px; background-color: palette(highlight)}')
		#self.setStyleSheet('QListView::icon { border-radius:10px; background-color:orange;}');
		#self.setMinimumHeight(170)

		self.setWrapping(False)
		self.activated.connect(self.onActivated)
		
	def contextMenuEvent(self, event):
		from qt.gui.menus import  SpecialEltMenu
		elt = self.getEltAt(self.indexAt(event.pos()).row())
		menu = SpecialEltMenu(elt, self.mapToGlobal(event.pos()))
		
	
		
	def onActivated(self, index):
		self.parent().openElement(self.getEltAt(index.row()))
		
	def getEltAt(self, i):
		return self.model.items[i]
		
	def wheelEvent(self, e):
		if e.delta() > 0:
			self.horizontalScrollBar().setSliderPosition(self.horizontalScrollBar().sliderPosition() - self.horizontalScrollBar().singleStep())
		else:
			self.horizontalScrollBar().setSliderPosition(self.horizontalScrollBar().sliderPosition() + self.horizontalScrollBar().singleStep())
			
class AbstractIconSelector(QtGui.QWidget):
	def __init__(self, manager):
		QtGui.QWidget.__init__(self)
		layout = QtGui.QVBoxLayout()
		self.manager = manager
		self.iconViewer = IconViewer(self.manager.module)
		
		buttonGroup = QtGui.QButtonGroup()
		self.buttonBar = QtGui.QToolBar()
		self.buttonBar.addAction(QtGui.QIcon.fromTheme('go-previous'), None, self.loadPrevious)
		self.buttonBar.addAction(QtGui.QIcon.fromTheme('go-next'), None, self.loadNext)
		self.buttonBar.addAction(QtGui.QIcon.fromTheme('edit-clear'), None, self.clear)
		
		layout.addWidget(self.iconViewer, 1)
		layout.addWidget(self.buttonBar, 0)
		self.setLayout(layout)
		
		
	def append(self, elt):
		print elt.thumbnail_path
		self.iconViewer.model.append(elt)
		#print self.iconViewer.contentsSize().height()
		#print self.iconViewer.verticalScrollBar().sizeHint().height()
		
		
	def clear(self):
		self.iconViewer.model.reset()
		
	def loadNext(self):
		cur = self.iconViewer.currentIndex()
		if(cur.isValid()):
			new = cur.sibling(cur.row()+1, cur.column())
		else:
			new = self.iconViewer.model.index(0, 0)
		self.iconViewer.setCurrentIndex(new)
		self.openElement(self.iconViewer.getEltAt(new.row()))
		
		
	def loadPrevious(self):
		cur = self.iconViewer.currentIndex()
		if(cur.isValid()):
			new = cur.sibling(cur.row()-1, cur.column())	
		else:
			new = self.iconViewer.model.lastIndex()
		self.iconViewer.setCurrentIndex(new)
		self.openElement(self.iconViewer.getEltAt(new.row()))

		
class ImageSelector(AbstractIconSelector):
	def __init__(self, manager):
		AbstractIconSelector.__init__(self, manager)
		self.imageWidget = manager.elementViewer
		
		self.buttonBar.addSeparator()
		self.buttonBar.addAction(QtGui.QIcon.fromTheme('zoom-original'), None, lambda: self.imageWidget.setMode('original'))
		self.buttonBar.addAction(QtGui.QIcon.fromTheme('zoom-fit-best'), None, lambda: self.imageWidget.setMode('fit'))
		self.buttonBar.addAction(QtGui.QIcon.fromTheme('zoom-in'), None)
		self.buttonBar.addAction(QtGui.QIcon.fromTheme('zoom-out'), None)
		
		from qt.util.stardelegate.stareditor import StarEditor
		from qt.util.stardelegate.starrating import StarRating
		starEditor = StarEditor()
		starEditor.starRating = StarRating()
		starEditor.setCurrent(0)
		starEditor.editingFinished.connect(self.updateRating)
		starEditor.setEnabled(False)
		self.starWidget = starEditor
		self.buttonBar.addSeparator()
		self.buttonBar.addWidget(starEditor)
		
	def openElement(self, elt):
		self.manager.openElement(elt)
		self.starWidget.setEnabled(True)
		self.currentElt = elt
		self.starWidget.setCurrent(elt.rating)
		
	def updateRating(self):
		self.currentElt.setRating(self.starWidget.current)
	
	
class VideoSelector(AbstractIconSelector):
	def __init__(self, manager):
		AbstractIconSelector.__init__(self, manager)
		self.playerWidget = manager.elementViewer
		
	def openElement(self, elt):
		self.playerWidget.player.playTrack(elt)
		
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
			if item.module != 'picture':
				return item.file[:20] + (item.file[20:] and '..')
			else:
				return None
		elif role == QtCore.Qt.DecorationRole:
			try:
				if(item.icon is None):
					item.icon = QtGui.QPixmap(item.thumbnail_path)
					
			except:
				item.icon = QtGui.QPixmap(item.thumbnail_path)
				
			if item.icon.isNull():
				item.icon = QtGui.QPixmap(xdg.get_data_dir() + os.sep + 'icons' + os.sep + item.module + '.png')
				
			return item.icon
	
	def flags(self, index):
		return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled
		
	def lastIndex(self):
		return self.index(len(self.items)-1, 0)

	def mimeData(self, indexes):
		'''
			What is passed during drag operations
		'''
		data = QtCore.QMimeData()
		selection = []
		for i in indexes:
			selection.append(self.items[i.row()].ID)
		data.setData('bullseye/ucelements', str(selection))
		return data
		
	def mimeTypes(self):
		return ('bullseye/ucelements',)
	
	def reset(self):
		self.beginResetModel()
		self.items = []
		self.endResetModel()
		
	def rowCount(self, parent):
		return len(self.items)