# -*- coding: utf-8 -*-
import sqlite3
import os
from music.tags import Tags
from datetime import datetime
import time
import logging
import threading
from common import messager, xdg
from data.bdd import BDD

logger = logging.getLogger(__name__)



			

class SpecialElement():
	def __init__(self, data, module, thumbnail_path=None):
		if(type(data).__name__=='int'):
			ID = str(data)
			query = "SELECT " + module + "_ID, filename, folder, rating, categorie_ID, univers_ID, size FROM " + module + "s WHERE " + module + "_ID = " + ID
			data = bdd.execute_and_return(query)
			
		self.module = module
		self.ID = str(data[0])
		self.folder = data[2]
		self.file = data[1]
		self.filename = data[1]
		self.path = data[2] + '/' + data[1]
		self.rating = data[3]
		self.c_ID = data[4]
		self.u_ID = data[5]
		self.size = data[6]
		
		self.thumbnail_path = thumbnail_path
		self.flags = set()
	
	def setRating(self, new_rating):
		query = "UPDATE " + self.module + "s SET rating = " + str(new_rating) + " WHERE " + self.module + "_ID = " + self.ID
		bdd.execute(query)
		self.rating = new_rating
	
	def set_path(self, folder, file_name):
		query = "UPDATE " + self.module + "s SET folder = ?, filename = ? WHERE " + self.module + "_ID = " + self.ID
		t = (folder, file_name)
		bdd.execute(query, t)
		self.path = folder + '/' + file_name
		self.folder = folder
		self.file = file_name

class Track():
	def __init__(self, data):
		'''
			Data might contain a Track ID (from which we retrieve real data from db) or a tuple containing all data necessary
		'''
		if(type(data).__name__=='int'):
			ID = str(data)
			query = "SELECT track_ID, path, title, album, artist, length, playcount, rating FROM tracks WHERE track_ID = " + ID
			data = bdd.execute_and_return(query)
		
		self.ID = str(data[0])
		self.path = data[1]
		self.tags = {'title':data[2], 'album':data[3], 'artist':data[4], 'length':data[5]}
		self.title = data[2]
		self.album = data[3]
		self.artist = data[4]
		self.length = data[5]
		self.play_count = data[6]
		self.playcount = data[6]
		self.rating = data[7]
		self.time_started = int( time.mktime( datetime.utcnow().timetuple() ) )
		temp, self.format = os.path.splitext(self.path)
		
		self.flags = set()
		self.priority = 0
		self.bridgeSrc = None
		self.bridgeDest = None
	
	def change_rating(self, w, new_rating):
		query = "UPDATE tracks SET rating = " + str(new_rating) + " WHERE track_ID = " + self.ID
		bdd.execute(query)
		self.rating = new_rating
		messager.diffuser('track_data_changed', self, self)
	
	@staticmethod
	def fromPath(path):
		try:
			track = bdd.getTracks({'path':path})[0] # This file exists in our database
		except IndexError:
			tags = Tags.fromPath(path)
			track = Track([0, path, tags['title'], tags['album'], tags['artist'], tags['length'], 0, 0])
		return track
			
			
	
	def get_tags(self):
		return Tags.fromPath(self.path)
		
	def incrementPlayCount(self):
		self.playcount += 1
		query = "UPDATE tracks SET playcount = playcount + 1  WHERE track_ID = " + self.ID
		bdd.execute(query)
		
		def scrobble():
			time_elapsed = int( time.mktime( datetime.utcnow().timetuple())) - self.time_started
			if(time_elapsed > 120):
				try:
					BDD.network.scrobble(self.artist, self.title, int(self.time_started))
					if len(BDD.network_cache) > 0:
						for tup in BDD.network_cache:
							BDD.network.scrobble(tup[0], tup[1], tup[2])
						BDD.network_cache = []
						BDD.saveCache() # update cache
				except:
					BDD.network_cache.append((self.artist, self.title, int(self.time_started)))
					
		task = threading.Thread(target=scrobble)
		task.start()
		
	def set_tag(self, tag, value):
		Tags.setValue(self.path, tag, value)
		query = 'UPDATE tracks SET ' + tag + ' = ? WHERE track_ID = ?'
		t = (value, self.ID)
		bdd.execute(query, t)
		self.tags[tag] = value
		messager.diffuser('track_data_changed', self, self)
		

class QueuedTrack(Track):
	'''
		A Track with many flags. Currently not used (Actually these flags are packed in every track)
	'''
	def __init__(self, data, queue):
		Track.__init__(self, data)
		self.queue = queue
		self.flags = set()
		self.priority = 0
		self.bridgeSrc = None
		self.bridgeDest = None
		
		
class Container():
	"""
		Either a category or a universe
		Categories are "form container" whereas universes are "content container"
		container_type (universe, container)
		type = module (images, videos, etc...)
		TODO delete recursive
	"""
	def __init__(self, data, container_type, module):
		# First we make sure container_type is the right SQL word
		container_type = self.getTrueContainerType(container_type)
			
		if(type(data).__name__ == 'int'):
			ID = str(data)
			query = "SELECT * FROM " + container_type + "_" + module + "s WHERE " + container_type + "_ID = " + ID
			data = bdd.execute_and_return(query)
		
		self.ID = data[0]
		self.label = data[1]
		self.parent_ID = data[2]
		self.thumbnail_ID = data[3]
		
		try:
			self.rating = data[4]
		except IndexError:
			self.rating = -1
		self.module = module
		self.container_type = container_type
		
	def __str__(self):
		return self.label + ' (' + self.container_type + ')'
	
	
	def addElements(self, IDList):
		bdd.conn.execute('UPDATE ' + self.module + 's SET ' + self.container_type + '_ID = ' + str(self.ID) + ' WHERE ' + self.module + '_ID IN (%s)' % ("?," * len(IDList))[:-1], IDList)
		bdd.conn.commit()
		
	@staticmethod
	def create(container_type, module, name, parent_ID=0):
		container_type = Container.getTrueContainerType(container_type)
		t = (unicode(name), parent_ID,)
		query = "INSERT INTO " + container_type + "_" + module + "s (" + container_type + "_L, parent_ID) VALUES(?, ?);"
		#ex = INSERT INTO categorie_images (categorie_L) VALUES(?)
		bdd.c.execute(query, t)
		newID = bdd.execute_and_return("SELECT last_insert_rowid() FROM " + container_type + "_" + module + "s;")[0]
		bdd.conn.commit()
		return Container((newID, name, parent_ID, 0), container_type, module)
	
	def delete(self):
		bdd.execute('DELETE FROM ' + self.container_type + '_' + self.module + 's WHERE ' + self.container_type + '_ID = ?', (self.ID,))
		
	
	def getThumbnailPath(self, size='128'):
		if(self.thumbnail_ID != 0):
			thumbnail_path = xdg.get_thumbnail_dir(self.module + '/128/')
			path = thumbnail_path + str(self.thumbnail_ID) + '.jpg'
		else:
			path = None
		return path
	
	@staticmethod
	def getTrueContainerType(container_type):
		if(container_type == 'category' or container_type == 'c'):
			container_type = 'categorie'
		elif(container_type == 'universe' or container_type == 'u'):
			container_type = 'univers'
			
		return container_type
	
	def set_thumbnail_ID(self, element_ID):
		query = 'UPDATE ' + self.container_type + '_' + self.module + 's SET thumbnail_ID = ? WHERE ' + self.container_type + '_ID = ?'
		t = (element_ID, self.ID)
		bdd.execute(query, t)
		
		self.thumbnail_ID = element_ID
		logger.debug("Thumbnail")
		
bdd = BDD()