# -*- coding: utf-8 -*-
class SimpleListModel(QtGui.QStandardItemModel):
 def __init__(self, mlist):
  QtGui.QStandardItemModel.__init__(self)
  self.setColumnCount(5)

  # Cache the passed data list as a class member.
  self._items = mlist

 # We need to tell the view how many rows we have present in our data.
 # For us, at least, it's fairly straightforward, as we have a python list of data,
 # so we can just return the length of that list.
 def rowCount(self, parent = QtCore.QModelIndex()):
  return len(self._items)

 # Here, it's a little more complex.
 # data() is where the view asks us for all sorts of information about our data:
 # this can be purely informational (the data itself), as well as all sorts of 'extras'
 # such as how the data should be presented.
 #
 # For the sake of keeping it simple, I'm only going to show you the data, and one presentational
 # aspect.
 #
 # For more information on what kind of data the views can ask for, take a look at:
 # http://doc.trolltech.com/4.6/qabstractitemmodel.html#data
 #
 # Oh, and just  to clarify: when it says 'invalid QVariant', it means a null QVariant.
 # i.e. QVariant().
 #
 # 'index' is of type QModelIndex, which actually has a whole host of stuff, but we
 # only really care about the row number for the sake of this tutorial.
 # For more information, see:
 # http://doc.trolltech.com/4.6/qmodelindex.html
 def data(self, index, role = Qt.DisplayRole):
  if role == Qt.DisplayRole:
   # The view is asking for the actual data, so, just return the item it's asking for.
   tr = self._items[index.row()]
   data = (tr.title, tr.artist, tr.album)
   return data
  elif role == Qt.BackgroundRole:
   # Here, it's asking for some background decoration.
   # Let's mix it up a bit: mod the row number to get even or odd, and return different
   # colours depending.
   # (you can, and should, more easily do this using this:
   # http://doc.trolltech.com/4.6/qabstractitemview.html#alternatingRowColors-prop
   # but I deliberately chose to show that you can put your own logic/processing here.)
   #
   # Exercise for the reader: make it print different colours for each row.
   # Implementation is up to you.
   if index.row() % 2 == 0:
    return QtGui.QColor(Qt.gray)
   else:
    return QtGui.QColor(Qt.lightGray)
  else:
   # We don't care about anything else, so make sure to return an empty QVariant.
   return None
   
   
class TreeNode(object):
	def __init__(self, parent, row):
		self.parent = parent
		self.row = row
		self.subnodes = self._getChildren()

	def _getChildren(self):
		raise NotImplementedError()	

	def append(self, elt):
		node = TreeNode(self, elt)
		self.subnodes.append(node)
		return node
  
class TreeModel(QAbstractItemModel):
	def __init__(self):
		QAbstractItemModel.__init__(self)
		self.rootNodes = self._getRootNodes()

	# à implémenter par la future classe fille
	def _getRootNodes(self):
		raise NotImplementedError()

	# cette méthode héritée de QAbstractItemModel doit retourner
	# l'indice de l'enregistrement en entrée moyennant le parent (un QModelIndex)
	# c.f. paragraph suivant pour plus d'explications.
	def index(self, row, column, parent):
		# si l'indice du parent est invalide
		if not parent.isValid():
			return self.createIndex(row, column, self.rootNodes[row])
		parentNode = parent.internalPointer()
		return self.createIndex(row, column, parentNode.subnodes[row])

		# cette méthode héritée de QAbstractItemModel doit retourner
		# l'indice du parent de l'indice donné en paramètre
		# ou un indice invalide (QModelIndex()) si le noeud n'a pas de parent
		# ou si la requête est incorrecte
		# c.f. paragraph suivant pour plus d'explications.
	def parent(self, index):
		if not index.isValid():
			return QModelIndex()
		# on récupère l'objet sous-jacent avec la méthode internalPointer de l'indice
		node = index.internalPointer()
		if node.parent is None:
			return QModelIndex()
		else:
			# si tout est valide alors on crée l'indice associé pointant vers le parent
			return self.createIndex(node.parent.row, 0, node.parent)

	def reset(self):
		self.rootNodes = self._getRootNodes()
		QAbstractItemModel.reset(self)

	def rowCount(self, parent):
		if not parent.isValid():
			return len(self.rootNodes)
		node = parent.internalPointer()
		return len(node.subnodes)

