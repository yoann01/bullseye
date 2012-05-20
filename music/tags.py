# -*- coding: utf-8 -*-
import os

from mutagen.easyid3 import EasyID3
from mutagen.oggvorbis import OggVorbis
from mutagen.mp3 import MP3


class Tags:
	@staticmethod
	def fromPath(path):
		format = os.path.splitext(path)[1]
		if(format == ".mp3"):
			try:
				audio = EasyID3(path)
			except:
				audio = None
		elif(format == ".ogg"):
			audio = OggVorbis(path)
			
		try:
			title = audio['title'][0]
		except:
			title = _("Unknown")
		
		try:
			#album = unicode(audio['TALB'])
			album = audio['album'][0]
		except:
			album = _("Unknown")
		try:
			#artist = unicode(audio['TPE1'])
			artist = audio['artist'][0]
		except:
			artist = _("Unknown")
			
		try:
			genre = audio['genre'][0]
		except:
			genre = _("Unknown")
			
		try:
			year = audio['date'][0][0:4]
		except:
			year = _("Unknown")
			
			
		try:
			performer = audio['performer'][0]
		except:
			performer = None
		
		if(format == ".mp3"):
			length = int(MP3(path).info.length)
		else:
			length =  int(audio.info.length)
			
		#print audio
			
		return {"title":title, "album":album, "artist":artist, "genre":genre, "year":year, "length":length, 'performer':performer}
	
	
	@staticmethod
	def setValue(path, tag, value):
		format = os.path.splitext(path)[1]
		if(format == ".mp3"):
			audio = EasyID3(path)
		elif(format == ".ogg"):
			audio = OggVorbis(path)
			
		audio[tag] = value
		audio.save()
		
		
	