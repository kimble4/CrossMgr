import wx
import os
import math
import datetime
import wx.lib.intctrl
import pickle

import Model
import Utils
import JChip
from ReadSignOnSheet import GetTagNums
from Undo		import undo
from HighPrecisionTimeEdit import HighPrecisionTimeEdit
from ModuleUnpickler import ModuleUnpickler
from GetResults import GetEntriesForNum



def DoCmnImport( importRace = None,	clearExistingData = False, startWaveOffset = None ):
	errors = []

	race = Model.race
	if race and race.isRunning():
		Utils.MessageOK( Utils.getMainWin(), _('Cannot Import into a Running Race.'), title = _('Cannot Import into Running Race'), iconMask = wx.ICON_ERROR )
		return
	
	if importRace is None:
		errors.insert( 0, _('No race to import.  Import aborted.') )
		return errors
	
	if startWaveOffset is None:
		startWaveOffset = datetime.timedelta(seconds=0.0)
	
	raceStart = None
	minPossibleLapTimeChanged = False
	
	try:
		with Model.LockRace() as race:
			
			if clearExistingData:
				race.clearAllRiderTimes()
			
			updateWaveCategories = []
			numTimeInfo = importRace.numTimeInfo
			
			for bib in importRace.riders:
				rider = importRace.getRider( bib )
				#print(rider)
				if rider.status == Model.Rider.Finisher:
					if race.getRider( bib ).status == Model.Rider.Finisher:
						errors.append('Warning: #' + str(bib) + ' is a finisher in both races.')
					waveCategory = race.getCategory( bib )
					importCategory = importRace.getCategory( bib )
					if waveCategory:
						if importCategory:
							raceLaps = importCategory.numLaps if importCategory.numLaps else None
							bestLaps = importCategory.bestLaps if importCategory.bestLaps else None
							raceMinutes = importCategory.raceMinutes if importCategory.raceMinutes else None
							if raceMinutes is None and raceLaps is None: #if no minutes set for start wave, and we're not using laps, use the overall race minutes
								raceMinutes = importRace.minutes
							lappedRidersMustContinue = importCategory.lappedRidersMustContinue if importCategory.lappedRidersMustContinue else False
							distance = importCategory.distance if importCategory.distance else None
							firstLapDistance = importCategory.firstLapDistance if importCategory.firstLapDistance else None
							if (waveCategory, raceLaps, bestLaps, raceMinutes, lappedRidersMustContinue, distance, firstLapDistance) not in updateWaveCategories:
								updateWaveCategories.append( (waveCategory, raceLaps, bestLaps, raceMinutes, lappedRidersMustContinue, distance, firstLapDistance) )
						else:
							errors.append('#' + str(bib) + ' has no start wave in imported race!')
					else:
						errors.append('#' + str(bib) + ' has no start wave in this race!')
				startOffset = importRace.getStartOffset( bib )				# 0.0 if isTimeTrial			
				unfilteredTimes = [t for t in rider.times if t > startOffset]
				for time in unfilteredTimes:
					if not race.hasTime(bib, time + startWaveOffset):
						race.addTime( bib, time + startWaveOffset )
				existingRaceRider = race.getRider(bib)
				tStatus = rider.tStatus
				if tStatus:
					tStatus += startWaveOffset
				existingRaceRider.setStatus( rider.status, tStatus )
				existingRaceRider.relegatedPosition = rider.relegatedPosition
				existingRaceRider.autocorrectLaps = rider.autocorrectLaps
				existingRaceRider.alwaysFilterMinPossibleLapTime = rider.alwaysFilterMinPossibleLapTime
				tFirst = rider.firstTime
				if tFirst:
					tFirst += startWaveOffset
				existingRaceRider.firstTime = tFirst
				info = numTimeInfo.getNumInfo( bib )
				for t in info:
					race.numTimeInfo.addData( bib, t + startWaveOffset, info[t] )
				
			if race.startTime is None:
				race.startTime = importRace.startTime
			if race.finishTime is None or importRace.finishTime > race.finishTime:
				race.finishTime = importRace.finishTime
			if race.minPossibleLapTime is None or importRace.minPossibleLapTime < race.minPossibleLapTime:
				race.minPossibleLapTime = importRace.minPossibleLapTime
				minPossibleLapTimeChanged = True
			
			for category, laps, best, raceMinutes, lappedRidersMustContinue, distance, firstLapDistance in updateWaveCategories:
				t = category.getStartOffsetSecs() + startWaveOffset
				category.startOffset = Utils.SecondsToStr(t)
				category.numLaps = laps
				category._bestLaps = best
				category.raceMinutes = raceMinutes
				category.lappedRidersMustContinue = lappedRidersMustContinue
				category.distance = distance
				category.firstLapDistance = firstLapDistance
				#print ('Updated categories: ' + str(updateWaveCategories))
			
			lapNotes = getattr(importRace, 'lapNote', {} )
			race.lapNote = getattr( race, 'lapNote', {} )
			for bib, lap in lapNotes:
				print('Setting lapnote: ' + str(bib) + ', ' + str(lap) + ',  ' + lapNotes[(bib, lap)])
				race.lapNote[(bib, lap)] = lapNotes[(bib, lap)]
			race.adjustAllCategoryWaveNumbers()
			race.setChanged()
	except:
		errors.append(_('An unexpected error occurred.  Import aborted.') )
		
	Utils.refresh()
	Utils.refreshForecastHistory()
		
	return errors, minPossibleLapTimeChanged

