# -*- coding: utf-8 -*-


import cairo
#import glob
#import glib
import gtk
#import os
#import pango


class ExtendedPixbuf(gtk.gdk.Pixbuf):
    """
        A Pixbuf wrapper class allowing for
        interaction using standard operators
    """
    def __init__(self, pixbuf):
        gtk.gdk.Pixbuf.__init__(self,
            pixbuf.get_colorspace(),
            pixbuf.get_has_alpha(),
            pixbuf.get_bits_per_sample(),
            pixbuf.get_width(),
            pixbuf.get_height()
        )
        pixbuf.copy_area(
            src_x=0, src_y=0,
            width=self.get_width(), height=self.get_height(),
            dest_pixbuf=self,
            dest_x=0, dest_y=0
        )

    def __add__(self, other):
        """
            Horizontally appends a pixbuf to the current
            
            :param other: the pixbuf to append
            :type other: :class:`gtk.gdk.Pixbuf`
            :returns: a new pixbuf
            :rtype: :class:`ExtendedPixbuf`
        """
        return self.add_horizontal(other)

    def __mul__(self, multiplier):
        """
            Horizontally multiplies the current pixbuf content

            :param multiplier: How often the pixbuf
                shall be multiplied
            :type multiplier: int
            :returns: a new pixbuf
            :rtype: :class:`ExtendedPixbuf`
        """
        return self.multiply_horizontal(multiplier)

    def __and__(self, other):
        """
            Composites a pixbuf on the current
            pixbuf at the location (0, 0)
            
            :param other: the pixbuf to composite
            :type other: :class:`gtk.gdk.Pixbuf`
            :returns: a new pixbuf
            :rtype: :class:`ExtendedPixbuf`
        """
        return self.composite_simple(other)


    def add_horizontal(self, other, spacing=0):
        """
            Horizontally appends a pixbuf to the current
            
            :param other: the pixbuf to append
            :type other: :class:`gtk.gdk.Pixbuf`
            :param spacing: amount of pixels between the pixbufs
            :type spacing: int
            :returns: a new pixbuf
            :rtype: :class:`ExtendedPixbuf`
        """
        height = max(self.get_height(), other.get_height())
        spacing = max(0, spacing)

        new_pixbuf = gtk.gdk.Pixbuf(
            self.get_colorspace(),
            self.get_has_alpha(),
            self.get_bits_per_sample(),
            self.get_width() + spacing + other.get_width(),
            height
        )
        new_pixbuf.fill(0xffffff00)

        self.copy_area(
            src_x=0, src_y=0,
            width=self.get_width(), height=self.get_height(),
            dest_pixbuf=new_pixbuf,
            dest_x=0, dest_y=0
        )
        other.copy_area(
            src_x=0, src_y=0,
            width=other.get_width(), height=other.get_height(),
            dest_pixbuf=new_pixbuf,
            dest_x=self.get_width() + spacing, dest_y=0
        )

        return ExtendedPixbuf(new_pixbuf)

    def add_vertical(self, other, spacing=0):
        """
            Vertically appends a pixbuf to the current
            
            :param other: the pixbuf to append
            :type other: :class:`gtk.gdk.Pixbuf`
            :param spacing: amount of pixels between the pixbufs
            :type spacing: int
            :returns: a new pixbuf
            :rtype: :class:`ExtendedPixbuf`
        """
        width = max(self.get_width(), other.get_width())
        spacing = max(0, spacing)

        new_pixbuf = gtk.gdk.Pixbuf(
            self.get_colorspace(),
            self.get_has_alpha(),
            self.get_bits_per_sample(),
            width,
            self.get_height() + spacing + other.get_height()
        )
        new_pixbuf.fill(0xffffff00)

        self.copy_area(
            src_x=0, src_y=0,
            width=self.get_width(), height=self.get_height(),
            dest_pixbuf=new_pixbuf,
            dest_x=0, dest_y=0
        )
        other.copy_area(
            src_x=0, src_y=0,
            width=other.get_width(), height=other.get_height(),
            dest_pixbuf=new_pixbuf,
            dest_x=0, dest_y=self.get_height() + spacing
        )

        return ExtendedPixbuf(new_pixbuf)

    def multiply_horizontal(self, multiplier, spacing=0):
        """
            Horizontally multiplies the current pixbuf content

            :param multiplier: How often the pixbuf
                shall be multiplied
            :type multiplier: int
            :param spacing: amount of pixels between the pixbufs
            :type spacing: int
            :returns: a new pixbuf
            :rtype: :class:`ExtendedPixbuf`
        """
        spacing = max(0, spacing)
        new_pixbuf = gtk.gdk.Pixbuf(
            self.get_colorspace(),
            self.get_has_alpha(),
            self.get_bits_per_sample(),
            self.get_width() * multiplier + spacing * multiplier,
            self.get_height()
        )
        new_pixbuf.fill(0xffffff00)

        for n in xrange(0, multiplier):
            self.copy_area(
                src_x=0, src_y=0,
                width=self.get_width(), height=self.get_height(),
                dest_pixbuf=new_pixbuf,
                dest_x=n * self.get_width() + n * spacing, dest_y=0
            )

        return ExtendedPixbuf(new_pixbuf)

    def multiply_vertical(self, multiplier, spacing=0):
        """
            Vertically multiplies the current pixbuf content

            :param multiplier: How often the pixbuf
                shall be multiplied
            :type multiplier: int
            :param spacing: amount of pixels between the pixbufs
            :type spacing: int
            :returns: a new pixbuf
            :rtype: :class:`ExtendedPixbuf`
        """
        spacing = max(0, spacing)
        new_pixbuf = gtk.gdk.Pixbuf(
            self.get_colorspace(),
            self.get_has_alpha(),
            self.get_bits_per_sample(),
            self.get_width(),
            self.get_height() * multiplier + spacing * multiplier
        )
        new_pixbuf.fill(0xffffff00)

        for n in xrange(0, multiplier):
            self.copy_area(
                src_x=0, src_y=0,
                width=self.get_width(), height=self.get_height(),
                dest_pixbuf=new_pixbuf,
                dest_x=0, dest_y=n * self.get_height() + n * spacing
            )

        return ExtendedPixbuf(new_pixbuf)

    def composite_simple(self, other):
        """
            Composites a pixbuf on the current
            pixbuf at the location (0, 0)
            
            :param other: the pixbuf to composite
            :type other: :class:`gtk.gdk.Pixbuf`
            :returns: a new pixbuf
            :rtype: :class:`ExtendedPixbuf`
        """
        width = max(self.get_width(), other.get_width())
        height = max(self.get_height(), other.get_height())

        new_pixbuf = gtk.gdk.Pixbuf(
            self.get_colorspace(),
            self.get_has_alpha(),
            self.get_bits_per_sample(),
            width, height
        )
        new_pixbuf.fill(0xffffff00)

        for pixbuf in (self, other):
            pixbuf.composite(
                dest=new_pixbuf,
                dest_x=0, dest_y=0,
                dest_width=pixbuf.get_width(),
                dest_height=pixbuf.get_height(),
                offset_x=0, offset_y=0,
                scale_x=1, scale_y=1,
                interp_type=gtk.gdk.INTERP_BILINEAR,
                # Alpha needs to be embedded in the pixbufs
                overall_alpha=255
            )

        return ExtendedPixbuf(new_pixbuf)

    def move(self, offset_x, offset_y, resize=False):
        """
            Moves the content of the current pixbuf within
            its boundaries (clips overlapping data) and
            optionally resizes the pixbuf to contain the
            movement

            :param offset_x: the amount of pixels to move
                in horizontal direction
            :type offset_x: int
            :param offset_y: the amount of pixels to move
                in vertical direction
            :type offset_y: int
            :param resize: whether to resize the pixbuf
                on movement
            :type resize: bool
            :returns: a new pixbuf
            :rtype: :class:`ExtendedPixbuf`
        """
        width = self.get_width()
        height = self.get_height()

        if resize:
            width += offset_x
            height += offset_y

        new_pixbuf = gtk.gdk.Pixbuf(
            self.get_colorspace(),
            self.get_has_alpha(),
            self.get_bits_per_sample(),
            width, height
        )
        new_pixbuf.fill(0xffffff00)

        self.copy_area(
            src_x=0, src_y=0,
            width=self.get_width(),
            height=self.get_height(),
            dest_pixbuf=new_pixbuf,
            dest_x=offset_x, dest_y=offset_y
        )

        return ExtendedPixbuf(new_pixbuf)

    def copy(self):
        """
            Override to return same type
        """
        return ExtendedPixbuf(gtk.gdk.Pixbuf.copy(self))

    def add_alpha(self, substitute_color, r, g, b):
        """
            Override to return same type
        """
        return ExtendedPixbuf(gtk.gdk.Pixbuf.add_alpha(
            self, substitute_color, r, g, b))

    def scale_simple(self, dest_width, dest_height, interp_type):
        """
            Override to return same type
        """
        return ExtendedPixbuf(gtk.gdk.Pixbuf.scale_simple(
            self, dest_width, dest_height, interp_type))

    def composite_color_simple(self, dest_width, dest_height, interp_type,
                               overall_alpha, check_size, color1, color2):
        """
            Override to return same type
        """
        return ExtendedPixbuf(gtk.gdk.Pixbuf.composite_color_simple(
            self, dest_width, dest_height, interp_type,
            overall_alpha, check_size, color1, color2))

    def subpixbuf(self, src_x, src_y, width, height):
        """
            Override to return same type
        """
        return ExtendedPixbuf(gtk.gdk.Pixbuf.subpixbuf(
            self, src_x, src_y, width, height))

    def rotate_simple(self, angle):
        """
            Override to return same type
        """
        return ExtendedPixbuf(gtk.gdk.Pixbuf.rotate_simple(self, angle))

    def flip(self, horizontal):
        """
            Override to return sampe type
        """
        return ExtendedPixbuf(gtk.gdk.Pixbuf.flip(self, horizontal))

