import threading
import datetime
import json
from json.decoder import JSONDecodeError
import Utils
import wx
import sys
import functools
from FitSheetWrapper import FitSheetWrapper, FitSheetWrapperXLSX

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

Genders = ['Open', 'Men', 'Women']  #order for sort
Open = 0
Men = 1
Women = 2

def keys2int(x):
    if isinstance(x, dict):
        return {int(k):v for k,v in x.items()}
    return x

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
		self.copyTagsWithDelim = False
		self.curSeason = None
		self.curEvt = None
		self.curRnd = None
		self.riders = {}
		self.seasons = {}
		self.tagTemplate = ''
		#self.riders = {1:{'FirstName':'Testy', 'LastName':'McTestFace', 'Gender':'Open', 'NatCode':'GBR', 'LastEntered':1705253444}, 2:{'FirstName':'Ian', 'LastName':'Cress', 'Gender':'Men', 'NatCode':'IRL', 'LastEntered':1705153444}, 3:{'FirstName':'Arnold', 'LastName':'Rimmer', 'Gender':'Women', 'NatCode':'GER', 'LastEntered':1705053444}, 4:{'FirstName':'Junior', 'LastName':'McTestFace', 'Gender':'Open', 'NatCode':'GBR', 'LastEntered':1705253445}}
		if jsonDataFile:
			try:
				data = json.load(jsonDataFile)
				#print(data)
				self.copyTagsWithDelim = data['copyTagsWithDelim'] if 'copyTagsWithDelim' in data else False
				self.tagTemplate = data['tagTemplate'] if 'tagTemplate' in data else ''
				self.riders = keys2int(data['riders']) if 'riders' in data else {}
				#print(self.riders)
				self.seasons = data['seasons'] if 'seasons' in data else {}
				self.curSeason = data['currentSeason'] if 'currentSeason' in data else None
				self.curEvt = data['currentEvent'] if 'currentEvent' in data else None
				self.curRnd = data['currentRound'] if 'currentRound' in data else None
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
		self.changed = False
		memoize.clear()
	
	@memoize
	def isRider( self, bib ):
		if bib in self.riders:
			return True
		else:
			return False
	
	@memoize
	def getBibs( self ):
		bibs = list(self.riders.keys())
		return sorted(bibs)
	
	def getRiders( self ):
		return self.riders
	
	def getRider( self, bib ):
		return self.riders[bib]
	
	@memoize
	def getRiderName( self, bib, firstNameFirst=False):
		rider = self.riders[bib]
		name = ''
		if rider:
			if firstNameFirst:
				name = ' '.join( n for n in [rider['FirstName'], rider['LastName']] if n )
			else:
				name = ', '.join( n for n in [rider['LastName'], rider['FirstName']] if n )
		return name
		
	@memoize
	def getRiderAge( self, bib ):
		rider = self.riders[bib]
		if 'DOB' in rider:
			dob = datetime.datetime.fromtimestamp(rider['DOB'])
			return int((datetime.datetime.now() - dob).days/365)
		else:
			return None
	
	def addRider( self, bib ):
		if bib in self.riders:
			Utils.writeLog( 'Tried to add existing rider!' )
			return
		self.riders[bib] = {'LastName':'Rider', 'FirstName':'New', 'Gender':Open, 'LastEntered':0}
		for i in range(10):
			self.riders[bib]['Tag' + (str(i) if i > 0 else '')] = self.tagTemplate.format(i,bib)
		self.setChanged()
		
	def deleteRider( self, bib ):
		if not bib in self.riders:
			Utils.writeLog( 'Tried to delete non-existent rider!' )
			return
		del self.riders[bib]
		self.setChanged()
	
	@memoize
	def getSeasonsList( self ):
		seasons = list(self.seasons.keys())
		return sorted(seasons)
		
	@memoize
	def getEventsList( self, season ):
		try:
			events = list(self.seasons[season].keys())
			return sorted(events)
		except KeyError:
			return []
			
	@memoize
	def getRoundsList( self, season, evt ):
		try:
			rnds = list(self.seasons[season][evt]['rounds'].keys())
			return sorted(rnds)
		except KeyError:
			return []
			
	@memoize
	def getRaces( self, season, evt, rnd ):
		try:
			races = self.seasons[season][evt]['rounds'][rnd]
			return races
		except KeyError:
			return []
			
	def getRoundAsExcelSheetXLSX( self, rndName, formats, sheet ):
		print('getRoundAsExcelSheetXLSX')
		''' Write a round to an xlwt excel sheet. '''
		titleStyle				= formats['titleStyle']
		headerStyleAlignLeft	= formats['headerStyleAlignLeft']
		headerStyleAlignRight	= formats['headerStyleAlignRight']
		styleAlignLeft			= formats['styleAlignLeft']
		styleAlignRight			= formats['styleAlignRight']
		
		styleTime				= formats['styleTime']
		styleMMSS				= formats['styleMMSS']
		styleSS					= formats['styleSS']
		
		styleTimeLP				= formats['styleTimeLP']
		styleMMSSLP				= formats['styleMMSSLP']
		styleSSLP				= formats['styleSSLP']
		
		colnames = ['StartTime', 'Bib#', 'FirstName', 'LastName', 'Gender', 'Age', 'NatCode', 'Machine', 'Team',
					'Tag', 'Tag1', 'Tag2', 'Tag3', 'Tag4', 'Tag5', 'Tag6', 'Tag7', 'Tag8', 'Tag9',
					'EventCategory', 'CustomCategory1', 'CustomCategory2', 'CustomCategory3',
					 'CustomCategory4', 'CustomCategory5', 'CustomCategory6', 'CustomCategory7',
					  'CustomCategory8', 'CustomCategory9' ]
		leftJustifyCols = ['FirstName', 'LastName', 'Gender', 'NatCode', 'Machine', 'Team',
						'EventCategory', 'CustomCategory1', 'CustomCategory2', 'CustomCategory3',
						'CustomCategory4', 'CustomCategory5', 'CustomCategory6', 'CustomCategory7',
						'CustomCategory8', 'CustomCategory9' ]
		timeCols = ['StartTime']
				
		rowTop = 0
		
		sheetFit = FitSheetWrapperXLSX( sheet )
		
		# Write the colnames and data.
		rowMax = 0
		for col, c in enumerate(colnames):
			headerStyle = headerStyleAlignLeft if c in leftJustifyCols else headerStyleAlignRight
			style = styleTimeLP if c in timeCols else styleAlignLeft if c in leftJustifyCols else styleAlignRight
			sheetFit.write( rowTop, col, c, headerStyle, bold=True )
			
			