#------------------------------------------------------------------------------------------------
class CmnImportDialog( wx.Dialog ):
	def __init__( self, parent, id = wx.ID_ANY, fileSuffix = 'cmn' ):
		super().__init__(parent)
		self.fileSuffix = fileSuffix
		self.importRace = None
		todoList = [
			'{} {}'.format(_('CrossMgr'), _('Import Data File')),
			'',
			_('You must first prepare a combined sign-on Excel sheet and link it to this race.'),
			'',
			_('\'Adjust start waves\' will reflect the real time that laps were ridden'),
			_('(preferred, requires different start waves for each race)'),
			_('otherwise imported times will be fudged to coincide with the existing race.'),
			_('(Beware of the Blinovitch Limitation Effect!)'),
			'',
			_('Warning: Importing times from another race could corrupt the lap data in this race.'),
			_('Make a backup and proceed with caution.'),
		]
		intro = '\n'.join(todoList)
		
		gs = wx.FlexGridSizer( rows=0, cols=3, vgap=10, hgap=5 )
		gs.Add( wx.StaticText(self, label = '{} {}:'.format(_('CrossMgr'), _('Data File'))), 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
		self.importDataFile = wx.TextCtrl( self, -1, '', size=(450,-1) )
		defaultPath = Utils.getFileName()
		if not defaultPath:
			defaultPath = Utils.getDocumentsDir()
		else:
			defaultPath = os.path.join( os.path.split(defaultPath)[0], '' )
		self.importDataFile.SetValue( defaultPath )
		gs.Add( self.importDataFile, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.GROW)

		btn = wx.Button( self, label=_('Browse') + '...' )
		btn.Bind( wx.EVT_BUTTON, self.onBrowseImportDataFile )
		gs.Add( btn, 0, wx.ALIGN_CENTER_VERTICAL )
		
		gs.AddSpacer(1)
		self.dataType = wx.StaticText( self, label = _("Data Is:") )
		gs.Add( self.dataType, 1, wx.ALIGN_LEFT )
		gs.AddSpacer(1)
		
		gs.Add( wx.StaticText(self, label = _('Race start time:')), 1, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
		self.raceStartTime = HighPrecisionTimeEdit( self, seconds=0, size=(140,-1) )
		self.raceStartTime.Enable( False )
		gs.Add( self.raceStartTime, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		gs.AddSpacer(1)

		gs.Add( wx.StaticText(self, label = _('Data Policy:') ), 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
		self.importPolicy = wx.Choice( self, choices = [
				_('Merge New Data with Existing'),
				_('Clear All Existing Data Before Import')
			] )
		self.importPolicy.SetSelection( 0 )
		gs.Add( self.importPolicy, 1, wx.ALIGN_LEFT )
		gs.AddSpacer(1)

		self.adjustStartWaves = wx.CheckBox(self, label = _('Adjust start waves:') )
		self.Bind( wx.EVT_CHECKBOX, self.onChangeAdjustStartWaves, self.adjustStartWaves )
		self.startWaveOffset = HighPrecisionTimeEdit( self, size=(140,-1) )
		self.startWaveOffset.SetSeconds( 0.0 )
		self.startWaveOffset.Disable()
		gs.Add( self.adjustStartWaves, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT )
		gs.Add( self.startWaveOffset, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT )
		gs.AddSpacer(1)
		
		with Model.LockRace() as race:
			isTimeTrial = getattr(race, 'isTimeTrial', False) if race else False

		if isTimeTrial:  #fixme do we need this?
			self.dataType.SetLabel( _('Data will be imported for a Time Trial') )
		else:
			self.dataType.SetLabel( _('Data will be imported for a Race') )
			
		bs = wx.BoxSizer( wx.VERTICAL )
		
		border = 4
		
		hs = wx.BoxSizer( wx.HORIZONTAL )
		
		try:
			image = wx.Image( os.path.join(Utils.getImageFolder(), 'CrossMgr.png'), wx.BITMAP_TYPE_PNG )
		except Exception as e:
			image = wx.EmptyImage( 32, 32, True )
		hs.Add( wx.StaticBitmap(self, wx.ID_ANY, image.ConvertToBitmap()), 0 )
		hs.Add( wx.StaticText(self, label = intro), 1, wx.EXPAND|wx.LEFT, border*2 )
		
		bs.Add( hs, 1, wx.EXPAND|wx.ALL, border )
		
		#-------------------------------------------------------------------
		bs.AddSpacer( border )
		
		bs.Add( gs, 0, wx.EXPAND | wx.ALL, border )
		
		btnSizer = self.CreateStdDialogButtonSizer( wx.OK|wx.CANCEL )
		self.Bind( wx.EVT_BUTTON, self.onOK, id=wx.ID_OK )
		if btnSizer:
			bs.Add( btnSizer, 0, wx.EXPAND | wx.ALL, border )
		
		self.SetSizerAndFit(bs)
		bs.Fit( self )
		
		self.CentreOnParent(wx.BOTH)
		wx.CallAfter( self.SetFocus )

	def onChangeAdjustStartWaves( self, event ):
		if event.IsChecked():
			if Model.race and self.importRace and Model.race.startTime:
				offset = self.importRace.startTime - Model.race.startTime
				if offset.total_seconds() < 0:
					Utils.MessageOK( self, 'Start wave offset is negative!\nPerfrom the merge from the earlier race.', title = _('Offset is negative'), iconMask = wx.ICON_ERROR)
					self.adjustStartWaves.SetValue(False)
					self.startWaveOffset.SetSeconds(0)
					
				else:
					self.startWaveOffset.Enable()
					self.startWaveOffset.SetSeconds(offset.total_seconds())
		else:
			self.startWaveOffset.Disable()
			self.startWaveOffset.SetSeconds(0)
		
	def onBrowseImportDataFile( self, event ):
		defaultPath = self.importDataFile.GetValue()
		if not defaultPath:
			defaultPath = Utils.getFileName()
			if defaultPath:
				defaultPath = os.path.split(defaultPath)[0]
			else:
				defaultPath = Utils.getDocumentsDir()
			defaultFile = ''
		else:
			defaultPath, defaultFile = os.path.split(defaultPath)
			
		with wx.FileDialog( self, '{} {}'.format( _('CrossMgr'), _('Import file') ),
							style=wx.FD_OPEN | wx.FD_CHANGE_DIR,
							wildcard='CrossMgr race (*.{})|*.{}'.format(self.fileSuffix, self.fileSuffix),
							defaultDir=defaultPath if defaultPath else '',
							defaultFile=defaultFile if defaultFile else '',
							) as dlg:
			if dlg.ShowModal() == wx.ID_OK:
				fname = dlg.GetPath()
				self.importDataFile.SetValue( fname )
				#try opening the file and determine race start time
				try:
					with open(fname, 'rb') as fp:
						try:
							importRace = pickle.load( fp, encoding='latin1', errors='replace' )
						except Exception:
							fp.seek( 0 )
							importRace = ModuleUnpickler( fp, module='CrossMgr', encoding='latin1', errors='replace' ).load()
				except IOError:
					Utils.MessageOK( self, '{}:\n\n"{}"'.format(_('Could not open data file for import'), fname),
											title = _('Cannot Open File'), iconMask = wx.ICON_ERROR)
					return
				if importRace:
					self.importRace = importRace
					#print('Successfully loaded race')
					seconds = importRace.startTime.hour * 3600 + importRace.startTime.minute * 60 + importRace.startTime.second + importRace.startTime.microsecond/1000000 
					self.raceStartTime.SetSeconds(seconds)
					if Model.race.startTime:
						offset = importRace.startTime - Model.race.startTime
						if offset.total_seconds() < 0:
							self.startWaveOffset.SetSeconds(0)
							self.startWaveOffset.Disable()
							self.adjustStartWaves.SetValue(False)
						else:
							self.startWaveOffset.SetSeconds(offset.total_seconds())
							self.startWaveOffset.Enable()
							self.adjustStartWaves.SetValue(True)
					else:
						self.startWaveOffset.SetSeconds(0)
						self.startWaveOffset.Disable()
						self.adjustStartWaves.SetValue(False)
	
	def onOK( self, event ):
		fname = self.importDataFile.GetValue()
		try:
			with open(fname) as f:
				pass
		except IOError:
			Utils.MessageOK( self, '{}:\n\n"{}"'.format(_('Could not open data file for import'), fname),
									title = _('Cannot Open File'), iconMask = wx.ICON_ERROR)
			return
			
		clearExistingData = (self.importPolicy.GetSelection() == 1)
		startWaveOffset = self.startWaveOffset.GetSeconds()
		
		if startWaveOffset < 0:
			Utils.MessageOK( self, 'Start wave offset is negative.  Perfrom merge from the earlier race!', title = _('Offset is negative'), iconMask = wx.ICON_ERROR)
			return
		
		#Get the start time.
		#if not clearExistingData:
			#if not Model.race or not Model.race.startTime:
				#Utils.MessageOK( self,
					#'\n\n'.join( [_('Cannot Merge into Unstarted Race.'), _('Clear All Existing Data is allowed.')] ),
					#title = _('Import Merge Failed'), iconMask = wx.ICON_ERROR
				#)
				#return
			#startTime = Model.race.startTime.time()
		#else:
			#startTime = None
			
		undo.pushState()
		errors, minPossibleLapTimeChanged = DoCmnImport( self.importRace, clearExistingData, startWaveOffset )
		
		if errors:
			# Copy the tags to the clipboard.
			clipboard = wx.Clipboard.Get()
			if not clipboard.IsOpened():
				clipboard.Open()
				clipboard.SetData( wx.TextDataObject('\n'.join(errors)) )
				clipboard.Close()
			
			if len(errors) > 10:
				errors = errors[:10]
				errors.append( '...' )
			tagStr = '\n'.join(errors)
			Utils.MessageOK( self,
							'{}:\n\n{}\n\n{}.'.format(_('Import File contains errors'), tagStr, _('All errors have been copied to the clipboard')),
							_('Import Warning'),
							iconMask = wx.ICON_WARNING )
		elif minPossibleLapTimeChanged:
			Utils.MessageOK( self, _('Caution: Minimum possible lap time has changed.'), _('Import Successful') )
		else:
			Utils.MessageOK( self, _('Import Successful'), _('Import Successful') )
		wx.CallAfter( Utils.refresh )
		self.EndModal( wx.ID_OK )
