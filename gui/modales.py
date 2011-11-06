# -*- coding: utf-8 -*-
import gtk
import logging

from common import messager, settings, xdg
from data import elements

logger = logging.getLogger(__name__)

class CriterionManager(gtk.VBox):
	"""
		Widget to handle SQL Query creation with GUI
	"""
	def __init__(self):
		gtk.VBox.__init__(self)
		self.liste = gtk.ListStore(str, str)
		self.liste.append(["artist", _("Artist")])
		self.liste.append(["album", _("Album")])
		self.liste.append(["note", _("Rating")])
		self.liste.append(["compteur", _("Play count")])
		self.liste.append(["path", _("Path")])
		
		self.liste_operateurs = gtk.ListStore(str, str)
		self.liste_operateurs.append([" = ", _("is")])
		self.liste_operateurs.append([" != ", _("is not")])
		self.liste_operateurs.append([" LIKE ", _("like")])
		self.liste_operateurs.append([" NOT LIKE ", _("not like")])
		
		self.liste_operateurs_note = gtk.ListStore(str, str)
		self.liste_operateurs_note.append([" = ", _("equals")])
		self.liste_operateurs_note.append([" < ", _("is inferior to")])
		self.liste_operateurs_note.append([" > ", _("is superior to")])
		self.liste_operateurs_note.append([" <= ", _("is lower than")])
		self.liste_operateurs_note.append([" >= ", _("is at least")])
		
		BB = gtk.HButtonBox()
		self.RB_Criterion = gtk.CheckButton(_("Whatever criterion match"))
		self.RB_Random = gtk.CheckButton(_("Random order"))
		B_Add = gtk.ToolButton(gtk.STOCK_ADD)
		B_Add.connect("clicked", self.add_criterion)
		BB.add(self.RB_Criterion)
		BB.add(self.RB_Random)
		BB.add(B_Add)
		self.pack_end(BB, False)
		self.Box_Criteres = gtk.VBox()
		self.pack_start(self.Box_Criteres)
		
	def add_criterion(self, button=None, criterion=None, operator=None, condition=None):
		'''
			Ajoute un nouveau critère de séléction (à configurer graphiquement) qui sera traité lors de la validation
		'''
		Box_Critere = gtk.HBox(spacing=12)
		Box_Critere.set_border_width(2)
		
		CB_Critere = gtk.ComboBox()
		CB_Critere.set_model(self.liste)
		cell = gtk.CellRendererText()
		CB_Critere.pack_start(cell)
		CB_Critere.add_attribute(cell, "text", 1)
		if(criterion == None):
			CB_Critere.set_active(0)
			liste_op = self.liste_operateurs
		else:
			i = 0
			while(self.liste[i][0] != criterion and i < len(self.liste)):
				i += 1
			if(self.liste[i][0] == criterion):
				CB_Critere.set_active(i)
			else:
				print("error : bad criterion")
			if(criterion in ('note', 'compteur')):
				liste_op = self.liste_operateurs_note
			else:
				liste_op = self.liste_operateurs
				
		CB_Operateur = gtk.ComboBox()
		CB_Operateur.set_model(liste_op)
		CB_Operateur.pack_start(cell)
		CB_Operateur.add_attribute(cell, "text", 1)
		if(operator == None):
			CB_Operateur.set_active(0)
		else:
			i = 0
			while(i < len(liste_op) and liste_op[i][0] != operator):
				i += 1
			try:
				if(liste_op[i][0] == operator):
					CB_Operateur.set_active(i)
				else:
					logger.debug("error : bad operator")
			except IndexError:
				logger.debug('exception : bad operator ' + operator)
		
		E_Condition = gtk.Entry()
		if(condition != None):
			E_Condition.set_text(condition)
			
		B_Delete = gtk.ToolButton(gtk.STOCK_REMOVE)
		B_Delete.connect("clicked", self.delete_criterion, Box_Critere)
		Box_Critere.pack_start(CB_Critere, False)
		Box_Critere.pack_start(CB_Operateur, False)
		Box_Critere.pack_start(E_Condition)
		Box_Critere.pack_end(B_Delete, False)
		Box_Critere.show_all()
		self.Box_Criteres.pack_start(Box_Critere, False)
		CB_Critere.connect("changed", self.format_widgets, Box_Critere)
		
	def delete_criterion(self, button, Box_Critere):
		Box_Critere.destroy()
		
	def format_widgets(self, CB, Box):
		'''
			Formatte une ligne de critères pour que les widgets soient conformes au type
		'''
		children = Box.get_children()
		if (children[0].get_active_text() == "note" or children[0].get_active_text() == "compteur"):
			children[1].set_model(self.liste_operateurs_note)
			children[1].set_active(0)
			children[2].destroy()
			SB = gtk.SpinButton(climb_rate=1)
			SB.set_increments(1, 2)
			SB.set_range(0, 5)
			Box.pack_start(SB, False)
		else:
			children[1].set_model(self.liste_operateurs)
			children[1].set_active(0)
			children[2].destroy()
			E_Condition = gtk.Entry()
			Box.pack_start(E_Condition)
		Box.show_all()
		
	def get_config(self):
		"""
			Return all parameter in dict
		"""
		config = {}
		if(self.RB_Random.get_active()):
			config['random'] = True
		else:
			config['random'] = False
			
		if(self.RB_Criterion.get_active()):
			config['link'] = ' OR '
		else:
			config['link'] = ' AND '
		
		config['criterions'] = []
		for critere in self.Box_Criteres:
			children = critere.get_children()
			criterion = children[0].get_active_text()
			operator = children[1].get_active_text()
			condition =  children[2].get_text()
			t = (criterion, operator, condition)
			#column, operator, condition = criterion
			config['criterions'].append(t)
			
		return config
		
	def load_criterions(self, dic):
		random = dic['random']
		logic_operator = dic['link']
		if(random):
			self.RB_Random.set_active(True)
		if(logic_operator == " OR "):
			self.RB_Criterion.set_active(True)
		
		crits = dic['criterions']
		for crit in crits:
			criterion = crit[0]
			operator = crit[1]
			condition = crit[2]
			self.add_criterion(None, criterion, operator, condition)
			
	def reset(self):
		self.RB_Random.set_active(False)
		self.RB_Criterion.set_active(False)
		for critere in self.Box_Criteres:
			critere.destroy()



