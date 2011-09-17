# -*- coding: utf-8 -*-
import gtk
import gobject
import icons
IM = icons.IconManager()
class RatingWidget(gtk.EventBox):
    """
        A rating widget which displays a row of
        images and allows for selecting the rating
        TODO? rating not setted (-1) to differenciate from rating 0
    """
    __gproperties__ = {
        'rating': (
            gobject.TYPE_INT,
            'rating',
            'The selected rating',
            0, # Minimum
            65535, # Maximum
            0, # Default
            gobject.PARAM_READWRITE
        )
    }
    __gsignals__ = {
        'rating-changed': (
            gobject.SIGNAL_RUN_LAST,
            gobject.TYPE_NONE,
            (gobject.TYPE_INT,)
        )
    }

    def __init__(self, rating=0, auto_update=True):
        """
            :param rating: the optional initial rating
            :type rating: int
            :param auto_update: whether to automatically
                retrieve the rating of the currently playing
                track if a rating was changed
            :type auto_update: bool
        """
        gtk.EventBox.__init__(self)

        self.set_visible_window(False)
        self.set_above_child(True)
        self.add_events(gtk.gdk.POINTER_MOTION_MASK)
        self.set_flags(self.flags() | gtk.CAN_FOCUS)

        self._image = gtk.Image()
        self.add(self._image)

        self._rating = -1
        self.props.rating = rating

        if auto_update:
            try:
                exaile = xl.main.exaile()
            except AttributeError:
                event.add_callback(self.on_exaile_loaded, 'exaile_loaded')
            else:
                self.on_exaile_loaded('exaile_loaded', exaile, None)

            for event_name in ('playback_track_start', 'playback_player_end',
                               'rating_changed'):
                event.add_callback(self.on_rating_update, event_name)

    def destroy(self):
        """
            Cleanups
        """
        for event_name in ('playback_track_start', 'playback_player_start',
                           'rating_changed'):
            event.remove_callback(self.on_rating_update, event_name)

    def do_get_property(self, property):
        """
            Getter for custom properties
        """
        if property.name == 'rating':
            return self._rating
        else:
            raise AttributeError('unkown property %s' % property.name)

    def do_set_property(self, property, value):
        """
            Setter for custom properties
        """
        if property.name == 'rating':
            #if value == self._rating:
                #value = 0
            #else:
            value = min(value, 5)

            self._rating = value
            self._image.set_from_pixbuf(
                IM.pixbuf_from_rating(value))

            #self.emit('rating-changed', value)
        else:
            raise AttributeError('unkown property %s' % property.name)

    def do_expose_event(self, event):
        """
            Takes care of painting the focus indicator
        """
        if self.is_focus():
            self.style.paint_focus(
                window=self.window,
                state_type=self.get_state(),
                area=event.area,
                widget=self,
                detail='button', # Borrow style from GtkButton
                x=event.area.x,
                y=event.area.y,
                width=event.area.width,
                height=event.area.height
            )

        gtk.EventBox.do_expose_event(self, event)

    def do_motion_notify_event(self, event):
        """
            Temporarily updates the displayed rating
        """
        if self.get_state() & gtk.STATE_INSENSITIVE:
            return

        allocation = self.get_allocation()
        maximum = 5
        pixbuf_width = self._image.get_pixbuf().get_width()
        # Activate pixbuf if half of it has been passed
        threshold = (pixbuf_width / maximum) / 2
        position = (event.x + threshold) / allocation.width
        rating = int(position * maximum)

        self._image.set_from_pixbuf(
           IM.pixbuf_from_rating(rating))

    def do_leave_notify_event(self, event):
        """
            Restores the original rating
        """
        if self.get_state() & gtk.STATE_INSENSITIVE:
            return

        self._image.set_from_pixbuf(
            IM.pixbuf_from_rating(self._rating))

    def do_button_release_event(self, event):
        """
            Applies the selected rating
        """
        if self.get_state() & gtk.STATE_INSENSITIVE:
            return

        allocation = self.get_allocation()
        maximum = 5
        pixbuf_width = self._image.get_pixbuf().get_width()
        # Activate pixbuf if half of it has been passed
        threshold = (pixbuf_width / maximum) / 2
        position = (event.x + threshold) / allocation.width
        self.props.rating = int(position * maximum)
        self.emit('rating-changed', self.props.rating)

    def do_key_press_event(self, event):
        """
            Changes the rating on keyboard interaction
            * Alt+Up/Right: increases the rating
            * Alt+Down/Left: decreases the rating
        """
        if self.get_state() & gtk.STATE_INSENSITIVE:
            return

        if not event.state & gtk.gdk.MOD1_MASK:
            return

        if event.keyval in (gtk.keysyms.Up, gtk.keysyms.Right):
            rating = self.props.rating + 1
        elif event.keyval in (gtk.keysyms.Down, gtk.keysyms.Left):
            rating = self.props.rating - 1
        else:
            return

        rating = max(0, rating)

        # Prevents unsetting rating if maximum is reached
        if rating == self.props.rating:
            return

        self.props.rating = rating


            
            
