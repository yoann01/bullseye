# -*- coding: utf-8 -*-
import threading
import gtk

from common import messager
from data.elements import SpecialElement
from gui import menus
from gui.util import etoiles




class IconSelector(gtk.IconView):
	'''
		Objet permettant d'afficher des icônes associées à des données dont le type est spécifiée (par une chaîne).
		Support du glisser-déposer (DND) et d'envoi de message pour interragir avec les Panel du typé associé
		
		TODO thumbnails size
		TODO prevent doubloons
	'''
	def __init__(self, type):
		gtk.IconView.__init__(self)
		self.index = -1
		self.data_type = type
		
		#messager.inscrire(self.charger_liste, "des_" + self.data_type + "s")
		
		self.connect("drag-begin", self.explication)
		self.connect("drag-data-get", self.on_drag_data_get)
	
		
		#ordre : ID, chemin, libellé,  apperçu, note, categorie_ID, univers_ID
		self.liste = gtk.ListStore(int, str, str, gtk.gdk.Pixbuf, int, int, int)
		self.set_model(self.liste)
		#self.set_text_column(2)
		self.set_pixbuf_column(3)
		self.set_selection_mode(gtk.SELECTION_MULTIPLE)
		self.show_all()
		
		#Le IV peut servir de base pour un glisser-déposer
		self.enable_model_drag_source(gtk.gdk.MODIFIER_MASK,  [('text/plain', 0, 0)] ,
                  gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
                  
		#IconView.enable_model_drag_dest([('text/plain', 0, 0)],
                  #gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE)
		self.connect("item-activated", self.on_thumbnail_click)
		self.connect("button-press-event", self.on_button_press)
		
		self.openElement = None
		
		self.oneRow = True
		if(self.oneRow):
			self.set_columns(999)
			self.connect('scroll-event', self.onScroll)
			self.connect('set-scroll-adjustments', self.onSetAdj)
		
	
	def append_element(self, tuple):
		self.liste.append(tuple)
		
	def charger_liste(self, desItems):
		def traiter():
			gtk.gdk.threads_enter()
			for image in desItems:
				#image[0] = ID, image[1] = chemin, image[2] = nom, image[3] = thumbnail,  image[4] = note, image[5] = categorie_ID, 6 = univers_ID
				self.liste.append([image[0], image[1], image[2], image[3], image[4], image[5], image[6]])
			gtk.gdk.threads_leave()
		task = threading.Thread(target=traiter)
		task.start()
		
	
	def clear(self, b):
		self.liste.clear()
	
		
	def on_button_press(self, IconView, event):
		if event.button == 1:
			self.selection = IconView.get_selected_items()
		elif event.button == 3:
			#clic droit
			path = IconView.get_path_at_pos(int(event.x),int(event.y))
			if (path != None):
				
				tuple_ID = self.liste[path][0]
				m = menus.MenuSpecialItem(self.data_type, tuple_ID)
				m.popup(None, None, None, event.button, event.time)
				
	def on_drag_data_get(self, widget, drag_context, selection_data, info, timestamp):
		#Début d'un DND
		items = widget.get_selected_items() #Cela correspond en fait à l'index de l'unique image cliquée (auto séléctionnée par l'événement button-press)
		if items[0] in self.selection: #On vérifie que cet index ne figure pas dans l'ancienne séléction multiple
			items = self.selection #Si c'est le cas, cela veut dire que l'on voulait DND la séléction multiple et non l'unique image cliquée
		T_ID = []
		for item in items:
			ID = self.liste[item][0]
			T_ID.append(ID)
		selection_data.set_text(str(T_ID))
		
	def on_thumbnail_click(self, widget, i):
		print("Vous devez redéfinir la fonction on_thumbnail_click dans la classe fille (polymorphisme)")
	
	
	def onScroll(self, widget, event):
		currentValue = self.hAdjustement.get_value()
		if event.direction == gtk.gdk.SCROLL_UP:
			step = -50#self.hAdjustement.get_page_increment()
		else:
			step = 50 #self.hAdjustement.get_page_increment()
		newVal = currentValue + step

		maxVal = self.hAdjustement.get_upper() - self.hAdjustement.get_page_size()
		if(newVal > maxVal):
			newVal = maxVal
		self.hAdjustement.set_value(newVal)
		return True
		
	def onSetAdj(self, widget, hadj, vadj):
		# Used to retrieve horizontal scroll bar adjustement upon initialisation
		self.hAdjustement = hadj
		
	def explication(self, widget, drag_context):
		#Début d'un DND
		item = widget.get_selected_items()[0]
		print(item)
		print(self.selection)
		if item in self.selection:
			for item in self.selection:
				self.select_path(item)
			print('true')
		#ID = self.liste[item][0]
		#selection_data.set_text(str(ID))
		
		

class VideoSelector(IconSelector):
	def __init__(self):
		IconSelector.__init__(self, "video")
		self.set_text_column(2)
			
	def on_thumbnail_click(self, widget, i):
		element = SpecialElement('video', self.liste[i][0])
		path = self.liste[i][1]
		messager.diffuser('video_a_lire', self, element)
		
		
		
class ImageSelector(IconSelector):
	"""
		TODO intégrer Box_Controls
	"""
	def __init__(self, imageWidget, Box_Controls):
		IconSelector.__init__(self, "image")
		
		self.imageWidget = imageWidget
		
		
		#self.Image.connect_after("size-request", self.fit_window_size)
		#messager.inscrire(self.avancer, 'image_suivante')
		#messager.inscrire(self.reculer, 'image_precedente')
		#messager.inscrire(self.charger_images, 'desImages')
	
		
		#Ini boutons de contrôles
		B_Next = gtk.ToolButton(gtk.STOCK_MEDIA_NEXT)
		B_Prev = gtk.ToolButton(gtk.STOCK_MEDIA_PREVIOUS)
		B_Clear = gtk.ToolButton(gtk.STOCK_CLEAR)
		B_100 = gtk.ToolButton(gtk.STOCK_ZOOM_100)
		B_Zoom_Fit = gtk.ToolButton(gtk.STOCK_ZOOM_FIT)
		B_Zoom_In = gtk.ToolButton(gtk.STOCK_ZOOM_IN)
		B_Zoom_Out = gtk.ToolButton(gtk.STOCK_ZOOM_OUT)
		
		B_Prev.connect("clicked", self.reculer)
		B_Next.connect("clicked", self.avancer)
		B_Clear.connect('clicked', self.clear)
		
		B_100.connect('clicked', self.imageWidget.change_zoom, "original")
		B_Zoom_Fit.connect('clicked', self.imageWidget.change_zoom, "fit")
		B_Zoom_In.connect('clicked', self.imageWidget.change_zoom, "+")
		B_Zoom_Out.connect('clicked', self.imageWidget.change_zoom, "-")
		
		
		
		liste_categories = gtk.ListStore(int, str)
		#messager.diffuser('liste_sectionsI', self, liste_categories)
		CB = gtk.ComboBoxEntry()
		CB.set_model(liste_categories)
		CB.set_text_column(1)
		CB.set_active(0)
			
		B_Ajouter = gtk.Button(None, gtk.STOCK_ADD)
		B_Ajouter.connect('clicked', self.set_categorie_on_image, CB)
		
		self.rating_item = etoiles.RatingWidget(3, auto_update=False)
		self.rating_item.connect('rating-changed', self.modifier_note)
		self.rating_item.set_sensitive(False)
		self.rating_item.show_all()
		
		#BB = Button Bar
		BB = gtk.HButtonBox()
		BB.add(B_Prev)
		BB.add(B_Next)
		BB.pack_end(B_Clear)
		BB.pack_start(B_Zoom_In)
		BB.pack_start(B_Zoom_Out)
		BB.pack_start(B_100)
		BB.pack_start(B_Zoom_Fit)
		Box_Controls.pack_start(BB, False)
		Box_Controls.pack_start(CB, False)
		Box_Controls.pack_start(B_Ajouter, False)
		Box_Controls.pack_start(self.rating_item, False)
		Box_Controls.show_all()
		
		self.imageWidget.set_image('icons/bullseye.svg')

		
		

		

			
			
	def afficher_image(self):
		image_path = self.liste[self.index][1]
		self.imageWidget.set_image(image_path)
		self.rating_item.set_property('rating', self.liste[self.index][4])
		self.rating_item.set_sensitive(True)
		#self.Image.set_size_request(img.get_width(),img.get_height())
		
		
		
	def avancer(self, b):
		if(self.index < len(self.liste) - 1):
			self.unselect_all()
			self.index += 1
			self.select_path(self.index)
			self.scroll_to_path(self.index, True, 0, 0)
			#self.IconView.item_activated(5)
			self.afficher_image()
			
	
	def fit_window_size(self, w, allocation):
		
		pixbuf = self.Image.get_property('pixbuf')
		#width = pixbuf.get_width()
		#height = pixbuf.get_height()
		#adapted_width, adapted_height = self.adapter_taille(width, height)
		#pixbuf = pixbuf.scale_simple(int(adapted_width), int(adapted_height), gtk.gdk.INTERP_BILINEAR)
		#self.Image.set_property('pixbuf', pixbuf)
		print('ok')
	
	

	
	
	
	def modifier_note(self, w, note):
		self.liste[self.index][4] = note
		ID = self.liste[self.index][0]
		self.openElement.change_rating(w, note)
		#messager.diffuser('modification_note', self, ['image', ID, note])
		
	
		
	def on_thumbnail_click(self, widget, i):
		self.openElement = SpecialElement(self.liste[i][0], self.data_type)
		self.index = i[0]
		try:
			self.afficher_image()
		except:
			#Old trick of mine to repair a bug in moveToUCStructure
			#import os
			#if not os.path.isfile(self.openElement.path):
				#(shortname, extension) = os.path.splitext(self.openElement.file)
				#self.openElement.set_path(self.openElement.folder, shortname[:-2] + extension)
				#print shortname
				#print(shortname[:-2] + extension)
			pass
		print(self.get_visible_range())
		
		
	def reculer(self, b):
		if (self.index > 0):
			self.unselect_all()
			self.index += -1
			self.select_path(self.index)
			self.scroll_to_path(self.index, True, 0, 0)
			self.afficher_image()
			
	def set_categorie_on_image(self, b, CB):
		if(self.index == -1):
			return False
			
		image_ID = self.liste[self.index][0]
		liste = CB.get_model()
		categorie = CB.get_active_text()
		i = 0	
		while((i < len(liste) -1) and (liste[i][1] != categorie)):
			i += 1
			
		if(liste[i][1] != categorie):
			Dialog = gtk.MessageDialog(buttons=gtk.BUTTONS_YES_NO, message_format="Cette catégorie n'existe pas, voulez vous la créer?")
			reponse = Dialog.run()
			Dialog.destroy()
			if(reponse == -8): #Oui
				messager.diffuser('nouvelle_categorieI', self, categorie)
				messager.diffuser('liste_sectionsI', self, liste)
			elif(reponse == -9): #Non
				return False
		
		i= 0
		while((i < len(liste) -1) and (liste[i][1] != categorie)):
			i += 1
		
		#TODO
		if(liste[i][1] == categorie):
			categorie_ID = liste[i][0]
			messager.diffuser('imageINcategory', self, [image_ID, categorie_ID])
		
		
		
		
	