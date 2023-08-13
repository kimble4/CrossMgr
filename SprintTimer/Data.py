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
import Model

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
	
	#def Enable( self, enable ):
		#wx.Panel.Enable( self, enable )
		

class Data( wx.Panel ):
	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		
		self.colnames = ['Count', 'Time of day', 'Bib', 'Name', 'Machine', 'Team', 'Seconds', 'Speed', 'Unit', 'Note', 'Distance', 'System µs', 'Satellites', 'Lat', 'Long', 'Ele']
		
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
		
		# fixme make bib column editable
		
		vs.Add( self.dataGrid, 1, wx.EXPAND|wx.ALL)
		
		vs.Add( self.showTagReads, flag=wx.ALIGN_RIGHT|wx.ALL, border = 4  )
		
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
				self.raceTime.SetForegroundColour(self.redColour)
			elif race.isRunning():
				tStr = 'Waiting...'
				self.raceTime.SetForegroundColour(self.redColour)
			else:
				tStr = 'Not recording'
				self.raceTime.SetForegroundColour(self.blackColour)
		else:
			tStr = 'No race loaded'
			self.raceTime.SetForegroundColour(self.blackColour)
		self.raceTime.SetLabel( tStr )
				
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
			Utils.writeLog( 'Results:doRightClick: {}'.format(e) )
			
	def onDelete( self, event, iSprint ):
		race = Model.race
		if not race:
			return
		print('delete callback: ' + str(iSprint))
		sprintDict = race.sprints[iSprint][1]
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
		print('ok')
		del race.sprints[iSprint]
		race.setChanged()
		wx.CallAfter(self.refresh)
		
	def onEditDistance( self, event, iSprint ):
		race = Model.race
		if not race:
			return
		sprintDict = race.sprints[iSprint][1]
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
				except:
					return
	
	def onRecalculateSpeed( self, event, iSprint ):
		race = Model.race
		if not race:
			return
		sprintDict = race.sprints[iSprint][1]
		# Now recalculate the speed
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
			wx.CallAfter(self.refresh)
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
		
		if col == 2: # bib
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
		elif col > 2 and col < 6: #name, machine, team
			excelLink = getattr(race, 'excelLink', None)
			if "sprintBib" in sprintDict and excelLink:
				Utils.MessageOK( self, _('Cannot edit') + ' \'' + self.colnames[col] + '\' ' +  _('field for sprints with a bib number') + '.\n' + _('Make the change in the sign-on spreadsheet instead.') , _('External spreadsheet linked') )
				# restore the old value
				self.dataGrid.SetCellValue(row, col, old)
			else:
				if col == 3:
					sprintDict["sprintNameEdited"] = value
				elif col == 4:
					sprintDict["sprintMachineEdited"] = value
				elif col == 5:
					sprintDict["sprintTeamEdited"] = value
				race.setChanged()
				self.dataGrid.SetCellBackgroundColour(row, col, self.orangeColour)
				wx.CallAfter(self.refresh)
		elif col == 9: #note
			sprintDict["sprintNote"] = value
			race.setChanged()
			wx.CallAfter(self.refresh)
		elif col == 10: #distance
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
			except:
				# restore the old value
				self.dataGrid.SetCellValue(row, col, old)
				return
		else:
			# restore the old value
			self.dataGrid.SetCellValue(row, col, old)

	
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
				sprintDict["isRFID"] = not manual
				sprintDict["isManualBib"] = manual
				if manual:
					sprintDict["sprintNote"] = 'Manual bib entry'
				else:
					sprintDict["sprintNote"] = 'RFID tag read'
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
			else:
				for c in range(len(self.colnames)):
					self.dataGrid.SetCellBackgroundColour(row, c, self.whiteColour)
			
			col = 0
			self.dataGrid.SetCellValue(row, col, str(index))
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_CENTER, wx.ALIGN_CENTER)
			col += 1
			self.dataGrid.SetCellValue(row, col, sortTime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_CENTER)
			col += 1
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
					
				except:
					pass
			elif "sprintMachineEdited" in sprintDict:
				machine = sprintDict["sprintMachineEdited"]
				self.dataGrid.SetCellBackgroundColour(row, col, self.orangeColour)
			self.dataGrid.SetCellValue(row, col, machine)
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_CENTER)
			col += 1
			#team
			if bib and excelLink is not None and excelLink.hasField('Team'):
				try:
					team = externalInfo[bib]['Team']
				except:
					pass
			elif "sprintTeamEdited" in sprintDict:
				team = sprintDict["sprintTeamEdited"]
				self.dataGrid.SetCellBackgroundColour(row, col, self.orangeColour)
			self.dataGrid.SetCellValue(row, col, team)
			self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_CENTER)
			col += 1
			if "sprintTime" in sprintDict:
				self.dataGrid.SetCellValue(row, col, '{:.3f}'.format(sprintDict["sprintTime"]))
				self.dataGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
				if ppsBad:
					self.dataGrid.SetCellBackgroundColour(row, col, self.yellowColour)
			col += 1
			if "sprintSpeed" in sprintDict:
				self.dataGrid.SetCellValue(row, col, '{:.2f}'.format(sprintDict["sprintSpeed"]))
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
				
		
		row = self.dataGrid.GetNumberRows() -1
		self.dataGrid.MakeCellVisible(row, 0)
			
		self.dataGrid.AutoSizeColumns()
		


