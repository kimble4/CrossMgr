import os
import sys
import operator
import functools
import GetModelInfo
import StringIO
import Utils

#----------------------------------------------------------------------
class memoize(object):
	"""Decorator that caches a function's return value each time it is called.
	If called later with the same arguments, the cached value is returned, and
	not re-evaluated.
	"""
   
	cache = {}
	
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
			value = self.func(*args)
			memoize.cache.setdefault(self.func.__name__, {})[args] = value
			return value
		except TypeError:
			# uncachable -- for instance, passing a list as an argument.
			# Better to not cache than to blow up entirely.
			return self.func(*args)
			
	def __repr__(self):
		"""Return the function's docstring."""
		return self.func.__doc__
		
	def __get__(self, obj, objtype):
		"""Support instance methods."""
		return functools.partial(self.__call__, obj)

def RaceNameFromPath( p ):
	raceName = os.path.basename( p )
	raceName = os.path.splitext( raceName )[0]
	while raceName.endswith('-'):
		raceName = raceName[:-1]
	raceName = raceName.replace( '-', ' ' )
	raceName = raceName.replace( ' ', '-', 2 )
	return raceName

class PointStructure( object ):

	participationPoints = 0
	dnfPoints = 0

	def __init__( self, name, pointsStr=None, participationPoints=0, dnfPoints=0 ):
		self.name = name
		if pointsStr is not None:
			self.setStr( pointsStr )
		else:
			self.setOCAOCup()
		self.participationPoints = participationPoints
		self.dnfPoints = dnfPoints
		
	def __getitem__( self, rank ):
		rank = int(rank)
		return self.dnfPoints if rank == 999999 else self.pointsForPlace.get( rank, self.participationPoints )
	
	def __len__( self ):
		return len(self.pointsForPlace)
	
	def setUCIWorldTour( self ):
		self.pointsForPlace = { 1:100, 2:80, 3:70, 4:60, 5:50, 6:40, 7:30, 8:20, 9:10, 10:4 }
		
	def setOCAOCup( self ):
		self.pointsForPlace = { 1:25, 2:20, 3:16, 4:13, 5:11, 6:10, 7:9, 8:8, 9:7, 10:6, 11:5, 12:4, 13:3, 14:2, 15:1 }
	
	def getStr( self ):
		return ', '.join( str(points) for points in sorted(self.pointsForPlace.values(), reverse=True) )
	
	def getHtml( self ):
		values = [(pos, points) for pos, points in self.pointsForPlace.iteritems()]
		values.sort()
		
		html = StringIO.StringIO()
		html.write( '<table class="points">\n' )
		html.write( '<tbody>\n' )
		
		pointsRange = []
		pointsForRange = []
		for i, (pos, points) in enumerate(values):
			if len(pointsRange) == i//10:
				lb, ub = i+1, min(i+10, len(values))
				if lb != ub:
					pointsRange.append( '{}-{}'.format(lb, ub) )
				else:
					pointsRange.append( '{}'.format(lb) )
					
				pointsForRange.append( [] )
			pointsForRange[-1].append( points )
			
		for i, (r, pfr) in enumerate(zip(pointsRange, pointsForRange)):
			html.write( '<tr{}>'.format(' class="odd"' if i & 1 else '') )
			html.write( '<td class="points-cell">{}:</td>'.format(r) )
			for p in pfr:
				html.write( '<td class="points-cell">{}</td>'.format(p) )
			html.write( '</tr>\n' )
			
		if self.participationPoints != 0:
			html.write( '<tr>' )
			html.write( '<td class="points-cell">Participation:</td>' )
			html.write( '<td class="points-cell">{}</td>'.format(self.participationPoints) )
			html.write( '</tr>\n' )
			
		if self.dnfPoints != 0:
			html.write( '<tr>' )
			html.write( '<td class="points-cell">DNF:</td>' )
			html.write( '<td class="points-cell">{}</td>'.format(self.dnfPoints) )
			html.write( '</tr>\n' )
			
		html.write( '</tbody>\n' )
		html.write( '</table>\n' )
		return html.getvalue()
	
	def setStr( self, s ):
		s = s.replace( ',', ' ' )
		values = []
		for v in s.split():
			try:
				values.append( int(v) )
			except:
				continue
		self.pointsForPlace = dict( (i+1, v) for i, v in enumerate(sorted(values, reverse=True)) )
		
	def __repr__( self ):
		return u'({}: {} + {}, dnf={})'.format( self.name, self.getStr(), self.participationPoints, self.dnfPoints )