def extended_pixbuf_new_from_file(filename):
    """
        Returns a new ExtendedPixbuf containing
        an image loaded from the specified file

        :param filename: the name of the file
            containing the image to load
        :type filename: string
        :returns: a new pixbuf
        :rtype: :class:`ExtendedPixbuf`
    """
    return ExtendedPixbuf(gtk.gdk.pixbuf_new_from_file(filename))
    
    
    
class IconManager:
	def __init__(self):
		self.system_visual = gtk.gdk.visual_get_system()
		self.system_colormap = gtk.gdk.colormap_get_system()
		# TODO: Make svg actually recognized
		self._sizes = [16, 22, 24, 32, 48, 'scalable']
		self._cache = {}
		self.rating_active_pixbuf = extended_pixbuf_new_from_file('icons/star.png')
		self.rating_inactive_pixbuf = extended_pixbuf_new_from_file('icons/emptystar.png')
		self.rating_pixbufs = []
		self._generate_rating_pixbufs()
		
	def pixbuf_from_rating(self, rating):
		"""
		Returns a pixbuf representing a rating

		:param rating: the rating
		:type rating: int

		:returns: the rating pixbuf
		:rtype: :class:`gtk.gdk.Pixbuf`
		"""
		rating = max(0, rating)
		rating = min(rating, len(self.rating_pixbufs) - 1)
		return self.rating_pixbufs[rating]

	def _generate_rating_pixbufs(self):
		"""
		Generates the pixbufs for
		the various rating stages
		"""
		maximum = 5
		width = self.rating_active_pixbuf.get_width()
		height = self.rating_active_pixbuf.get_height()

		self.rating_pixbufs = [self.rating_inactive_pixbuf * maximum]

		for n in xrange(1, maximum):
			active_pixbufs = self.rating_active_pixbuf * n
			inactive_pixbufs = self.rating_inactive_pixbuf * (maximum - n)
			self.rating_pixbufs += [active_pixbufs + inactive_pixbufs]

		self.rating_pixbufs += [self.rating_active_pixbuf * maximum]
		
	def pixbuf_from_text(self, text, size, background_color='#456eac',
	border_color='#000', text_color='#fff'):
		"""
		Generates a pixbuf based on a text, width and height
		
		:param size: A tuple describing width and height
		:type size: tuple of int
		:param background_color: The color of the background as
		hexadecimal value
		:type background_color: string
		:param border_color: The color of the border as
		hexadecimal value
		:type border_color: string
		:param text_color: The color of the text as
		hexadecimal value
		:type text_color: string
		"""
		pixmap_width, pixmap_height = size
		key = '%s - %sx%s - %s' % (text, pixmap_width, pixmap_height,
		background_color)
		
		if self._cache.has_key(key):
			return self._cache[key]
			
		pixmap = gtk.gdk.Pixmap(None, pixmap_width, pixmap_height,
		self.system_visual.depth)
		context = pixmap.cairo_create()
		
		context.set_source_color(gtk.gdk.Color(background_color))
		context.set_line_width(1)
		context.rectangle(1, 1, pixmap_width - 2, pixmap_height - 2)
		context.fill()
		
		context.set_source_color(gtk.gdk.Color(text_color))
		context.select_font_face('sans-serif 10')
		x_bearing, y_bearing, width, height = context.text_extents(text)[:4]
		x = pixmap_width / 2 - width / 2 - x_bearing
		y = pixmap_height / 2 - height / 2 - y_bearing
		context.move_to(x, y)
		context.show_text(text)
		
		context.set_source_color(gtk.gdk.Color(border_color))
		context.set_antialias(cairo.ANTIALIAS_NONE)
		context.rectangle(0, 0, pixmap_width - 1, pixmap_height - 1)
		context.stroke()
		
		pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8,
		pixmap_width, pixmap_height)
		pixbuf = pixbuf.get_from_drawable(pixmap, self.system_colormap,
		0, 0, 0, 0, pixmap_width, pixmap_height)
		
		self._cache[key] = pixbuf
		
		return pixbuf