class IntelligentPlaylistCreator(gtk.Dialog):
	'''
		Créateur de fichiers contenant des paramètres pour créer une requête SQL séléctionnant des pistes y correspondant
	'''
	def __init__(self, name=None):
		
		self.E_Name = gtk.Entry()
		
		if(name == None):
			titre = _("Add an intelligent playlist")
		else:
			titre = _("Edit an intelligent playlist")
			self.E_Name.set_text(name)
			
		gtk.Dialog.__init__(self, title=titre, buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
		
		Box_Main = self.get_content_area()
		Box_Name = gtk.HBox()
		L_Name = gtk.Label(_("Name") + " : ")
		Box_Name.pack_start(L_Name, False)
		Box_Name.pack_start(self.E_Name)
		
		
		Box_Main.pack_start(Box_Name, False)
		self.c_manager = CriterionManager()
		Box_Main.pack_start(self.c_manager)
		
		
		
		
		
		if(name == None):
			self.c_manager.add_criterion()
		else:
			self.load_criterions(name)
			
		self.show_all()
		reponse = self.run()
		if(reponse == -3):
			self.valider(name)
		self.destroy()

	def load_criterions(self, name):
		fichier = open('playlists/intelligents/' + name,'r')
		data = fichier.readlines()
		fichier.close()
		self.c_manager.load_criterions(eval(data[0]))
		#logic_operator = data[1] #AND or OR
		#if(random == "random\n"):
			#self.RB_Random.set_active(True)
		#if(logic_operator == "OR\n"):
			#self.RB_Criterion.set_active(True)
		#i = 2
		#while(i < len(data)):
			#liste = eval(data[i]) #Conversion de string en list
			#criterion = liste[0]
			#operator = liste[1]
			#condition = liste[2]
			#self.add_criterion(None, criterion, operator, condition)
			#i += 1
		
		
	def valider(self, edit):
		name = self.E_Name.get_text()
		fichier = open('playlists/intelligents/' + name, 'w')
		fichier.write(str(self.c_manager.get_config()))
		#if(self.RB_Random.get_active()):
			#fichier.write("random" + "\n")
		#else:
			#fichier.write("notrandom" + "\n")
			
		#if(self.RB_Criterion.get_active()):
			#fichier.write(" OR " + "\n")
		#else:
			#fichier.write(" AND " + "\n")
			
		#for critere in self.Box_Criteres:
			#children = critere.get_children()
			#criterion = children[0].get_active_text()
			#operator = children[1].get_active_text()
			#condition =  children[2].get_text()
			#t = [criterion, operator, condition]
			##column, operator, condition = criterion
			#fichier.write(str(t) + "\n")
		#fichier.close()
		if(edit == None): #Pas une édition
			messager.diffuser('playlist_ajoutee', self, ["intelligent", name])		
		
		
class TagsEditor(gtk.Dialog):
	'''
		Éditeur de tags de fichiers musicaux
		TODO indicator to show what we're editing
	'''
	def __init__(self, data):
		gtk.Dialog.__init__(self, title=_("Tags editor"), buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
		Box_Main = self.get_content_area()
		Box = gtk.Table(2,2)
		
		i = 0
		
		self.tags = {}
		def add_line_for(tag, text=''):
			print i
			#Box = gtk.HBox()
			L = gtk.Label(_(tag) + " : ")
			Box.attach(L, 0, 1, i, i+1)
			self.tags[tag] = gtk.Entry()
			self.tags[tag].set_text(text)
			Box.attach(self.tags[tag], 1, 2, i, i+1)

		def add_line_forDEPREC(tag, text=''):
			Box = gtk.HBox()
			L = gtk.Label(_(tag) + " : ")
			self.tags[tag] = gtk.Entry()
			self.tags[tag].set_text(text)
			Box.pack_start(L)
			Box.pack_start(self.tags[tag])
			Box_Main.pack_start(Box)
		if type(data).__name__=='dict':
			self.dic = data
			for key in self.dic.iterkeys():
				add_line_for(key, self.dic[key])
				i += 1
		else:
			piste_ID = data
			add_line_for('artist')
			i += 1
			add_line_for('album')
			i += 1
			add_line_for('title')
			
			
			self.charger_tags(piste_ID)
		Box_Main.pack_start(Box)
		self.show_all()
		reponse = self.run()
		if(reponse == -3):
			self.valider()
		self.destroy()
		
	def charger_tags(self, piste_ID):
		self.track = elements.Track(piste_ID)
		fichier = self.track.path
		audio = self.track.get_tags()
		
		try:
			titre = audio["title"][0]
		except:
			titre = _("Unknown")
		
		try:
			album = audio["album"][0]
		except:
			album =  _("Unknown")
		try:
			artiste = audio["artist"][0]
		except:
			artiste =  _("Unknown")
		
		self.dic = {'title':titre, 'album':album, 'artist':artiste}
		self.tags['title'].set_text(titre)
		self.tags['album'].set_text(album)
		self.tags['artist'].set_text(artiste)
		
	def valider(self):
		try:
			tracks = (self.track,)
		except AttributeError:
			tracks = elements.bdd.get_tracks(self.dic)
		for track in tracks:
			for key in self.dic.iterkeys():
				if(self.tags[key].get_text() != self.dic[key]):
					track.set_tag(key, self.tags[key].get_text())
		#self.track.set_tag("title", self.E_Titre.get_text())
		#self.track.set_tag("artist", self.E_Artist.get_text())
		#self.track.set_tag("album", self.E_Album.get_text())
		

class SettingsEditor(gtk.Dialog):
		def __init__(self):
			gtk.Dialog.__init__(self, title=_("Settings editor"), buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
			self.Box_Main = gtk.HBox()
			self.get_content_area().pack_start(self.Box_Main)
			
			icons_dir = xdg.get_data_dir() + 'icons/'
			TreeView = gtk.TreeView()
			TreeView.connect("button-press-event", self.on_section_click)
			self.liste_sections = gtk.TreeStore(str, str, gtk.gdk.Pixbuf)
			self.liste_sections.append(None, ['general', _('General'), None])
			self.liste_sections.append(None, ['folders', _('Indexed folders'), None])
			music_node = self.liste_sections.append(None, ['music', _('Music'), gtk.gdk.pixbuf_new_from_file(icons_dir + 'track.png')])
			self.liste_sections.append(music_node, ['music_filters', _('Filters'), None])
			self.liste_sections.append(music_node, ['audioscrobbler', _('Audioscrobbler'), None])
			self.liste_sections.append(None, ['pictures', _('Pictures'), None])
			self.liste_sections.append(None, ['videos', _('Videos'), None])
			
			cell = gtk.CellRendererText()
			cellpb = gtk.CellRendererPixbuf()
			Col_Label = gtk.TreeViewColumn(_('Section'), cellpb, pixbuf=2)
			Col_Label.pack_start(cell, False)
			Col_Label.set_attributes(cell, text=1)
			TreeView.append_column(Col_Label)
			TreeView.set_model(self.liste_sections)
			self.Box_Main.pack_start(TreeView, False)
			
			self.show_all()
			self.initialiser_composants()
			self.load_section('general')
			
			reponse = self.run()
			if(reponse == -3):
				self.valider()
			self.destroy()
		
		def createUCBox(self, module):
			"""
				Create settings section for standard UC module
			"""
			Box = UCSettingsBox(module)

			self.Box_Main.pack_start(Box)
			self.widgets[module] = Box
		
		def initialiser_composants(self):
			self.widgets = {}
			
			# Général
			Box_General = gtk.VBox()
			self.picture_enabled = gtk.CheckButton(_('Enable pictures manager'))
			self.picture_enabled.set_active(settings.get_option('pictures/enabled', False))
			self.video_enabled = gtk.CheckButton(_('Enable videos manager'))
			self.video_enabled.set_active(settings.get_option('videos/enabled', False))
			
			# Option : Cacher les menus de la barre d'outils en fonction de la section
			
			Box_General.pack_start(self.picture_enabled)
			Box_General.pack_start(self.video_enabled)
			self.Box_Main.pack_start(Box_General)
			self.widgets['general'] = Box_General
			
			# Folders section
			Box_folders = gtk.VBox()
			TV_folders = gtk.TreeView()
			self.folders = gtk.ListStore(str, bool)
			cell = gtk.CellRendererText()
			Col_Label = gtk.TreeViewColumn(_('Folders'), cell, text=0)
			cell_toggle = gtk.CellRendererToggle()
			Col_Recursive = gtk.TreeViewColumn(_('Dig'), cell_toggle, active=1)
			cell_toggle.connect('toggled', self.toggle_recursive_folder)
			TV_folders.append_column(Col_Label)
			TV_folders.append_column(Col_Recursive)
			TV_folders.set_model(self.folders)
			
			for folder in settings.get_option('music/folders', []):
				self.folders.append([folder[0], folder[1]])
			
			def add_folder(*args):
				dialog = gtk.FileChooserDialog(action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_OPEN, gtk.FILE_CHOOSER_ACTION_OPEN))
				dialog.run()
				fichier = dialog.get_filename()
				dialog.destroy()
				self.folders.append([fichier, False])
				
			def remove_folder(*args):
				try:
					model, iter = TV_folders.get_selection().get_selected()
					model.remove(iter)
				except TypeError:
					warning = gtk.MessageDialog(self, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE, message_format=_('You must select a folder before clicking the remove button'))
					warning.run()
					warning.destroy()
			
			B_add_folder = gtk.Button(_('Add'), gtk.STOCK_ADD)
			B_add_folder.connect('clicked', add_folder)
			B_remove_folder = gtk.Button(_('Remove'), gtk.STOCK_REMOVE)
			B_remove_folder.connect('clicked', remove_folder)
			Box_folders.pack_start(TV_folders)
			Box_folders.pack_start(B_add_folder)
			Box_folders.pack_start(B_remove_folder)
			
			self.Box_Main.pack_start(Box_folders)
			self.widgets['folders'] = Box_folders
			
			# ******* Music section *********
			Box_music = gtk.Table(2,2)
			i = 0
			Box_music.attach(gtk.Label(_('Playback library') + ' :'), 0, 1, i, i+1)
			self.CB_music_playback_lib = gtk.combo_box_new_text()
			libs = {'GStreamer':0, 'MPlayer':1, 'VLC':2}
			self.CB_music_playback_lib.append_text('GStreamer')
			self.CB_music_playback_lib.append_text('MPlayer')
			self.CB_music_playback_lib.append_text('VLC')
			
			self.CB_music_playback_lib.set_active(libs[settings.get_option('music/playback_lib', 'GStreamer')])
			Box_music.attach(self.CB_music_playback_lib, 1, 2, i, i+1)
			
			
			i += 1
			Box_music.attach(gtk.Label(_('Panel icon size') + ' :'), 0, 1, i, i+1)
			self.CB_icon_size_panel_music = gtk.combo_box_new_text()
			self.CB_icon_size_panel_music.append_text('16')
			self.CB_icon_size_panel_music.append_text('24')
			self.CB_icon_size_panel_music.append_text('32')
			self.CB_icon_size_panel_music.append_text('48')
			self.CB_icon_size_panel_music.append_text('64')
			
			self.CB_icon_size_panel_music.set_active(settings.get_option('music/panel_icon_size', 32) /16)
			Box_music.attach(self.CB_icon_size_panel_music, 1, 2, i, i+1)
			
			self.Box_Main.pack_start(Box_music)
			self.widgets['music'] = Box_music
			
			
			self.Box_mfilters = FilterManager(settings.get_option('music/filters', {}))
			
			
			
			self.Box_Main.pack_start(self.Box_mfilters)
			self.widgets['music_filters'] = self.Box_mfilters
			
			# Audioscrobbler section
			Box_audioscrobbler = gtk.Table(2, 2)
			Box_audioscrobbler.attach(gtk.Label(_('Login') + ' : '), 0, 1, 0, 1) 
			
			self.audioscrobbler_login = gtk.Entry()
			self.audioscrobbler_login.set_text(settings.get_option('music/audioscrobbler_login', ''))
			Box_audioscrobbler.attach(self.audioscrobbler_login, 1, 2, 0, 1) 
			
			
			Box_audioscrobbler.attach(gtk.Label(_('Password') + ' : '), 0, 1, 1, 2) 
			self.audioscrobbler_password = gtk.Entry()
			self.audioscrobbler_password.set_text(settings.get_option('music/audioscrobbler_password', ''))
			Box_audioscrobbler.attach(self.audioscrobbler_password, 1, 2, 1, 2) 
			
			self.Box_Main.pack_start(Box_audioscrobbler)
			self.widgets['audioscrobbler'] = Box_audioscrobbler
			
			
			# Pictures section
			Box_pictures = gtk.Table(2,2)
			i = 0
			self.picture_preload = gtk.CheckButton(_('Preload pictures manager'))
			self.picture_preload.set_active(settings.get_option('pictures/preload', False))
			self.picture_preload.set_tooltip_text(_('If true, will be preloaded before application start, else will be loaded on demand (slightly faster startup)'))
			Box_pictures.attach(self.picture_preload, 0, 2, i, i+1)
			i += 1
			Box_pictures.attach(gtk.Label(_('Panel thumbnail size')), 0, 1, i, i+1)
			self.CB_icon_size_panel_pictures = gtk.combo_box_new_text()
			self.CB_icon_size_panel_pictures.append_text('16')
			self.CB_icon_size_panel_pictures.append_text('24')
			self.CB_icon_size_panel_pictures.append_text('32')
			self.CB_icon_size_panel_pictures.append_text('48')
			self.CB_icon_size_panel_pictures.append_text('64')
			
			self.CB_icon_size_panel_pictures.set_active(settings.get_option('pictures/panel_icon_size', 32) /16)
			Box_pictures.attach(self.CB_icon_size_panel_pictures, 1, 2, i, i+1)
			
			self.Box_Main.pack_start(Box_pictures)
			self.widgets['pictures'] = Box_pictures
			
			#Videos section
			#Box_pictures = gtk.Table(2,2)
			#i = 0
			#self.picture_preload = gtk.CheckButton(_('Preload pictures manager'))
			#self.picture_preload.set_active(settings.get_option('pictures/preload', False))
			#self.picture_preload.set_tooltip_text(_('If true, will be preloaded before application start, else will be loaded on demand (slightly faster startup)'))
			#Box_pictures.attach(self.picture_preload, 0, 2, i, i+1)
			#i += 1
			#Box_pictures.attach(gtk.Label(_('Panel thumbnail size')), 0, 1, i, i+1)
			#self.CB_icon_size_panel_pictures = gtk.combo_box_new_text()
			#self.CB_icon_size_panel_pictures.append_text('16')
			#self.CB_icon_size_panel_pictures.append_text('24')
			#self.CB_icon_size_panel_pictures.append_text('32')
			#self.CB_icon_size_panel_pictures.append_text('48')
			#self.CB_icon_size_panel_pictures.append_text('64')
			
			#self.CB_icon_size_panel_pictures.set_active(settings.get_option('pictures/panel_icon_size', 32) /16)
			#Box_pictures.attach(self.CB_icon_size_panel_pictures, 1, 2, i, i+1)
			
			#self.Box_Main.pack_start(Box_pictures)
			#self.widgets['pictures'] = Box_pictures
			
			self.createUCBox('videos')
			i = 3
			self.widgets['videos'].attach(gtk.Label(_('Playback library') + ' :'), 0, 1, i, i+1)
			self.CB_video_playback_lib = gtk.combo_box_new_text()
			libs = {'GStreamer':0, 'MPlayer':1, 'VLC':2}
			self.CB_video_playback_lib.append_text('GStreamer')
			self.CB_video_playback_lib.append_text('MPlayer')
			self.CB_video_playback_lib.append_text('VLC')
			
			self.CB_video_playback_lib.set_active(libs[settings.get_option('videos/playback_lib', 'GStreamer')])
			self.widgets['videos'].attach(self.CB_video_playback_lib, 1, 2, i, i+1)
			
			
			
			
		def load_section(self, section):
			try:
				self.active_widget.hide_all()
			except:
				pass
			self.active_widget = self.widgets[section]
			self.active_widget.show_all()
			
		def on_section_click(self, TreeView, event):
			if event.button == 1:
				path = TreeView.get_path_at_pos(int(event.x),int(event.y))[0]
				if (path != None):
					section = self.liste_sections[path][0]
					self.load_section(section)
					
		def valider(self):
			settings.set_option('pictures/enabled', self.picture_enabled.get_active())
			settings.set_option('videos/enabled', self.video_enabled.get_active())
			
			folders = []
			iter = self.folders.get_iter_first()
			while iter is not None:
				folders.append((self.folders.get_value(iter, 0), self.folders.get_value(iter, 1)))
				iter = self.folders.iter_next(iter)
			settings.set_option('music/folders', folders)
				
			#Music settings:
			settings.set_option('music/playback_lib', self.CB_music_playback_lib.get_active_text())
			settings.set_option('music/panel_icon_size', int(self.CB_icon_size_panel_music.get_active_text()))
			
			settings.set_option('music/filters', self.Box_mfilters.get_config())
			
			#Pictures settings :
			settings.set_option('pictures/panel_icon_size', int(self.CB_icon_size_panel_pictures.get_active_text()))

			#Audioscrobbler settings :
			settings.set_option('music/audioscrobbler_login', self.audioscrobbler_login.get_text())
			settings.set_option('music/audioscrobbler_password', self.audioscrobbler_password.get_text())
			
			#Videos settings
			settings.set_option('videos/playback_lib', self.CB_video_playback_lib.get_active_text())
			
			for UCmodule in ('videos',):
				settings.set_option(UCmodule + '/indexed_extensions', self.widgets[UCmodule].extensions.get_text())
				settings.set_option(UCmodule + '/preload', self.widgets[UCmodule].preload.get_active())
				settings.set_option(UCmodule + '/panel_icon_size', int(self.widgets[UCmodule].CB_icon_size_panel.get_active_text()))
				
			
			settings.MANAGER.save()
			
		def toggle_recursive_folder(self, cell, path):
			iter = self.folders.get_iter((int(path),))
			val = self.folders.get_value(iter, 1)
		
			# toggle the value
			val = not val
		
			# set new value
			self.folders.set(iter, 1, val)
			
class UCSettingsBox(gtk.Table):
	def __init__(self, module):
		gtk.Table.__init__(self)
		i = 0
		self.attach(gtk.Label(_('Indexed extensions') + ' :'), 0, 1, i, i+1)
		self.extensions = gtk.Entry()
		self.extensions.set_text(settings.get_option(module + '/indexed_extensions', ''))
		self.attach(self.extensions, 1, 2, i, i+1)
		i += 1
		self.preload = gtk.CheckButton(_('Preload this module'))
		self.preload.set_active(settings.get_option(module + '/preload', False))
		self.preload.set_tooltip_text(_('If true, will be preloaded before application start, else will be loaded on demand (slightly faster startup)'))
		self.attach(self.preload, 0, 2, i, i+1)
		i += 1
		self.attach(gtk.Label(_('Panel thumbnail size') + ' :'), 0, 1, i, i+1)
		self.CB_icon_size_panel = gtk.combo_box_new_text()
		self.CB_icon_size_panel.append_text('16')
		self.CB_icon_size_panel.append_text('24')
		self.CB_icon_size_panel.append_text('32')
		self.CB_icon_size_panel.append_text('48')
		self.CB_icon_size_panel.append_text('64')
		
		self.CB_icon_size_panel.set_active(settings.get_option(module + '/panel_icon_size', 32) /16)
		self.attach(self.CB_icon_size_panel, 1, 2, i, i+1)
		
	
class FilterManager(gtk.VBox):
	"""
		Widget that handles filter managment with a CriterionManager
	"""
	def __init__(self, config):
		gtk.VBox.__init__(self)
		self.config = config
		self.CB_filters = gtk.combo_box_new_text()
		self.CB_filters.connect('changed', self.load_filter)
		B_add = gtk.Button('', gtk.STOCK_ADD)
		B_add.connect('clicked', self.add_filter)
		B_remove = gtk.Button('', gtk.STOCK_REMOVE)
		self.RB_enabled = gtk.CheckButton(_("Enabled"))
		Box = gtk.HBox()
		Box.pack_start(self.RB_enabled, False)
		Box.pack_start(self.CB_filters)
		Box.pack_start(B_add, False)
		Box.pack_start(B_remove, False)
		self.pack_start(Box, False)
		
		
		self.c_manager = CriterionManager()
		self.pack_start(self.c_manager)
		
		for key in self.config.iterkeys():
			self.CB_filters.append_text(key)
		
		try:
			self.CB_filters.set_active(0)
			self.active_filter = self.CB_filters.get_active_text()
		except:
			pass
		
	
		
	def add_filter(self, button=None):
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
		label = Entry.get_text()
		DN.destroy()
		if(action == 1):
			self.CB_filters.append_text(label)
			self.CB_filters.set_active(self.count)
			self.count += 1
			
			
	def get_config(self):
		"""
			Return a dict with all filters configuration for this model
		"""
		filter = self.CB_filters.get_active_text()
		if(filter != None): # saving current
			self.config[filter] = self.c_manager.get_config()
			self.config[filter]['enabled'] = self.RB_enabled.get_active()
		return self.config
	
	
	def load_filter(self, widget):
		try:
			if(self.active_filter != None): # saving previous
				self.config[self.active_filter] = self.c_manager.get_config()
				self.config[self.active_filter]['enabled'] = self.RB_enabled.get_active()
		except:
			pass
			
		filter = self.CB_filters.get_active_text()
		self.active_filter = filter
		self.c_manager.reset()
		self.RB_enabled.set_active(False)
		try:
			self.c_manager.load_criterions(self.config[filter])
			if(self.config[filter]['enabled']):
				self.RB_enabled.set_active(True)
		except KeyError:
			pass

class ImportHelper(gtk.Dialog):
	def __init__(self, bdd):
		gtk.Dialog.__init__(self, title=_("Import helper"), buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
		self.Box_Main = gtk.VBox()
		self.get_content_area().pack_start(self.Box_Main)
		self.button = gtk.FileChooserButton(_("Choose a database file"))
		self.Box_Main.pack_start(self.button)
		
		self.c_manager = CriterionManager()
		self.Box_Main.pack_start(self.c_manager)
		
		self.show_all()
		reponse = self.run()
		if(reponse == -3):
			bdd.retrieveFromSave(self.button.get_filename(), self.c_manager.get_config())
		self.destroy()