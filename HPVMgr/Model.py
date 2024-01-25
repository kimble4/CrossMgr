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
		self.eventCategoryTemplate = 'Race{:d}'
		if jsonDataFile:
			try:
				data = json.load(jsonDataFile)
				#print(data)
				self.copyTagsWithDelim = data['copyTagsWithDelim'] if 'copyTagsWithDelim' in data else False
				self.tagTemplate = data['tagTemplate'] if 'tagTemplate' in data else ''
				self.eventCategoryTemplate = data['eventCategoryTemplate'] if 'eventCategoryTemplate' in data else 'Race{:d}'
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
		if bib in self.riders:
			return self.riders[bib]
		else:
			return None
	
	@memoize
	def getRiderName( self, bib, firstNameFirst=False):
		name = ''
		if bib in self.riders:
			rider = self.riders[bib]
			if rider:
				if firstNameFirst:
					name = ' '.join( n for n in [rider['FirstName'], rider['LastName']] if n )
				else:
					name = ', '.join( n for n in [rider['LastName'], rider['FirstName']] if n )
		return name
		
	@memoize
	def getRiderFirstName( self, bib):
		if bib in self.riders:
			rider = self.riders[bib]
			return rider['FirstName']
		return ''
		
	@memoize
	def getRiderLastName( self, bib):
		if bib in self.riders:
			rider = self.riders[bib]
			return rider['LastName']
		return ''
		
	@memoize
	def getRiderAge( self, bib ):
		if bib in self.riders:
			rider = self.riders[bib]
			if 'DOB' in rider:
				dob = datetime.datetime.fromtimestamp(rider['DOB'])
				return int((datetime.datetime.now() - dob).days/365)
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
			
	def getRoundAsExcelSheetXLSX( self, rndName, formats, sheet, raceNr=None ):
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
		
		colnames = ['StartTime', 'Bib#', 'FirstName', 'LastName', 'Gender', 'Age', 'NatCode', 'License', 'Machine', 'Team', 'TeamCode',
					'Tag', 'Tag1', 'Tag2', 'Tag3', 'Tag4', 'Tag5', 'Tag6', 'Tag7', 'Tag8', 'Tag9',
					'EventCategory', 'CustomCategory', 'CustomCategory1', 'CustomCategory2', 'CustomCategory3',
					 'CustomCategory4', 'CustomCategory5', 'CustomCategory6', 'CustomCategory7',
					  'CustomCategory8', 'CustomCategory9' ]
		leftJustifyCols = ['FirstName', 'LastName', 'Gender', 'NatCode', 'Machine', 'Team', 'TeamCode',
						'EventCategory', 'CustomCategory', 'CustomCategory1', 'CustomCategory2', 'CustomCategory3',
						'CustomCategory4', 'CustomCategory5', 'CustomCategory6', 'CustomCategory7',
						'CustomCategory8', 'CustomCategory9' ]
		timeCols = ['StartTime']
				
		row = 0
		
		sheetFit = FitSheetWrapperXLSX( sheet )
		
		
		seasonName = self.getSeasonsList()[self.curSeason]
		season = self.seasons[seasonName]
		evtName = list(season['events'])[self.curEvt]
		evt = season['events'][evtName]
		rnd = evt['rounds'][rndName]
		evtRacersDict = {}
		if 'racers' in evt:
			for bibMachineCategoriesTeam in evt['racers']:
				evtRacersDict[bibMachineCategoriesTeam[0]] = (bibMachineCategoriesTeam[1], bibMachineCategoriesTeam[2] if len(bibMachineCategoriesTeam) >=3 else None, bibMachineCategoriesTeam[3] if len(bibMachineCategoriesTeam) >=4 else None)
		
		for col, c in enumerate(colnames):
			#write headers
			headerStyle = headerStyleAlignLeft if c in leftJustifyCols else headerStyleAlignRight
			style = styleTimeLP if c in timeCols else styleAlignLeft if c in leftJustifyCols else styleAlignRight
			sheetFit.write( row, col, c, headerStyle, bold=True )
			
		#now the data
		iRace = 0
		haveStartTime = True # always show the StartTime column
		haveGender = False
		haveAge = False
		haveNatCode = False
		haveLicense = False
		#haveFactor = False
		haveMachine = False
		haveTeam = False
		for race in rnd:
			if raceNr is None or raceNr == iRace + 1: # only the selected race
				eventCategory = self.eventCategoryTemplate.format(iRace+1) if len(rnd) > 1 else self.eventCategoryTemplate.format(iRace+1)[:-len(str(iRace+1))] # strip the race number if there's only a single race
				for bibMachineCategories in sorted(race):
					if bibMachineCategories[0] in evtRacersDict:
						rider = self.getRider(bibMachineCategories[0])
						if rider is None:  #skip deleted riders, even if they're in the race
							continue
						eventsMachineCategoriesTeam = evtRacersDict[bibMachineCategories[0]]
						row += 1
						col = 0
						#StartTime
						col += 1
						#bib
						sheetFit.write( row, col, bibMachineCategories[0],styleAlignRight )
						col += 1
						#first name
						sheetFit.write( row, col, rider['FirstName'] if 'FirstName' in rider else '', styleAlignLeft )
						col += 1
						#last name
						sheetFit.write( row, col, rider['LastName'] if 'LastName' in rider else '', styleAlignLeft )
						col += 1
						#gender
						if 'Gender' in rider:
							sheetFit.write( row, col, Genders[rider['Gender']], styleAlignLeft )
							haveGender = True
						col += 1
						#age
						if self.getRiderAge(bibMachineCategories[0]):
							sheetFit.write( row, col, self.getRiderAge(bibMachineCategories[0]), styleAlignRight )
							haveAge = True
						col += 1
						#natcode
						if 'NatCode' in rider:
							sheetFit.write( row, col, rider['NatCode'], styleAlignLeft )
							haveNatCode = True
						col += 1
						#license
						if 'License' in rider:
							sheetFit.write( row, col, rider['License'], styleAlignRight )
							haveLicense = True
						col += 1
						#factor
						# if 'Factor' in rider:
						# 	sheetFit.write( row, col, rider['Factor'], styleAlignRight )
						# 	haveFactor = True
						# col += 1
						#machine
						if bibMachineCategories[1] is None:
							# machine has not been changed from event default
							if eventsMachineCategoriesTeam[0]:
								sheetFit.write( row, col, eventsMachineCategoriesTeam[0], styleAlignLeft )
								haveMachine = True
						elif bibMachineCategories[1]:
							sheetFit.write( row, col, bibMachineCategories[1], styleAlignLeft )
							haveMachine = True
						col += 1
						#team
						if eventsMachineCategoriesTeam[2]:
							sheetFit.write( row, col, eventsMachineCategoriesTeam[2], styleAlignLeft )
							haveTeam = True
						col += 1
						#teamcode
						col += 1
						#tag
						sheetFit.write( row, col, rider['Tag'] if 'Tag' in rider else '', styleAlignRight )
						col += 1
						#tag1-9
						for i in range(1, 10):
							sheetFit.write( row, col, rider['Tag' + str(i)] if 'Tag' + str(i) in rider else '', styleAlignRight )
							col += 1
						#eventcategory
						sheetFit.write( row, col, eventCategory, styleAlignLeft )
						col += 1
						#customcategories
						if bibMachineCategories[2] is None:
							# categories have not been changed from event default
							for i in range(len(eventsMachineCategoriesTeam[1])):
								sheetFit.write( row, col, eventsMachineCategoriesTeam[1][i], styleAlignLeft )
								col += 1
						else:
							for i in range(len(bibMachineCategories[2])):
								sheetFit.write( row, col, bibMachineCategories[2][i], styleAlignLeft )
								col += 1
			iRace += 1
		sheet.set_column(colnames.index('StartTime'), colnames.index('StartTime'), None, None, {'hidden': 0 if haveStartTime else 1})
		sheet.set_column(colnames.index('Gender'), colnames.index('Gender'), None, None, {'hidden': 0 if haveGender else 1})
		sheet.set_column(colnames.index('Age'), colnames.index('Age'), None, None, {'hidden': 0 if haveAge else 1})
		sheet.set_column(colnames.index('NatCode'), colnames.index('NatCode'), None, None, {'hidden': 0 if haveNatCode else 1})
		sheet.set_column(colnames.index('License'), colnames.index('License'), None, None, {'hidden': 0 if haveLicense else 1})
		#sheet.set_column(colnames.index('Factor'), colnames.index('Factor'), None, None, {'hidden': 0 if haveFactor else 1})
		sheet.set_column(colnames.index('Machine'), colnames.index('Machine'), None, None, {'hidden': 0 if haveMachine else 1})
		sheet.set_column(colnames.index('Team'), colnames.index('Team'), None, None, {'hidden': 0 if haveTeam else 1})
		sheet.set_column(colnames.index('TeamCode'), colnames.index('TeamCode'), None, None, {'hidden': 1}) # always hide the TeamCode column
		sheet.set_column(colnames.index('Tag'), colnames.index('Tag9'), None, None, {'hidden': 1})  #always hide the tag columns
	
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
		db['eventCategoryTemplate'] = self.eventCategoryTemplate
		db['currentSeason'] = self.curSeason
		db['currentEvent'] = self.curEvt
		db['currentRound'] = self.curRnd
		db['riders'] = dict(sorted(self.riders.items()))
		db['seasons'] = dict(sorted(self.seasons.items()))
		return json.dumps(db, indent=2)

	def resetCache( self ):
		memoize.clear()
		

