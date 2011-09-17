# -*- coding: utf-8 -*-
# Copyright (C) 2008-2010 Adam Olsen
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
#
# The developers of the Exaile media player hereby grant permission
# for non-GPL compatible GStreamer and Exaile plugins to be used and
# distributed together with GStreamer and Exaile. This permission is
# above and beyond the permissions granted by the GPL license by which
# Exaile is covered. If you modify this code, you may extend this
# exception to your version of the code, but you are not obligated to
# do so. If you do not wish to do so, delete this exception statement
# from your version.

"""
Provides a signals-like system for sending and listening for 'events'


Events are kind of like signals, except they may be listened for on a
global scale, rather than connected on a per-object basis like signals
are. This means that ANY object can emit ANY event, and these events may
be listened for by ANY object. Events may be emitted either syncronously
or asyncronously, the default is asyncronous.

The events module also provides an idle_add() function similar to that of
glib. However this should not be used for long-running tasks as they
may block other events queued via idle_add().

Events should be emitted AFTER the given event has taken place. Often the
most appropriate spot is immediately before a return statement.

	Ce procédé doit être utilisé pour gérer des signaux custom de façon simple.
	Je l'ai utilisé pour ne pas faire de liens directs entre les objets mais c'est clairement un détournement malvenu.
	Il faut plutôt l'utiliser quand on se contrefiche du ou des récepteurs.
	Par exemple l'éditeur de tags pourrait envoyer le signal (tag_changed, ID) 
	et ainsi toutes les queues ouvertes et le librarybrowser (qui sont abonnés à tag_changed)
	mettraient à jour la valeur dans leur modèle.
"""


from __future__ import with_statement

from inspect import ismethod
import logging
from new import instancemethod
import re
import threading
import time
import traceback
import weakref
import glib

# define this here so the interperter doesn't complain
EVENT_MANAGER = None

logger = logging.getLogger(__name__)

class Nothing(object):
    pass

_NONE = Nothing() # used by event for a safe None replacement

def diffuser(type, obj, data, async=True):
    """
        Sends an event.

        type: the 'type' or 'name' of the event. [string]
        obj: the object sending the event. [object]
        data: some data about the event, None if not required [object]
        async: whether or not to emit asyncronously. [bool]
    """
    global EVENT_MANAGER
    e = Event(type, obj, data, time.time())
    if async:
        EVENT_MANAGER.emit_async(e)
    else:
        EVENT_MANAGER.emit(e)

def log_event_sync(type, obj, data, async=False):
    # same as log_event, but defaults to synchronous
    log_event(type, obj, data, async)

def inscrire(function, type=None, obj=None, *args, **kwargs):
    """
        Abonne un objet à un type de message
        Lorsque le messager recevra un message du type demandé, il demandera à l'objet d'exécuter sa méthode associée.

        You should ALWAYS specify one of the two options on what to listen
        for. While not forbidden to listen to all events, doing so will
        cause your callback to be called very frequently, and possibly may
        cause slowness within the player itself.

        @param function: the function to call when the event happens [function]
        @param type: the 'type' or 'name' of the event to listen for, eg
                "tracks_added",  "cover_changed". Defaults to any event if
                not specified. [string]
        @param obj: the object to listen to events from, eg exaile.collection,
                exaile.cover_manager. Defaults to any object if not
                specified. [object]
        Any additional paramaters will be passed to the callback.
    """
    global EVENT_MANAGER
    EVENT_MANAGER.add_callback(function, type, obj, args, kwargs)

def remove_callback(function, type=None, obj=None):
    """
        Removes a callback

        The parameters passed should match those that were passed when adding
        the callback
    """
    global EVENT_MANAGER
    EVENT_MANAGER.remove_callback(function, type, obj)


class Event(object):
    """
        Represents an Event
    """
    def __init__(self, type, obj, data, time):
        """
            type: the 'type' or 'name' for this Event [string]
            obj: the object emitting the Event [object]
            data: some piece of data relevant to the Event [object]
        """
        self.type = type
        self.object = obj
        self.data = data
        self.time = time

class Callback(object):
    """
        Represents a callback
    """
    def __init__(self, function, time, args, kwargs):
        """
            @param function: the function to call
            @param time: the time this callback was added
        """
        self.valid = True
        self.wfunction = _getWeakRef(function, self.vanished)
        self.time = time
        self.args = args
        self.kwargs = kwargs

    def vanished(self, ref):
        self.valid = False