class LibraryItem:
	def __init__(self, icon, ID, label, playcount, rating, burn, rounded_burn, is_separator):
		self.icon = icon
		self.ID = ID
		self.label = label
		self.playcount = playcount
		self.rating = rating
		self.burn = burn
		self.rounded_burn = rounded_burn
		self.is_separator = is_separator
		
		self.subelements = []
		
class NamedElement(object): # notre structure interne pour gérer les objets
    def __init__(self, name, subelements=[]):
        self.name = name

# notre noeud concret implémentant getChildren
class NamedNode(TreeNode):
    def __init__(self, ref, parent, row):
        self.ref = ref
        TreeNode.__init__(self, parent, row)

	# renvoie la liste des noeuds fils en utilisant la liste subelements de 
	# notre objet (interne) NamedElement
    def _getChildren(self):
        return [NamedNode(elem, self, index)
            for index, elem in enumerate(self.ref.subelements)]
        
# et enfin notre modèle avec 
class NamesModel(TreeModel):
	def __init__(self, rootElements):
		self.rootElements = rootElements
		TreeModel.__init__(self)

	def _getRootNodes(self):
		return [NamedNode(elem, None, index)
			for index, elem in enumerate(self.rootElements)]

	def columnCount(self, parent):
		return 2

	# permet de récupérer les données liées à un indice et un rôle.
	# ces données peuvent ainsi varier selon le rôle.
	def data(self, index, role):
		if not index.isValid():
			return None
		node = index.internalPointer()
		if role == Qt.DisplayRole:
			if index.column() == 0:
				return node.ref.name.title
			elif index.column() == 1:
				return node.ref.name.album
		elif role == Qt.DecorationRole and index.column() == 0:
			return QtGui.QPixmap('icons/genre.png')
		return None

	def headerData(self, section, orientation, role):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			if section == 0:
				return 'Name'
			elif section == 1:
				return 'Album'
			
		return None
		
class LibraryModel(TreeModel):
	def __init__(self, rootElements=[]):
		self.rootElements = rootElements
		TreeModel.__init__(self)

		
	def _getRootNodes(self):
		return [NamedNode(elem, None, index)
			for index, elem in enumerate(self.rootElements)]

	def columnCount(self, parent):
		return 2

	# permet de récupérer les données liées à un indice et un rôle.
	# ces données peuvent ainsi varier selon le rôle.
	def data(self, index, role):
		if not index.isValid():
			return None
		node = index.internalPointer()
		if role == Qt.DisplayRole:
			if index.column() == 0:
				return node.row.label
			elif index.column() == 1:
				return node.row.playcount
		elif role == Qt.DecorationRole and index.column() == 0:
			return node.row.icon
		return None

	def headerData(self, section, orientation, role):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			if section == 0:
				return 'Name'
			elif section == 1:
				return 'Album'
			
		return None
	
	def append(self, elt):
		node = NamedNode(self, self, elt)
		self.rootElements.append(node)
		return node

		
		
		
class NodeContainer(object):
    def __init__(self):
        self._subnodes = None
        self._ref2node = {}
    
    #--- Protected
    def _createNode(self, ref, row):
        # This returns a TreeNode instance from ref
        raise NotImplementedError()
    
    def _getChildren(self):
        # This returns a list of ref instances, not TreeNode instances
        raise NotImplementedError()
    
    #--- Public
    def invalidate(self):
        # Invalidates cached data and list of subnodes without resetting ref2node.
        self._subnodes = None
    
    #--- Properties
    @property
    def subnodes(self):
        if self._subnodes is None:
            children = self._getChildren()
            self._subnodes = []
            for index, child in enumerate(children):
                if child in self._ref2node:
                    node = self._ref2node[child]
                    node.row = index
                else:
                    node = self._createNode(child, index)
                    self._ref2node[child] = node
                self._subnodes.append(node)
        return self._subnodes
    