class RatingCellRenderer(gtk.CellRendererPixbuf):
    """
        A cell renderer drawing rating images
        and allowing for selection of ratings
    """
    __gproperties__ = {
        'rating': (
            gobject.TYPE_INT,
            'Rating',
            'The selected rating',
            0, # Minimum
            65535, # Maximum
            0, # Default
            gobject.PARAM_READWRITE
        )
    }
    __gsignals__ = {
        'rating-changed': (
            gobject.SIGNAL_RUN_LAST,
            gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT, gobject.TYPE_INT)
        )
    }

    def __init__(self):
        gtk.CellRendererPixbuf.__init__(self)
        self.props.mode = gtk.CELL_RENDERER_MODE_ACTIVATABLE
        self.props.xalign = 0

    def do_get_property(self, property):
        """
            Getter for GObject properties
        """
        if property.name == 'rating':
            return self.rating
        else:
            raise AttributeError('unkown property %s' % property.name)

    def do_set_property(self, property, value):
        """
            Setter for GObject properties
        """
        if property == 'rating':
            self.rating = value
            self.props.pixbuf = IM.pixbuf_from_rating(self.rating)
        else:
            raise AttributeError('unkown property %s' % property.name)

    def do_activate(self, event, widget, path,
                    background_area, cell_area, flags):
        """
            Checks if a button press event did occur
            within the clickable rating image area
        """
        if event is None: # Keyboard activation
            return

        # Locate click area at zero
        click_area = gtk.gdk.Rectangle(
            x=0,
            y=self.props.ypad,
            width=self.props.pixbuf.get_width(),
            height=self.props.pixbuf.get_height()
        )

        # Move event location relative to zero
        event.x -= cell_area.x + click_area.x
        event.y -= cell_area.y + click_area.y + 5

        if 0 <= event.x <= click_area.width and \
           0 <= event.y <= click_area.height:
            fraction = event.x / click_area.width
            maximum = 5
            rating = fraction * maximum + 1
            self.emit('rating-changed', (int(path),), rating)

    def do_render(self, window, widget, background_area,
                  cell_area, expose_area, flags):
        """
            Renders the rating images
            (Overriden since gtk.CellRendererPixbuf
             fails at vertical padding)
        """
        cell_area.width *= self.props.xalign
        cell_area.height *= self.props.yalign

        pixbuf_width = self.props.pixbuf.get_width() * self.props.xalign
        pixbuf_height = self.props.pixbuf.get_height() * self.props.yalign

        x = cell_area.x + cell_area.width - pixbuf_width
        y = cell_area.y + cell_area.height - pixbuf_height

        window.draw_pixbuf(None, self.props.pixbuf, 0, 0, int(x), int(y))
        
        
        
class RatingMenuItem(gtk.MenuItem):
    """
        A menuitem containing a rating widget
    """
    __gproperties__ = {
        'rating': (
            gobject.TYPE_INT,
            'rating',
            'The selected rating',
            0, # Minimum
            65535, # Maximum
            0, # Default
            gobject.PARAM_READWRITE
        )
    }
    __gsignals__ = {
        'rating-changed': (
            gobject.SIGNAL_RUN_LAST,
            gobject.TYPE_NONE,
            (gobject.TYPE_INT,)
        )
    }
    def __init__(self, rating=0, auto_update=True):
        """
            :param rating: the optional initial rating
            :type rating: int
            :param auto_update: whether to automatically
                retrieve the rating of the currently playing
                track if a rating was changed
            :type auto_update: bool
        """
        gtk.MenuItem.__init__(self)

        box = gtk.HBox(spacing=6)
        box.pack_start(gtk.Label(_('Rating:')), False, False)
        self.rating_widget = RatingWidget(rating, auto_update)
        box.pack_start(self.rating_widget, False, False)

        self.add(box)

        self.rating_widget.connect('rating-changed',
            self.on_rating_changed)

    def do_get_property(self, property):
        """
            Getter for custom properties
        """
        if property.name == 'rating':
            return self.rating_widget.props.rating
        else:
            raise AttributeError('unkown property %s' % property.name)

    def do_set_property(self, property, value):
        """
            Setter for custom properties
        """
        if property.name == 'rating':
            self.rating_widget.props.rating = value
        else:
            raise AttributeError('unkown property %s' % property.name)

    def do_motion_notify_event(self, event):
        """
            Forwards the event to the rating widget
        """
        allocation = self.rating_widget.get_allocation()

        if allocation.x < event.x < allocation.x + allocation.width:
            x, y = self.translate_coordinates(self.rating_widget,
                int(event.x), int(event.y))
            event.x, event.y = float(x), float(y)
            self.rating_widget.emit('motion-notify-event', event)

    def do_leave_notify_event(self, event):
        """
            Forwards the event to the rating widget
        """
        self.rating_widget.emit('leave-notify-event', event)

    def do_button_release_event(self, event):
        """
            Forwards the event to the rating widget
        """
        allocation = self.rating_widget.get_allocation()

        if allocation.x < event.x < allocation.x + allocation.width:
            x, y = self.translate_coordinates(self.rating_widget,
                int(event.x), int(event.y))
            event.x, event.y = float(x), float(y)
            self.rating_widget.emit('button-release-event', event)

    def on_rating_changed(self, widget, rating):
        """
            Forwards the event
        """
        self.emit('rating-changed', rating)


