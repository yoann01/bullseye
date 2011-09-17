import gtk

from gui.menus import TrayMenu

class BullseyeTrayIcon(gtk.StatusIcon):
	def __init__(self, core):
		gtk.StatusIcon.__init__(self)
		self.set_from_stock(gtk.STOCK_MEDIA_PLAY)
		menu = TrayMenu(core)
		self.connect('activate', self.iconify_to_tray)
		self.connect('popup-menu', menu.popup)
		self.connect('button-press-event', self.on_button_press)
		self.core = core
		
	
			
	def iconify_to_tray(self, status_icon):
		if self.core.F_Main.get_property('visible'):
			self.core.F_Main.hide()
		else:
			self.core.F_Main.present()
			
			
	def on_button_press(self, widget, event):
		if(event.button == 2):
			self.core.player.toggle_pause()