class TreeNode(NodeContainer):
    def __init__(self, model, parent, row):
        NodeContainer.__init__(self)
        self.model = model
        self.parent = parent
        self.row = row
    
    @property
    def index(self):
        return self.model.createIndex(self.row, 0, self)
        
    def append(self, elt):
	    self.subnodes.append(elt)
    

class RefNode(TreeNode):
    """Node pointing to a reference node.
    
    Use this if your Qt model wraps around a tree model that has iterable nodes.
    """
    def __init__(self, model, parent, ref, row):
        TreeNode.__init__(self, model, parent, row)
        self.ref = ref
    
    def _createNode(self, ref, row):
        return RefNode(self.model, self, ref, row)
    
    def _getChildren(self):
        return list(self.ref)
    

class TreeModel(QAbstractItemModel, NodeContainer):
    def __init__(self):
        QAbstractItemModel.__init__(self)
        NodeContainer.__init__(self)
        self._dummyNodes = set() # dummy nodes' reference have to be kept to avoid segfault
    
    #--- Private
    def _createDummyNode(self, parent, row):
        # In some cases (drag & drop row removal, to be precise), there's a temporary discrepancy
        # between a node's subnodes and what the model think it has. This leads to invalid indexes
        # being queried. Rather than going through complicated row removal crap, it's simpler to
        # just have rows with empty data replacing removed rows for the millisecond that the drag &
        # drop lasts. Override this to return a node of the correct type.
        return TreeNode(self, parent, row)
    
    def _lastIndex(self):
        """Index of the very last item in the tree.
        """
        currentIndex = QModelIndex()
        rowCount = self.rowCount(currentIndex)
        while rowCount > 0:
            currentIndex = self.index(rowCount-1, 0, currentIndex)
            rowCount = self.rowCount(currentIndex)
        return currentIndex
    
    #--- Overrides
    def index(self, row, column, parent):
        if not self.subnodes:
            return QModelIndex()
        node = parent.internalPointer() if parent.isValid() else self
        try:
            return self.createIndex(row, column, node.subnodes[row])
        except IndexError:
            parentNode = parent.internalPointer() if parent.isValid() else None
            dummy = self._createDummyNode(parentNode, row)
            self._dummyNodes.add(dummy)
            return self.createIndex(row, column, dummy)
    
    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        node = index.internalPointer()
        if node.parent is None:
            return QModelIndex()
        else:
            return self.createIndex(node.parent.row, 0, node.parent)
    
    def reset(self):
        self.invalidate()
        self._ref2node = {}
        self._dummyNodes = set()
        QAbstractItemModel.reset(self)
    
    def rowCount(self, parent=QModelIndex()):
        node = parent.internalPointer() if parent.isValid() else self
        return len(node.subnodes)
    
    #--- Public
    def findIndex(self, rowPath):
        """Returns the QModelIndex at `rowPath`
        
        `rowPath` is a sequence of node rows. For example, [1, 2, 1] is the 2nd child of the
        3rd child of the 2nd child of the root.
        """
        result = QModelIndex()
        for row in rowPath:
            result = self.index(row, 0, result)
        return result
    
    @staticmethod
    def pathForIndex(index):
        reversedPath = []
        while index.isValid():
            reversedPath.append(index.row())
            index = index.parent()
        return list(reversed(reversedPath))
    
    def refreshData(self):
        """Updates the data on all nodes, but without having to perform a full reset.
        
        A full reset on a tree makes us lose selection and expansion states. When all we ant to do
        is to refresh the data on the nodes without adding or removing a node, a call on
        dataChanged() is better. But of course, Qt makes our life complicated by asking us topLeft
        and bottomRight indexes. This is a convenience method refreshing the whole tree.
        """
        columnCount = self.columnCount()
        topLeft = self.index(0, 0, QModelIndex())
        bottomLeft = self._lastIndex()
        bottomRight = self.sibling(bottomLeft.row(), columnCount-1, bottomLeft)
        self.dataChanged.emit(topLeft, bottomRight)