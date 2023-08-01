import wx
import os
import sys
import copy
import bisect
import datetime
import wx.lib.intctrl
import wx.lib.buttons
import wx.lib.agw.flatnotebook as flatnotebook
import wx.grid

from collections import defaultdict
from NonBusyCall import NonBusyCall

import Utils
#from GetResults import GetResults, GetLastFinisherTime, GetLeaderFinishTime, GetLastRider, RiderResult, IsRiderOnCourse
import Model



SplitterMinPos = 390
SplitterMaxPos = 530

class BibEntry( wx.Panel ):
	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		self.SetBackgroundColour( wx.WHITE )
		
		fontPixels = 36
		font = wx.Font((0,fontPixels), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		dc = wx.WindowDC( self )
		dc.SetFont( font )
		wNum, hNum = dc.GetTextExtent( '999' )
		wNum += 8
		hNum += 8
		
		outsideBorder = 4

		vsizer = wx.BoxSizer( wx.VERTICAL )
		
		self.numEditHS = wx.BoxSizer( wx.HORIZONTAL )
		
		self.numEditLabel = wx.StaticText(self, label='{}'.format(_('Enter Bib:')))
		self.numEditLabel.SetFont( font )
		
		editWidth = 140
		self.numEdit = wx.TextCtrl( self, style=wx.TE_RIGHT | wx.TE_PROCESS_ENTER )
		self.numEdit.Bind( wx.EVT_TEXT_ENTER, self.onEnterPress )
		self.numEdit.SetFont( font )
		
		self.numEditHS.Add( self.numEditLabel, wx.ALIGN_CENTRE | wx.ALIGN_CENTRE_VERTICAL )
		self.numEditHS.Add( self.numEdit, flag=wx.LEFT|wx.EXPAND, border = 4 )
		vsizer.Add( self.numEditHS, flag=wx.EXPAND|wx.LEFT|wx.TOP, border = outsideBorder )

		self.SetSizer( vsizer )
	
	def onEnterPress( self, event = None ):
		nums = self.numEdit.GetValue()
		if not nums:
			wx.CallAfter( self.numEdit.SetValue, '' )
			return
		
		race = Model.race
		if not race or not race.isRunning():
			wx.CallAfter( self.numEdit.SetValue, '' )
			return
		#t = race.curRaceTime()
		t=datetime.datetime.now()
		
		if not isinstance(nums, (list, tuple)):
			nums = [nums]
			
		#Add the times to the model.
		numTimes = []
		for num in nums:
			try:
				num = int(num)
			except Exception:
				continue
			#race.addTime( num, t, False )
			race.addSprintBib( num )
			numTimes.append( (num, t) )
		
		# Write to the log.
		#OutputStreamer.writeNumTimes( numTimes )
			
		# Schedule a photo.
		#if race.enableUSBCamera:
			#for num in nums:
				#try:
					#num = int(num)
				#except Exception:
					#continue
				
				#race.photoCount += TakePhoto(num, t) if okTakePhoto(num, t) else 0
			
		#self.playBlip()
		race.setChanged()

		wx.CallAfter( self.numEdit.SetValue, '' )
	
	#def doAction( self, action ):
		#race = Model.race
		#t = race.curRaceTime() if race and race.isRunning() else None
		#success = False
		#for num in getRiderNumsFromText( self.numEdit.GetValue() ):
			#if action(self, num, t):
				#success = True
		#if success:
			#self.numEdit.SetValue( '' )
			#wx.CallAfter( Utils.refreshForecastHistory )
	
	def Enable( self, enable ):
		wx.Panel.Enable( self, enable )
		

class Data( wx.Panel ):
	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		
		self.colnames = ['Time', 'Bib', 'Name', 'Machine', 'Team', 'Sprint Time', 'Speed', 'Unit']
	
		self.SetBackgroundColour( wx.WHITE )
		
		self.refreshInputUpdateNonBusy = NonBusyCall( self.refreshInputUpdate, min_millis=1000, max_millis=3000 )
		
		fontPixels = 50
		font = wx.Font((0,fontPixels), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

		vs = wx.BoxSizer( wx.VERTICAL )
		
		self.bibEntry = BibEntry( self )
		
		
		#------------------------------------------------------------------------------
		# Race time.
		#
		self.raceTime = wx.StaticText( self, label = '')
		self.raceTime.SetFont( font )
		self.raceTime.SetDoubleBuffered( True )
				
		self.clockSync = wx.StaticText( self, label = 'δt=?')
		self.showTagReads = wx.CheckBox( self, label='Show RFID reads' )
		
		self.showTagReads.Bind( wx.EVT_CHECKBOX, self.refresh )
		
		hs = wx.BoxSizer( wx.HORIZONTAL )
		hs.Add( self.bibEntry, flag=wx.ALIGN_CENTRE_VERTICAL|wx.ALL, border = 4 )
		hs.Add( self.raceTime, flag=wx.ALIGN_CENTRE_VERTICAL|wx.ALL, border = 4  )
		hs.Add( self.clockSync, flag=wx.ALIGN_BOTTOM|wx.ALL, border = 4  )
		hs.Add( self.showTagReads, flag=wx.ALIGN_CENTRE_VERTICAL|wx.ALL, border = 4  )
		vs.Add( hs, flag=wx.EXPAND|wx.ALL, border = 2 )
		#self.raceHUD = RaceHUD( splitter, wx.ID_ANY, style=wx.BORDER_SUNKEN, lapInfoFunc=getLapInfo, leftClickFunc=self.doLeftClickHUD )
		
		#splitter.SetMinimumPaneSize( 20 )
		#splitter.SplitHorizontally( panel, self.raceHUD, -100 )
		#verticalMainSizer.Add( splitter, 1, flag=wx.EXPAND )
		
		self.dataGrid = wx.grid.Grid( self )
		self.dataGrid.CreateGrid(0, len(self.colnames))
		i = 0
		for col in self.colnames:
			self.dataGrid.SetColLabelValue(i, col)
			i+=1
		self.dataGrid.HideRowLabels()
		self.dataGrid.AutoSize()
		
		# fixme make bib colum editable
		
		#self.dataGrid.SetRowLabelSize( 0 )
		#self.dataGrid.SetMargins( 0, 0 )
		#self.dataGrid.SetRightAlign( True )
		#self.dataGrid.AutoSizeColumns( True )
		#self.dataGrid.DisableDragColSize()
		#self.dataGrid.DisableDragRowSize()
		
		vs.Add( self.dataGrid, 1, wx.EXPAND|wx.ALL)
		
		self.SetSizer( vs )
		self.isEnabled = True
		
		self.refreshRaceTime()

	def doClockUpdate( self ):
		mainWin = Utils.getMainWin()
		return not mainWin or mainWin.isShowingPage(self)
	
	
	def refreshInputUpdate( self ):
		self.refreshLaps()
		self.refreshRiderLapCountList()
		self.refreshLastRiderOnCourse()
	
	def updateLayout( self ):
		self.sizerLapInfo.Layout()
		self.sizerSubVertical.Layout()
		self.horizontalMainSizer.Layout()
		self.Layout()
		
	def refreshRaceTime( self ):
		race = Model.race
		
		if race is not None:
			tRace = race.getInProgressSprintTime()
			if tRace:
				tStr = Utils.formatTime( tRace )
				if tStr.startswith('0'):
					tStr = tStr[1:]
				tStr = 'Timing: ' + tStr
			elif race.isRunning():
				tStr = 'Waiting...'
				self.raceTime.SetForegroundColour(wx.Colour(255,0,0))
			else:
				tStr = 'Not recording'
				self.raceTime.SetForegroundColour(wx.Colour(0,0,0))
		else:
			tStr = 'No race'
			self.raceTime.SetForegroundColour(wx.Colour(0,0,0))
		self.raceTime.SetLabel( tStr )
		
		
		
		#self.hbClockPhoto.Layout()
		
		#mainWin = Utils.mainWin
		#if mainWin is not None:
			#try:
				#mainWin.refreshRaceAnimation()
			#except Exception:
				#pass
				
	def updateClockDelta( self, d ):
		if d is not None:
			self.clockSync.SetLabel( 'δt=' + '{:.3f}'.format(d.total_seconds()) )
		else:
			self.clockSync.SetLabel( '' )
	
	def refreshLaps( self ):
		wx.CallAfter( self.refreshRaceHUD )
	
	
	def refreshAll( self ):
		self.refreshRaceTime()
		self.refreshLaps()
	
	def commit( self ):
		pass
			
	def refresh( self, event=None ):
		#self.clock.Start()

		race = Model.race
		
		excelLink = getattr(race, 'excelLink', None)
		if excelLink:
			externalInfo = excelLink.read()
		
		enable = bool(race and race.isRunning())
		if self.isEnabled != enable:
			self.isEnabled = enable
			
		sprints = race.getSprints()
		if self.showTagReads.IsChecked():
			timeBibs = race.getSprintBibs()
			for timeBib in timeBibs:
				t = timeBib[0]
				bib = timeBib[1]
				sprintDict = {}
				sprintDict["sprintBib"] = bib
				sprints.append( (t, sprintDict) )

		sprints.sort()
			
		if self.dataGrid.GetNumberRows():
			self.dataGrid.DeleteRows(0, self.dataGrid.GetNumberRows())
		
		for sprint in sprints:
			bib = None
			name = ''
			machine = ''
			team = ''
			sortTime = sprint[0]
			sprintDict = sprint[1]
			self.dataGrid.AppendRows(1)
			row = self.dataGrid.GetNumberRows() -1
			# Shade tag reads light grey
			if not "sprintTime" in sprintDict:
				for c in range(len(self.colnames)):
					self.dataGrid.SetCellBackgroundColour(row, c, wx.Colour ( 211, 211, 211 ))
			else:
				for c in range(len(self.colnames)):
					self.dataGrid.SetCellBackgroundColour(row, c, wx.Colour ( 255, 255, 255 ))
			
			col = 0
			self.dataGrid.SetCellValue(row, col, str(sortTime)[:-3])
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_CENTER)
			col += 1
			bibstring = str(sprintDict["sprintBib"]) if "sprintBib" in sprintDict else ''
			bib = None
			self.dataGrid.SetCellValue(row, col, bibstring)
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
			if ',' in bibstring:
				name = '[Multiple Bibs]'
				self.dataGrid.SetCellBackgroundColour(row, col, wx.Colour( 255, 255, 0 ))
			else:
				#self.dataGrid.SetCellBackgroundColour(row, col, wx.Colour( 255, 255, 255 ))
				try:
					bib = int(bibstring)
				except:
					pass
			col += 1
			#name
			if bib and excelLink is not None and excelLink.hasField('FirstName'):
				try:
					name = ', '.join( n for n in [externalInfo[bib]['LastName'], externalInfo[bib]['FirstName']] if n )
				except:
					pass
			# Do this outside the try, because name may have been written above
			self.dataGrid.SetCellValue(row, col, name)
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_CENTER)
			col += 1
			#Machine
			if bib and excelLink is not None and excelLink.hasField('Machine'):
				try:
					machine = externalInfo[bib]['Machine']
					self.dataGrid.SetCellValue(row, col, machine)
					self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_CENTER)
				except:
					pass
			col += 1
			#team
			if bib and excelLink is not None and excelLink.hasField('Team'):
				try:
					machine = externalInfo[bib]['Team']
					self.dataGrid.SetCellValue(row, col, team)
					self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_CENTER)
				except:
					pass
			col += 1
			self.dataGrid.SetCellValue(row, col, '{:.3f}'.format(sprintDict["sprintTime"]) if "sprintTime" in sprintDict else '')
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
			col += 1
			self.dataGrid.SetCellValue(row, col, '{:.2f}'.format(sprintDict["sprintSpeed"]) if "sprintSpeed" in sprintDict else '')
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
			col += 1
			self.dataGrid.SetCellValue(row, col, str(sprintDict["speedUnit"]) if "speedUnit" in sprintDict else '')
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_CENTER)
			col += 1
			
				
		
		row = self.dataGrid.GetNumberRows() -1
		self.dataGrid.MakeCellVisible(row, 0)
			
		self.dataGrid.AutoSizeColumns()
		
			
		#self.photoCount.Show( bool(race and race.enableUSBCamera) )
		#self.photoBitmap.Show( bool(race and race.enableUSBCamera) )
		
		#Refresh the race start time.
		#changed = False
		#rst, rstSource = '', ''
		#if race and race.startTime:
			#st = race.startTime
			#if race.enableJChipIntegration and race.resetStartClockOnFirstTag:
				#if race.firstRecordedTime:
					#rstSource = _('Chip Start')
				#else:
					#rstSource = _('Waiting...')
			#else:
				#rstSource = _('Manual Start')
			#rst = '{:02d}:{:02d}:{:02d}.{:02d}'.format(st.hour, st.minute, st.second, int(st.microsecond / 10000.0))
		#changed |= SetLabel( self.raceStartMessage, rstSource )
		#changed |= SetLabel( self.raceStartTime, rst )

		#self.refreshInputUpdateNonBusy()
		
		#if self.isKeypadInputMode():
			#wx.CallLater( 100, self.keypad.numEdit.SetFocus )
		#elif self.isBibTimeInputMode():
			#wx.CallLater( 100, self.bibTimeRecord.numEdit.SetFocus )
	
#if __name__ == '__main__':
	#Utils.disable_stdout_buffering()
	#app = wx.App(False)
	#mainWin = wx.Frame(None,title="CrossMan", size=(1000,800))
	#Model.setRace( Model.Race() )
	#model = Model.getRace()
	#model._populate()
	#model.enableUSBCamera = True
	#numKeypad = NumKeypad(mainWin)
	#numKeypad.refresh()
	#mainWin.Show()
	#app.MainLoop()


