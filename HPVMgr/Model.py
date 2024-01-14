import threading
import datetime
import json
from json.decoder import JSONDecodeError
import Utils
import wx
import sys

lock = threading.RLock()
#----------------------------------------------------------------------
class memoize:
	"""
	Decorator that caches a function's return value each time it is called.
	If called later with the same arguments, the cached value is returned, and
	not re-evaluated.
	
	Does NOT work with kwargs.
	"""
   
	cache = {}
	rlock = threading.RLock()
	
	@classmethod
	def clear( cls ):
		cls.cache = {}
   
	def __init__(self, func):
		# print( 'memoize:', func.__name__ )
		self.func = func
		
	def __call__(self, *args):
		# print( self.func.__name__, args )
		try:
			return memoize.cache[self.func.__name__][args]
		except KeyError:
			with self.rlock:
				value = self.func(*args)
				memoize.cache.setdefault(self.func.__name__, {})[args] = value
				return value
		except TypeError:
			with self.rlock:
				# uncachable -- for instance, passing a list as an argument.
				# Better to not cache than to blow up entirely.
				return self.func(*args)
		with self.rlock:
			return self.func(*args)
			
	def __repr__(self):
		"""Return the function's docstring."""
		return self.func.__doc__
		
	def __get__(self, obj, objtype):
		"""Support instance methods."""
		return functools.partial(self.__call__, obj)

#------------------------------------------------------------------------------
# define a global database
database = None

class LockDatabase:
	def __enter__(self):
		lock.acquire()
		return database
		
	def __exit__( self, type, value, traceback ):
		lock.release()
		return False

class Database:
	def __init__( self, fileName=None, jsonDataFile=None):
		self.fileName = fileName
		#self.riders = {1:{'FirstName':'Testy', 'LastName':'McTestFace', 'Gender':'Open', 'NatCode':'GBR', 'LastEntered':1705253444}, 2:{'FirstName':'Ian', 'LastName':'Cress', 'Gender':'Men', 'NatCode':'IRL', 'LastEntered':1705153444}, 3:{'FirstName':'Arnold', 'LastName':'Rimmer', 'Gender':'Women', 'NatCode':'GER', 'LastEntered':1705053444}, 4:{'FirstName':'Junior', 'LastName':'McTestFace', 'Gender':'Open', 'NatCode':'GBR', 'LastEntered':1705253445}}
		if jsonDataFile:
			try:
				data = json.load(jsonDataFile)
				#print(data)
				self.riders = data['riders']
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
				self.riders = {}
		else:
			self.riders = {}
		self.changed = False
		
	def getRiders( self ):
		return self.riders
	
	def setChanged( self ):
		self.changed = True
		
	def hasChanged( self ):
		return self.changed
	
	def getDatabaseAsJSON( self ):
		self.resetCache()
		db = {}
		db['riders'] = self.riders
		return json.dumps(db, indent=2)

	def resetCache( self ):
		memoize.clear()
		

