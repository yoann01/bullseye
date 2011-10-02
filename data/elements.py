# -*- coding: utf-8 -*-
import sqlite3
import os
from mutagen.easyid3 import EasyID3
from mutagen.oggvorbis import OggVorbis
from datetime import datetime
import time
import logging
from common import messager
from data.bdd import BDD
logger = logging.getLogger(__name__)



			

class SpecialElement():
	def __init__(self, type, ID):
		self.type = type
		ID = str(ID)
		query = "SELECT " + type + "_ID, fichier, dossier, note, categorie_ID, univers_ID, size FROM " + type + "s WHERE " + type + "_ID = " + ID
		data = bdd.execute_and_return(query)
		self.ID = str(data[0])
		self.folder = data[2]
		self.file = data[1]
		self.path = data[2] + '/' + data[1]
		self.rating = data[3]
		self.c_ID = data[4]
		self.u_ID = data[5]
		self.size = data[6]
	
	def change_rating(self, w, new_rating):
		query = "UPDATE " + self.type + "s SET note = " + str(new_rating) + " WHERE " + self.type + "_ID = " + self.ID
		bdd.execute(query)
		self.rating = new_rating
	
	def set_path(self, folder, file_name):
		query = "UPDATE " + self.type + "s SET dossier = " + folder + ", fichier = " + file_name + " WHERE " + self.type + "_ID = " + self.ID
		bdd.execute(query)
		self.path = folder + '/' + file_name
		self.folder = folder
		self.file = file_name

class Track():
	def __init__(self, ID):
		ID = str(ID)
		query = "SELECT track_ID, path, title, album, artist, length, compteur, note FROM tracks WHERE track_ID = " + ID
		data = bdd.execute_and_return(query)
		self.ID = str(data[0])
		self.path = data[1]
		self.tags = {'title':data[2], 'album':data[3], 'artist':data[4], 'length':data[5]}
		self.title = data[2]
		self.album = data[3]
		self.artist = data[4]
		self.length = data[5]
		self.play_count = data[6]
		self.rating = data[7]
		self.time_started = int( time.mktime( datetime.utcnow().timetuple() ) )
		temp, self.format = os.path.splitext(self.path)
		
	
	def change_rating(self, w, new_rating):
		query = "UPDATE tracks SET note = " + str(new_rating) + " WHERE track_ID = " + self.ID
		bdd.execute(query)
		self.rating = new_rating
		messager.diffuser('track_data_changed', self, self)
	
	def get_tags(self):
		if(self.format == ".mp3"):
			audio = EasyID3(self.path)
		elif(self.format == ".ogg"):
			audio = OggVorbis(self.path)
		return audio
		
	def set_tag(self, tag, value):
		audio = self.get_tags()
		audio[tag] = value
		audio.save()
		query = 'UPDATE tracks SET ' + tag + ' = ? WHERE track_ID = ?'
		t = (value, self.ID)
		bdd.execute(query, t)
		self.tags[tag] = value
		messager.diffuser('track_data_changed', self, self)
		
		
class Container():
	"""
		Either a category or a universe
		TODO delete recursive
	"""
	def __init__(self, container_type, type, ID):
		ID = str(ID)
		query = "SELECT * FROM " + container_type + "_" + type + "s WHERE " + container_type + "_ID = " + ID
		data = bdd.execute_and_return(query)
		
		self.ID = data[0]
		self.label = data[1]
		self.parent_ID = data[2]
		self.thumbnail_ID = data[3]
		self.type = type
		self.container_type = container_type
	
	def delete(self):
		bdd.execute('DELETE FROM ' + self.container_type + '_' + self.type + 's WHERE ' + self.container_type + '_ID = ?', (self.ID,))
		
	def set_thumbnail_ID(self, element_ID):
		query = 'UPDATE ' + self.container_type + '_' + self.type + 's SET thumbnail_ID = ? WHERE ' + self.container_type + '_ID = ?'
		t = (element_ID, self.ID)
		bdd.execute(query, t)
		
		self.thumbnail_ID = element_ID
		logger.debug("Thumbnail")
		
bdd = BDD()