class _WeakMethod:
    """Represent a weak bound method, i.e. a method doesn't keep alive the
    object that it is bound to. It uses WeakRef which, used on its own,
    produces weak methods that are dead on creation, not very useful.
    Typically, you will use the getRef() function instead of using
    this class directly. """

    def __init__(self, method, notifyDead = None):
        """
            The method must be bound. notifyDead will be called when
            object that method is bound to dies.
        """
        assert ismethod(method)
        if method.im_self is None:
            raise ValueError, "We need a bound method!"
        if notifyDead is None:
            self.objRef = weakref.ref(method.im_self)
        else:
            self.objRef = weakref.ref(method.im_self, notifyDead)
        self.fun = method.im_func
        self.cls = method.im_class

    def __call__(self):
        if self.objRef() is None:
            return None
        else:
            return instancemethod(self.fun, self.objRef(), self.cls)

    def __eq__(self, method2):
        if not isinstance(method2, _WeakMethod):
            return False
        return      self.fun      is method2.fun \
                and self.objRef() is method2.objRef() \
                and self.objRef() is not None

    def __hash__(self):
        return hash(self.fun)

    def __repr__(self):
        dead = ''
        if self.objRef() is None:
            dead = '; DEAD'
        obj = '<%s at %s%s>' % (self.__class__, id(self), dead)
        return obj

    def refs(self, weakRef):
        """Return true if we are storing same object referred to by weakRef."""
        return self.objRef == weakRef

def _getWeakRef(obj, notifyDead=None):
    """
        Get a weak reference to obj. If obj is a bound method, a _WeakMethod
        object, that behaves like a WeakRef, is returned, if it is
        anything else a WeakRef is returned. If obj is an unbound method,
        a ValueError will be raised.
    """
    if ismethod(obj):
        createRef = _WeakMethod
    else:
        createRef = weakref.ref

    if notifyDead is None:
        return createRef(obj)
    else:
        return createRef(obj, notifyDead)



class EventManager(object):
	"""
	Gère tous les messages
	À la reception d'un message, il demande à tous les objets enregistrés (à ce type de message) d'exécuter leur réponse
	"""
	def __init__(self, use_logger=False, logger_filter=None):
		self.callbacks = {}
		self.use_logger = use_logger
		self.logger_filter = logger_filter

		# RLock is needed so that event callbacks can themselves send
		# synchronous events and add or remove callbacks
		self.lock = threading.RLock()

	def emit(self, message):
		"""
		Diffuse un message : tous les objets abonnés à ce type de message exécutent leur méthode (réponse) enregistrée lors de l'inscription
		event: the Event to emit [Event]
		"""
		print ("Message : " + message.type)
		with self.lock:
			callbacks = set()
			for tcall in [_NONE, message.type]:
				for ocall in [_NONE, message.object]:
					try:
						callbacks.update(self.callbacks[tcall][ocall])
					except KeyError:
						pass

			# now call them
			for cb in callbacks:
				#try:
				if not cb.valid:
					try:
						self.callbacks[message.type][message.object].remove(cb)
					except KeyError:
						pass
					except ValueError:
						pass
				elif message.time >= cb.time:
					if self.use_logger and (not self.logger_filter or \
							re.search(self.logger_filter, message.type)):
							logger.debug("Attempting to call "
							"%(function)s in response "
							"to %(message)s." % {
								'function': cb.wfunction(),
								'event': message.type})
					#cb.wfunction().__call__(event.type, event.object,
							#event.data, *cb.args, **cb.kwargs)
					cb.wfunction().__call__(message.data, *cb.args, **cb.kwargs)
				#except:
				## something went wrong inside the function we're calling
				#common.log_exception(logger,
						#message="Event callback exception caught!")

		if self.use_logger:
			if not self.logger_filter or re.search(self.logger_filter, message.type):
				logger.debug("Sent '%(type)s' event from "
				"'%(object)s' with data '%(data)s'." %
					{'type' : message.type, 'object' : repr(message.object),
					'data' : repr(message.data)})

	def emit_async(self, event):
		"""
		Same as emit(), but does not block.
		"""
		glib.idle_add(self.emit, event)

	def add_callback(self, function, type, obj, args, kwargs):
		"""
		Registers a callback.
		You should always specify at least one of type or object.

		@param function: The function to call [function]
		@param type: The 'type' or 'name' of event to listen for. Defaults
			to any. [string]
		@param obj: The object to listen to events from. Defaults
			to any. [string]
		"""
		with self.lock:
			# add the specified categories if needed.
			if not self.callbacks.has_key(type):
				self.callbacks[type] = weakref.WeakKeyDictionary()
			if obj is None:
				obj = _NONE
			try:
				callbacks = self.callbacks[type][obj]
			except KeyError:
				callbacks = self.callbacks[type][obj] = []

			# add the actual callback
			callbacks.append(Callback(function, time.time(), args, kwargs))

		if self.use_logger:
			if not self.logger_filter or re.search(self.logger_filter, type):
				logger.debug("Added callback %s for [%s, %s]" %
					(function, type, obj))

	def remove_callback(self, function, type=None, obj=None):
		"""
		Unsets a callback

		The parameters must match those given when the callback was
		registered. (minus any additional args)
		"""
		if obj is None:
			obj = _NONE
		remove = []

		with self.lock:
			try:
				callbacks = self.callbacks[type][obj]
				for cb in callbacks:
					if cb.wfunction() == function:
						remove.append(cb)
			except KeyError:
				return
			except TypeError:
				return

			for cb in remove:
				callbacks.remove(cb)

		if self.use_logger:
			if not self.logger_filter or re.search(self.logger_filter, type):
				logger.debug("Removed callback %s for [%s, %s]" %
					(function, type, obj))



EVENT_MANAGER = EventManager()

# vim: et sts=4 sw=4

