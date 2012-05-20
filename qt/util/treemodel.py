from PySide import QtGui, QtCore
from PySide.QtCore import Qt

class TreeItem(object):
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def append(self, item):
        self.childItems.append(item)
        return item

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        try:
            return self.itemData[column]
        except IndexError:
            return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0

class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self, parent=None):
        super(TreeModel, self).__init__(parent)

        self.rootItem = TreeItem(("Title", "Summary"))
        #self.setupModelData(data.split('\n'), self.rootItem)

    def append(self, parentNode, item):
	    if(parentNode is None):
		    parentNode = self.rootItem
	    rowCount = self.rowCount(QtCore.QModelIndex())
	    self.beginInsertRows(QtCore.QModelIndex(), rowCount, rowCount + 1)
	    self.endInsertRows()
	    return parentNode.append(item)
    
    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

        if role != QtCore.Qt.DisplayRole:
            return None

        item = index.internalPointer()

        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.rootItem.data(section)

        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem or parentItem == None:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()
        
    def reset(self):
	self.beginResetModel()
	#self.beginRemoveRows(QtCore.QModelIndex(), 0, 0)
	self.rootItem = TreeItem(("Title", "Summary"))
	#self.endRemoveRows()
	self.endResetModel()
	

    def setupModelData(self, lines, parent):
        parents = [parent]
        indentations = [0]

        number = 0

        while number < len(lines):
            position = 0
            while position < len(lines[number]):
                if lines[number][position] != ' ':
                    break
                position += 1

            lineData = lines[number][position:].strip()

            if lineData:
                # Read the column data from the rest of the line.
                columnData = [s for s in lineData.split('\t') if s]

                if position > indentations[-1]:
                    # The last child of the current parent is now the new
                    # parent unless the current parent has no children.

                    if parents[-1].childCount() > 0:
                        parents.append(parents[-1].child(parents[-1].childCount() - 1))
                        indentations.append(position)

                else:
                    while position < indentations[-1] and len(parents) > 0:
                        parents.pop()
                        indentations.pop()

                # Append a new item to the current parent's list of children.
                parents[-1].appendChild(TreeItem(columnData, parents[-1]))

            number += 1
            
            
            
            
            
            
class SimpleTreeItem(TreeItem):
	def __init__(self, parent, key, icon, label):
		TreeItem.__init__(self, label, parent)
		self.key = key
		self.label = label
		self.iconPath = icon
		self.icon = None
		self.subelements = []
		
	def __str__( self ):
		return self.label
		
	def __repr__(self):
		return self.label



class SimpleTreeModel(TreeModel):
	def __init__(self):
		TreeModel.__init__(self)


	def columnCount(self, parent):
		return 1

	def data(self, index, role):
		if not index.isValid():
			return None
		item = index.internalPointer()
		if role == Qt.DisplayRole:
			if index.column() == 0:
				return item.label
		elif role == Qt.DecorationRole and index.column() == 0:
			if(item.icon is None):
				try:
					path = item.iconPath
					item.icon = QtGui.QPixmap(path)
					#item.icon = item.icon.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation) #scaledToHeight(icon_size)
						
				except:
					item.icon = None
			
			return item.icon
		return None

	#def flags(self, index):
		#return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled
	
	#def headerData(self, section, orientation, role):
		#if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			#if section == 0:
				#return 'Icon'
			#elif section == 1:
				#return 'Label'
			#elif section == 2:
				#return _('Count')
			
		#return None