# 			for row, v in enumerate(self.data[col]):
# 				if isSpeed and v:
# 					v = ('{}'.format(v).split() or [''])[0]
# 					if v == '"':
# 						v += '    '
# 				elif col in self.timeCols:
# 					if v:
# 						try:
# 							v = Utils.StrToSeconds(v) / (24.0*60.0*60.0)	# Convert seconds to fraction of a day for Excel.
# 						except Exception:
# 							pass
# 				
# 				rowCur = rowTop + 1 + row
# 				if rowCur > rowMax:
# 					rowMax = rowCur
# 				sheetFit.write( rowCur, col, v, style )
# 			
# 			if isSpeed:
# 				self.colnames[col] = _('Speed')
	
	def setChanged( self, changed=True ):
		self.changed = changed
		self.resetCache()
		
	def hasChanged( self ):
		return self.changed
	
	def getDatabaseAsJSON( self ):
		self.resetCache()
		db = {}
		db['copyTagsWithDelim'] = self.copyTagsWithDelim
		db['tagTemplate'] = self.tagTemplate
		db['currentSeason'] = self.curSeason
		db['currentEvent'] = self.curEvt
		db['currentRound'] = self.curRnd
		db['riders'] = dict(sorted(self.riders.items()))
		db['seasons'] = dict(sorted(self.seasons.items()))
		return json.dumps(db, indent=2)

	def resetCache( self ):
		memoize.clear()
		

