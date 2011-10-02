# -*- coding: utf-8 -*-
import gtk
import os

from common import messager

from data import elements

from gui import modales
from gui.util import etoiles

class CreatePlaylistMenu(gtk.Menu):
	def __init__(self):
		gtk.Menu.__init__(self)
		
		i = gtk.ImageMenuItem(_("Add an intelligent playlist"))
		image = gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_MENU)
                i.set_image(image)
                i.connect('activate', self.add_intelligent_playlist)
		self.append(i)
		
		i = gtk.ImageMenuItem(_("Add a playlist"))
		image = gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_MENU)
		i.set_image(image)
		i.connect('activate', self.add_playlist)
		self.append(i)
		
		self.show_all()
		
	def add_intelligent_playlist(self, button):
		d = modales.IntelligentPlaylistCreator()
		
	def add_playlist(self, button):
		DN = gtk.Dialog()
		Entry = gtk.Entry()
		hbox = gtk.HBox()
		hbox.pack_start(gtk.Label(_("Name") + " : "), False, 5, 5)
		hbox.pack_end(Entry)
		DN.vbox.add(hbox)
		
		DN.add_button('OK', 1)
		DN.add_button(_("Cancel"), 0)
		DN.show_all()
		action = DN.run()
		name = Entry.get_text()
		DN.destroy()
		if(action == 1):
			fichier = open('playlists/' + name,'w')
			fichier.close()
			messager.diffuser('playlist_ajoutee', self, ['personalised', name])


class MenuSpecialItem(gtk.Menu):
	"""
		menu popped on standard element (the ones with universe & categories stuff) right click
	"""
	def __init__(self, type_fichier, tuple_ID):
		self.type_fichier = type_fichier
		gtk.Menu.__init__(self)
		i = gtk.MenuItem(str(tuple_ID))
		file = elements.SpecialElement(type_fichier, tuple_ID)
		self.element = file
		rating_item = etoiles.RatingMenuItem(file.rating, False)
		rating_item.connect('rating-changed', file.change_rating)
		self.append(rating_item)
		
		
		self.append(i)
		i = gtk.MenuItem(self.element.path)
		self.append(i)
		
		i = gtk.MenuItem(str(self.element.size))
		self.append(i)
		
		i = gtk.ImageMenuItem(_("Set thumbnail as category thumbnail"))
		image = gtk.image_new_from_stock(gtk.STOCK_HOME, gtk.ICON_SIZE_MENU)
		i.set_image(image)
		i.connect('activate', self.on_set_container_thumbnail, 'categorie')
		self.append(i)
		
		i = gtk.ImageMenuItem(_("Set thumbnail as universe thumbnail"))
		image = gtk.image_new_from_stock(gtk.STOCK_HOME, gtk.ICON_SIZE_MENU)
		i.set_image(image)
		i.connect('activate', self.on_set_container_thumbnail, 'univers')
		self.append(i)
		
		i = gtk.ImageMenuItem(_("Move to category folder"))
		image = gtk.image_new_from_stock(gtk.STOCK_HOME, gtk.ICON_SIZE_MENU)
		i.set_image(image)
		i.connect('activate', self.move)
		self.append(i)
		
		self.show_all()
		
	def on_set_container_thumbnail(self, menuitem, container_type):
		if(container_type == 'categorie'):
			container_ID = self.element.c_ID
		else:
			container_ID = self.element.u_ID
		container = elements.Container(container_type, self.type_fichier, container_ID)
		container.set_thumbnail_ID(self.element.ID)
	
	def move(self, *args):
		# potentially remove os from import
		old_path = self.element.path
		new_path = '/home/piccolo/Images/' + str(self.element.c_ID) + '/' + self.element.file
		print("TODO")
		#self.element.set_path(
		#os.renames(old_path, new_path)
		


