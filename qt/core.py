# -*- coding: utf-8 -*-
## Import minimum obligatoire pour réaliser une application graphique en PySide.
import sys
from PySide import QtGui

#Création de la classe Frame issue de QWidget. 
#Toute application graphique doit contenir au moins une telle classe.
class Frame(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        
#Redimensionnement de la fenêtre principale.
        self.resize(600,500)

#Application de la police d'écriture Verdana à la fenêtre mais aussi à tous les widgets enfants. 
#À noter que nous aurions aussi pu choisir la taille et la mise en forme (gras, italique...)
        self.setFont(QtGui.QFont("Verdana")) 

#Titre de la fenêtre 
        self.setWindowTitle("Présentation PySide... Présentation des widgets de base")

#Utilisation d'une icône pour la fenêtre si celui est présent dans le répertoire courant... 
#sinon on passe.
        try:
            self.setWindowIcon(QtGui.Icon("icon.jpg")) 
        except:pass
        
	self.NB_Main = QtGui.QTabWidget(self)
	self.NB_Main.set_tab_pos(gtk.POS_LEFT)
        

#Les quatre lignes ci-dessous sont impératives pour lancer l'application.
app = QtGui.QApplication(sys.argv)
frame = Frame()
frame.show()
sys.exit(app.exec_())