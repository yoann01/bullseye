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
class Frame(QtGui.QWidget):
	def __init__(self, parent=None):
		QtGui.QWidget.__init__(self, parent)
		
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
		
		
		from qt.music.musicpanel import LibraryPanel
		from qt.music.playerwidget import PlayerWidget
		from media.playerr import Player
		#, Playlists_Panel
		from qt.music.queue import QueueManager
		from data.bdd import MainBDD
		self.BDD = MainBDD()
		
		player = Player()
		playerWidget = PlayerWidget(player)
		
		self.HPaned_Music = QtGui.QSplitter(self)
		self.pnl_1 = QtGui.QWidget(self.NB_Main)
		self.pnl_2 = QtGui.QWidget(self.NB_Main)
		self.queueManager = QueueManager(playerWidget)
		self.HPaned_Music.addWidget(LibraryPanel(self.BDD, self.queueManager))
		
		
		
		
		rightLayout = QtGui.QVBoxLayout()
		rightLayout.addWidget(self.queueManager)
		rightLayout.addWidget(playerWidget)
		rightWidget = QtGui.QWidget()
		rightWidget.setLayout(rightLayout)
		self.HPaned_Music.addWidget(rightWidget)
		
		self.HPaned_Music.setStretchFactor(0,0)
		self.HPaned_Music.setStretchFactor(1,1)
		
		self.NB_Main.addTab(self.HPaned_Music, "Music")
		
		from qt.uc_sections.pictures.imagewidget import ImageWidget
		self.NB_Main.addTab(ImageWidget(), 'Pictures')
		
		layout = QtGui.QVBoxLayout()
		from qt.gui.menubar import MenuBar
		layout.addWidget(MenuBar())
		layout.addWidget(self.NB_Main)
		self.setLayout(layout)
		
		self.destroyed.connect(self.onWindowDestroyed)
	
	def closeEvent(self, e):
		self.BDD.quit()
		settings.MANAGER.save()
		print 'Good bye'
		
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