class MenuCU(gtk.Menu):
	"""
		menu popped on category or universe right click
	"""
	def __init__(self, container_type, type_fichier, id):
		self.type_fichier = type_fichier
		if(container_type == 'u'):
			container_type = 'univers'
		elif(container_type == 'c'):
			container_type = 'categorie'
		if(container_type != 'unknown'):
			self.container = elements.Container(container_type, self.type_fichier, id)
		gtk.Menu.__init__(self)
		
		i = gtk.ImageMenuItem(_("Add an universe"))
		image = gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_MENU)
		i.set_image(image)
		i.connect('activate', self.add_section, "universe", id)
		self.append(i)
		i = gtk.ImageMenuItem(_("Add a category"))
		image = gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_MENU)
		i.set_image(image)
		i.connect('activate', self.add_section, "category", id)
		self.append(i)
		
		i = gtk.ImageMenuItem(_("Remove"))
		image = gtk.image_new_from_stock(gtk.STOCK_DELETE, gtk.ICON_SIZE_MENU)
		i.set_image(image)
		i.connect('activate', self.delete)
		self.append(i)
		
		self.show_all()
		
	def add_section(self, button, type, parent_id):
		dialog = gtk.Dialog(buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
		box = dialog.get_content_area()
		hbox = gtk.HBox()
		hbox.pack_start(gtk.Label(_("Name") + " : "), False, 5, 5)
		entry = gtk.Entry()
		hbox.pack_start(entry)
		box.pack_start(hbox)
		box.show_all()
		reponse = dialog.run()
		section = entry.get_text()
		dialog.destroy()
		if(reponse == -3): #Valider
			if(type == "universe"):
				messager.diffuser('new_universe', self, [self.type_fichier, section, parent_id])
			else:
				messager.diffuser('new_category', self, [self.type_fichier, section, parent_id])
		elif(reponse == -2): #Annuler
			return False
	
	def delete(self, button):
		dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_YES_NO, _('Are you sure you want to delete container ' + self.container.label + '?'))
		resp = dialog.run()
		if resp == gtk.RESPONSE_YES:
			self.container.delete()
		dialog.destroy()
	
		
class PlaylistMenu(gtk.Menu):
	def __init__(self, unPlaylistPanel, uneLigne):
		gtk.Menu.__init__(self)
		i = gtk.ImageMenuItem(gtk.STOCK_DELETE)
		i.connect('activate', unPlaylistPanel.supprimer, uneLigne)
		self.append(i)
		i = gtk.ImageMenuItem(gtk.STOCK_EDIT)
		i.connect('activate', unPlaylistPanel.editer, uneLigne)
		self.append(i)
		self.show_all()

class TrackMenu(gtk.Menu):
	def __init__(self, ID):
		gtk.Menu.__init__(self)
		track = elements.Track(ID)
		i = gtk.MenuItem(_("Title") + " : " + track.title)
		self.append(i)
		
		rating_item = etoiles.RatingMenuItem(track.rating, auto_update=False)
		rating_item.connect('rating-changed', track.change_rating)
		self.append(rating_item)
		
		i = gtk.ImageMenuItem(_("Edit tags"))
		i.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT, gtk.ICON_SIZE_MENU))
		i.connect('activate', self.editer_piste, ID)
		self.append(i)

	def editer_piste(self, button, piste_ID):
		dialog = modales.TagsEditor(piste_ID)
		
class TrackContainerMenu(gtk.Menu):
	def __init__(self, dic):
		gtk.Menu.__init__(self)
		#i = gtk.MenuItem(dic[len(dic)])
		#self.append(i)
		i = gtk.ImageMenuItem(_("Edit tags"))
		i.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT, gtk.ICON_SIZE_MENU))
		i.connect('activate', self.editer_conteneur, dic)
		self.append(i)
		
		i = gtk.ImageMenuItem(_("Delete from DB"))
		i.set_image(gtk.image_new_from_stock(gtk.STOCK_DELETE, gtk.ICON_SIZE_MENU))
		i.connect('activate', self.supprimmer_conteneur, dic)
		self.append(i)


	def editer_conteneur(self, button, dic):
		dialog = modales.TagsEditor(dic)
	def supprimmer_conteneur(self, button, dic):
		print('suppr')
		
class TrayMenu(gtk.Menu):
	def __init__(self, MainApp):
		gtk.Menu.__init__(self)
		i = gtk.ImageMenuItem(gtk.STOCK_QUIT)
		i.connect('activate', MainApp.on_window_destroy)
		self.append(i)
		self.show_all()
		
	def popup(self, status_icon, button, activate_time):
		gtk.Menu.popup(self, None, None, None, button, activate_time)
		
		
	