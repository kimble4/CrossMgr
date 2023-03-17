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


def DoCmnImport(	fname, parseTagTime, startTime = None,
					clearExistingData = True, StartWaveOffset = None ):
	
	errors = []

	race = Model.race
	if race and race.isRunning():
		Utils.MessageOK( Utils.getMainWin(), '\n\n'.join( [_('Cannot Import into a Running Race.'), _('Wait until you have a complete data set, then import the full data into a New race.')] ),
						title = _('Cannot Import into Running Race'), iconMask = wx.ICON_ERROR )
		return

	# If startTime is None, the first time will be taken as the start time.
	# All first time's for each rider will then be ignored.
	
	if StartWaveOffset is None:
		StartWaveOffset = datetime.timedelta(seconds=0.0)
	
	raceStart = None
	
	#with open(fname) as f, Model.LockRace() as race:
		#year, month, day = [int(n) for n in race.date.split('-')]
		#raceDate = datetime.date( year=year, month=month, day=day )
		#JChip.reset( raceDate )
		#if startTime:
			#raceStart = datetime.datetime.combine( raceDate, startTime )
			#race.resetStartClockOnFirstTag = False
		#else:
			#race.resetStartClockOnFirstTag = True
		
		#tagNums = GetTagNums( True )
		#race.missingTags = set()
		
		#tFirst, tLast = None, None
		#lineNo = 0
		#riderRaceTimes = {}
		#for line in f:
			#lineNo += 1
			
			#line = line.strip()
			#if not line or line[0] in '#;':
				#continue
			
			#tag, t = parseTagTime( line, lineNo, errors )
			#if tag is None:
				#continue
			#if raceStart and t < raceStart:
				#errors.append( '{} {}: {} ({})'.format(_('line'), lineNo, _('time is before race start'), t.strftime('%H:%M:%S.%f')) )
				#continue
			
			#tag = tag.lstrip('0').upper()
			#t += StartWaveOffset
			
			#if not tFirst:
				#tFirst = t
			#tLast = t
			#try:
				#num = tagNums[tag]
				#riderRaceTimes.setdefault( num, [] ).append( t )
			#except KeyError:
				#if tag not in race.missingTags:
					#errors.append( '{} {}: {}: {}'.format(_('line'), lineNo, _('tag missing from Excel sheet'), tag) )
					#race.missingTags.add( tag )
				#continue

		#------------------------------------------------------------------------------
		#Populate the race with the times.
		#if not riderRaceTimes:
			#errors.insert( 0, _('No matching tags found in Excel link.  Import aborted.') )
			#return errors
		
		#Put all the rider times into the race.
		#if clearExistingData:
			#race.clearAllRiderTimes()
			
		#if not raceStart:
			#raceStart = tFirst
			
		#race.startTime = raceStart
		
		#for num, lapTimes in riderRaceTimes.items():
			#for t in lapTimes:
				#raceTime = (t - raceStart).total_seconds()
				#if not race.hasTime(num, raceTime):
					#race.addTime( num, raceTime )
			
		#if tLast:
			#race.finishTime = tLast + datetime.timedelta( seconds = 0.0001 )
			
		#Figure out the race minutes from the recorded laps.
		#if riderRaceTimes:
			#lapNumMax = max( len(ts) for ts in riderRaceTimes.values() )
			#if lapNumMax > 0:
				#tElapsed = min( ts[-1] for ts in riderRaceTimes.values() if len(ts) == lapNumMax )
				#raceMinutes = int((tElapsed - raceStart).total_seconds() / 60.0) + 1
				#race.minutes = raceMinutes
		
	return errors

#------------------------------------------------------------------------------------------------
class CmnImportDialog( wx.Dialog ):
	def __init__( self, parent, id = wx.ID_ANY, fileSuffix = 'cmn' ):
		super().__init__(parent)
		self.fileSuffix = fileSuffix
		self.importRace = None
		todoList = [
			'{} {}'.format(_('CrossMgr'), _('Import Data File')),
			'',
			_('You must first "New" a race and fill in the details.'),
			_('You must also prepare your Sign-On Excel Sheet and link the sheet to the race.'),
			'',
			_('\'Adjust start waves\' will reflect their actual time,'),
			_('otherwise imported waves will start simultaneously with existing waves.'),
			'',
			_('Warning: Importing from another race could replace all the data in this race.'),
			_('Proceed with caution.'),
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
					print('Successfully loaded race')
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
		print(startWaveOffset)
		
		if startWaveOffset < 0:
			Utils.MessageOK( self, 'Start wave offset is negative.  Perfrom merge from the earlier race!', title = _('Offset is negative'), iconMask = wx.ICON_ERROR)
			return
		
		# Get the start time.
		if not clearExistingData:
			if not Model.race or not Model.race.startTime:
				Utils.MessageOK( self,
					'\n\n'.join( [_('Cannot Merge into Unstarted Race.'), _('Clear All Existing Data is allowed.')] ),
					title = _('Import Merge Failed'), iconMask = wx.ICON_ERROR
				)
				return
			startTime = Model.race.startTime.time()
		else:
			startTime = None
			
		undo.pushState()
		#errors = DoChipImport(	fname, self.parseTagTime, startTime,
								#clearExistingData,
								#datetime.timedelta(seconds = StartWaveOffset) )
		
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
		else:
			Utils.MessageOK( self, _('Import Successful'), _('Import Successful') )
		wx.CallAfter( Utils.refresh )
		self.EndModal( wx.ID_OK )
