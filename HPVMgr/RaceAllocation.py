import wx
import re
import os
import sys
import Utils
#import ColGrid
from collections import defaultdict
#from Undo import undo
import datetime
import Model
import wx.lib.intctrl as intctrl


class RaceAllocation( wx.Panel ):
	
	maxRaces = 5
	whiteColour = wx.Colour( 255, 255, 255 )
	orangeColour = wx.Colour( 255, 165, 0 )
	yellowColour = wx.Colour( 255, 255, 0 )
	lightBlueColour = wx.Colour( 153, 205, 255 )
	
	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		
		self.season = None
		self.evt = None
		self.rnd = None
		self.race = 0
		self.nrRaces = 0
		self.colnames = ['Bib', 'Name', 'Factor', 'Machine', 'Categories']
		
		bigFont =  wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
		bigFont.SetFractionalPointSize( Utils.getMainWin().defaultFontSize + 4 )
		bigFont.SetWeight( wx.FONTWEIGHT_BOLD )
		
		boldFont =  wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
		boldFont.SetWeight( wx.FONTWEIGHT_BOLD )
		
		self.riderBibNames = []
		self.unallocatedBibs = []
		
		vs = wx.BoxSizer(wx.VERTICAL)
		hs = wx.BoxSizer( wx.HORIZONTAL )
		self.currentSelection = wx.StaticText( self, label='No round selected' )
		self.currentSelection.SetFont( bigFont )
		hs.Add( self.currentSelection, flag=wx.ALIGN_CENTRE )
		self.chooseRound = wx.Choice( self, choices=[], name='Select round' )
		self.chooseRound.SetFont( bigFont )
		hs.Add( self.chooseRound, flag=wx.ALIGN_CENTER_VERTICAL )
		self.totalRacers = wx.StaticText( self, label='' )
		self.totalRacers.SetFont( bigFont )
		hs.Add( self.totalRacers, flag=wx.ALIGN_CENTER_VERTICAL )
		vs.Add( hs, flag=wx.ALIGN_CENTRE )
		
		hs = wx.BoxSizer( wx.HORIZONTAL )
		
		self.chooseRound.Bind( wx.EVT_CHOICE, self.onChooseRound )
		
		hs.Add( wx.StaticText( self, label='Number of races in this round:' ), flag=wx.ALIGN_CENTER_VERTICAL )
		
		self.numberOfRaces = intctrl.IntCtrl( self, value=self.nrRaces, name='Number of races', min=0, max=RaceAllocation.maxRaces, limited=1, allow_none=1, style=wx.TE_PROCESS_ENTER )
		self.numberOfRaces.Bind( wx.EVT_TEXT_ENTER, self.onChangeNumberOfRaces )
		hs.Add( self.numberOfRaces, flag=wx.ALIGN_CENTER_VERTICAL )
		hs.AddStretchSpacer()
		self.copyAllocationButton = wx.Button( self, label='Copy allocation' )
		self.copyAllocationButton.SetToolTip( wx.ToolTip('Copy the race allocations from another round'))
		self.copyAllocationButton.Bind( wx.EVT_BUTTON, self.copyAllocation )
		hs.Add( self.copyAllocationButton, flag=wx.ALIGN_CENTER_VERTICAL )
		self.writeSignonButton = wx.Button( self, label='Write sign-on sheet')
		self.writeSignonButton.Bind( wx.EVT_BUTTON, self.writeSignonSheet )
		hs.AddStretchSpacer()
		hs.Add( self.writeSignonButton,  flag=wx.ALIGN_CENTER_VERTICAL )
		hs.AddStretchSpacer()
		self.showDetails = wx.CheckBox( self, label='Show machine/category details' )
		self.showDetails.Bind( wx.EVT_CHECKBOX, self.onShowDetails )
		hs.Add( self.showDetails, flag=wx.ALIGN_CENTER_VERTICAL )

		vs.Add( hs, flag=wx.EXPAND )
		vs.AddStretchSpacer()
		
		hs = wx.BoxSizer( wx.HORIZONTAL )
		hs.AddStretchSpacer()
		for i in range(RaceAllocation.maxRaces):
			raceSizer = wx.BoxSizer( wx.VERTICAL )
			setattr(self, 'raceGridTitle' + str(i), wx.StaticText(self, label='Race ' + str(i+1)) )
			getattr(self, 'raceGridTitle' + str(i), None).SetFont( boldFont )
			setattr(self, 'raceGrid' + str(i), wx.grid.Grid( self ) )
			getattr(self, 'raceGrid' + str(i), None).CreateGrid(0, len(self.colnames) )
			for col, name in enumerate(self.colnames):
				getattr(self, 'raceGrid' + str(i), None).SetColLabelValue(col, name)
			getattr(self, 'raceGrid' + str(i), None).HideRowLabels()
			getattr(self, 'raceGrid' + str(i), None).SetRowLabelSize( 0 )
			getattr(self, 'raceGrid' + str(i), None).SetMargins( 0, 0 )
			getattr(self, 'raceGrid' + str(i), None).AutoSizeColumns( True )
			getattr(self, 'raceGrid' + str(i), None).DisableDragColSize()
			getattr(self, 'raceGrid' + str(i), None).DisableDragRowSize()
			getattr(self, 'raceGrid' + str(i), None).EnableEditing(False)
			getattr(self, 'raceGrid' + str(i), None).SetSelectionMode(wx.grid.Grid.GridSelectRows)
			getattr(self, 'raceGrid' + str(i), None).Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, lambda event, race=i: self.onRacerRightClick(event, race) )
			raceSizer.Add( getattr(self, 'raceGridTitle' + str(i), None), flag=wx.ALIGN_CENTRE )
			raceSizer.Add( getattr(self, 'raceGrid' + str(i), None), flag=wx.ALIGN_CENTRE )
			hs.Add( raceSizer, flag=wx.EXPAND )
			hs.AddStretchSpacer()
			self.installGridHint( getattr(self, 'raceGrid' + str(i), None), self.getGridToolTip )
			getattr(self, 'raceGrid' + str(i), None).Hide()
			getattr(self, 'raceGridTitle' + str(i), None).Hide()
		vs.Add( hs, flag=wx.EXPAND )
		vs.AddStretchSpacer()
		
		self.SetDoubleBuffered( True )
		self.SetSizer(vs)
		vs.SetSizeHints(self)
		
	def getGridToolTip( self, grid, row, col ):
		if not self.showDetails.IsChecked():
			text = '\"' + grid.GetCellValue(row, 2) + '\": ' + grid.GetCellValue(row, 3)
			return text
		else:
			return None
		
	def installGridHint(self, grid, rowcolhintcallback):
		prev_rowcol = [None,None]
		def OnMouseMotion(evt):
			# evt.GetRow() and evt.GetCol() would be nice to have here,
			# but as this is a mouse event, not a grid event, they are not
			# available and we need to compute them by hand.
			x, y = grid.CalcUnscrolledPosition(evt.GetPosition())
			row = grid.YToRow(y)
			col = grid.XToCol(x)

			if (row,col) != prev_rowcol and row >= 0 and col >= 0:
				prev_rowcol[:] = [row,col]
				hinttext = rowcolhintcallback(grid, row, col)
				if hinttext is None:
					hinttext = ''
				grid.GetGridWindow().SetToolTip( wx.ToolTip(hinttext) )
			evt.Skip()
		grid.GetGridWindow().Bind( wx.EVT_MOTION, OnMouseMotion)
		
	def onShowDetails( self, event):
		config = Utils.getMainWin().config
		config.WriteBool( 'raceAllocationShowDetails', self.showDetails.GetValue() )
		config.Flush()
		self.refreshRaceTables()
		
	def onRacerRightClick( self, event, race ):
		row = event.GetRow()
		col = event.GetCol()
		try:
			bib = int(getattr(self, 'raceGrid' + str(race), None).GetCellValue(row, 0))
			name = getattr(self, 'raceGrid' + str(race), None).GetCellValue(row, 1)
		except:
			return
		menu = wx.Menu()
		menu.SetTitle('#' + str(bib) + ' ' + name)
		if race < self.nrRaces - 1:
			right = menu.Append( wx.ID_ANY, 'Move to next  ->', 'Move rider to next race...' )
			self.Bind( wx.EVT_MENU, lambda event: self.moveRacerToNextRace(event, bib, race), right )
		if race > 0:
			left = menu.Append( wx.ID_ANY, '<-  Move to previous', 'Move rider to previous race...' )
			self.Bind( wx.EVT_MENU, lambda event: self.moveRacerToPreviousRace(event, bib, race), left )
		editMachine = menu.Append( wx.ID_ANY, 'Change machine', 'Change machine for this race only...' )
		self.Bind( wx.EVT_MENU, lambda event: self.editRacerMachine(event, bib, race), editMachine )
		editCategories = menu.Append( wx.ID_ANY, 'Change categories', 'Change categories for this race only...' )
		self.Bind( wx.EVT_MENU, lambda event: self.editRacerCategories(event, bib, race), editCategories )
		try:
			self.PopupMenu( menu )
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
			
	def moveRacerToNextRace( self, event, bib, iRace ):
		database = Model.database
		if database is None:
			return
		if self.season is not None and self.evt is not None and self.rnd is not None:
			try:
				with Model.LockDatabase() as db:
					seasonName = db.getSeasonsList()[self.season]
					season = db.seasons[seasonName]
					evtName = list(season['events'])[self.evt]
					evt = season['events'][evtName]
					rndName = list(evt['rounds'])[self.rnd]
					rnd = evt['rounds'][rndName]
					race = rnd['races'][iRace]
					newRace = rnd['races'][iRace+1]
					for raceEntryDict in race:
						if raceEntryDict['bib'] == bib:
							race.remove(raceEntryDict)
							newRace.append(raceEntryDict)
							db.setChanged()
							break
				if bib in self.unallocatedBibs:
					self.unallocatedBibs.remove(bib)
				self.refreshRaceTables()
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
		
	def moveRacerToPreviousRace( self, event, bib, iRace ):
		database = Model.database
		if database is None:
			return
		if self.season is not None and self.evt is not None and self.rnd is not None:
			try:
				with Model.LockDatabase() as db:
					seasonName = db.getSeasonsList()[self.season]
					season = db.seasons[seasonName]
					evtName = list(season['events'])[self.evt]
					evt = season['events'][evtName]
					rndName = list(evt['rounds'])[self.rnd]
					rnd = evt['rounds'][rndName]
					race = rnd['races'][iRace]
					newRace = rnd['races'][iRace-1]
					for raceEntryDict in race:
						if raceEntryDict['bib'] == bib:
							race.remove(raceEntryDict)
							newRace.append(raceEntryDict)
							db.setChanged()
							break
				if bib in self.unallocatedBibs:
					self.unallocatedBibs.remove(bib)
				self.refreshRaceTables()
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
				
	def onChooseRound( self, event ):
		self.rnd = self.chooseRound.GetSelection()
		with Model.LockDatabase() as db:
			db.curRnd = self.rnd
			db.setChanged()
		wx.CallAfter( self.refresh )
		
	def copyAllocation( self, event ):
		database = Model.database
		if database is None:
			return
		if self.season is not None and self.evt is not None and self.rnd is not None:
			try:
				seasonName = database.getSeasonsList()[self.season]
				season = database.seasons[seasonName]
				evtName = list(season['events'])[self.evt]
				evt = season['events'][evtName]
				rndName = list(evt['rounds'])[self.rnd]
				rnd = evt['rounds'][rndName]
				choices = list(evt['rounds'])
				del choices[self.rnd]  # remove current round from list
				with wx.SingleChoiceDialog(self, 'Select round to copy allocations from', 'Copy allocation', choices ) as dlg:
					if dlg.ShowModal() == wx.ID_OK:
						sourceRound = dlg.GetStringSelection()
						if self.season is not None and self.evt is not None and self.rnd is not None:
							with Model.LockDatabase() as db:
								season = db.seasons[seasonName]
								evt = season['events'][evtName]
								rnd = evt['rounds'][rndName]
								# delete all races from current round
								rnd['races'].clear()
								# copy the allocations
								for sourceRace in evt['rounds'][sourceRound]:
									rnd['races'].append(sourceRace)
								db.setChanged()
							Utils.writeLog( 'copyAllocation: Copied race allocation in event "' + evtName + '" from round "' + sourceRound + '" to round "' + rndName + '"' )
							wx.CallAfter( self.refresh )
			except Exception as e:
					Utils.logException( e, sys.exc_info() )
					
	def writeSignonSheet( self, event ):
		Utils.getMainWin().events.writeSignonSheet()
	
	def editRacerMachine( self, event, bib, iRace ):
		database = Model.database
		if database is None:
			return
		if self.season is not None and self.evt is not None and self.rnd is not None:
			try:
				with Model.LockDatabase() as db:
					seasonName = db.getSeasonsList()[self.season]
					season = db.seasons[seasonName]
					evtName = list(season['events'])[self.evt]
					evt = season['events'][evtName]
					rndName = list(evt['rounds'])[self.rnd]
					rnd = evt['rounds'][rndName]
					race = rnd['races'][iRace]
					rider = database.getRider(bib)
					machineChoices = ['[Enter New]']
					if 'Machines' in rider:
						for machineCategories in rider['Machines']:
							machineChoices.append(machineCategories[0])
					with wx.SingleChoiceDialog(self, 'Select machine for #' + str(bib) + ' ' + database.getRiderName(bib, True) + ' in race ' + str(iRace+1), 'Change machine', machineChoices ) as dlg:
						if dlg.ShowModal() == wx.ID_OK:
							if dlg.GetSelection() == 0: #enter new
								with wx.TextEntryDialog(self, 'Enter the name for the new machine:', caption='Change machine', value='', style=wx.OK|wx.CANCEL) as entryDlg:
									if entryDlg.ShowModal() == wx.ID_OK:
										newMachine = entryDlg.GetValue()
										if 'Machines' not in db.riders[bib]:
											db.riders[bib]['Machines'] = []
										found = False
										for machineCategories in db.riders[bib]['Machines']:
											if newMachine == machineCategories[0]:
												found = True
												break
										if not found:
											db.riders[bib]['Machines'].append((newMachine, []))
									else:
										return
							else: #selected from list
								newMachine = dlg.GetStringSelection()
							for raceEntryDict in race:
								if raceEntryDict['bib'] == bib:
									raceEntryDict['machine'] = newMachine
									db.setChanged()
									break
				self.refreshRaceTables()
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
		
	def editRacerCategories( self, event, bib, iRace ):
		database = Model.database
		if database is None:
			return
		if self.season is not None and self.evt is not None and self.rnd is not None:
			try:
				with Model.LockDatabase() as db:
					seasonName = db.getSeasonsList()[self.season]
					season = db.seasons[seasonName]
					evtName = list(season['events'])[self.evt]
					evt = season['events'][evtName]
					rndName = list(evt['rounds'])[self.rnd]
					rnd = evt['rounds'][rndName]
					race = rnd['races'][iRace]
					rider = database.getRider(bib)
					evtRacersDict = {}
					if 'racers' in evt:
						for bibMachineCategoriesTeam in evt['racers']:
							evtRacersDict[bibMachineCategoriesTeam[0]] = (bibMachineCategoriesTeam[1], bibMachineCategoriesTeam[2])
					editCategories = None
					for raceEntryDict in race:
						if raceEntryDict['bib'] == bib:
							editedCategories = raceEntryDict['categories'] if 'categories' in raceEntryDict else None
					catChoices = []
					catSelectedOrig = []
					catSelected = []
					#get the original categories for the event
					if 'categories' in season:
						if season['categories']:  
							iCategory = 0
							for categoryAbbrev in season['categories']:
								catChoices.append(categoryAbbrev[0])
								#check for previous change
								if editedCategories is not None:
									if categoryAbbrev[0] in editedCategories:
										catSelected.append(iCategory)
								elif categoryAbbrev[0] in evtRacersDict[bib][1]:
									catSelected.append(iCategory)
								#get the event categories
								if categoryAbbrev[0] in evtRacersDict[bib][1]:
									catSelectedOrig.append(iCategory)
								iCategory += 1
						else:
							Utils.writeLog('editRacerCategories: Zero-length categories in ' + seasonName)
						with wx.MultiChoiceDialog(self, 'Select categories', 'Change categories', catChoices) as dlg:
							dlg.SetSelections(catSelected)
							if dlg.ShowModal() == wx.ID_OK:
								newSelections = dlg.GetSelections()
								if newSelections == catSelectedOrig:
									Utils.writeLog('editRacerCategories: Reverting #' + str(bib) + '\'s categories to event default')
									for raceEntryDict in race:
										if raceEntryDict['bib'] == bib:
											del raceEntryDict['categories']
											db.setChanged()
											self.refreshRaceTables()
									return
								if newSelections == catSelected:
									Utils.writeLog('editRacerCategories: No change to #' + str(bib) + '\'s categories')
									return
								iChoice = 0
								selectedCategories = []
								for category in catChoices:
									if iChoice in newSelections:
										selectedCategories.append(category)
									iChoice += 1
								# for bibMachineCategories in race:
								# 	if bibMachineCategories[0] == bib:
								# 		race.remove(bibMachineCategories)
								# 		race.append([bibMachineCategories[0], bibMachineCategories[1], selectedCategories])
								for raceEntryDict in race:
									if raceEntryDict['bib'] == bib:
										raceEntryDict['categories'] = selectedCategories
										db.setChanged()
										break
					else:
						Utils.writeLog('editRacerCategories: No categories in ' + seasonName)
				self.refreshRaceTables()
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
		
	def onChangeNumberOfRaces( self, event ):
		database = Model.database
		if database is None:
			return
		if self.numberOfRaces.GetValue() != self.nrRaces:
			if not Utils.MessageOKCancel( self, 'Are you sure you want to change the number of races?\nExisting race allocations will be lost!', title='Change number of races', iconMask=wx.ICON_QUESTION):
				self.numberOfRaces.SetValue(self.nrRaces)
				return
			self.nrRaces = self.numberOfRaces.GetValue()
			if self.season is not None and self.evt is not None and self.rnd is not None:
				try:
					with Model.LockDatabase() as db:
						seasonName = db.getSeasonsList()[self.season]
						season = db.seasons[seasonName]
						evtName = list(season['events'])[self.evt]
						evt = season['events'][evtName]
						rndName = list(evt['rounds'])[self.rnd]
						rnd = evt['rounds'][rndName]
						if 'races' not in rnd:
							rnd['races'] = []
						curLen = len(rnd['races'])
						if curLen < self.nrRaces:
							for i in range(self.nrRaces - curLen):
								rnd['races'].append([])
						elif curLen > self.nrRaces:
							for i in range(curLen - self.nrRaces):
								rnd['races'].pop()
						db.setChanged()
					self.addUnallocatedRiders()
					self.refreshRaceTables()
				except Exception as e:
					Utils.logException( e, sys.exc_info() )
			self.refreshNumberOfRaces()
	
	def addUnallocatedRiders( self ):
		for i in range(RaceAllocation.maxRaces):
			self.clearGrid( getattr(self, 'raceGrid' + str(i), None) )
		database = Model.database
		if database is None:
			return
		try:
			seasonName = database.getSeasonsList()[self.season]
			season = database.seasons[seasonName]
			evtName = list(season['events'])[self.evt]
			evt = season['events'][evtName]
			rndName = list(evt['rounds'])[self.rnd]
			rnd = evt['rounds'][rndName]
			allocatedBibs = []
			if 'races' in rnd:
				for race in rnd['races']:  # first pass to see what's allocated
					for raceEntryDict in race:
						allocatedBibs.append(raceEntryDict['bib'])
			self.unallocatedBibs.clear()
			enteredBibs = []
			if 'racers' in evt: # build list of unallocated riders
				for bibMachineCategoriesTeam in sorted(evt['racers']):
					enteredBibs.append(bibMachineCategoriesTeam[0])
					if bibMachineCategoriesTeam[0] not in allocatedBibs:
						self.unallocatedBibs.append(bibMachineCategoriesTeam[0])
			missingBibs = [bib for bib in allocatedBibs if bib not in enteredBibs]
			with Model.LockDatabase() as db:
					seasonName = db.getSeasonsList()[self.season]
					season = db.seasons[seasonName]
					evtName = list(season['events'])[self.evt]
					evt = season['events'][evtName]
					rndName = list(evt['rounds'])[self.rnd]
					rnd = evt['rounds'][rndName]
					# remove racers from the race who are not in the event
					if len(missingBibs) > 0:
						iRace = 0
						for race in rnd['races']:
							for raceEntryDict in race:
								if raceEntryDict['bib'] in missingBibs:
									Utils.writeLog( 'addUnallocatedRiders: #' + str(raceEntryDict['bib']) + ' "' + database.getRiderName(raceEntryDict['bib'], True) + '" in race ' + str(iRace+1) + ' but not in event "' + evtName + '"!  Removing rider from race.' )
							iRace += 1
						db.setChanged()
					# now add the unallocated racers to the first race
					if len(self.unallocatedBibs) > 0:
						if len(rnd['races']) > 0:
							race = rnd['races'][0] # first race
							for bib in self.unallocatedBibs:
								Utils.writeLog( 'addUnallocatedRiders: #' + str(bib) + ' "' + database.getRiderName(bib, True) + '" in event "' + evtName + '" but not in any race, allocating them to race 1.' )
								race.append({'bib': bib})
							db.setChanged()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
			
	def refreshRaceTables( self, event=None ):
		for i in range(RaceAllocation.maxRaces):
			self.clearGrid( getattr(self, 'raceGrid' + str(i), None) )
		database = Model.database
		if database is None:
			return
		if self.season is not None and self.evt is not None and self.rnd is not None:
			try:
				seasonName = database.getSeasonsList()[self.season]
				season = database.seasons[seasonName]
				evtName = list(season['events'])[self.evt]
				evt = season['events'][evtName]
				rndName = list(evt['rounds'])[self.rnd]
				rnd = evt['rounds'][rndName]
				evtRacersDict = {}
				if 'racers' in evt:
					for bibMachineCategoriesTeam in evt['racers']:
						evtRacersDict[bibMachineCategoriesTeam[0]] = (bibMachineCategoriesTeam[1], bibMachineCategoriesTeam[2])
				iRace = 0
				deletedRiders = []
				totalRacers = 0
				if 'races' in rnd:
					for race in rnd['races']:
						for raceEntryDict in sorted(race, key=lambda raceEntryDict: raceEntryDict['bib']):
							if raceEntryDict['bib'] in evtRacersDict:
								eventsMachineCategories = evtRacersDict[raceEntryDict['bib']]
								getattr(self, 'raceGrid' + str(iRace), None).AppendRows(1)
								row = getattr(self, 'raceGrid' + str(iRace), None).GetNumberRows() -1
								col = 0
								getattr(self, 'raceGrid' + str(iRace), None).SetCellValue(row, col, str(raceEntryDict['bib']))
								getattr(self, 'raceGrid' + str(iRace), None).SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
								col += 1
								getattr(self, 'raceGrid' + str(iRace), None).SetCellValue(row, col, database.getRiderName(raceEntryDict['bib']) if database.isRider(raceEntryDict['bib']) else '[DELETED RIDER]' )
								col += 1
								getattr(self, 'raceGrid' + str(iRace), None).SetCellValue(row, col, str(database.getRiderFactor(raceEntryDict['bib'])) if database.getRiderFactor(raceEntryDict['bib']) is not None else '' )
								getattr(self, 'raceGrid' + str(iRace), None).SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
								col += 1
								if 'machine' not in raceEntryDict or raceEntryDict['machine'] is None:
									# machine has not been changed from event default
									getattr(self, 'raceGrid' + str(iRace), None).SetCellValue(row, col, str(eventsMachineCategories[0]))
									getattr(self, 'raceGrid' + str(iRace), None).SetCellBackgroundColour(row, col, self.whiteColour)
								else:
									getattr(self, 'raceGrid' + str(iRace), None).SetCellValue(row, col, str(raceEntryDict['machine']))
									getattr(self, 'raceGrid' + str(iRace), None).SetCellBackgroundColour(row, col, self.orangeColour)
								col += 1
								if 'categories' not in raceEntryDict or raceEntryDict['categories'] is None:
									# categories have not been changed from event default
									getattr(self, 'raceGrid' + str(iRace), None).SetCellValue(row, col, ','.join(database.getAbbreviatedCategory(c) for c in eventsMachineCategories[1]))
									getattr(self, 'raceGrid' + str(iRace), None).SetCellBackgroundColour(row, col, self.whiteColour)
								else:
									getattr(self, 'raceGrid' + str(iRace), None).SetCellValue(row, col, ','.join(database.getAbbreviatedCategory(c) for c in raceEntryDict['categories']))
									getattr(self, 'raceGrid' + str(iRace), None).SetCellBackgroundColour(row, col, self.orangeColour)
								col += 1
								if not database.isRider(raceEntryDict['bib']):
									deletedRiders.append(raceEntryDict['bib'])
									for c in range(col):
										getattr(self, 'raceGrid' + str(iRace), None).SetCellBackgroundColour(row, c, self.lightBlueColour)
								if raceEntryDict['bib'] in self.unallocatedBibs:
									for c in range(col):
										getattr(self, 'raceGrid' + str(iRace), None).SetCellBackgroundColour(row, c, self.yellowColour)
							else:
								Utils.writeLog( 'refreshRaceTables: Bib #' + str(raceEntryDict['bib']) + ' in race ' + str(iRace) + ' but not in event, skipping.' )
						nrRacers = getattr(self, 'raceGrid' + str(iRace), None).GetNumberRows()
						getattr(self, 'raceGridTitle' + str(iRace), None).SetLabel('Race ' + str(iRace + 1) + ' (' + str(nrRacers) + ' racers)')
						totalRacers += nrRacers
						if self.showDetails.IsChecked():
							if database.useFactors:
								getattr(self, 'raceGrid' + str(iRace), None).ShowCol(2)
							else:
								getattr(self, 'raceGrid' + str(iRace), None).HideCol(2)
							getattr(self, 'raceGrid' + str(iRace), None).ShowCol(3)
							getattr(self, 'raceGrid' + str(iRace), None).ShowCol(4)
						else:
							getattr(self, 'raceGrid' + str(iRace), None).HideCol(2)
							getattr(self, 'raceGrid' + str(iRace), None).HideCol(3)
							getattr(self, 'raceGrid' + str(iRace), None).HideCol(4)
						getattr(self, 'raceGrid' + str(iRace), None).AutoSize()
						iRace += 1
				self.totalRacers.SetLabel(' (' + str(totalRacers) + ' racers)')
				self.Layout()
				if len(deletedRiders) > 0:
					Utils.writeLog('Racer(s): ' + ', '.join([str(r) for r in deletedRiders if r]) + ' do not exist in Riders database!')
					Utils.MessageOK( self, 'Racer(s) do not exist in Riders database:\n' + ', '.join([str(r) for r in deletedRiders if r]) + '\nThey will not be added to the sign-on sheet.', 'Riders do not exist')
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
		else:
			for iRace in range(RaceAllocation.maxRaces):
				getattr(self, 'raceGridTitle' + str(iRace), None).SetLabel('Race ' + str(iRace + 1))
		
	def refreshNumberOfRaces( self ):
		self.numberOfRaces.SetValue(self.nrRaces)
		for i in range(self.nrRaces):
			getattr(self, 'raceGrid' + str(i), None).Show()
			getattr(self, 'raceGridTitle' + str(i), None).Show()
		for i in range(self.nrRaces, RaceAllocation.maxRaces):
			getattr(self, 'raceGrid' + str(i), None).Hide()
			getattr(self, 'raceGridTitle' + str(i), None).Hide()
		self.Layout()
		
	def refreshCurrentSelection( self ):
		database = Model.database
		if database is None:
			return
		selection = []
		title = 'No round selected'
		if self.season is not None and self.evt is not None:
			seasonName = database.getSeasonsList()[self.season]
			selection.append( seasonName )
			season = database.seasons[seasonName]
			evtName = list(season['events'])[self.evt]
			selection.append( evtName )
			title = ', '.join(n for n in selection)
		self.currentSelection.SetLabel( title + ', ' )
		database.selection = selection
		
	def clearGrid( self, grid ):
		if grid is None:
			return
		rows = grid.GetNumberRows()
		#print('clearGrid deleting rows: ' + str(rows))
		if rows:
			grid.DeleteRows( 0, rows )

	def commit( self, event=None ):
		Utils.writeLog('RaceAllocation commit: ' + str(event))
		if event: #called by button
			wx.CallAfter( self.refresh )
	
	def refresh( self, event=None ):
		Utils.writeLog('RaceAllocation refresh')
		database = Model.database
		if database is None:
			return
		try:
			config = Utils.getMainWin().config
			#get current selection
			self.season = database.curSeason
			self.evt = database.curEvt
			self.rnd = database.curRnd
			self.refreshCurrentSelection()
			self.chooseRound.Clear()
			#number of races
			if self.season is not None and self.evt is not None:
				seasonName = database.getSeasonsList()[self.season]
				season = database.seasons[seasonName]
				evtName = list(season['events'])[self.evt]
				evt = season['events'][evtName]
				#enable button if we have a sign-on sheet
				if 'signonFileName' in evt:
					if evt['signonFileName']:
						self.writeSignonButton.Enable()
						self.writeSignonButton.SetToolTip( wx.ToolTip('Click to write the sign-on sheet for the selected event to disk'))
					else:
						self.writeSignonButton.Disable()
						self.writeSignonButton.SetToolTip( wx.ToolTip('Sign-on sheet filename is empty!'))
				else:
					self.writeSignonButton.Disable()
					self.writeSignonButton.SetToolTip( wx.ToolTip('Sign-on sheet filename is not set!'))
				#update round choice
				rounds = list(evt['rounds'])
				self.chooseRound.AppendItems( rounds  )
				self.chooseRound.SetSelection(self.rnd if self.rnd is not None else wx.NOT_FOUND)
				if self.rnd is not None:
					#update tables
					rndName = list(evt['rounds'])[self.rnd]
					rnd = evt['rounds'][rndName]
					self.nrRaces = len(rnd['races']) if 'races' in rnd else 0
					self.numberOfRaces.ChangeValue(self.nrRaces)
					self.showDetails.SetValue( config.ReadBool('raceAllocationShowDetails') )
					self.refreshNumberOfRaces()
					#process unallocated/missing Riders
					self.addUnallocatedRiders()
			self.refreshRaceTables()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
			self.nrRaces = 0
		self.Layout()
