# -*- coding: utf-8 -*-
import gtk
import messager
import menus
import etoiles
from iconselector import IconSelector
from panel import Panel

class ImagePanel(Panel):
	def __init__(self):
		Panel.__init__(self, "image")
	
	
class ImagePPanel(Panel):
	def __init__(self, BDD, TreeView, TVI, CB):
		self.BDD = BDD
		self.data_type = "image"
		
		#Ini panel dossiers
		self.liste_TV = gtk.ListStore(str, str)
		self.BDD.charger_images(self.liste_TV)
		TreeView.set_model(self.liste_TV)
		colonne = gtk.TreeViewColumn('Column 0')
		TreeView.append_column(colonne)
		cell = gtk.CellRendererText()
		pb = gtk.CellRendererPixbuf()
		pb.set_property('stock-id', gtk.STOCK_DIRECTORY)
		colonne.pack_start(pb, True)
		colonne.pack_start(cell, True)
		colonne.add_attribute(cell, 'text', 1)
		TreeView.connect("row-activated", self.on_dossier_click)
		
		#Ini panel catégories
		self.liste_sections = gtk.TreeStore(int, str, gtk.gdk.Pixbuf)
		messager.diffuser('liste_sectionsI', self, ["category", self.liste_sections])
		TVI.set_model(self.liste_sections)
		colonne = gtk.TreeViewColumn('Column 27')
		TVI.append_column(colonne)
		cell = gtk.CellRendererText()
		pb = gtk.CellRendererPixbuf()
		colonne.pack_start(pb, False)
		colonne.pack_start(cell, True)
		colonne.add_attribute(cell, 'text', 1)
		colonne.add_attribute(pb, 'pixbuf', 2)
		TVI.connect("row-activated", self.on_section_click)
		TVI.connect("drag-data-received", self.on_drag_data_receive)
		TVI.connect("button-press-event", self.on_right_click)
		
		#Le TreeView sera la destination à toucher avec la souris
		TVI.enable_model_drag_dest([('text/plain', 0, 0)],
                  gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE)
                  
		
                  
		#Ini panel univers
		#liste_univers = gtk.ListStore(int, str)
		#messager.diffuser('liste_universI', self, liste_univers)
		#messager.inscrire(self.reload_sections, 'nouvelle_categorieI')
		
		LS_CB = gtk.ListStore(str, str)
		LS_CB.append(["category", "Categories"])
		LS_CB.append(["universe", "Universe"])
		cell = gtk.CellRendererText()
		CB.pack_start(cell)
		CB.add_attribute(cell, "text", 1)
		CB.set_model(LS_CB)
		CB.set_active(0)
		CB.connect("changed", self.changer_mode)
		self.CB = CB
		messager.inscrire(self.reload_sections, "new_categoryI")
		messager.inscrire(self.reload_sections, "new_universeI")

			
	def on_section_click(self, w, i, c):
		#ID = w.get_model()[i][0]
		section, ID = self.what_is(i)
		level = len(i)
		if(level == 2):
			if(section == "universe"):
				path_category = i[0]
				ID_category = self.liste_sections[path_category][0]
				messager.diffuser('need_data_of', self, [self.data_type, "category_and_universe", ID_category, ID])
			elif(section == "category"):
				path_universe = i[0]
				ID_universe = self.liste_sections[path_universe][0]
				messager.diffuser('need_data_of', self, [self.data_type, "category_and_universe", ID, ID_universe])
		else: #level = 1
			messager.diffuser('need_data_of', self, [self.data_type, section, ID])

	
	def changer_mode(self, CB):
		messager.diffuser('liste_sectionsI', CB, [CB.get_active_text(), self.liste_sections])
		
	def on_dossier_click(self, w, i, c):
		dossier = self.liste_TV[i][0]
		messager.diffuser('need_images', self, ["dossier", dossier])
	
	def on_drag_data_receive(self, TV_cate, drag_context, x, y, selection_data, info, timestamp):
		#fin d'un DND
		numero_tuple = TV_cate.get_dest_row_at_pos(x, y)[0]
		section, section_ID = self.what_is(numero_tuple)
		
		T_images_ID = eval(selection_data.get_text()) # eval => permet de retransformer la chaîne de caractères en tableau
		#print(T_images_ID)
		message = 'imageIN' + section
		messager.diffuser(message, self, [T_images_ID, section_ID])
			
	def on_right_click(self, TreeView, event):
		if event.button == 3:
			path = TreeView.get_path_at_pos(int(event.x),int(event.y))
			m = menus.MenuCU()
			m.popup(None, None, None, event.button, event.time)
			
	def reload_sections(self, new_section=None):
		messager.diffuser('liste_sectionsI', self, [self.CB.get_active_text(), self.liste_sections])
		
		
	def what_is(self, section_path):
		#Détermine le type de section (category ou universe) d'un chemin de l'arbre des sections, ainsi que son identifiant
		mode = self.CB.get_active_text()
		level = len(section_path)
		ID = self.liste_sections[section_path][0]
		if(level == 2):
			if(mode == "category"):
				section = "universe"
			elif(mode == "universe"):
				section = "category"
		else:
			section = mode
			
		return [section, ID]
	
	
	

		
		
		
		
