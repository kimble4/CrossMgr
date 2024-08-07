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
from HighPrecisionTimeEdit import HighPrecisionTimeEdit

import Utils
import Model
import Flags

bitmapCache = {}
class IOCCodeRenderer(wx.grid.GridCellRenderer):
	def getImgWidth( self, ioc, height ):
		img = Flags.GetFlagImage( ioc )
		if img:
			imgHeight = int( height * 0.8 )
			imgWidth = int( float(img.GetWidth()) / float(img.GetHeight()) * float(imgHeight) )
			padding = int(height * 0.1)
			return img, imgWidth, imgHeight, padding
		return None, 0, 0, 0

	def Draw(self, grid, attr, dc, rect, row, col, isSelected):
		text = grid.GetCellValue(row, col)

		dc.SetFont( attr.GetFont() )
		w, h = dc.GetTextExtent( text )
		
		ioc = text[:3]
		img, imgWidth, imgHeight, padding = self.getImgWidth(ioc, h)
		
		fg = attr.GetTextColour()
		bg = attr.GetBackgroundColour()
		if isSelected:
			fg, bg = bg, fg
		
		dc.SetBrush( wx.Brush(bg, wx.SOLID) )
		dc.SetPen( wx.TRANSPARENT_PEN )
		dc.DrawRectangle( rect )

		rectText = wx.Rect( rect.GetX()+padding+imgWidth, rect.GetY(), rect.GetWidth()-padding-imgWidth, rect.GetHeight() )
		
		hAlign, vAlign = attr.GetAlignment()
		dc.SetTextForeground( fg )
		dc.SetTextBackground( bg )
		grid.DrawTextRectangle(dc, text, rectText, hAlign, vAlign)

		if img:
			key = (ioc, imgHeight)
			if key not in bitmapCache:
				bitmapCache[key] = img.Scale(imgWidth, imgHeight, wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()
			dc.DrawBitmap( bitmapCache[key], rect.GetX(), rect.GetY()+(rect.GetHeight()-imgHeight)//2 )

	def GetBestSize(self, grid, attr, dc, row, col):
		text = grid.GetCellValue(row, col)
		dc.SetFont(attr.GetFont())
		w, h = dc.GetTextExtent( text )
		
		img, imgWidth, imgHeight, padding = self.getImgWidth(text[:3], h)
		if img:
			return wx.Size(w + imgWidth + padding, h)
		else:
			return wx.Size(w, h)

	def Clone(self):
		return IOCCodeRenderer()

class BibEntry( wx.Panel ):
	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		self.SetBackgroundColour( wx.WHITE )
		
		fontPixels = 36
		font = wx.Font((0,fontPixels), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		#dc = wx.WindowDC( self )
		#dc.SetFont( font )
		
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
			Utils.writeLog('Got manual bib entry: ' + str(num))
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
			
		Utils.PlaySound('blip6.wav')
		race.setChanged()

		wx.CallAfter( self.numEdit.SetValue, '' )
	
	#def Enable( self, enable ):
		#wx.Panel.Enable( self, enable )


class ManualEntryDialog( wx.Dialog ):
	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__( parent, id, _("Manual sprint entry"),
						style=wx.DEFAULT_DIALOG_STYLE|wx.TAB_TRAVERSAL|wx.RESIZE_BORDER )
		
		border=4
		
		
		
		bs = wx.BoxSizer( wx.VERTICAL )
		bs.Add( wx.StaticText(self, label='Enter sprint data:') )
		bs.AddSpacer( border )
		
		gridBagSizer = wx.GridBagSizer()
		
		now = datetime.datetime.now()
		seconds_since_midnight = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
		self.sprintStart = HighPrecisionTimeEdit( self, display_seconds=True, allow_none=True, seconds=seconds_since_midnight, size=(200,-1) )
		gridBagSizer.Add( wx.StaticText( self, label=_('Time of day:') ),
						pos=(0,0), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL )
		gridBagSizer.Add( self.sprintStart,
						pos=(0,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL )
		

		gridBagSizer.Add( wx.StaticText( self, label=_('Rider bib#:') ),
						pos=(1,0), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL )

		self.bibEntry = wx.lib.intctrl.IntCtrl(self, allow_none=True, value=None)
		gridBagSizer.Add( self.bibEntry,
						pos=(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL )
		
		gridBagSizer.Add( wx.StaticText( self, label=_('Sprint duration:') ),
						pos=(2,0), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL )

		self.secondsEntry = HighPrecisionTimeEdit( self, display_seconds=True, display_milliseconds=True, allow_none=True, value=None, size=(200,-1) )
		gridBagSizer.Add( self.secondsEntry,
						pos=(2,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL )
		
		gridBagSizer.Add( wx.StaticText( self, label=_('Trap distance (metres):') ),
						pos=(3,0), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL )
		self.distanceEntry = wx.TextCtrl(self, value='')
		gridBagSizer.Add( self.distanceEntry,
						pos=(3,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL )
		
		gridBagSizer.Add( wx.StaticText( self, label=_('Note:') ),
						pos=(4,0), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL )
		self.noteEntry = wx.TextCtrl(self, value='', size=(300, -1))
		gridBagSizer.Add( self.noteEntry,
						pos=(4,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL )
		
		
		bs.Add( gridBagSizer )
		bs.AddSpacer( border )
		
		btnSizer = self.CreateStdDialogButtonSizer( wx.OK|wx.CANCEL)
		self.Bind( wx.EVT_BUTTON, self.onOK, id=wx.ID_OK )
		self.Bind( wx.EVT_BUTTON, self.onCancel, id=wx.ID_CANCEL )
		if btnSizer:
			bs.Add( btnSizer, 0, wx.EXPAND | wx.ALL, border )

		race = Model.race
		if race is not None:
			distance = str(getattr(race, "sprintDistance", ''))
			self.distanceEntry.SetValue(distance)

		self.SetSizerAndFit(bs)
		bs.Fit( self )
		
		self.CentreOnParent(wx.BOTH)
		wx.CallAfter( self.SetFocus )
		
		
	def onOK( self, event ):
		now = datetime.datetime.now()
		
		race = Model.race
		if race is None:
			return
		
		sprintTime = self.secondsEntry.GetSeconds()
		if sprintTime:
		
			sprintDict = {}
			
			startSeconds = self.sprintStart.GetSeconds()
			if startSeconds is not None:
				midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
				t = midnight + datetime.timedelta(seconds=startSeconds)
			else:
				t = now
	
			sprintDict['sprintStart'] = int(t.timestamp())
			sprintDict['sprintStartMillis'] = (t.timestamp() - int(t.timestamp())) * 1000.0
			
			sprintDict['sprintBib'] = self.bibEntry.GetValue()
			
			sprintDict['sprintTime'] = sprintTime
			
			try:
				distance = float(self.distanceEntry.GetValue())
				sprintDict['sprintDistance'] = distance
				sprintDict
			except:
				pass
			
			note = self.noteEntry.GetValue()
			if note:
				sprintDict['sprintNote'] = note
			else:
				sprintDict['sprintNote'] = 'Manual entry'
			
			sprintDict['manualEntry'] = True
			
			with Model.LockRace() as race:
				race.addSprint( t, sprintDict )
			wx.CallAfter( Data.onRecalculateSpeed, None, None )
		else:
			Utils.MessageOK( self, '{}'.format( _("Sprint duration cannot be zero!")), _("Error") )
		self.EndModal( wx.ID_OK )
		
	def onCancel( self, event ):
		self.EndModal( wx.ID_CANCEL )
		

class Data( wx.Panel ):
	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		
		self.colnames = ['Count', 'Time of Day', 'RTC Δt', 'T1 Time', 'T2 Time', 'Bib', 'Name', 'Machine', 'Team', 'Gender', 'Nat', 'Seconds', 'Speed', 'Unit', 'Note', 'Distance', 'System µs', 'Satellites', 'Lat', 'Long', 'Ele']
		
		self.whiteColour = wx.Colour( 255, 255, 255 )
		self.blackColour = wx.Colour( 0, 0, 0 )
		self.yellowColour = wx.Colour( 255, 255, 0 )
		self.orangeColour = wx.Colour( 255, 165, 0 )
		self.greyColour = wx.Colour( 150, 150, 150 )
		self.lightGreyColour = wx.Colour ( 211, 211, 211 )
		self.greenColour = wx.Colour( 127, 210, 0 )
		self.lightBlueColour = wx.Colour( 153, 205, 255 )
		self.redColour = wx.Colour( 255, 0, 0 )
	
		self.SetBackgroundColour( wx.WHITE )
		
		#self.refreshInputUpdateNonBusy = NonBusyCall( self.refreshInputUpdate, min_millis=1000, max_millis=3000 )
		
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
				
		self.clockSync = wx.StaticText( self, label = 'Sprint timer not connected')
		self.showTagReads = wx.CheckBox( self, label='Show bib entry / RFID read times' )
		
		self.showTagReads.Bind( wx.EVT_CHECKBOX, self.refresh )
		
		hs = wx.BoxSizer( wx.HORIZONTAL )
		
		hs.Add( self.bibEntry, flag=wx.ALIGN_CENTRE_VERTICAL|wx.RIGHT|wx.ALL, border = 4 )
		hs.Add( self.raceTime, flag=wx.ALIGN_CENTRE_VERTICAL|wx.ALL, border = 4  )
		hs.Add( self.clockSync, flag=wx.ALIGN_BOTTOM|wx.RIGHT|wx.ALL, border = 4  )
		
		vs.Add( hs, flag=wx.EXPAND|wx.ALL, border = 2 )

		self.dataGrid = wx.grid.Grid( self )
		self.dataGrid.CreateGrid(0, len(self.colnames))
		i = 0
		for col in self.colnames:
			self.dataGrid.SetColLabelValue(i, col)
			i+=1
		self.dataGrid.HideRowLabels()
		self.dataGrid.AutoSize()
		self.dataGrid.Bind( wx.grid.EVT_GRID_CELL_CHANGED, self.OnCellChanged )
		self.dataGrid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.onRightClick )
		
		vs.Add( self.dataGrid, 1, wx.EXPAND|wx.ALL)
		
		vs.Add( self.showTagReads, flag=wx.ALIGN_RIGHT|wx.ALL, border = 4  )
		
		self.SetSizer( vs )
		self.isEnabled = True
		
		self.refreshRaceTime()

	def doClockUpdate( self ):
		mainWin = Utils.getMainWin()
		return not mainWin or mainWin.isShowingPage(self)
		
	def refreshRaceTime( self ):
		race = Model.race
		if race is not None:
			if race.isRunning():
				tRace = race.getInProgressSprintTime()
				if tRace:
					if tRace >= 1:
						Utils.PlaySound('pip.wav')
					tStr = Utils.formatTime( tRace )
					if tStr.startswith('0'):
						tStr = tStr[1:]
					if race.getInProgressSprintBib() is not None:
						tStr = '#' + str(race.getInProgressSprintBib()) + ' Timing: ~' + tStr
					else:
						tStr = 'Timing: ~' + tStr
					self.raceTime.SetBackgroundColour(self.redColour)
					self.raceTime.SetForegroundColour(self.whiteColour)
					if Utils.mainWin:
						Utils.mainWin.updateLapCounter()
				else:
					tStr = 'Ready...'
					self.raceTime.SetBackgroundColour(self.whiteColour)
					self.raceTime.SetForegroundColour(self.redColour)
			else:
				tStr = 'Not recording'
				self.raceTime.SetBackgroundColour(self.whiteColour)
				self.raceTime.SetForegroundColour(self.greyColour)
		else:
			tStr = 'No race loaded'
			self.raceTime.SetBackgroundColour(self.whiteColour)
			self.raceTime.SetForegroundColour(self.blackColour)
		self.raceTime.SetLabel( tStr )
		self.Layout()
				
	def updateClockDelta( self, d, havePPS ):
		if d is not None:
			t = 'Δt=' + '{:.3f}'.format(d.total_seconds())
		else:
			t = 'Not Connected'
			
		if havePPS:
			t += ', PPS OK'
		elif havePPS is not None:
			t += ', No PPS!'
			
		self.clockSync.SetLabel( t )
	
	def refreshLaps( self ):
		wx.CallAfter( self.refreshRaceHUD )
	
	
	def refreshAll( self ):
		self.refreshRaceTime()
		self.refreshLaps()
	
	def commit( self ):
		pass
			
	def onRightClick( self, event ):
		row = event.GetRow()
		col = event.GetCol()
		try:
			iSprint = int(self.dataGrid.GetCellValue(row, 0)) - 1
		except:
			return
		menu = wx.Menu()
		recalc = menu.Append( wx.ID_ANY, 'Recalculate speed...', 'Recalculate the speed in the current unit...' )
		self.Bind( wx.EVT_MENU, lambda event: self.onRecalculateSpeed(event, iSprint), recalc )
		delete = menu.Append( wx.ID_ANY, 'Delete sprint...', 'Delete this sprint...' )
		self.Bind( wx.EVT_MENU, lambda event: self.onDelete(event, iSprint), delete )
		distance = menu.Append( wx.ID_ANY, 'Edit trap distance...', 'Change trap distance for this sprint...' )
		self.Bind( wx.EVT_MENU, lambda event: self.onEditDistance(event, iSprint), distance )
		try:
			self.PopupMenu( menu )
		except Exception as e:
			Utils.writeLog( 'Data:doRightClick: {}'.format(e) )
			
	def onDelete( self, event, iSprint ):
		race = Model.race
		if not race:
			return
		sprintDict = race.sprints[iSprint][1]
		mainWin = Utils.getMainWin()
		if 'sprintBib' in sprintDict:
			sprintString = '#' + str(sprintDict['sprintBib'])
			try:
				bib = int(sprintDict['sprintBib'])
				excelLink = getattr(race, 'excelLink', None)
				if excelLink:
					externalInfo = excelLink.read()
					name = ', '.join( n for n in [externalInfo[bib]['LastName'], externalInfo[bib]['FirstName']] if n )
					sprintString += ' ' + name
			except:
				pass
		else:
			sprintString = 'Unknown rider'
		if not Utils.MessageOKCancel(self, '{}\n{}\n\n{}'.format(
			_('Delete sprint') + ' ' + str(iSprint+1) + _(' for' + ':'),
			sprintString,
			_('Continue?') ),
			_('Confirm delete'), wx.ICON_QUESTION, ):
			return
		del race.sprints[iSprint]
		race.setChanged()
		wx.CallAfter(self.refresh)
		wx.CallLater( race.rfidTagAssociateSeconds*1000, mainWin.refreshResults )
		
	def onEditDistance( self, event, iSprint ):
		race = Model.race
		if not race:
			return
		sprintDict = race.sprints[iSprint][1]
		mainWin = Utils.getMainWin()
		if 'sprintBib' in sprintDict:
			sprintString = '#' + str(sprintDict['sprintBib'])
			try:
				bib = int(sprintDict['sprintBib'])
				excelLink = getattr(race, 'excelLink', None)
				if excelLink:
					externalInfo = excelLink.read()
					name = ', '.join( n for n in [externalInfo[bib]['LastName'], externalInfo[bib]['FirstName']] if n )
					sprintString += ' ' + name
			except:
				pass
		else:
			sprintString = 'Unknown rider'
			
		with wx.TextEntryDialog(self, 'Enter new trap distance for sprint ' + str(iSprint+1) + '\n' + sprintString + ':', 'Edit trap distance') as dlg:
			dlg.SetValue(str(sprintDict['sprintDistance'] if 'sprintDistance' in sprintDict else ''))
			if dlg.ShowModal() == wx.ID_OK:
				try:
					distance = float(dlg.GetValue())
					sprintDict['sprintDistance'] = distance
					# Now recalculate the speed
					speed = distance / sprintDict['sprintTime']
					if race.distanceUnit == Model.Race.UnitKm:
						sprintDict['sprintSpeed'] = speed * 3.6
						sprintDict['speedUnit'] = 'kph'
					elif race.distanceUnit == Model.Race.UnitMiles:
						sprintDict['sprintSpeed'] = speed * 2.23694
						sprintDict['speedUnit'] = 'mph'
					else:
						sprintDict['sprintSpeed'] = None
						sprintDict['speedUnit'] = None
					race.setChanged()
					wx.CallAfter(self.refresh)
					wx.CallLater( race.rfidTagAssociateSeconds*1000, mainWin.refreshResults )
				except:
					return
	
	def onRecalculateSpeed( self, event=None, iSprint=None ):
		race = Model.race
		if not race:
			return
		if iSprint is None:
			iSprint = len(race.sprints) - 1
		sprintDict = race.sprints[iSprint][1]
		mainWin = Utils.getMainWin()
		try:
			speed = float(sprintDict['sprintDistance']) / float(sprintDict['sprintTime'])
			if race.distanceUnit == Model.Race.UnitKm:
				sprintDict['sprintSpeed'] = speed * 3.6
				sprintDict['speedUnit'] = 'kph'
			elif race.distanceUnit == Model.Race.UnitMiles:
				sprintDict['sprintSpeed'] = speed * 2.23694
				sprintDict['speedUnit'] = 'mph'
			else:
				sprintDict['sprintSpeed'] = None
				sprintDict['speedUnit'] = None
			race.setChanged()
			Utils.getMainWin().updateLapCounter() # race clock may be displaying the calculated speed
			wx.CallAfter(Utils.refresh)
			wx.CallLater( race.rfidTagAssociateSeconds*1000, mainWin.refreshResults )
		except:
			return
	
	def OnCellChanged( self, event ):
		row = event.GetRow()
		col = event.GetCol()
		old = event.GetString()
		value = self.dataGrid.GetCellValue(row, col)
		if col <2: # count, sortTime
			# restore the old value
			self.dataGrid.SetCellValue(row, col, old)
			return
		
		race = Model.race
		try:
			iSprint = int(self.dataGrid.GetCellValue(row, 0)) - 1
		except ValueError:
			# We tried to edit a bib entry / RFID read row
			self.dataGrid.SetCellValue(row, col, old)
			return
		
		sprintDict = race.sprints[iSprint][1]
		mainWin = Utils.getMainWin()
		
		if col == self.colnames.index('Bib'):
			if value != '':
				try:
					newBib = int(value)
				except:
					# restore the old value
					self.dataGrid.SetCellValue(row, col, old)
					return
			else:
				newBib = ''
			if newBib == '':
				del sprintDict["sprintBib"]
			else:
				sprintDict["sprintBib"] = newBib
			sprintDict["sprintBibEdited"] = True
			race.setChanged()
			self.dataGrid.SetCellBackgroundColour(row, col, self.orangeColour)
			wx.CallAfter(self.refresh)
			wx.CallLater( race.rfidTagAssociateSeconds*1000, mainWin.refreshResults )
		elif col >= self.colnames.index('Name') and col <= self.colnames.index('Nat'): #name, machine, team, gender, nat
			excelLink = getattr(race, 'excelLink', None)
			if "sprintBib" in sprintDict and excelLink:
				Utils.MessageOK( self, _('Cannot edit') + ' \'' + self.colnames[col] + '\' ' +  _('field for sprints with a bib number') + '.\n' + _('Make the change in the sign-on spreadsheet instead.') , _('External spreadsheet linked') )
				# restore the old value
				self.dataGrid.SetCellValue(row, col, old)
			else:
				if col == self.colnames.index('Name'):
					sprintDict["sprintNameEdited"] = value
				elif col == self.colnames.index('Machine'):
					sprintDict["sprintMachineEdited"] = value
				elif col == self.colnames.index('Team'):
					sprintDict["sprintTeamEdited"] = value
				elif col == self.colnames.index('Gender'):
					sprintDict["sprintGenderEdited"] = value
				elif col == self.colnames.index('Nat'):
					sprintDict["sprintNatcodeEdited"] = value
				race.setChanged()
				self.dataGrid.SetCellBackgroundColour(row, col, self.orangeColour)
				wx.CallAfter(self.refresh)
				wx.CallLater( race.rfidTagAssociateSeconds*1000, mainWin.refreshResults )
		elif col == self.colnames.index('Note'):
			sprintDict["sprintNote"] = value
			race.setChanged()
			wx.CallAfter(self.refresh)
			wx.CallLater( race.rfidTagAssociateSeconds*1000, mainWin.refreshResults )
		elif col == self.colnames.index('Distance'):
			try:
				distance = float(value)
				sprintDict['sprintDistance'] = distance
				# Now recalculate the speed
				speed = distance / sprintDict['sprintTime']
				if race.distanceUnit == Model.Race.UnitKm:
					sprintDict['sprintSpeed'] = speed * 3.6
					sprintDict['speedUnit'] = 'kph'
				elif race.distanceUnit == Model.Race.UnitMiles:
					sprintDict['sprintSpeed'] = speed * 2.23694
					sprintDict['speedUnit'] = 'mph'
				else:
					sprintDict['sprintSpeed'] = None
					sprintDict['speedUnit'] = None
				race.setChanged()
				wx.CallAfter(self.refresh)
				wx.CallLater( race.rfidTagAssociateSeconds*1000, mainWin.refreshResults )
			except:
				# restore the old value
				self.dataGrid.SetCellValue(row, col, old)
				return
		else:
			# restore the old value
			self.dataGrid.SetCellValue(row, col, old)

	def clearGrid( self ):
		if self.dataGrid.GetNumberRows():
			self.dataGrid.DeleteRows(0, self.dataGrid.GetNumberRows())
		for col in range(self.dataGrid.GetNumberCols()):
			self.dataGrid.ShowCol(col)

	
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
			timeBibManuals = race.getSprintBibs()
			for timeBibManual in timeBibManuals:
				t = timeBibManual[0]
				bib = timeBibManual[1]
				manual = timeBibManual[2]
				sprintDict = {}
				sprintDict["sprintBib"] = bib
				sprintDict["isRFID"] = False
				sprintDict["isManualBib"] = False
				if manual == Model.Race.BibManual:
					sprintDict["isManualBib"] = True
					sprintDict["sprintNote"] = 'Manual bib entry'
				elif manual == Model.Race.BibRFID:
					sprintDict["isRFID"] = True
					sprintDict["sprintNote"] = 'RFID tag read'
				elif manual == Model.Race.BibSequential:
					sprintDict["isRFID"] = True
					sprintDict["sprintNote"] = 'Sequential bib number'
				else:
					sprintDict["isManualBib"] = True
					sprintDict["sprintNote"] = '?Unknown bib source.'
					
				sprints.append( (t, sprintDict) )

		sprints.sort(key=lambda item: item[0])
			
		self.clearGrid()
			
		haveMachine = False
		haveTeam = False
		haveGender = False
		haveNat = False
		
		for sprint in sprints:
			bib = None
			name = ''
			gender = ''
			natcode = ''
			machine = ''
			team = ''
			sortTime = sprint[0]
			sprintDict = sprint[1]
			try:
				index = race.sprints.index(sprint) + 1
			except ValueError:
				index = ''
			ppsBad = False
			if "ppsGood" in sprintDict:
				if sprintDict["ppsGood"] == False:
					ppsBad = True
			self.dataGrid.AppendRows(1)
			row = self.dataGrid.GetNumberRows() -1
			# Shade tag reads light grey
			if "isRFID" in sprintDict and sprintDict["isRFID"]:
				for c in range(len(self.colnames)):
					self.dataGrid.SetCellBackgroundColour(row, c, self.lightGreyColour)
			elif "isManualBib" in sprintDict and sprintDict["isManualBib"]:
				for c in range(len(self.colnames)):
					self.dataGrid.SetCellBackgroundColour(row, c, self.greyColour)
			elif 'manualEntry' in sprintDict and sprintDict['manualEntry']:
				for c in range(len(self.colnames)):
					self.dataGrid.SetCellBackgroundColour(row, c, self.orangeColour)
			else:
				for c in range(len(self.colnames)):
					self.dataGrid.SetCellBackgroundColour(row, c, self.whiteColour)
			
			col = 0 #count
			self.dataGrid.SetCellValue(row, col, str(index))
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_CENTER, wx.ALIGN_CENTER)
			
			col += 1 #ToD
			sprintStart = None
			if 'sprintStart' in sprintDict:
				sprintStart = datetime.datetime.fromtimestamp(sprintDict['sprintStart'])
				if 'sprintStartMillis' in sprintDict:
					sprintStart += datetime.timedelta(milliseconds = sprintDict['sprintStartMillis'])
			self.dataGrid.SetCellValue(row, col, sortTime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] if sortTime else '')
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_CENTER)
			if index and (sprintStart is None or sortTime != sprintStart):
				self.dataGrid.SetCellBackgroundColour(row, col, self.yellowColour)
				
			col += 1 #Δt
			if 'clockDelta' in sprintDict:
				self.dataGrid.SetCellValue(row, col, "{:.3f}".format(sprintDict['clockDelta'].total_seconds())) 
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_CENTER)
			col += 1 #T1
			if "isRFID" in sprintDict and sprintDict["isRFID"] and not race.rfidAtT2:
				self.dataGrid.SetCellValue(row, col, sortTime.strftime('%H:%M:%S.%f')[:-3] if sortTime else '')
			else:
				if 'sprintStartMillis' in sprintDict:
					self.dataGrid.SetCellValue(row, col, sprintStart.strftime('%H:%M:%S.%f')[:-3] if sprintStart else '')
				else:
					self.dataGrid.SetCellValue(row, col, sprintStart.strftime('%H:%M:%S') if sprintStart else '')
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_CENTER)
			
			col += 1 #T2
			sprintFinish = None
			if "isRFID" in sprintDict and sprintDict["isRFID"] and race.rfidAtT2:
				self.dataGrid.SetCellValue(row, col, sortTime.strftime('%H:%M:%S.%f')[:-3] if sortTime else '')
			else:
				if 'sprintFinish' in sprintDict:
					sprintFinish = datetime.datetime.fromtimestamp(sprintDict['sprintFinish'])
					if 'sprintFinishMillis' in sprintDict:
						sprintFinish += datetime.timedelta(milliseconds = sprintDict['sprintFinishMillis'])
						self.dataGrid.SetCellValue(row, col, sprintFinish.strftime('%H:%M:%S.%f')[:-3])
					else:
						self.dataGrid.SetCellValue(row, col, sprintFinish.strftime('%H:%M:%S'))
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_CENTER)
			
			col += 1 # Bib
			bibstring = str(sprintDict["sprintBib"]) if "sprintBib" in sprintDict else ''
			bib = None
			self.dataGrid.SetCellValue(row, col, bibstring)
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
			if ',' in bibstring:
				name = '[Multiple Bibs]'
				self.dataGrid.SetCellBackgroundColour(row, col, self.lightBlueColour)
			else:
				try:
					bib = int(bibstring)
				except:
					pass
				if "sprintBibEdited" in sprintDict and sprintDict["sprintBibEdited"] == True:
					self.dataGrid.SetCellBackgroundColour(row, col, self.orangeColour)
			col += 1
			#name
			if bib and excelLink is not None and ((excelLink.hasField('FirstName') or excelLink.hasField('LastName'))):
				try:
					name = ', '.join( n for n in [externalInfo[bib]['LastName'], externalInfo[bib]['FirstName']] if n )
				except:
					pass
			elif "sprintNameEdited" in sprintDict:
					name = sprintDict["sprintNameEdited"]
					self.dataGrid.SetCellBackgroundColour(row, col, self.orangeColour)
			self.dataGrid.SetCellValue(row, col, name)
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_CENTER)
			col += 1
			#Machine
			if bib and excelLink is not None and excelLink.hasField('Machine'):
				try:
					machine = externalInfo[bib]['Machine']
					haveMachine = True
				except:
					pass
			elif "sprintMachineEdited" in sprintDict:
				machine = sprintDict["sprintMachineEdited"]
				haveMachine = True
				self.dataGrid.SetCellBackgroundColour(row, col, self.orangeColour)
			self.dataGrid.SetCellValue(row, col, machine)
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_CENTER)
			col += 1
			#team
			if bib and excelLink is not None and excelLink.hasField('Team'):
				try:
					team = externalInfo[bib]['Team']
					haveTeam = True
				except:
					pass
			elif "sprintTeamEdited" in sprintDict:
				team = sprintDict["sprintTeamEdited"]
				haveTeam = True
				self.dataGrid.SetCellBackgroundColour(row, col, self.orangeColour)
			self.dataGrid.SetCellValue(row, col, team)
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_CENTER)
			col += 1
			#Gender
			if bib and excelLink is not None and excelLink.hasField('Gender'):
				try:
					gender = externalInfo[bib]['Gender']
					haveGender = True
				except:
					pass
			elif "sprintGenderEdited" in sprintDict:
				gender = sprintDict["sprintGenderEdited"]
				haveGender = True
				self.dataGrid.SetCellBackgroundColour(row, col, self.orangeColour)
			self.dataGrid.SetCellValue(row, col, gender)
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_CENTER)
			col += 1
			#NatCode
			if bib and excelLink is not None and excelLink.hasField('NatCode'):
				try:
					natcode = externalInfo[bib]['NatCode']
					haveNat = True
				except:
					if excelLink.hasField('UCICode'):
						try:
							natcode = externalInfo[bib]['UCICode']
							haveNat = True
						except:
							pass
			elif "sprintNatcodeEdited" in sprintDict:
				natcode = sprintDict["sprintNatcodeEdited"]
				haveNat = True
				self.dataGrid.SetCellBackgroundColour(row, col, self.orangeColour)
			self.dataGrid.SetCellRenderer(row, col, IOCCodeRenderer() )
			self.dataGrid.SetCellValue(row, col, natcode)
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_CENTER)
			col += 1
			if "sprintTime" in sprintDict:
				self.dataGrid.SetCellValue(row, col, '{:.3f}'.format(sprintDict["sprintTime"]))
				self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
				if ppsBad:
					self.dataGrid.SetCellBackgroundColour(row, col, self.yellowColour)
			col += 1
			if "sprintSpeed" in sprintDict:
				self.dataGrid.SetCellValue(row, col, '{:.3f}'.format(sprintDict["sprintSpeed"]))
				self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
				if ppsBad:
					self.dataGrid.SetCellBackgroundColour(row, col, self.yellowColour)
			col += 1
			self.dataGrid.SetCellValue(row, col, str(sprintDict["speedUnit"]) if "speedUnit" in sprintDict else '')
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_CENTER)
			col += 1
			self.dataGrid.SetCellValue(row, col, str(sprintDict["sprintNote"]) if "sprintNote" in sprintDict else '')
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_LEFT)
			col += 1
			self.dataGrid.SetCellValue(row, col, '{:.1f}'.format(sprintDict["sprintDistance"]) if "sprintDistance" in sprintDict else '')
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
			col += 1
			self.dataGrid.SetCellValue(row, col, str(sprintDict["sprintTimeSystemMicros"]) if "sprintTimeSystemMicros" in sprintDict else '')
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
			col += 1
			self.dataGrid.SetCellValue(row, col, str(sprintDict["satellites"]) if "satellites" in sprintDict else '')
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
			col += 1
			self.dataGrid.SetCellValue(row, col, '{:.5f}'.format(sprintDict["latitude"]) if "latitude" in sprintDict else '')
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
			col += 1
			self.dataGrid.SetCellValue(row, col, '{:.5f}'.format(sprintDict["longitude"]) if "longitude" in sprintDict else '')
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
			col += 1
			self.dataGrid.SetCellValue(row, col, '{:.1f}'.format(sprintDict["elevation"]) if "elevation" in sprintDict else '')
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
			col += 1
		
		#hide unused info columns
		if not haveMachine:
			self.dataGrid.HideCol( self.colnames.index('Machine') )
		if not haveTeam:
			self.dataGrid.HideCol( self.colnames.index('Team') )
		if not haveGender:
			self.dataGrid.HideCol( self.colnames.index('Gender') )
		if not haveNat:
			self.dataGrid.HideCol( self.colnames.index('Nat') )
		
		row = self.dataGrid.GetNumberRows() -1
		self.dataGrid.MakeCellVisible(row, 0)
			
		self.dataGrid.AutoSizeColumns()
		