class Race( object ):
	def __init__( self, fileName, pointStructure ):
		self.fileName = fileName
		self.pointStructure = pointStructure
		
	def getRaceName( self ):
		return RaceNameFromPath( self.fileName )
		
	def postReadFix( self ):
		if getattr( self, 'fname', None ):
			self.fileName = getattr(self, 'fname')
			delattr( self, 'fname' )
				
	def getFileName( self ):
		return self.fileName
		
	def __repr__( self ):
		return ', '.join( '{}={}'.format(a, repr(getattr(self, a))) for a in ['fileName', 'pointStructure'] )
		
class SeriesModel( object ):
	DefaultPointStructureName = 'Regular'
	useMostEventsCompleted = False
	scoreByTime = False
	scoreByPercent = False
	scoreByTrueSkill = False
	considerPrimePointsOrTimeBonus = True
	teamResultsMax = 4			# Maximum number of team member results to consider per race.
	licenseLinkTemplate = u''	# Used to create an html link from the rider's license number in the html output.
	bestResultsToConsider = 0	# 0 == all
	mustHaveCompleted = 0		# Number of events to complete to be eligible for results.
	organizer = u''
	upgradePaths = []
	upgradeFactors = []
	showLastToFirst = True		# If True, show the latest races first in the output.
	postPublishCmd = ''
	categorySequence = {}
	categorySequencePrevious = {}
	categoryHide = set()
	references = []
	referenceLicenses = []
	aliasLookup = {}
	aliasLicenseLookup = {}

	def __init__( self ):
		self.name = '<Series Name>'
		self.races = []
		self.pointStructures = [PointStructure(self.DefaultPointStructureName)]
		self.numPlacesTieBreaker = 5
		self.errors = []
		self.changed = False
		
	def postReadFix( self ):
		memoize.clear()
		for r in self.races:
			r.postReadFix()
	
	def setPoints( self, pointsList ):
		oldPointsList = [(p.name, p.name, p.getStr(), u'{}'.format(p.participationPoints), u'{}'.format(p.dnfPoints))
			for p in self.pointStructures]
		if oldPointsList == pointsList:
			return
			
		newPointStructures = []
		oldToNewName = {}
		newPS = {}
		for name, oldName, points, participationPoints, dnfPoints in pointsList:
			name = name.strip()
			oldName = oldName.strip()
			points = points.strip()
			if not name or name in newPS:
				continue
			participationPoints = int(participationPoints or '0')
			dnfPoints = int(dnfPoints or '0')
			ps = PointStructure( name, points, participationPoints, dnfPoints )
			oldToNewName[oldName] = name
			newPS[name] = ps
			newPointStructures.append( ps )
			
		if not newPointStructures:
			newPointStructures = [PointStructure(self.DefaultPointStructureName)]
			
		for r in self.races:
			r.pointStructure = newPS.get( oldToNewName.get(r.pointStructure.name, ''), newPointStructures[0] )
			
		self.pointStructures = newPointStructures
		self.setChanged()
	
	def setRaces( self, raceList ):
		oldRaceList = [(r.fileName, r.pointStructure.name) for r in self.races]
		if oldRaceList == raceList:
			return
		
		self.changed = True
		
		newRaces = []
		ps = dict( (p.name, p) for p in self.pointStructures )
		for fileName, pname in raceList:
			fileName = fileName.strip()
			pname = pname.strip()
			if not fileName:
				continue
			try:
				p = ps[pname]
			except KeyError:
				continue
			newRaces.append( Race(fileName, p) )
			
		self.races = newRaces
		memoize.clear()
		
	def setReferences( self, references ):
		dNew = dict( references )
		dExisting = dict( self.references )
		
		changed = (len(dNew) != len(dExisting))
		updated = False
		
		for name, aliases in dNew.iteritems():
			if name not in dExisting:
				changed = True
				if aliases:
					updated = True
			elif aliases != dExisting[name]:
				changed = True
				updated = True
	
		for name, aliases in dExisting.iteritems():
			if name not in dNew:
				changed = True
				if aliases:
					updated = True
				
		if changed:
			self.changed = changed
			self.references = references
			self.aliasLookup = {}
			for name, aliases in self.references:
				for alias in aliases:
					key = tuple( [Utils.removeDiacritic(n).lower() for n in alias] )
					self.aliasLookup[key] = name				
	
		#if updated:
		#	memoize.clear()
	
	def setReferenceLicenses( self, referenceLicenses ):
		dNew = dict( referenceLicenses )
		dExisting = dict( self.referenceLicenses )
		
		changed = (len(dNew) != len(dExisting))
		updated = False
		
		for name, aliases in dNew.iteritems():
			if name not in dExisting:
				changed = True
				if aliases:
					updated = True
			elif aliases != dExisting[name]:
				changed = True
				updated = True
	
		for name, aliases in dExisting.iteritems():
			if name not in dNew:
				changed = True
				if aliases:
					updated = True
				
		if changed:
			self.changed = changed
			self.referenceLicenses = referenceLicenses
			self.aliasLicenseLookup = {}
			for license, aliases in self.referenceLicenses:
				for alias in aliases:
					key = Utils.removeDiacritic(alias).upper()
					self.aliasLicenseLookup[key] = license				
	
		#if updated:
		#	memoize.clear()
	
	def getReferenceName( self, lastName, firstName ):
		key = (Utils.removeDiacritic(lastName).lower(), Utils.removeDiacritic(firstName).lower())
		try:
			return self.aliasLookup[key]
		except KeyError:
			self.aliasLookup[key] = (lastName, firstName)
			return lastName, firstName
	
	def getReferenceLicense( self, license ):
		key = Utils.removeDiacritic(license).upper()
		try:
			return self.aliasLicenseLookup[key]
		except KeyError:
			self.aliasLicenseLookup[key] = key
			return key
	
	def setCategorySequence( self, categoryList, categoryHide ):
		categorySequenceNew = { c:i for i, c in enumerate(categoryList) }
		if self.categorySequence != categorySequenceNew or self.categoryHide != categoryHide:
			self.categorySequence = categorySequenceNew
			self.categoryHide = categoryHide
			self.changed = True
	
	def harmonizeCategorySequence( self, raceResults ):
		categorySequenceSave = self.categorySequence
		
		categoriesFromRaces = set(rr.categoryName for rr in raceResults)
		if not categoriesFromRaces:
			if self.categorySequence:
				self.categorySequence = {}
				self.changed = True
			return
		
		categorySequence = (self.categorySequence or self.categorySequencePrevious)
		categoriesCur = set( categorySequence.iterkeys() )
		categoriesNew = categoriesFromRaces - categoriesCur
		categoriesDel = categoriesCur - categoriesFromRaces

		categoriesCur = sorted( categoriesCur, key=lambda c: categorySequence[c] )
		categoriesCur = [c for c in categoriesCur if c not in categoriesDel]
		categoriesCur.extend( sorted(categoriesNew) )
		
		self.categorySequence = { c:i for i, c in enumerate(categoriesCur) }
		self.categorySequencePrevious = self.categorySequence
		if categorySequenceSave != self.categorySequence:
			self.changed = True
			
		for c in list(self.categoryHide):
			if c not in self.categorySequence:
				self.categoryHide.remove( c )
				self.changed = True
			
	def getCategoryNamesSorted( self ):
		cs = self.categorySequence
		return sorted( (c for c in cs.iterkeys()), key=lambda c: cs[c] )
		
	def getCategoryNamesSortedPublish( self ):
		return [c for c in self.getCategoryNamesSorted() if c not in self.categoryHide]
	
	def setRootFolder( self, path ):
		if 'win' in sys.platform:
			fixFName = lambda fn: fn.replace( '/', '\\' )
		else:
			fixFName = lambda fn: fn.replace( '\\', '/' )
		
		raceFileNames = {os.path.basename(fixFName(r.fileName)):r for r in self.races }
		
		for top, directories, files in os.walk(path):
			for f in files:
				try:
					r = raceFileNames[f]
				except KeyError:
					continue
				r.fileName = os.path.join( top, f )
				self.setChanged()
	
	def setChanged( self, changed = True ):
		self.changed = changed
		if changed:
			memoize.clear()
	
	def addRace( self, name ):
		race = Race( name, self.pointStructures[0] )
		self.races.append( race )
		self.setChanged()
		
	def removeRace( self, name ):
		raceCount = len(self.races)
		self.races = [r for r in self.races if r.fileName != name]
		if raceCount != len(self.races):
			self.setChanged()
			
	def removeAllRaces( self ):
		if self.races:
			self.races = []
			self.setChanged()
	
	def clearCache( self ):
		memoize.clear()		
	
	@memoize
	def extractAllRaceResults( self ):
		raceResults = []
		oldErrors = self.errors
		self.errors = []
		for r in self.races:
			success, ex, results = GetModelInfo.ExtractRaceResults( r )
			if success:
				raceResults.extend( results )
			else:
				self.errors.append( (r, ex) )
				
		GetModelInfo.AdjustForUpgrades( raceResults )
		self.harmonizeCategorySequence( raceResults )
		
		if oldErrors != self.errors:
			self.changed = True
		return raceResults
			
model = SeriesModel()
