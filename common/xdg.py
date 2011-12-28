import os, glib

config_home = glib.get_user_config_dir()
config_home = os.path.join(config_home, "bullseye")

data_home = glib.get_user_data_dir()
data_home = os.path.join(data_home, "bullseye")

data_thumbnails = os.path.join(data_home, 'thumbnails')

data_dir = '/home/piccolo/workspace/python/'

def get_data_dir():
	return data_dir
	
def get_data_home():
	return data_home
	
def get_config_dir():
	return config_home
	
def get_thumbnail_dir(subdir):
	dir = os.path.join(data_thumbnails, subdir)
	return dir
	
	
def make_missing_dirs():
	"""
		Called in MainBDD. Not elsewhere.
	"""
	dirs = (config_home, data_home, get_thumbnail_dir('artist/medium'), get_thumbnail_dir('album/medium'), get_thumbnail_dir('title/medium'), get_thumbnail_dir('image/128'))
	for dir in dirs:
		if not os.path.exists(dir):
			os.makedirs(dir)