MANAGER = IconManager()
#class IconManager(object):
    #"""
        #Provides convenience functions for
        #managing icons and images in general
    #"""
    #def __init__(self):
        #self.icon_theme = gtk.icon_theme_get_default()
        #self.icon_factory = gtk.IconFactory()
        #self.icon_factory.add_default()
        ## Any arbitrary widget is fine
        #self.render_widget = gtk.Button()
        #self.system_visual = gtk.gdk.visual_get_system()
        #self.system_colormap = gtk.gdk.colormap_get_system()
        ## TODO: Make svg actually recognized
        #self._sizes = [16, 22, 24, 32, 48, 'scalable']
        #self._cache = {}

        #self.rating_active_pixbuf = extended_pixbuf_new_from_file(
                #xdg.get_data_path('images', 'star.png'))
        #self.rating_inactive_pixbuf = extended_pixbuf_new_from_file(
            #xdg.get_data_path('images', 'emptystar.png'))
        #self.rating_pixbufs = []
        #self._generate_rating_pixbufs()

        #event.add_callback(self.on_option_set, 'rating_option_set')

    #def add_icon_name_from_directory(self, icon_name, directory):
        #"""
            #Registers an icon name from files found in a directory
            
            #:param icon_name: the name for the icon
            #:type icon_name: string
            #:param directory: the location to search for icons
            #:type directory: string
        #"""
        #for size in self._sizes:
            #try: # WxH/icon_name.png and scalable/icon_name.svg
                #sizedir = '%dx%d' % (size, size)
            #except TypeError:
                #sizedir = size
            #filepath = os.path.join(directory, sizedir, icon_name)
            #files = glob.glob('%s.*' % filepath)
            #try:
                #icon_size = size if size != 'scalable' else -1
                #self.add_icon_name_from_file(icon_name, files[0], icon_size)
            #except IndexError: # icon_nameW.png and icon_name.svg
                #try:
                    #filename = '%s%d' % (icon_name, size)
                #except TypeError:
                    #filename = icon_name
                #filepath = os.path.join(directory, filename)
                #files = glob.glob('%s.*' % filepath)
                #try:
                    #icon_size = size if size != 'scalable' else -1
                    #self.add_icon_name_from_file(icon_name, files[0], icon_size)
                #except IndexError: # Give up
                    #pass

    #def add_icon_name_from_file(self, icon_name, filename, size=None):
        #"""
            #Registers an icon name from a filename
            
            #:param icon_name: the name for the icon
            #:type icon_name: string
            #:param filename: the filename of an image
            #:type filename: string
            #:param size: the size the icon shall be registered for
            #:type size: int
        #"""
        #try:
            #pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
            #self.add_icon_name_from_pixbuf(icon_name, pixbuf, size)
        #except Exception:
            ## Happens if, e.g., librsvg is not installed.
            #pass

    #def add_icon_name_from_pixbuf(self, icon_name, pixbuf, size=None):
        #"""
            #Registers an icon name from a pixbuf
            
            #:param icon_name: the name for the icon
            #:type icon_name: string
            #:param pixbuf: the pixbuf of an image
            #:type pixbuf: :class:`gtk.gdk.Pixbuf`
            #:param size: the size the icon shall be registered for
            #:type size: int
        #"""
        #if size is None:
            #size = pixbuf.get_width()

        #gtk.icon_theme_add_builtin_icon(icon_name, size, pixbuf)

    #def add_stock_from_directory(self, stock_id, directory):
        #"""
            #Registers a stock icon from files found in a directory

            #:param stock_id: the stock id for the icon
            #:type stock_id: string
            #:param directory: the location to search for icons
            #:type directory: string
        #"""
        #files = []
        #self._sizes.reverse() # Prefer small over downscaled icons

        #for size in self._sizes:
            #try: # WxH/stock_id.png and scalable/stock_id.svg
                #sizedir = '%dx%d' % (size, size)
            #except TypeError:
                #sizedir = size
            #filepath = os.path.join(directory, sizedir, stock_id)
            #try:
                #files += [glob.glob('%s.*' % filepath)[0]]
            #except IndexError: # stock_idW.png and stock_id.svg
                #try:
                    #filename = '%s%d' % (stock_id, size)
                #except TypeError:
                    #filename = stock_id
                #filepath = os.path.join(directory, filename)
                #try:
                    #files += [glob.glob('%s.*' % filepath)[0]]
                #except IndexError: # Give up
                    #pass

        #self.add_stock_from_files(stock_id, files)

    #def add_stock_from_file(self, stock_id, filename):
        #"""
            #Registers a stock icon from a filename

            #:param stock_id: the stock id for the icon
            #:type stock_id: string
            #:param filename: the filename of an image
            #:type filename: string
        #"""
        #self.add_stock_from_files([filename])

    #def add_stock_from_files(self, stock_id, filenames):
        #"""
            #Registers a stock icon from filenames

            #:param stock_id: the stock id for the icon
            #:type stock_id: string
            #:param filenames: the filenames of images
            #:type filenames: list of string
        #"""
        #pixbufs = [gtk.gdk.pixbuf_new_from_file(filename) for filename in filenames]
        #self.add_stock_from_pixbufs(stock_id, pixbufs)

    #def add_stock_from_pixbuf(self, stock_id, pixbuf):
        #"""
            #Registers a stock icon from a pixbuf

            #:param stock_id: the stock id for the icon
            #:type stock_id: string
            #:param pixbuf: the pixbuf of an image
            #:type pixbuf: :class:`gtk.gdk.Pixbuf`
        #"""
        #self.add_stock_from_pixbufs(stock_id, [pixbuf])

    #def add_stock_from_pixbufs(self, stock_id, pixbufs):
        #"""
            #Registers a stock icon from pixbufs

            #:param stock_id: the stock id for the icon
            #:type stock_id: string
            #:param pixbuf: the pixbufs of images
            #:type pixbuf: list of :class:`gtk.gdk.Pixbuf`
        #"""
        #icon_set = gtk.IconSet()

        #for pixbuf in pixbufs:
            #icon_source = gtk.IconSource()
            #icon_source.set_pixbuf(pixbuf)
            #icon_set.add_source(icon_source)

        #self.icon_factory.add(stock_id, icon_set)

    #def pixbuf_from_stock(self, stock_id, size=gtk.ICON_SIZE_BUTTON):
        #"""
            #Generates a pixbuf from a stock id

            #:param stock_id: a stock id
            #:type stock_id: string
            #:param size: the size of the icon
            #:type size: GtkIconSize

            #:returns: the generated pixbuf
            #:rtype: :class:`gtk.gdk.Pixbuf` or None
        #"""
        ## TODO: Check if fallbacks are necessary
        #return self.render_widget.render_icon(stock_id, size)

    #def pixbuf_from_icon_name(self, icon_name, size=gtk.ICON_SIZE_BUTTON):
        #"""
            #Generates a pixbuf from an icon name

            #:param stock_id: an icon name
            #:type stock_id: string
            #:param size: the size of the icon
            #:type size: GtkIconSize

            #:returns: the generated pixbuf
            #:rtype: :class:`gtk.gdk.Pixbuf` or None
        #"""
        #try:
            #pixbuf = self.icon_theme.load_icon(
                #icon_name, size, gtk.ICON_LOOKUP_NO_SVG)
        #except glib.GError:
            #pixbuf = None

        ## TODO: Check if fallbacks are necessary
        #return pixbuf
    
    #def pixbuf_from_data(self, data, size=None, keep_ratio=True, upscale=False):
        #"""
            #Generates a pixbuf from arbitrary image data

            #:param data: The raw image data
            #:type data: byte
            #:param size: Size to scale to; if not specified,
                #the image will render to its native size
            #:type size: tuple of int
            #:param keep_ratio: Whether to keep the original
                #image ratio on resizing operations
            #:type keep_ratio: bool
            #:param upscale: Whether to upscale if the requested
                #size exceeds the native size
            #:type upscale: bool

            #:returns: the generated pixbuf
            #:rtype: :class:`gtk.gdk.Pixbuf` or None
        #"""
        #if not data:
            #return None

        #def on_size_prepared(loader, width, height):
            #"""
                #Keeps the ratio if requested
            #"""
            #if size is not None:
                #if keep_ratio:
                    #scale = min(size[0] / float(width), size[1] / float(height))

                    #if scale > 1.0 and upscale:
                        #width = int(width * scale)
                        #height = int(height * scale)
                    #elif scale <= 1.0:
                        #width = int(width * scale)
                        #height = int(height * scale)
                #else:
                    #if upscale:
                        #width, height = size
                    #else:
                        #width = height = max(width, height)

            #loader.set_size(width, height)

        #loader = gtk.gdk.PixbufLoader()
        #loader.connect('size-prepared', on_size_prepared)
        #try:
            #loader.write(data)
            #loader.close()
        #except glib.GError:
            #return None

        #return loader.get_pixbuf()



    #def pixbuf_from_rating(self, rating):
        #"""
            #Returns a pixbuf representing a rating

            #:param rating: the rating
            #:type rating: int

            #:returns: the rating pixbuf
            #:rtype: :class:`gtk.gdk.Pixbuf`
        #"""
        #rating = max(0, rating)
        #rating = min(rating, len(self.rating_pixbufs) - 1)

        #return self.rating_pixbufs[rating]

    #def _generate_rating_pixbufs(self):
        #"""
            #Generates the pixbufs for
            #the various rating stages
        #"""
        #maximum = settings.get_option('rating/maximum', 5)
        #width = self.rating_active_pixbuf.get_width()
        #height = self.rating_active_pixbuf.get_height()

        #self.rating_pixbufs = [self.rating_inactive_pixbuf * maximum]

        #for n in xrange(1, maximum):
            #active_pixbufs = self.rating_active_pixbuf * n
            #inactive_pixbufs = self.rating_inactive_pixbuf * (maximum - n)
            #self.rating_pixbufs += [active_pixbufs + inactive_pixbufs]

        #self.rating_pixbufs += [self.rating_active_pixbuf * maximum]

    #def on_option_set(self, event_type, settings, option):
        #"""
            #Regenerates the rating pixbufs
        #"""
        #if option == 'rating/maximum':
            #self._generate_rating_pixbufs()



# vim: et sts=4 sw=4
