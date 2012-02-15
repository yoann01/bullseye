# -*- coding: utf-8 -*-
import sys
from PySide import QtGui
from common import messager, settings
from data.elements import Track

#Initialisation de la traduction
import gettext
gettext.install("bullseye")

import gobject

#Création de la classe Frame issue de QWidget. 
#Toute application graphique doit contenir au moins une telle classe.
class Frame(QtGui.QMainWindow):
	def __init__(self, parent=None):
		QtGui.QMainWindow.__init__(self, parent)
		
	#Redimensionnement de la fenêtre principale.
		self.resize(settings.get_option('gui/window_width', 700), settings.get_option('gui/window_height', 500))

	#Application de la police d'écriture Verdana à la fenêtre mais aussi à tous les widgets enfants. 
	#À noter que nous aurions aussi pu choisir la taille et la mise en forme (gras, italique...)
		self.setFont(QtGui.QFont("Verdana")) 

	#Titre de la fenêtre 
		self.setWindowTitle("Bullseye")

	#Utilisation d'une icône pour la fenêtre si celui est présent dans le répertoire courant... 
	#sinon on passe.
		try:
			self.setWindowIcon(QtGui.Icon("icon.jpg")) 
		except:pass
		self.NB_Main = QtGui.QTabWidget(self)
		self.NB_Main.setTabPosition(QtGui.QTabWidget.West)
		
		
		
		from data.bdd import MainBDD
		self.BDD = MainBDD()
		
		if(settings.get_option('pictures/preload', False)):
			self.loadMusic()
		else:
			button = QtGui.QPushButton('load')
			button.clicked.connect(self.loadMusic)
			self.NB_Main.addTab(button, "Music")
			
		
		
		
		#from qt.uc_sections.pictures.imagewidget import ImageWidget
		#self.NB_Main.addTab(ImageWidget(), 'Pictures')
		
		#layout = QtGui.QVBoxLayout()
		from qt.gui.menubar import MenuBar
		#layout.addWidget(MenuBar())
		#layout.addWidget(self.NB_Main)
		#self.setLayout(layout)
		
		self.setMenuBar(MenuBar())
		self.setCentralWidget(self.NB_Main)
		
		self.destroyed.connect(self.onWindowDestroyed)
	
	def closeEvent(self, e):
		self.BDD.quit()
		settings.MANAGER.save()
		print 'Good bye'
		
	
	def loadMusic(self):
		from qt.music.musicpanel import LibraryPanel
		from qt.music.playerwidget import PlayerWidget
		from media.playerr import Player
		#, Playlists_Panel
		from qt.music.queue import QueueManager
		player = Player()
		playerWidget = PlayerWidget(player)
		
		self.NB_Main.removeTab(self.NB_Main.currentIndex())
		self.HPaned_Music = QtGui.QSplitter(self)

		self.queueManager = QueueManager(playerWidget)
		self.libraryPanel = LibraryPanel(self.BDD, self.queueManager)
		self.HPaned_Music.addWidget(self.libraryPanel)
		
		
		
		
		rightLayout = QtGui.QVBoxLayout()
		rightLayout.addWidget(self.queueManager)
		
		dockPlayer = QtGui.QDockWidget('Player')
		dockPlayer.setFeatures(QtGui.QDockWidget.DockWidgetFloatable | QtGui.QDockWidget.DockWidgetMovable)
		dockPlayer.setWidget(playerWidget)
		rightLayout.addWidget(dockPlayer)
		rightWidget = QtGui.QWidget()
		rightWidget.setLayout(rightLayout)
		self.HPaned_Music.addWidget(rightWidget)
		
		self.HPaned_Music.setStretchFactor(0,0)
		self.HPaned_Music.setStretchFactor(1,1)
		
		self.NB_Main.addTab(self.HPaned_Music, "Music")
		
	def onWindowDestroyed(self):
		self.BDD.quit()
		settings.MANAGER.save()
		print 'Good bye'
        

#Les quatre lignes ci-dessous sont impératives pour lancer l'application.
app = QtGui.QApplication(sys.argv)
gobject.threads_init()
frame = Frame()
frame.show()
sys.exit(app.exec_())