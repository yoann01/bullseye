# -*- coding: utf-8 -*-
import gtk
import gobject
import time
import threading


class ImageWidget(gtk.ScrolledWindow):
	def __init__(self, display):
		gtk.ScrolledWindow.__init__(self)
		
		self.display = display
		self.Image = gtk.Image()

		self.add_with_viewport(self.Image)
		
		
		self.Image.get_parent().connect("scroll-event", self.change_zoom) #Image parent = viewport
		
		self.Image.get_parent().connect('button-press-event', self.enable_move)
		self.Image.get_parent().connect('button-release-event', self.disable_move)
		self.vadjustment = self.get_vadjustment()
		self.hadjustment = self.get_hadjustment()
		
		#self.Image.get_parent().connect('motion-notify-event', self.update_position)
		self.Image.get_parent().add_events(gtk.gdk.BUTTON_PRESS | gtk.gdk.BUTTON_RELEASE_MASK)
		#self.Image.add_events(gtk.gdk.KEY_PRESS_MASK |
              #gtk.gdk.POINTER_MOTION_MASK |
              #gtk.gdk.BUTTON_PRESS_MASK | 
              #gtk.gdk.SCROLL_MASK)
		#self.Image.get_parent().drag_source_set(gtk.gdk.MODIFIER_MASK,  [('BS_image', 0, 0)] ,
                  #gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
                  
                #self.drag_dest_set(0, [('BS_image', 0, 0)], 0)
		#self.connect("drag-motion", self.temp)
		
		self.mode = "zoom"
		self.zoom = 1
		
		
	def temp(self, widget, context, x, y, time):
		print context
		#context.drag_status(gtk.gdk.ACTION_COPY, time)
		#y += self.SW.get_vadjustment().get_value()
		depart = self.y#- self.SW.get_vadjustment().get_value()
		arrivee =  y + self.vadjustment_value
		print('départ = ' + str(depart) + ' arrivée = ' + str(arrivee))
		
		distance = (arrivee - depart) * 1.5
		print('Distance = ' + str(distance))
		nouveau = - distance + self.vadjustment_value
		if(nouveau < self.height - 280):
			#print('origine = ' + str(self.vadjustment_value) + ' nouveau = ' + str(nouveau))
			#self.SW.get_vadjustment().set_value(nouveau)
			
			self.vadjustment.set_value(-1 * (y -self.y))
		
		
		self.hadjustment.set_value(-1 * ( x - self.x) )
		
		
	def temp2(self, *args):
		print('ok')
		
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

	def change_zoom(self, b, mode):
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
		
		# Prevent propagation to avoid scrolling up and down in the ScrolledWindow
		return True

	def enable_move(self, widget, event):
		pointer = self.display.get_pointer()
		self.x = pointer[1]
		self.y = pointer[2]
		self.vadjustment_value = self.vadjustment.get_value()
		self.hadjustment_value = self.hadjustment.get_value()
		self.moving = True
		def start_moving():
			while self.moving is True:
				gobject.idle_add(self.move)
				time.sleep(0.05)
		task = threading.Thread(target=start_moving)
		task.start()
		
	def disable_move(self, widget, event):
		self.moving = False
		
	def move(self):
		t, x, y, p = self.display.get_pointer()
		self.hadjustment.set_value(self.hadjustment_value + self.x - x)
		self.vadjustment.set_value(self.vadjustment_value + self.y - y )
		
	def fit_zoom(self):
		img = self.img_original
		width = img.get_width()
		height = img.get_height()
		if(self.mode == "fit"):
			adapted_width, adapted_height = self.adapter_taille(width, height)
		elif(self.mode == "zoom"):
			adapted_width = img.get_width() * self.zoom
			adapted_height = img.get_height() * self.zoom
			self.width = adapted_width
			self.height = adapted_height
			
		img = img.scale_simple(int(adapted_width), int(adapted_height), gtk.gdk.INTERP_BILINEAR)
		return img
		
		
	def set_image(self, path):
		self.img_original = gtk.gdk.pixbuf_new_from_file(path)
		img = self.fit_zoom()
		self.Image.set_from_pixbuf(img)
		
	def update_position(self, widget, event):
		print('reseting position' + str(event.y));
		self.x = event.x
		self.y = event.y
		self.vadjustment_value = self.vadjustment.get_value()
		self.hadjustment_value = self.hadjustment.get_value()

	