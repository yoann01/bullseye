import threading
from functools import wraps


def threaded(f):
	"""
		A decorator that will make any function run in a new thread
	"""
	@wraps(f)
	def wrapper(*args, **kwargs):
		t = threading.Thread(target=f, args=args, kwargs=kwargs)
		#t = multiprocessing.Process(target = func, args = args, kwargs = kwargs)
		t.setDaemon(True)
		t.start()
		
	return wrapper