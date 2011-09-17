# -*- coding: utf-8 -*-
import gtk
import messager
from iconselector import IconSelector
class VideoPanel:
	def __init__(self, TreeView):
		self.liste_TV = gtk.ListStore(str)
		TreeView.set_model(self.liste_TV)
		colonne = gtk.TreeViewColumn('Column 0')
		TreeView.append_column(colonne)
		cell = gtk.CellRendererText()
		#pb = gtk.CellRendererPixbuf()
		#colonne.pack_start(pb, False)
		colonne.pack_start(cell, True)
		colonne.add_attribute(cell, 'text', 0)
		#colonne.set_attributes(pb, pixbuf=1)
		messager.diffuser('TS_video', self, self.liste_TV)
		TreeView.connect("row-activated", self.on_dossier_click)
		theme = gtk.icon_theme_get_default()
		#self.dirIcon = theme.load_icon(gtk.STOCK_FILE, 48, 0)
		#self.dirIcon = gtk.gdk.pixbuf_new_from_file("/home/piccolo/test.png")
		#i = 0
		#while i < 2:
			#self.liste.append(["mdr", "lol", self.dirIcon])
			#i += 1
			
	def on_dossier_click(self, widget, i, c):
		dossier = self.liste_TV[i][0]
		messager.diffuser('need_videos', self, [dossier, self.liste])
		
		
		
		

		