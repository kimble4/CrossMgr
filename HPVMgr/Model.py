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
		self.writeAbbreviatedTeams = False
		self.useFactors = False
		self.allocateBibsFrom = 1
		self.ttStartDelay = 60
		self.ttInterval = 30
		self.curSeason = None
		self.curEvt = None
		self.curRnd = None
		self.riders = {}
		self.teams = []
		self.seasons = {}
		self.tagTemplates = {}
		self.eventCategoryTemplate = 'Race{:d}'
		if jsonDataFile:
			try:
				data = json.load(jsonDataFile)
				#print(data)
				self.copyTagsWithDelim = data['copyTagsWithDelim'] if 'copyTagsWithDelim' in data else False
				self.writeAbbreviatedTeams = data['writeAbbreviatedTeams'] if 'writeAbbreviatedTeams' in data else False
				self.useFactors = data['useFactors'] if 'useFactors' in data else False
				self.allocateBibsFrom = data['allocateBibsFrom'] if 'allocateBibsFrom' in data else 1
				self.ttStartDelay = data['ttStartDelay'] if 'ttStartDelay' in data else 60
				self.ttInterval = data['ttInterval'] if 'ttInterval' in data else 30
				self.tagTemplates = keys2int(data['tagTemplates']) if 'tagTemplates' in data else {}
				self.eventCategoryTemplate = data['eventCategoryTemplate'] if 'eventCategoryTemplate' in data else 'Race{:d}'
				self.riders = keys2int(data['riders']) if 'riders' in data else {}
				self.teams = data['teams'] if 'teams' in data else []
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
	
	def getNextUnusedBib( self, startBib=None ):
		bibs = self.getBibs()
		if startBib is not None:
			bib = startBib
		else:
			bib = self.allocateBibsFrom
		print(bib)
		while bib in bibs:
			bib += 1
		return bib
	
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
	def getRiderAge( self, bib, atDate=datetime.datetime.now() ):
		if bib in self.riders:
			rider = self.riders[bib]
			if 'DOB' in rider:
				dob = datetime.datetime.fromtimestamp(rider['DOB'])
				return int((atDate - dob).days/365.2425)
		return None
		
	def getRiderFactor( self, bib):
		if bib in self.riders:
			rider = self.riders[bib]
			if 'Factor' in rider:
				return rider['Factor']
		return None
	
	def addRider( self, bib, firstName=None, lastName=None, gender=Open ):
		if bib in self.riders:
			Utils.writeLog( 'Tried to add existing rider!' )
			return
		self.riders[bib] = {'LastName':lastName if lastName is not None else '' if firstName is not None else 'Rider', 'FirstName':firstName if firstName is not None else 'New', 'Gender':gender, 'LastEntered':0}
		tagsNoInit = []
		for i in range(10):
			try:
				self.riders[bib]['Tag' + (str(i) if i > 0 else '')] = self.tagTemplates[i].format(bib)
			except KeyError:
				tagsNoInit.append(i)
		if len(tagsNoInit) > 0:
			Utils.writeLog('Not initialising ' + ', '.join(['Tag' + str(tag) for tag in tagsNoInit]) + ' for rider #' + str(bib) + ': no Tag Template defined.')
		self.setChanged()
		
	def deleteRider( self, bib ):
		if not bib in self.riders:
			Utils.writeLog( 'Tried to delete non-existent rider!' )
			return
		del self.riders[bib]
		self.setChanged()
	
	@memoize
	def getAbbreviatedCategory( self, categoryName ):
		if self.curSeason is not None:
			seasonName = self.getSeasonsList()[self.curSeason]
			season = self.seasons[seasonName]
			catCount = 0
			if 'categories' in season:
				for categoryAbbrev in season['categories']:
					if categoryName.lower() == categoryAbbrev[0].lower():
						return categoryAbbrev[1]
		return ''
	
	@memoize
	def getAbbreviatedTeam( self, teamName ):
		if self.teams is not None:
			for teamAbbrevEntered in self.teams:
				if teamAbbrevEntered[0].lower() == teamName.lower():
					return teamAbbrevEntered[1] if len(teamAbbrevEntered[1]) > 0 else teamName
		return teamName
	
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
			
	def getCurEvtDate( self ):
		if self.curSeason is not None:
			seasonName = self.getSeasonsList()[self.curSeason]
			season = self.seasons[seasonName]
			if self.curEvt is not None:
				evtName = list(season['events'])[self.curEvt]
				evt = season['events'][evtName]
				if 'date' in evt:
					try:
						dt = datetime.datetime.fromtimestamp(evt['date'])
						return dt
					except Exception:
						return None
		return None
		
	def getRoundAsExcelSheetXLSX( self, rndName, formats, sheet, raceNr=None ):
		try:
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
			
			colnames = ['StartTime', 'Bib#', 'FirstName', 'LastName', 'Gender', 'Age', 'NatCode', 'License', 'Factor', 'Machine', 'Team', 'TeamCode',
						'EventCategory', 'CustomCategory', 'CustomCategory1', 'CustomCategory2', 'CustomCategory3',
						'CustomCategory4', 'CustomCategory5', 'CustomCategory6', 'CustomCategory7',
						'CustomCategory8', 'CustomCategory9',
						'Tag', 'Tag1', 'Tag2', 'Tag3', 'Tag4', 'Tag5', 'Tag6', 'Tag7', 'Tag8', 'Tag9']
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
			else:
				Utils.writeLog('WriteSignonSheet: Event ' + evtName + ' has no racers!')
				return
				
			if 'races' not in rnd:
				Utils.writeLog('WriteSignonSheet: Event ' + evtName + ' round ' + rndName + ' has no races!')
				return
				
			#first pass to determine which columns we need
			haveStartTime = False
			haveGender = False
			haveAge = False
			haveNatCode = False
			haveLicense = False
			haveFactor = False
			haveMachine = False
			haveTeam = False
			iRace = 0
			for race in rnd['races']:
				if raceNr is None or raceNr == iRace + 1: # only the selected race
					for raceEntryDict in race:
						if raceEntryDict['bib'] in evtRacersDict:
							rider = self.getRider(raceEntryDict['bib'])
							if rider is None:  #skip deleted riders, even if they're in the race
								continue
							eventsMachineCategoriesTeam = evtRacersDict[raceEntryDict['bib']]
							if 'startTime' in raceEntryDict:
								if raceEntryDict['startTime']:
									haveStartTime = True
							if 'Gender' in rider:
								haveGender = True
							if self.getRiderAge(raceEntryDict['bib']) is not None:
								haveAge = True
							if 'NatCode' in rider:
								if len(rider['NatCode']) > 0:
									haveNatCode = True
							if 'License' in rider:
								if len(rider['License']) > 0:
									haveLicense = True
							if 'Factor' in rider:
								if rider['Factor'] >0:
									haveFactor = True
							if 'machine' not in raceEntryDict or raceEntryDict['machine'] is None:
								# machine has not been changed from event default
								if eventsMachineCategoriesTeam[0]:
									haveMachine = True
							elif raceEntryDict['machine']:
								haveMachine = True	
							if eventsMachineCategoriesTeam[2]:
								haveTeam = True
				iRace += 1
			
			#override presence of factors if disabled in settings
			if not self.useFactors:
				haveFactor = False
			
			#write the headers, without unused colnames
			if not haveStartTime:
				colnames.remove('StartTime')
			if not haveGender:
				colnames.remove('Gender')
			if not haveAge:
				colnames.remove('Age')
			if not haveNatCode:
				colnames.remove('NatCode')
			if not haveLicense:
				colnames.remove('License')
			if not haveFactor:
				colnames.remove('Factor')
			if not haveMachine:
				colnames.remove('Machine')
			if not haveTeam:
				colnames.remove('Team')
				colnames.remove('TeamCode')
			for col, c in enumerate(colnames):
				headerStyle = headerStyleAlignLeft if c in leftJustifyCols else headerStyleAlignRight
				sheetFit.write( row, col, c, headerStyle, bold=True )
				
			#second pass to write the data  #fixme changed race allocation data structure
			iRace = 0
			for race in rnd['races']:
				if raceNr is None or raceNr == iRace + 1: # only the selected race
					eventCategory = self.eventCategoryTemplate.format(iRace+1) if len(rnd['races']) > 1 else self.eventCategoryTemplate.format(iRace+1)[:-len(str(iRace+1))] # strip the race number if there's only a single race
					for raceEntryDict in sorted(race, key=lambda raceEntryDict: raceEntryDict['bib']):
						if raceEntryDict['bib'] in evtRacersDict:
							rider = self.getRider(raceEntryDict['bib'])
							if rider is None:  #skip deleted riders, even if they're in the race
								continue
							eventsMachineCategoriesTeam = evtRacersDict[raceEntryDict['bib']]
							row += 1
							col = 0
							#StartTime
							if haveStartTime:
								# just create an empty column so TT start times can be added in the spreadsheet
								sheetFit.write( row, col, Utils.formatTime(raceEntryDict['startTime']),styleAlignRight )
								col += 1
							#bib
							sheetFit.write( row, col, raceEntryDict['bib'],styleAlignRight )
							col += 1
							#first name
							sheetFit.write( row, col, rider['FirstName'] if 'FirstName' in rider else '', styleAlignLeft )
							col += 1
							#last name
							sheetFit.write( row, col, rider['LastName'] if 'LastName' in rider else '', styleAlignLeft )
							col += 1
							#gender
							if haveGender:
								if 'Gender' in rider:
									sheetFit.write( row, col, Genders[rider['Gender']], styleAlignLeft )
								col += 1
							#age
							if haveAge:
								if self.getRiderAge(raceEntryDict['bib']) is not None:
									sheetFit.write( row, col, self.getRiderAge(raceEntryDict['bib'], datetime.datetime.fromtimestamp(evt['date']) if 'date' in evt else datetime.datetime.now()), styleAlignRight )
								col += 1
							#natcode
							if haveNatCode:
								if 'NatCode' in rider:
									if len(rider['NatCode']) > 0:
										sheetFit.write( row, col, rider['NatCode'], styleAlignLeft )
								col += 1
							#license
							if haveLicense:
								if 'License' in rider:
									if len(rider['License']) > 0:
										sheetFit.write( row, col, rider['License'], styleAlignRight )
								col += 1
							#factor
							if haveFactor:
								if 'Factor' in rider:
									if rider['Factor'] > 0:
										sheetFit.write( row, col, rider['Factor'], styleAlignRight )
								col += 1
							#machine
							if haveMachine:
								if 'machine' not in raceEntryDict or raceEntryDict['machine'] is None: # machine has not been changed from event default
									if eventsMachineCategoriesTeam[0]:
										sheetFit.write( row, col, eventsMachineCategoriesTeam[0], styleAlignLeft )
								elif raceEntryDict['machine']: # machine has been edited for this race
									sheetFit.write( row, col, raceEntryDict['machine'], styleAlignLeft )
								col += 1
							#team
							if haveTeam:
								if eventsMachineCategoriesTeam[2]:
									if self.writeAbbreviatedTeams:
										sheetFit.write( row, col, self.getAbbreviatedTeam(eventsMachineCategoriesTeam[2]), styleAlignLeft )
									else:
										sheetFit.write( row, col, eventsMachineCategoriesTeam[2], styleAlignLeft )
								col += 1
								#teamcode
								#sheetFit.write( row, col, self.getAbbreviatedTeam(eventsMachineCategoriesTeam[2]), styleAlignLeft )
								col += 1
							#eventcategory
							sheetFit.write( row, col, eventCategory, styleAlignLeft )
							col += 1
							#customcategories
							if 'categories' not in raceEntryDict or raceEntryDict['categories'] is None: # categories have not been changed from event default
								for i in range(len(eventsMachineCategoriesTeam[1])):
									sheetFit.write( row, col, eventsMachineCategoriesTeam[1][i], styleAlignLeft )
									col += 1
								for i in range(10 - len(eventsMachineCategoriesTeam[1])): # add empty columns for unused CustomCategories
									col += 1
							else: # categories have been edited for this race
								for i in range(len(raceEntryDict['categories'])):
									sheetFit.write( row, col, raceEntryDict['categories'][i], styleAlignLeft )
									col += 1
								for i in range(10 - len(raceEntryDict['categories'])): # add empty columns for unused CustomCategories
									col += 1
							#tag
							if 'tag' not in raceEntryDict or raceEntryDict['tag'] is None: # tag has not been changed from event default
								sheetFit.write( row, col, rider['Tag'] if 'Tag' in rider else '', styleAlignRight )
							elif raceEntryDict['tag']: # tag has been edited
								sheetFit.write( row, col, raceEntryDict['tag'], styleAlignRight )
							col += 1
							#tag1-9
							for i in range(1, 10):
								if 'tag' + str(i) not in raceEntryDict or raceEntryDict['tag' + str(i)] is None: # tag has not been changed from event default
									sheetFit.write( row, col, rider['Tag' + str(i)] if 'Tag' + str(i) in rider else '', styleAlignRight )
								elif raceEntryDict['tag' + str(i)]: #tag has been edited
									sheetFit.write( row, col, raceEntryDict['tag' + str(i)], styleAlignRight )
								col += 1
				iRace += 1
			# if haveTeam:
			# 	sheet.set_column(colnames.index('TeamCode'), colnames.index('TeamCode'), None, None, {'hidden': 1}) # always hide the TeamCode column
			#sheet.set_column(colnames.index('Tag'), colnames.index('Tag9'), None, None, {'hidden': 1})  #always hide the tag columns
		except Exception as e:
				Utils.logException( e, sys.exc_info() )
	
	def setChanged( self, changed=True ):
		self.changed = changed
		self.resetCache()
		Utils.getMainWin().events.refreshCurrentSelection()
		
	def hasChanged( self ):
		return self.changed
	
	def getDatabaseAsJSON( self ):
		self.resetCache()
		db = {}
		db['copyTagsWithDelim'] = self.copyTagsWithDelim
		db['writeAbbreviatedTeams'] = self.writeAbbreviatedTeams
		db['useFactors'] = self.useFactors
		db['allocateBibsFrom'] = self.allocateBibsFrom
		db['ttStartDelay'] = self.ttStartDelay
		db['ttInterval'] = self.ttInterval
		db['tagTemplates'] = self.tagTemplates
		db['eventCategoryTemplate'] = self.eventCategoryTemplate
		db['currentSeason'] = self.curSeason
		db['currentEvent'] = self.curEvt
		db['currentRound'] = self.curRnd
		db['riders'] = dict(sorted(self.riders.items()))
		db['teams'] = sorted(self.teams)
		db['seasons'] = dict(sorted(self.seasons.items()))
		return json.dumps(db, indent=4)

	def resetCache( self ):
		memoize.clear()
		