class ImageSSSelector(IconSelector):
	def __init__(self, IconView, Image, Box_Controls):
		self.Image = Image

		#self.Image.connect_after("size-request", self.fit_window_size)
		self.Image.get_parent().connect("scroll-event", self.zoom)
		self.IconView = IconView
		self.index = -1
		#messager.inscrire(self.avancer, 'image_suivante')
		#messager.inscrire(self.reculer, 'image_precedente')
		messager.inscrire(self.charger_images, 'desImages')
		
		IconView.connect("drag-begin", self.tmp)
		IconView.connect("drag-data-get", self.on_drag_data_get)
	
		#ordre : id, x, x, thumbnail, note
		self.liste = gtk.ListStore(int, str, str, gtk.gdk.Pixbuf, int)
		IconView.set_model(self.liste)
		#IconView.set_text_column(1)
		IconView.set_pixbuf_column(3)
		IconView.show_all()
		
		#Le IV sera la base du glisser-déposer
		#IconView.enable_model_drag_source(gtk.gdk.MODIFIER_MASK, [('text/plain', 0, 0)],
                  #gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE)
                  
		#IconView.enable_model_drag_dest([('text/plain', 0, 0)],
                  #gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE)
		IconView.connect("item-activated", self.on_thumbnail_click)
		IconView.connect("button-press-event", self.on_button_press)
		#IconView.connect("selection-changed", self.on_selection_changed)
		
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
		B_100.connect('clicked', self.zoom, "original")
		B_Zoom_Fit.connect('clicked', self.zoom, "fit")
		B_Zoom_In.connect('clicked', self.zoom, "+")
		B_Zoom_Out.connect('clicked', self.zoom, "-")
		
		
		
		liste_categories = gtk.ListStore(int, str)
		messager.diffuser('liste_sectionsI', self, liste_categories)
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
		BB.pack_start(B_100)
		BB.pack_start(B_Zoom_Fit)
		BB.pack_start(B_Zoom_In)
		BB.pack_start(B_Zoom_Out)
		Box_Controls.pack_start(BB, False)
		Box_Controls.pack_start(CB, False)
		Box_Controls.pack_start(B_Ajouter, False)
		Box_Controls.pack_start(self.rating_item, False)
		Box_Controls.show_all()
		

		IconView.enable_model_drag_source(gtk.gdk.MODIFIER_MASK,  [('text/plain', 0, 0)] ,
                  gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
		
		self.Image.set_from_file('icons/bullseye.svg')
		self.mode = "zoom"
		self.zoom = 1
		
		
	
		
	def adapter_taille(self, width_orig, height_orig):
		width_orig=float(width_orig)
		height_orig=float(height_orig)
		width_max=float(self.Image.get_parent().allocation.width)
		height_max=float(self.Image.get_parent().allocation.height)
		if (width_orig/width_max) > (height_orig/height_max):
			height=int((height_orig/width_orig)*width_max)
			width=int(width_max)
			self.zoom = width_max/width_orig
		else:
			width=int((width_orig/height_orig)*height_max)
			height=int(height_max)
			self.zoom = height_max/height_orig	
		return width, height
			
			
	def afficher_image(self):
		image_path = self.liste[self.index][1]
		self.img_original = gtk.gdk.pixbuf_new_from_file(image_path)
		img = self.fit_zoom()
		self.Image.set_from_pixbuf(img)
		self.rating_item.set_property('rating', self.liste[self.index][4])
		self.rating_item.set_sensitive(True)
		#self.Image.set_size_request(img.get_width(),img.get_height())
		
		
		
	def avancer(self, b):
		if(self.index < len(self.liste) - 1):
			self.index += 1
			self.IconView.select_path(self.index)
			self.IconView.scroll_to_path(self.index, True, 0, 0)
			#self.IconView.item_activated(5)
			self.afficher_image()
			
		
	def charger_images(self, desImages):
		for image in desImages:
			#image[0] = ID, image[1] = chemin, image[2] = nom, image[3] = thumbnail,  image[4] = note
			self.liste.append([image[0], image[1], image[2], image[3], image[4]])
	
	def clear(self, b):
		self.liste.clear()
	
	def fit_window_size(self, w, allocation):
		
		pixbuf = self.Image.get_property('pixbuf')
		#width = pixbuf.get_width()
		#height = pixbuf.get_height()
		#adapted_width, adapted_height = self.adapter_taille(width, height)
		#pixbuf = pixbuf.scale_simple(int(adapted_width), int(adapted_height), gtk.gdk.INTERP_BILINEAR)
		#self.Image.set_property('pixbuf', pixbuf)
		print('ok')
	
	def fit_zoom(self):
		img = self.img_original
		width = img.get_width()
		height = img.get_height()
		if(self.mode == "fit"):
			adapted_width, adapted_height = self.adapter_taille(width, height)
		elif(self.mode == "zoom"):
			adapted_width = img.get_width() * self.zoom
			adapted_height = img.get_height() * self.zoom
			
		img = img.scale_simple(int(adapted_width), int(adapted_height), gtk.gdk.INTERP_BILINEAR)
		return img
		
		
	def modifier_note(self, w, note):
		self.liste[self.index][4] = note
		ID = self.liste[self.index][0]
		messager.diffuser('modification_note', self, ['image', ID, note])
		
	def on_button_press(self, IconView, event):
		if event.button == 1:
			self.selection = IconView.get_selected_items()
		elif event.button == 3:
			#clic droit
			path = IconView.get_path_at_pos(int(event.x),int(event.y))
			if (path != None):
				image_ID = self.liste[path][0]
				m = gtk.Menu()
				i = gtk.MenuItem(self.liste[path][1])
				rating_item = etoiles.RatingMenuItem(3, False)
				#i.connect('activate', self.enregistrer)
				m.append(i)
				m.append(rating_item)
				m.show_all()
				m.popup(None, None, None, event.button, event.time)
				
	def on_drag_data_get(self, widget, drag_context, selection_data, info, timestamp):
		#Début d'un DND
		items = widget.get_selected_items() #Cela correspond en fait à l'index de l'unique image cliquée (auto séléctionnée par l'événement button-press)
		if items[0] in self.selection: #On vérifie que cet index ne figure pas dans l'ancienne séléction multiple
			items = self.selection #Si c'est le cas, cela veut dire que l'on voulait DND la séléction multiple et non l'unique image cliquée
		
		T_images = []
		for item in items:
			ID = self.liste[item][0]
			T_images.append(ID)
		selection_data.set_text(str(T_images))
	
	def on_selection_changed(self, IV):
		selection = IV.get_selected_items()
		#if(len(selection) > 1):
		self.selection = selection
		
	def tmp(self, widget, drag_context):
		#Début d'un DND
		item = widget.get_selected_items()[0]
		print(item)
		print(self.selection)
		if item in self.selection:
			print('true')
		#ID = self.liste[item][0]
		#selection_data.set_text(str(ID))
		
	
		
	def on_thumbnail_click(self, widget, i):
		self.index = i[0]
		self.afficher_image()
		print(self.IconView.get_visible_range())
		
		
	def reculer(self, b):
		if (self.index > 0):
			self.index += -1
			self.IconView.select_path(self.index)
			self.IconView.scroll_to_path(self.index, True, 0, 0)
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
			
	def zoom(self, b, mode):
		try:
			if(mode.direction == gtk.gdk.SCROLL_UP):
				self.zoom += 0.1
			elif(mode.direction == gtk.gdk.SCROLL_DOWN):
				self.zoom -= 0.1
			self.mode = "zoom"
		except:
			print("Not a scroll")
			if (mode == "+"):
				self.zoom += 0.1
				self.mode = "zoom"
			elif(mode == "-"):
				self.zoom -= 0.1
				self.mode = "zoom"
			elif(mode == "original"):
				self.zoom = 1
				self.mode = "zoom"
			elif(mode == "fit"):
				self.mode = "fit"
		#self.mode = mode
		self.Image.set_from_pixbuf(self.fit_zoom())